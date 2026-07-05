import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.config import Settings
from src.live_history.repository import LiveHistoryRepository
from src.logging_config import create_logger
from src.replay.exceptions import ReplayAlreadyExists, ReplayUploadError
from src.replay.repository import ReplayRepository
from src.replay.schemas import ReplayDetailResponse, ReplayResponse
from src.storage.repository import StorageRepository
from src.storage.service import StorageService

logger = create_logger("replay_service", __name__)


def _parse_jsonl(content: bytes) -> list[dict]:
    lines = content.decode("utf-8", errors="replace").strip().split("\n")
    chats = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            chat = json.loads(line)
            chats.append(chat)
        except json.JSONDecodeError:
            logger.warning(f"Skipping invalid JSONL line: {line[:100]}")
    return chats


def _compute_chat_stats(
    chats: list[dict], platform: str
) -> tuple[list[dict], list[dict], int, int, int, int, int]:
    gift_map: dict[str, dict] = {}
    fan_map: dict[str, dict] = {}
    chat_count = 0
    gift_count = 0
    loveletter_count = 0
    total_gold = 0
    free_gift_count = 0

    for raw in chats:
        if platform == "idn" or not platform:
            user = raw.get("user", {})
            if not isinstance(user, dict) or not user:
                continue

            gift_data = raw.get("gift")
            if gift_data:
                name = gift_data.get("name", "Gift")
                gold = gift_data.get("gold", 0) or 0
                total_gold += gold
                gift_count += 1

                entry = gift_map.setdefault(
                    name, {"count": 0, "total_gold": 0, "image": None}
                )
                entry["count"] += 1
                entry["total_gold"] += gold
                if entry["image"] is None:
                    entry["image"] = (
                        gift_data.get("animation_small")
                        or gift_data.get("animation_small_url")
                        or gift_data.get("animation_large")
                        or gift_data.get("animation_large_url")
                        or gift_data.get("image_url")
                        or gift_data.get("image")
                        or gift_data.get("icon_url")
                        or gift_data.get("icon")
                        or gift_data.get("sticker_url")
                    )

                username = user.get("name", "Unknown")
                avatar = user.get("avatar_url")
                fan_entry = fan_map.setdefault(
                    username, {"total_gold": 0, "count": 0, "avatar": None}
                )
                fan_entry["total_gold"] += gold
                fan_entry["count"] += 1
                if avatar and not fan_entry["avatar"]:
                    fan_entry["avatar"] = avatar
            elif raw.get("letter"):
                loveletter_count += 1
            elif raw.get("chat"):
                chat_count += 1
            elif raw.get("message") or raw.get("text"):
                chat_count += 1

        elif platform == "showroom":
            if raw.get("type") == "gift":
                is_free = raw.get("free") == True
                gift_name = raw.get("gift_name", "Unknown")
                total_point = raw.get("total_point", 0) or 0
                num = raw.get("num", 0)

                if is_free:
                    free_gift_count += num
                else:
                    total_gold += total_point
                    gift_count += num

                entry = gift_map.setdefault(
                    gift_name,
                    {"count": 0, "total_gold": 0, "image": None, "free": None},
                )
                entry["count"] += num
                entry["total_gold"] += total_point
                if entry["image"] is None:
                    entry["image"] = raw.get("image", "")
                if entry["free"] is None:
                    entry["free"] = is_free

                username = raw.get("name", "Unknown")
                avatar = raw.get("avatar_url")
                fan_entry = fan_map.setdefault(
                    username,
                    {
                        "total_gold": 0,
                        "count": 0,
                        "avatar": None,
                        "free_gold": 0,
                        "free_count": 0,
                    },
                )
                if is_free:
                    fan_entry["free_gold"] += total_point
                    fan_entry["free_count"] += num
                else:
                    fan_entry["total_gold"] += total_point
                    fan_entry["count"] += num
                if avatar and not fan_entry["avatar"]:
                    fan_entry["avatar"] = avatar
            else:
                chat_count += 1

    top_gifts = sorted(
        [
            {
                "name": k,
                "count": v["count"],
                "total_gold": v["total_gold"],
                "image": v.get("image"),
                "free": v.get("free"),
            }
            for k, v in gift_map.items()
        ],
        key=lambda x: (x["total_gold"], x["count"]),
        reverse=True,
    )
    top_fans = sorted(
        [
            {
                "user": k,
                "avatar": v["avatar"],
                "total_gold": v["total_gold"],
                "count": v["count"],
                "free_gold": v.get("free_gold", 0),
                "free_count": v.get("free_count", 0),
            }
            for k, v in fan_map.items()
        ],
        key=lambda x: x["total_gold"],
        reverse=True,
    )

    return (
        top_gifts,
        top_fans,
        chat_count,
        gift_count,
        free_gift_count,
        total_gold,
        loveletter_count,
    )


