import asyncio
import base64
import json
import logging
import time as _time
from datetime import datetime, timedelta, timezone

from src.admin.constants import SuccessMessage
from src.admin.exceptions import (
    AdminConfigFetchError,
    AdminConfigUpdateError,
    AdminStatsFetchError,
)
from src.admin.repository import AdminRepository
from src.admin.schemas import (
    DataMyPageStats,
    DataTheaterStats,
    DataUsersStats,
    IDNLivePlusConfig,
    IDNLivePlusConfigResponse,
)
from src.live.idn_auth import cognito_refresh_tokens, extract_session_id
from src.utils import fernet_decrypt_value, fernet_encrypt_value

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository

    async def get_users_stats(self, active_days: int = 7) -> DataUsersStats:
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=active_days)
            now = datetime.now()
            start_of_day = datetime(now.year, now.month, now.day)

            total_users = await self.repository.count_documents("users")
            verified_users = await self.repository.count_documents(
                "users", {"isEmailVerified": True}
            )
            unverified_users = await self.repository.count_documents(
                "users", {"isEmailVerified": False}
            )
            total_admins = await self.repository.count_documents(
                "users", {"isAdmin": True}
            )
            public_profiles = await self.repository.count_documents(
                "users", {"isPublic": True}
            )
            active_users_last_days = await self.repository.count_documents(
                "users", {"lastActiveAt": {"$gte": cutoff_date}}
            )

            total_feedback = await self.repository.count_documents("feedback")

            users_joined_today = await self.repository.count_documents(
                "users", {"createdAt": {"$gte": start_of_day}}
            )

            return DataUsersStats(
                total_users=total_users,
                verified_users=verified_users,
                unverified_users=unverified_users,
                total_admins=total_admins,
                total_feedback=total_feedback,
                active_users_last_days=active_users_last_days,
                public_profiles=public_profiles,
                users_joined_today=users_joined_today,
            )
        except Exception:
            logger.exception("Error fetching users stats")
            raise AdminStatsFetchError()

    async def get_mypage_stats(self) -> DataMyPageStats:
        try:
            total_tickets = await self.repository.count_documents("tickets")
            total_2shot = await self.repository.count_documents(
                "tickets", {"two_shot": {"$ne": None}}
            )
            total_journal = await self.repository.count_documents(
                "tickets", {"notes": {"$nin": [None, ""]}}
            )
            total_favorites = await self.repository.count_documents(
                "tickets", {"is_favorite": True}
            )
            total_sorter = await self.repository.count_documents("sorter_results")

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total": {
                            "$sum": {
                                "$add": ["$price", {"$ifNull": ["$two_shot.price", 0]}]
                            }
                        },
                    }
                }
            ]
            result = await self.repository.aggregate("tickets", pipeline)
            total_money = result[0]["total"] if result else 0.0

            return DataMyPageStats(
                total_tickets=total_tickets,
                total_2shot=total_2shot,
                total_journal=total_journal,
                total_favorites=total_favorites,
                total_sorter=total_sorter,
                total_money_spent_idr=float(total_money),
            )
        except Exception:
            logger.exception("Error fetching mypage stats")
            raise AdminStatsFetchError()

    async def get_theater_stats(self) -> DataTheaterStats:
        try:
            now = datetime.now()
            start_of_day = datetime(now.year, now.month, now.day)

            # Define all queries to run concurrently
            queries = [
                self.repository.count_documents("members"),
                self.repository.count_documents("members", {"active": True}),
                self.repository.count_documents("setlists"),
                self.repository.count_documents("setlists", {"active": True}),
                self.repository.count_documents("news"),
                self.repository.count_documents("live_history"),
                self.repository.count_documents(
                    "live_history", {"platform": "showroom"}
                ),
                self.repository.count_documents("live_history", {"platform": "idn"}),
                self.repository.count_documents("replay"),
                self.repository.count_documents("replay", {"platform": "showroom"}),
                self.repository.count_documents("replay", {"platform": "idn"}),
                self.repository.find("members", {"active": True}),
                self.repository.count_documents(
                    "events", {"setlistId": {"$in": [None, ""]}}
                ),
                self.repository.count_documents(
                    "events", {"setlistId": {"$nin": [None, ""]}}
                ),
                self.repository.count_documents(
                    "events", {"date": {"$gte": start_of_day}}
                ),
                self.repository.count_documents(
                    "events",
                    {"date": {"$gte": start_of_day}, "setlistId": {"$in": [None, ""]}},
                ),
                self.repository.count_documents(
                    "events",
                    {"date": {"$gte": start_of_day}, "setlistId": {"$nin": [None, ""]}},
                ),
            ]

            results = await asyncio.gather(*queries)

            (
                total_members_jkt,
                active_members_count,
                total_setlists,
                active_setlists_count,
                total_news,
                total_live_member,
                showroom_live_count,
                idn_live_count,
                total_replay_live,
                showroom_replay_count,
                idn_replay_count,
                members,
                total_events,
                total_show_setlist,
                total_upcoming,
                total_upcoming_events,
                total_upcoming_shows,
            ) = results

            graduated_members_count = total_members_jkt - active_members_count
            inactive_setlists_count = total_setlists - active_setlists_count

            # Calculate upcoming birthdays for the rest of the year
            upcoming_birthdays_count = 0
            today = now.date()
            months_map = {
                "Januari": 1,
                "Februari": 2,
                "Maret": 3,
                "April": 4,
                "Mei": 5,
                "Juni": 6,
                "Juli": 7,
                "Agustus": 8,
                "September": 9,
                "Oktober": 10,
                "November": 11,
                "Desember": 12,
            }
            end_of_year = datetime(today.year, 12, 31).date()

            for member in members:
                if not member.get("birthdate"):
                    continue
                try:
                    parts = member["birthdate"].split()
                    if len(parts) != 3:
                        continue
                    day = int(parts[0])
                    month_str = parts[1]
                    if month_str not in months_map:
                        continue
                    month = months_map[month_str]
                    # We check if the birthday in the CURRENT year is upcoming
                    birthday_this_year = datetime(today.year, month, day).date()
                    if today <= birthday_this_year <= end_of_year:
                        upcoming_birthdays_count += 1
                except (ValueError, TypeError):
                    continue

            return DataTheaterStats(
                total_members_jkt=total_members_jkt,
                active_members_count=active_members_count,
                graduated_members_count=graduated_members_count,
                total_setlists=total_setlists,
                active_setlists_count=active_setlists_count,
                inactive_setlists_count=inactive_setlists_count,
                total_events=total_events,
                total_show_setlist=total_show_setlist,
                total_upcoming_events_and_shows=total_upcoming,
                total_upcoming_events=total_upcoming_events,
                total_upcoming_shows=total_upcoming_shows,
                upcoming_birthdays_count=upcoming_birthdays_count,
                total_news=total_news,
                total_live_member=total_live_member,
                showroom_live_count=showroom_live_count,
                idn_live_count=idn_live_count,
                total_replay_live=total_replay_live,
                showroom_replay_count=showroom_replay_count,
                idn_replay_count=idn_replay_count,
            )
        except Exception:
            logger.exception("Error fetching theater stats")
            raise AdminStatsFetchError()

    async def get_idn_live_plus_config(self) -> IDNLivePlusConfigResponse:
        try:
            doc = await self.repository.get_setting("idn_live_plus_config")
            if not doc or "data" not in doc:
                config = IDNLivePlusConfig()
            else:
                data = doc["data"]
                updated_at = doc.get("updated_at")
                if isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at)
                elif not isinstance(updated_at, datetime):
                    updated_at = None
                config = IDNLivePlusConfig(
                    auth_token=fernet_decrypt_value(data.get("auth_token")),
                    access_token=fernet_decrypt_value(data.get("access_token")),
                    session_id=fernet_decrypt_value(data.get("session_id")),
                    api_key=fernet_decrypt_value(data.get("api_key")),
                    aes_key=fernet_decrypt_value(data.get("aes_key")),
                    refresh_token=fernet_decrypt_value(data.get("refresh_token")),
                    cognito_client_id=fernet_decrypt_value(
                        data.get("cognito_client_id")
                    ),
                    updated_at=updated_at,
                    enabled=data.get("enabled", True),
                )
            return IDNLivePlusConfigResponse(
                data=config, detail=SuccessMessage.IDN_LIVE_PLUS_CONFIG_FETCHED
            )
        except Exception:
            logger.exception("Error fetching idn live plus config")
            raise AdminConfigFetchError()

    async def _refresh_via_cognito(
        self, config: IDNLivePlusConfig
    ) -> IDNLivePlusConfig:
        if not config.refresh_token or not config.cognito_client_id:
            return config
        result = await cognito_refresh_tokens(
            config.refresh_token, config.cognito_client_id
        )
        if result:
            config.auth_token = result["id_token"]
            config.access_token = result["access_token"]
            config.updated_at = datetime.now(timezone.utc)
            session_id = extract_session_id(result["id_token"])
            if session_id:
                config.session_id = session_id
            logger.info(
                "Cognito refresh successful on save: "
                f"auth_token={result['id_token'][:10]}..., "
                f"access_token={result['access_token'][:10]}..., "
                f"session_id={session_id}"
            )
        return config

    async def update_idn_live_plus_config(
        self, config: IDNLivePlusConfig
    ) -> IDNLivePlusConfigResponse:
        try:
            doc = await self.repository.get_setting("idn_live_plus_config")
            existing = (doc or {}).get("data", {})

            def _merge_encrypted(val, key):
                return val if val else fernet_decrypt_value(existing.get(key))

            config.auth_token = _merge_encrypted(config.auth_token, "auth_token")
            config.access_token = _merge_encrypted(config.access_token, "access_token")
            config.session_id = _merge_encrypted(config.session_id, "session_id")
            config.api_key = _merge_encrypted(config.api_key, "api_key")
            config.aes_key = _merge_encrypted(config.aes_key, "aes_key")
            config.refresh_token = _merge_encrypted(
                config.refresh_token, "refresh_token"
            )
            config.cognito_client_id = _merge_encrypted(
                config.cognito_client_id, "cognito_client_id"
            )
            if config.enabled is None:
                config.enabled = existing.get("enabled", True)

            should_refresh = False
            if config.refresh_token and config.cognito_client_id:
                auth_token = config.auth_token
                if not auth_token:
                    should_refresh = True
                else:
                    try:
                        _, payload_b64, _ = auth_token.split(".")
                        padding = 4 - len(payload_b64) % 4
                        if padding != 4:
                            payload_b64 += "=" * padding

                        payload = json.loads(base64.b64decode(payload_b64))
                        exp = int(payload.get("exp", 0))
                        if not exp or _time.time() >= exp - 1800:
                            should_refresh = True
                    except Exception:
                        should_refresh = True

            if should_refresh:
                config = await self._refresh_via_cognito(config)
            else:
                config.updated_at = datetime.now(timezone.utc)

            data = {
                "auth_token": fernet_encrypt_value(config.auth_token)
                if config.auth_token
                else None,
                "access_token": fernet_encrypt_value(config.access_token)
                if config.access_token
                else None,
                "session_id": fernet_encrypt_value(config.session_id)
                if config.session_id
                else None,
                "api_key": fernet_encrypt_value(config.api_key)
                if config.api_key
                else None,
                "aes_key": fernet_encrypt_value(config.aes_key)
                if config.aes_key
                else None,
                "refresh_token": fernet_encrypt_value(config.refresh_token)
                if config.refresh_token
                else None,
                "cognito_client_id": fernet_encrypt_value(config.cognito_client_id)
                if config.cognito_client_id
                else None,
                "enabled": config.enabled if config.enabled is not None else True,
            }
            config.updated_at = datetime.now(timezone.utc)
            await self.repository.upsert_setting("idn_live_plus_config", data)
            return IDNLivePlusConfigResponse(
                data=config, detail=SuccessMessage.IDN_LIVE_PLUS_CONFIG_UPDATED
            )
        except Exception:
            logger.exception("Error updating idn live plus config")
            raise AdminConfigUpdateError()
