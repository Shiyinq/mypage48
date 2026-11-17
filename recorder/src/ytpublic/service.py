"""Standalone title-based publisher.

Existing record/upload/Drive workers are untouched.
"""

import asyncio
import logging
import random
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import partial

from ..process_lock import process_lock
from .client import (
    APIRequestError,
    AuthorizationError,
    QuotaExceededError,
    YouTubeClient,
)
from .policy import evaluate_video
from .state import VIDEO_ID, DailyLimitError, PublicationState, SpacingError, StateError

log = logging.getLogger("ytpublic")


class StopRequested(Exception):
    pass


class YTPublicService:
    def __init__(self, config, *, client=None, state=None, clock=None):
        self.config = config
        self.client = client
        self.state = state
        self.clock = clock if clock is not None else time.time
        self.stop_event = None
        self._executor = None
        self._channel = None
        self._catalog = None
        self._messages = {}
        self._paused = False
        self._retry_after = 0

    def _now(self):
        return datetime.fromtimestamp(self.clock(), timezone.utc)

    def _stopped(self):
        return self.stop_event is not None and self.stop_event.is_set()

    async def _call(self, method, *args, **kwargs):
        if self._stopped():
            raise StopRequested()
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="ytpublic"
            )
        return await asyncio.get_running_loop().run_in_executor(
            self._executor, partial(method, *args, **kwargs)
        )

    async def close(self):
        if self._executor is not None:
            if self.client is not None and callable(
                getattr(self.client, "close", None)
            ):
                # Cleanup must still run after stop_event is set, on the owner thread.
                await asyncio.get_running_loop().run_in_executor(
                    self._executor, self.client.close
                )
            self._executor.shutdown(wait=True)
            self._executor = None

    async def run(self, stop_event):
        self.stop_event = stop_event
        with process_lock(self.config.logs_dir, "ytpublic"):
            if not self.config.ytpublic_enabled:
                log.info("ytpublic IDLE: worker disabled")
                await stop_event.wait()
                return
            failures = 0
            try:
                while not stop_event.is_set():
                    try:
                        if self._paused:
                            await stop_event.wait()
                            break
                        if self.clock() >= self._retry_after:
                            await self.scan_once()
                            failures = 0
                    except StopRequested:
                        break
                    except AuthorizationError:
                        self._paused = True
                        log.critical(
                            "ytpublic authorization invalid; processing paused until "
                            "credentials are corrected and the ytpublic service "
                            "is restarted"
                        )
                        continue
                    except DailyLimitError as exc:
                        self._retry_after = exc.reset_at
                        self._log_limit(exc)
                    except QuotaExceededError:
                        self.state.mark_quota_exhausted()
                        self._retry_after = self.state.status()["reset_at"]
                        log.warning(
                            "ytpublic daily API quota exhausted; paused until %s",
                            self._stamp(self._retry_after),
                        )
                    except SpacingError as exc:
                        self._retry_after = exc.deadline
                        log.info(
                            "ytpublic WAIT: update spacing until %s",
                            self._stamp(exc.deadline),
                        )
                    except StateError as exc:
                        self._paused = True
                        log.critical(
                            "ytpublic state/safety error; paused for manual review: %s",
                            exc,
                        )
                        continue
                    except Exception as exc:
                        failures += 1
                        delay = min(
                            900, 15 * 2 ** min(failures - 1, 6)
                        ) + random.uniform(0, 5)
                        self._retry_after = self.clock() + delay
                        detail = (
                            str(exc)
                            if isinstance(exc, APIRequestError)
                            else type(exc).__name__
                        )
                        log.error(
                            "ytpublic scan failed (%s); retry in %.1fs", detail, delay
                        )
                    delay = (
                        max(0, self._retry_after - self.clock())
                        if self._retry_after
                        else self.config.ytpublic_poll_interval
                    )
                    if delay <= 0:
                        delay = self.config.ytpublic_poll_interval
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=delay)
                    except asyncio.TimeoutError:
                        pass
            finally:
                await self.close()

    @staticmethod
    def _stamp(value):
        return datetime.fromtimestamp(value, timezone.utc).isoformat()

    def _log_limit(self, exc):
        usage = self.state.status()
        log.info(
            "ytpublic WAIT: %s; updates=%d/%d; estimated_units=%d/%d; "
            "next Pacific reset=%s",
            exc.kind,
            usage["update_attempts"],
            self.config.ytpublic_max_updates_per_day,
            usage["used_units"],
            self.config.ytpublic_daily_quota_budget,
            self._stamp(exc.reset_at),
        )

    async def _initialize(self):
        # Validate exclusions before making an external request.
        try:
            self.config.ytpublic_excluded_video_ids
        except ValueError as exc:
            raise StateError("Invalid ytpublic exclusion configuration") from exc
        if self.state is None:
            self.state = PublicationState(self.config, clock=self.clock)
        usage = self.state.status()
        if usage["quota_pause_until"] > self.clock():
            raise DailyLimitError("quota_pause", usage["reset_at"])
        if usage["used_units"] >= self.config.ytpublic_daily_quota_budget:
            raise DailyLimitError("quota_budget", usage["reset_at"])
        if (
            not self.config.ytpublic_dry_run
            and usage["update_attempts"] >= self.config.ytpublic_max_updates_per_day
        ):
            raise DailyLimitError("update_attempts", usage["reset_at"])
        if self.client is None:
            self.client = await self._call(
                YouTubeClient.from_config, self.config, self.state
            )
        if self._channel is None:
            channel = await self._call(self.client.discover_channel)
            catalog = self.state.load_catalog()
            if catalog and (
                catalog.get("channel_id") != channel["channel_id"]
                or catalog.get("playlist_id") != channel["playlist_id"]
            ):
                raise StateError(
                    "Authorized channel differs from persisted ytpublic catalog"
                )
            if not catalog:
                catalog = {
                    **channel,
                    "videos": {},
                    "known_ids": [],
                    "full_scan_complete": False,
                    "page_token": None,
                    "seen_tokens": [],
                    "head_token": None,
                    "head_seen_tokens": [],
                    "refresh_cursor": 0,
                }
            self._validate_catalog(catalog)
            self._channel, self._catalog = channel, catalog

    @staticmethod
    def _validate_catalog(catalog):
        if (
            not isinstance(catalog.get("videos"), dict)
            or not isinstance(catalog.get("known_ids"), list)
            or any(
                not isinstance(value, str) or VIDEO_ID.fullmatch(value) is None
                for value in catalog["known_ids"]
            )
            or type(catalog.get("full_scan_complete")) is not bool
            or type(catalog.get("refresh_cursor")) is not int
            or catalog["refresh_cursor"] < 0
        ):
            raise StateError("Invalid ytpublic catalog")
        for field in ("page_token", "head_token"):
            if catalog.get(field) is not None and not isinstance(catalog[field], str):
                raise StateError("Invalid catalog pagination token")
        for field in ("seen_tokens", "head_seen_tokens"):
            values = catalog.get(field)
            if not isinstance(values, list) or any(
                not isinstance(value, str) for value in values
            ):
                raise StateError("Invalid catalog pagination history")
        for key, video in catalog["videos"].items():
            if not isinstance(video, dict) or video.get("id") != key:
                raise StateError("Invalid cached video resource")

    def _save_catalog(self):
        self.state.save_catalog(self._catalog)

    async def _refresh(self, ids):
        if not ids:
            return
        videos = await self._call(self.client.get_videos, ids)
        for video_id in ids:
            self._catalog["videos"].pop(video_id, None)
        for video in videos:
            if video.get("snippet", {}).get("channelId") != self._channel["channel_id"]:
                raise StateError("Cached video channel mismatch")
            self._catalog["videos"][video["id"]] = video

    async def _discover(self):
        catalog = self._catalog
        was_complete = catalog["full_scan_complete"]
        token_field = "head_token" if was_complete else "page_token"
        seen_field = "head_seen_tokens" if was_complete else "seen_tokens"
        known = set(catalog["known_ids"])
        while not self._stopped():
            token = catalog[token_field]
            page = await self._call(
                self.client.list_upload_page, catalog["playlist_id"], token
            )
            ids = page["ids"]
            new_ids = [value for value in ids if value not in known]
            await self._refresh(new_ids if was_complete else ids)
            had_known = any(value in known for value in ids)
            known.update(ids)
            catalog["known_ids"] = sorted(known)
            next_token = page["next_page_token"]
            if next_token and (
                next_token == token or next_token in catalog[seen_field]
            ):
                raise StateError("Repeated YouTube uploads pagination token")
            if token is not None:
                catalog[seen_field].append(token)
            if next_token is None or (was_complete and had_known):
                catalog[token_field] = None
                catalog[seen_field] = []
                catalog["full_scan_complete"] = True
                self._save_catalog()
                break
            catalog[token_field] = next_token
            self._save_catalog()
        if self._stopped():
            raise StopRequested()
        # Rotate one status batch per poll; do not re-read a large channel in full
        # every 15 minutes. Due candidates always get another fresh read below.
        if was_complete and catalog["known_ids"]:
            ids = catalog["known_ids"]
            start = catalog["refresh_cursor"] % len(ids)
            batch = (ids[start:] + ids[:start])[:50]
            await self._refresh(batch)
            catalog["refresh_cursor"] = (start + len(batch)) % len(ids)
            self._save_catalog()

    def _decision(self, video, receipt):
        return evaluate_video(
            video,
            self._now(),
            base_delay_hours=self.config.ytpublic_base_delay_hours,
            buffer_hours=self.config.ytpublic_buffer_hours,
            excluded_ids=self.config.ytpublic_excluded_video_ids,
            already_published=bool(receipt and receipt["status"] == "published"),
        )

    def _log_decision(self, video, decision):
        key = video["id"]
        fingerprint = (
            video.get("snippet", {}).get("title"),
            video.get("status"),
            decision.action,
            decision.reason,
            decision.eligible_at,
        )
        if self._messages.get(key) == fingerprint:
            return
        self._messages[key] = fingerprint
        if decision.action == "wait":
            log.info(
                "ytpublic WAIT: %s; base=%dh; buffer=%dh; eligible_at=%s",
                key,
                self.config.ytpublic_base_delay_hours,
                self.config.ytpublic_buffer_hours,
                decision.eligible_at.isoformat(),
            )
        elif decision.action == "skip":
            log.info("ytpublic SKIP: %s; %s", key, decision.reason)

    async def _spacing(self):
        deadline = self.state.status()["next_update_at"]
        delay = max(0, deadline - self.clock())
        if delay:
            log.info("ytpublic WAIT: %.1fs before next privacy update", delay)
            if self.stop_event is None:
                await asyncio.sleep(delay)
            else:
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=delay)
                    raise StopRequested()
                except asyncio.TimeoutError:
                    pass
        if self._stopped():
            raise StopRequested()

    async def scan_once(self):
        if not self.config.ytpublic_enabled or self._paused or self._stopped():
            return
        await self._initialize()
        log.info("ytpublic SCAN: checking authorized channel videos")
        await self._discover()
        counts = Counter()
        candidates = []
        for video in self._catalog["videos"].values():
            receipt = self.state.read_receipt(video["id"])
            if receipt and receipt.get("channel_id") not in (
                None,
                self._channel["channel_id"],
            ):
                raise StateError("Receipt belongs to another YouTube channel")
            if receipt and receipt["status"] in {"publishing", "needs_reconciliation"}:
                if self.config.ytpublic_dry_run:
                    log.info(
                        "ytpublic DRY-RUN: pending receipt for %s; "
                        "reconciliation skipped",
                        video["id"],
                    )
                else:
                    await self._reconcile(video["id"], receipt)
                counts["reconciliation"] += 1
                continue
            decision = self._decision(video, receipt)
            self._log_decision(video, decision)
            counts[decision.reason] += 1
            if decision.action == "eligible":
                candidates.append((video, decision))

        def order(candidate):
            video, decision = candidate
            stamp = (
                decision.start_at.isoformat()
                if decision.start_at
                else video.get("snippet", {}).get("publishedAt", "")
            )
            return stamp, video["id"]

        candidates.sort(key=order)
        attempts = 0
        for video, decision in candidates:
            if self._stopped():
                raise StopRequested()
            if self.config.ytpublic_dry_run:
                fingerprint = (video.get("snippet", {}).get("title"), decision.rule)
                if self._messages.get((video["id"], "dry_run")) != fingerprint:
                    log.info(
                        "ytpublic DRY-RUN: would publish %s; rule=%s",
                        video["id"],
                        decision.reason,
                    )
                    self._messages[(video["id"], "dry_run")] = fingerprint
                continue
            if attempts >= self.config.ytpublic_max_updates_per_scan:
                break
            usage = self.state.status()
            if usage["update_attempts"] >= self.config.ytpublic_max_updates_per_day:
                raise DailyLimitError("update_attempts", usage["reset_at"])
            await self._spacing()
            # Read after spacing so a manual privacy/title change is respected.
            latest = await self._call(self.client.get_videos, [video["id"]])
            if not latest:
                self._catalog["videos"].pop(video["id"], None)
                self._save_catalog()
                continue
            fresh = latest[0]
            self._catalog["videos"][fresh["id"]] = fresh
            self._save_catalog()
            fresh_decision = self._decision(fresh, self.state.read_receipt(fresh["id"]))
            if fresh_decision.action != "eligible":
                self._log_decision(fresh, fresh_decision)
                continue
            if self._stopped():
                raise StopRequested()
            receipt = self._new_receipt(fresh, fresh_decision)

            def before_update():
                if self._stopped():
                    raise StopRequested()
                self.state.write_receipt(fresh["id"], receipt)

            try:
                result = await self._call(self.client.make_public, fresh, before_update)
            except (DailyLimitError, SpacingError, StopRequested):
                raise
            except Exception:
                # An API response can be lost after the update committed. Never
                # blindly retry a private video following an ambiguous attempt.
                if self.state.read_receipt(fresh["id"]) is not None:
                    receipt["status"] = "needs_reconciliation"
                    self.state.write_receipt(fresh["id"], receipt)
                raise
            attempts += 1
            if (
                result.get("id") != fresh["id"]
                or result.get("status", {}).get("privacyStatus") != "public"
            ):
                receipt["status"] = "needs_reconciliation"
                self.state.write_receipt(fresh["id"], receipt)
                log.error(
                    "ytpublic update unconfirmed: %s; manual reconciliation required",
                    fresh["id"],
                )
                continue
            self._published(fresh["id"], receipt)
            fresh["status"]["privacyStatus"] = "public"
            counts["published"] += 1
            self._save_catalog()
        usage = self.state.status()
        log.info(
            "ytpublic SUMMARY: %s; attempted_this_scan=%d; updates=%d/%d; "
            "estimated_units=%d/%d; reset=%s",
            dict(counts),
            attempts,
            usage["update_attempts"],
            self.config.ytpublic_max_updates_per_day,
            usage["used_units"],
            self.config.ytpublic_daily_quota_budget,
            self._stamp(usage["reset_at"]),
        )
        if not candidates:
            log.info("ytpublic IDLE: no eligible private videos")

    def _new_receipt(self, video, decision):
        return {
            "schema_version": 1,
            "video_id": video["id"],
            "channel_id": self._channel["channel_id"],
            "matched_rule": "idn_delayed"
            if decision.rule == "idn"
            else "showroom_immediate",
            "observed_title": video["snippet"]["title"],
            "parsed_start_at": decision.start_at.isoformat()
            if decision.start_at
            else None,
            "eligible_at": decision.eligible_at.isoformat()
            if decision.eligible_at
            else None,
            "base_delay_hours": self.config.ytpublic_base_delay_hours
            if decision.rule == "idn"
            else None,
            "buffer_hours": self.config.ytpublic_buffer_hours
            if decision.rule == "idn"
            else None,
            "status": "publishing",
            "attempted_at": self._now().isoformat(),
            "published_at": None,
        }

    def _published(self, video_id, receipt):
        receipt.update(status="published", published_at=self._now().isoformat())
        self.state.write_receipt(video_id, receipt)
        log.info("ytpublic PUBLIC: %s; rule=%s", video_id, receipt["matched_rule"])

    async def _reconcile(self, video_id, receipt):
        fresh = await self._call(self.client.get_videos, [video_id])
        if fresh:
            self._catalog["videos"][video_id] = fresh[0]
            self._save_catalog()
        if fresh and fresh[0].get("status", {}).get("privacyStatus") == "public":
            self._published(video_id, receipt)
        else:
            if receipt["status"] != "needs_reconciliation":
                receipt["status"] = "needs_reconciliation"
                self.state.write_receipt(video_id, receipt)
            message_key = (video_id, "reconciliation")
            if message_key not in self._messages:
                log.warning(
                    "ytpublic SKIP: %s; prior update outcome ambiguous; "
                    "manual review required",
                    video_id,
                )
                self._messages[message_key] = True