class ReplayService:
    def __init__(
        self,
        repository: ReplayRepository,
        storage_repository: StorageRepository,
        live_history_repo: LiveHistoryRepository,
        config: Settings,
    ):
        self.repository = repository
        self.storage = storage_repository
        self.live_history_repo = live_history_repo
        self.storage_service = StorageService(storage_repository, config)
        self.config = config

    async def upload(
        self,
        live_id: str,
        metadata_bytes: bytes,
        jsonl_bytes: bytes,
        srt_bytes: bytes,
        screenshot_bytes_list: list[tuple[str, bytes]],
        thumbnail_bytes: Optional[bytes] = None,
    ) -> ReplayResponse:
        try:
            metadata = json.loads(metadata_bytes)
        except json.JSONDecodeError as e:
            raise ReplayUploadError(f"Invalid metadata JSON: {e}")

        status = metadata.get("status")
        if status != "completed":
            raise ReplayUploadError(
                f"Cannot upload replay with status '{status}'. "
                "Only 'completed' allowed."
            )

        if await self.repository.exists(live_id):
            logger.warning(f"Replay {live_id} already exists, skipping")
            raise ReplayAlreadyExists(f"Replay {live_id} already exists")

        r2_base = f"replay/{live_id}"

        files = {}
        files["json_file"] = await self._upload_bytes(
            metadata_bytes, f"{r2_base}/{live_id}.json", "application/json"
        )
        if thumbnail_bytes:
            thumbnail_path = f"{r2_base}/{live_id}.webp"
            await self.storage_service.process_and_upload_webp(
                thumbnail_bytes, thumbnail_path
            )
            files["thumbnail"] = thumbnail_path
        else:
            files["thumbnail"] = None
        files["jsonl"] = await self._upload_bytes(
            jsonl_bytes, f"{r2_base}/{live_id}.jsonl", "application/x-ndjson"
        )
        files["srt"] = await self._upload_bytes(
            srt_bytes, f"{r2_base}/{live_id}.srt", "text/plain"
        )

        screenshot_paths = []
        for filename, data in screenshot_bytes_list:
            base, _ = os.path.splitext(filename)
            webp_filename = f"{base}.webp"
            path = f"{r2_base}/screenshots/{webp_filename}"
            await self.storage_service.process_and_upload_webp(data, path)
            screenshot_paths.append(webp_filename)

        chats = _parse_jsonl(jsonl_bytes)

        doc = {
            "live_id": live_id,
            "platform": metadata.get("platform"),
            "room_id": metadata.get("room_id"),
            "room_identifier": metadata.get("room_identifier"),
            "title": metadata.get("title"),
            "member_name": metadata.get("member_name"),
            "member_nickname": metadata.get("member_nickname"),
            "status": status,
            "start_at": metadata.get("start_at"),
            "recording_started_at": metadata.get("recording_started_at"),
            "recording_ended_at": metadata.get("recording_ended_at"),
            "duration_seconds": metadata.get("duration_seconds", 0),
            "srt_file": metadata.get("srt_file"),
            "youtube_id": metadata.get("youtube_id"),
            "youtube_title": metadata.get("youtube_title"),
            "files": {
                "json_file": files["json_file"],
                "thumbnail": files["thumbnail"],
                "jsonl": files["jsonl"],
                "srt": files["srt"],
                "screenshots": screenshot_paths,
            },
            "chats": chats,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        doc_id = await self.repository.insert(doc)
        doc["_id"] = doc_id

        logger.info(
            f"Replay uploaded: {live_id} "
            f"({len(chats)} chats, {len(screenshot_paths)} screenshots)"
        )
        return ReplayResponse(**doc)

    async def _upload_bytes(self, data: bytes, path: str, content_type: str) -> str:
        await self.storage.upload_file(data, path, content_type=content_type)
        return path

    async def find_by_live_id(self, live_id: str) -> Optional[ReplayResponse]:
        doc = await self.repository.find_by_live_id(live_id)
        if doc:
            doc["_id"] = str(doc["_id"])
            return ReplayResponse(**doc)
        return None

    async def get_detail(self, live_id: str) -> Optional[ReplayDetailResponse]:
        doc = await self.repository.find_by_live_id(live_id)
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])

        # Fetch live history data
        lh_doc = await self.live_history_repo.get_global_history_by_live_id(live_id)
        if lh_doc:
            doc["title"] = lh_doc.get("title") or doc.get("title")
            doc["image"] = lh_doc.get("image")
            doc["view_num"] = lh_doc.get("view_num", 0)
            doc["start_at"] = lh_doc.get("start_at") or doc.get("start_at")
            doc["end_at"] = lh_doc.get("end_at")
            doc["last_seen_at"] = lh_doc.get("last_seen_at")
            doc["status"] = lh_doc.get("status", "ended")
            doc["member"] = lh_doc.get("member", {})
            doc["duration"] = lh_doc.get("duration", doc.get("duration_seconds", 0))
            doc["blurHash"] = lh_doc.get("blurHash")

            if doc.get("image") and doc["image"].startswith("live/"):
                variants = await self.storage_service.resolve_image_variants(
                    doc["image"]
                )
                doc["image"] = variants.get("url")
                doc["image_medium"] = variants.get("url_medium")
                doc["image_small"] = variants.get("url_small")
                if variants.get("blurHash") and not doc.get("blurHash"):
                    doc["blurHash"] = variants.get("blurHash")

        raw_chats = doc.get("chats", [])
        platform = doc.get("platform", "")
        (
            top_gifts,
            top_fans,
            chat_count,
            gift_count,
            free_gift_count,
            total_gold,
            loveletter_count,
        ) = _compute_chat_stats(raw_chats, platform)

        doc["total_chats"] = chat_count
        doc["total_gifts"] = gift_count
        doc["total_free_gifts"] = free_gift_count
        doc["total_gold"] = total_gold
        doc["total_loveletters"] = loveletter_count
        doc["top_gifts"] = top_gifts
        doc["top_fans"] = top_fans
        doc.pop("chats", None)

        files = doc.get("files", {})
        screenshots = files.get("screenshots", [])

        # Get absolute URLs for screenshots
        r2_base = f"replay/{live_id}/screenshots"
        resolved_screenshots = []
        for s in screenshots:
            url = await self.storage_service.resolve_url(f"{r2_base}/{s}")
            if url:
                resolved_screenshots.append(url)

        doc["files"] = {"screenshots": resolved_screenshots}

        return ReplayDetailResponse(**doc)

    async def list_all(self) -> list[dict]:
        wib = timezone(timedelta(hours=7))
        docs = await self.repository.find_all()
        result = []
        for doc in docs:
            start_at = doc.get("start_at") or doc.get("recording_started_at")
            if isinstance(start_at, str):
                try:
                    dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                    start_at = dt.astimezone(wib)
                except (ValueError, AttributeError):
                    start_at = None
            elif isinstance(start_at, datetime):
                start_at = start_at.astimezone(wib)
            date_str = start_at.strftime("%Y-%m-%d") if start_at else None
            result.append(
                {
                    "live_id": doc.get("live_id", ""),
                    "youtube_id": doc.get("youtube_id") or "",
                    "title": doc.get("youtube_title") or doc.get("title"),
                    "member": doc.get("member_nickname", ""),
                    "date": date_str,
                    "platform": doc.get("platform", "").upper(),
                    "added_at": doc.get("created_at"),
                    "live_id": doc.get("live_id", ""),
                }
            )
        return result

    async def get_srt_content(self, live_id: str) -> Optional[str]:
        doc = await self.repository.find_by_live_id(live_id)
        if not doc:
            return None
        srt_path = doc.get("files", {}).get("srt")
        if not srt_path:
            return None
        content = await self.storage.get_file(srt_path)
        if content is None:
            return None
        return content.decode("utf-8", errors="replace")
