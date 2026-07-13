import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin

import httpx

from src.admin.service import AdminService
from src.auth.schemas import UserCurrent
from src.config import Settings
from src.live.exceptions import (
    CommentsFetchError,
    FetchIdnError,
    FetchShowroomError,
    GiftsFetchError,
    ProxyError,
    StreamingUrlNotFoundError,
)
from src.live.schemas import (
    LiveMember,
    LiveResponse,
    LiveStatus,
    LiveStreamInfo,
    LiveStreamingURL,
)
from src.logging_config import create_logger
from src.members.repository import MemberRepository

logger = create_logger("live_service", __name__)


class LiveService:
    def __init__(
        self,
        member_repository: MemberRepository,
        admin_service: AdminService,
        config: Settings,
    ):
        self.member_repository = member_repository
        self.admin_service = admin_service
        self.config = config
        self._cache = {}
        self._cache_ttl = 60  # seconds cache
        self._idn_config_cache = None
        self._idn_config_updated_at = 0
        self.showroom_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.showroom-live.com/",
        }

    async def get_live_status(self) -> LiveResponse:
        """Get unified live status from Showroom and IDN"""
        now = datetime.now(timezone.utc)
        if "data" in self._cache:
            updated_at = self._cache.get("updated_at")
            if updated_at and (now - updated_at).total_seconds() < self._cache_ttl:
                return self._cache["data"]

        showroom_lives, idn_lives = await asyncio.gather(
            self.fetch_showroom_lives(), self.fetch_idn_lives(), return_exceptions=True
        )

        if isinstance(showroom_lives, Exception):
            logger.error(f"Error fetching Showroom lives: {showroom_lives}")
            showroom_lives = []

        if isinstance(idn_lives, Exception):
            logger.error(f"Error fetching IDN lives: {idn_lives}")
            idn_lives = []

        all_lives = showroom_lives + idn_lives
        response = LiveResponse(data=all_lives, total=len(all_lives), updated_at=now)

        self._cache["data"] = response
        self._cache["updated_at"] = now
        return response

    async def fetch_showroom_lives(self) -> List[LiveStatus]:
        """Fetch active JKT48 rooms from official Showroom API"""
        url = "https://www.showroom-live.com/api/live/onlives"
        try:
            async with httpx.AsyncClient(headers=self.showroom_headers) as client:
                res = await client.get(url, timeout=10.0)
                res.raise_for_status()
                data = res.json()

                all_rooms_map = {}
                for genre in data.get("onlives", []):
                    for room in genre.get("lives", []):
                        rid = room.get("room_id")
                        if rid:
                            all_rooms_map[rid] = room

                all_rooms = list(all_rooms_map.values())

                if not all_rooms:
                    return []

                # Fetch all members to match (including trainees)
                active_members = await self.member_repository.find_all(limit=500)
                member_map = {}
                for m in active_members:
                    showroom_url = m.get("socials", {}).get("showroom", "")
                    if showroom_url:
                        # Extract room_url_key from URL (last part)
                        key = showroom_url.split("/")[-1].strip()
                        if key:
                            member_map[key] = m

                results = []
                for room in all_rooms:
                    key = room.get("room_url_key")
                    if key in member_map or key == "officialJKT48":
                        if key in member_map:
                            member_data = member_map[key]
                            member = LiveMember(
                                id=member_data["id"],
                                name=member_data["name"],
                                nickname=member_data.get("nickname"),
                                img=member_data.get("img"),
                            )
                        else:
                            # Fallback for official account
                            member = LiveMember(
                                id=f"temp_sr_{key}",
                                name=room.get("main_name", "JKT48 Official"),
                                nickname="officialJKT48",
                                img=room.get("image")
                                or "/media/news/migrated/jkt48logo.jpg",
                            )

                        results.append(
                            LiveStatus(
                                platform="showroom",
                                room_id=str(room.get("room_id")),
                                room_url_key=key,
                                live_id=f"{room.get('room_id')}-{room.get('started_at')}"
                                if room.get("started_at")
                                else None,
                                title=room.get("main_name"),
                                view_num=room.get("view_num", 0),
                                image=room.get("image"),
                                start_at=datetime.fromtimestamp(
                                    room.get("started_at"), tz=timezone.utc
                                )
                                if room.get("started_at")
                                else None,
                                member=member,
                            )
                        )

                # DEBUG MOCK: If no JKT48 members are live, take up to 8 Showroom lives for testing multi-view
                if self.config.is_env_dev and not results and all_rooms:
                    for room in all_rooms[:1]:
                        results.append(
                            LiveStatus(
                                platform="showroom",
                                room_id=str(room.get("room_id")),
                                room_url_key=room.get("room_url_key"),
                                live_id=f"{room.get('room_id')}-{room.get('started_at')}"
                                if room.get("started_at")
                                else None,
                                title=f"[DEBUG] {room.get('main_name')}",
                                view_num=room.get("view_num", 0),
                                image=room.get("image"),
                                start_at=datetime.fromtimestamp(
                                    room.get("started_at"), tz=timezone.utc
                                )
                                if room.get("started_at")
                                else datetime.now(timezone.utc),
                                member=LiveMember(
                                    id=f"debug_{room.get('room_id')}",
                                    name=room.get("main_name"),
                                    nickname=room.get("nickname")
                                    or room.get("main_name"),
                                    img="",
                                ),
                            )
                        )

                return results
        except Exception as e:
            logger.exception(f"Exception in fetch_showroom_lives: {str(e)}")
            raise FetchShowroomError()

    async def _get_idn_config(self) -> dict:
        """Fetch IDN config from cache or DB, fallback to .env."""
        now = time.time()
        if self._idn_config_cache and (now - self._idn_config_updated_at) < 60:
            return self._idn_config_cache

        try:
            db_config = await self.admin_service.get_idn_live_plus_config()
        except Exception as e:
            logger.warning(f"Failed to fetch IDN config from DB: {e}")
            db_config = None

        merged_config = {
            "api_key": self.config.idn_live_plus_api_key,
            "auth_token": self.config.idn_auth_token,
            "access_token": self.config.idn_access_token,
            "session_id": self.config.idn_session_id,
            "aes_key": self.config.IDN_AES_KEY,
        }

        if db_config:
            config_data = db_config.data
            if config_data.api_key:
                merged_config["api_key"] = config_data.api_key
            if config_data.auth_token:
                merged_config["auth_token"] = config_data.auth_token
            if config_data.access_token:
                merged_config["access_token"] = config_data.access_token
            if config_data.session_id:
                merged_config["session_id"] = config_data.session_id
            if config_data.aes_key:
                merged_config["aes_key"] = config_data.aes_key

        self._idn_config_cache = merged_config
        self._idn_config_updated_at = now
        return merged_config

    async def _fetch_premium_idn_raw_streams(
        self, status_filter: Optional[List[str]] = None
    ) -> List[dict]:
        """Fetch premium streams (IDN Live+) using the IDN API Key"""
        idn_config = await self._get_idn_config()
        api_key = idn_config.get("api_key")
        if not api_key:
            return []

        url = "https://api.idn.app/api/v4/livestreams?category=idnliveplus&n=1"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    url, headers={"x-api-key": api_key}, timeout=30.0
                )
                res.raise_for_status()
                res_data = res.json()
                items = res_data.get("data") or []

                normalized = []
                for item in items:
                    status = str(item.get("status", "")).upper()
                    if status_filter is not None and status not in status_filter:
                        continue

                    # Normalize live_at integer to ISO format string so the existing parser doesn't break
                    live_at_int = item.get("live_at")
                    live_at_str = None
                    if live_at_int:
                        try:
                            # Convert to ISO string with Z
                            dt = datetime.fromtimestamp(live_at_int, tz=timezone.utc)
                            live_at_str = dt.isoformat().replace("+00:00", "Z")
                        except Exception:
                            pass

                    item["live_at"] = live_at_str
                    item["live_type"] = "idnliveplus"
                    item["streamer_uuid"] = item.get("creator", {}).get("uuid")
                    normalized.append(item)
                return normalized
        except Exception as e:
            logger.warning(f"Failed to fetch IDN premium streams: {e}")
            return []

    async def fetch_idn_lives(self) -> List[LiveStatus]:
        """Fetch active JKT48 streams from official IDN GraphQL"""
        url = "https://api.idn.app/graphql"
        query = """
        query GetLivestream($page: Int) {
            getLivestreams(page: $page) {
            slug
            title
            image_url
            view_count
            playback_url
            room_identifier
            status
            live_at
            creator {
              name
              username
            }
          }
        }
        """
        try:
            async with httpx.AsyncClient() as client:
                # Fetch first 4 pages concurrently to ensure we capture all active streams
                tasks = []
                for page in range(1, 5):
                    tasks.append(
                        client.post(
                            url,
                            json={"query": query, "variables": {"page": page}},
                            timeout=30.0,
                        )
                    )

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                raw_streams = []
                for res in responses:
                    if isinstance(res, Exception):
                        logger.warning(f"Failed to fetch IDN page: {res}")
                        continue
                    try:
                        res.raise_for_status()
                        res_data = res.json()
                        page_streams = res_data.get("data", {}).get(
                            "getLivestreams", []
                        )
                        if page_streams:
                            raw_streams.extend(page_streams)
                    except Exception as parse_err:
                        logger.warning(f"Error parsing IDN response page: {parse_err}")

                premium_streams = await self._fetch_premium_idn_raw_streams(
                    status_filter=["LIVE", "ON_LIVE"]
                )
                raw_streams = premium_streams + raw_streams

                if not raw_streams:
                    return []

                # Deduplicate streams by slug
                seen_slugs = set()
                streams = []
                for s in raw_streams:
                    slug = s.get("slug")
                    if slug and slug not in seen_slugs:
                        seen_slugs.add(slug)
                        streams.append(s)

                # Fetch all members to match
                active_members = await self.member_repository.find_all(limit=500)
                member_map = {}
                for m in active_members:
                    idn_url = m.get("socials", {}).get("idn_app", "")
                    if idn_url:
                        # Normalize username: remove trailing slash, take last part, remove @
                        username = (
                            idn_url.rstrip("/")
                            .split("/")[-1]
                            .replace("@", "")
                            .strip()
                            .lower()
                        )
                        if username:
                            member_map[username] = m

                results = []
                for stream in streams:
                    # IDN status can be "live" (lowercase) or "ON_LIVE"
                    status = str(stream.get("status", "")).upper()
                    if status not in ["LIVE", "ON_LIVE"]:
                        continue

                    username = (
                        str(stream.get("creator", {}).get("username") or "")
                        .replace("@", "")
                        .strip()
                        .lower()
                    )
                    if username in member_map:
                        member = member_map[username]
                        playback_url = stream.get("playback_url")
                        streaming_urls = []
                        if playback_url:
                            streaming_urls.append(
                                LiveStreamingURL(
                                    url=playback_url, label="HLS", quality=0
                                )
                            )

                        results.append(
                            LiveStatus(
                                platform="idn",
                                live_id=stream.get("slug"),
                                title=stream.get("title"),
                                image=stream.get("image_url"),
                                view_num=stream.get("view_count") or 0,
                                start_at=datetime.fromisoformat(
                                    stream.get("live_at").replace("Z", "+00:00")
                                ).astimezone(timezone.utc)
                                if stream.get("live_at")
                                else None,
                                streaming_url=streaming_urls,
                                room_identifier=stream.get("chat_room_id")
                                if stream.get("live_type") == "idnliveplus"
                                and stream.get("chat_room_id")
                                else stream.get("room_identifier"),
                                room_url_key=stream.get("creator", {}).get("username"),
                                member=LiveMember(
                                    id=member["id"],
                                    name=member["name"],
                                    nickname=member.get("nickname"),
                                    img=member.get("img"),
                                ),
                                live_type=stream.get("live_type", "public"),
                                streamer_uuid=stream.get("streamer_uuid"),
                            )
                        )
                    else:
                        # Fallback for IDN JKT48 members not in DB
                        creator_name = str(stream.get("creator", {}).get("name") or "")
                        if (
                            "JKT48" in creator_name.upper()
                            or "JKT48" in str(stream.get("title") or "").upper()
                        ):
                            playback_url = stream.get("playback_url")
                            streaming_urls = []
                            if playback_url:
                                streaming_urls.append(
                                    LiveStreamingURL(
                                        url=playback_url, label="HLS", quality=0
                                    )
                                )

                            results.append(
                                LiveStatus(
                                    platform="idn",
                                    live_id=stream.get("slug"),
                                    title=stream.get("title"),
                                    image=stream.get("image_url"),
                                    view_num=stream.get("view_count") or 0,
                                    start_at=datetime.fromisoformat(
                                        stream.get("live_at").replace("Z", "+00:00")
                                    ).astimezone(timezone.utc)
                                    if stream.get("live_at")
                                    else None,
                                    streaming_url=streaming_urls,
                                    room_identifier=stream.get("chat_room_id")
                                    if stream.get("live_type") == "idnliveplus"
                                    and stream.get("chat_room_id")
                                    else stream.get("room_identifier"),
                                    room_url_key=stream.get("creator", {}).get(
                                        "username"
                                    ),
                                    member=LiveMember(
                                        id=username,
                                        name=creator_name,
                                        nickname=creator_name.split(" ")[0],
                                        img=stream.get("creator", {}).get("avatar")
                                        or "/media/news/migrated/jkt48logo.jpg",
                                    ),
                                    live_type=stream.get("live_type", "public"),
                                    streamer_uuid=stream.get("streamer_uuid"),
                                )
                            )

                # DEBUG MOCK: If no JKT48 members are live, take the first available IDN live for testing
                if self.config.is_env_dev and not results and streams:
                    stream = streams[0]
                    room_id = (
                        stream.get("chat_room_id")
                        if stream.get("live_type") == "idnliveplus"
                        and stream.get("chat_room_id")
                        else stream.get("room_identifier")
                    )
                    results.append(
                        LiveStatus(
                            platform="idn",
                            live_id=stream.get("slug"),
                            title=f"[DEBUG] {stream.get('title')}",
                            image=stream.get("image_url"),
                            view_num=stream.get("view_count") or 0,
                            start_at=datetime.fromisoformat(
                                stream.get("live_at").replace("Z", "+00:00")
                            ).astimezone(timezone.utc)
                            if stream.get("live_at")
                            else datetime.now(timezone.utc),
                            streaming_url=[
                                LiveStreamingURL(
                                    url=stream.get("playback_url"),
                                    label="HLS",
                                    quality=0,
                                )
                            ]
                            if stream.get("playback_url")
                            else [],
                            room_identifier=room_id,
                            room_url_key=stream.get("creator", {}).get("username"),
                            member=LiveMember(
                                id=f"debug_{stream.get('slug')}",
                                name=stream.get("creator", {}).get("name")
                                or "DEBUG TEST STREAM",
                                nickname=stream.get("creator", {}).get("username")
                                or "Debug",
                                img="",
                            ),
                        )
                    )

                return results
        except Exception as e:
            logger.exception(f"Exception in fetch_idn_lives: {str(e)}")
            raise FetchIdnError()

    async def get_idn_playback_token(
        self, streamer_uuid: str, slug: str
    ) -> Optional[str]:
        """Fetch AWS IVS playback token for premium streams"""
        idn_config = await self._get_idn_config()
        auth_token = idn_config.get("auth_token")
        if not auth_token:
            logger.warning("IDN_AUTH_TOKEN is missing. Cannot fetch playback token.")
            return None

        url = f"https://api.idn.app/api/v1/apt?streamer_uuid={streamer_uuid}&slug={slug}&n=1"
        try:
            # Note: auth_token is expected to include "Bearer ", but let's handle if it doesn't
            bearer = (
                auth_token
                if auth_token.startswith("Bearer ")
                else f"Bearer {auth_token}"
            )

            headers = {"Authorization": bearer}
            if idn_config.get("api_key"):
                headers["X-Api-Key"] = idn_config["api_key"]
            if idn_config.get("access_token"):
                headers["Access-Token"] = idn_config["access_token"]
            if idn_config.get("session_id"):
                headers["Session-Id"] = idn_config["session_id"]

            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, timeout=10.0)
                res.raise_for_status()
                data = res.json()
                # `arishem` is the primary playback token for IVS, but it is AES-256-CBC encrypted
                encrypted_arishem = data.get("data", {}).get("arishem")
                if not encrypted_arishem:
                    return None

                import base64
                import json

                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives.ciphers import (
                    Cipher,
                    algorithms,
                    modes,
                )

                try:
                    # The arishem token is a base64 encoded JSON string
                    if isinstance(encrypted_arishem, str):
                        try:
                            decoded_str = base64.b64decode(encrypted_arishem).decode(
                                "utf-8"
                            )
                            payload = json.loads(decoded_str)
                        except Exception:
                            # Fallback if it's not base64 encoded
                            if encrypted_arishem.startswith("{"):
                                payload = json.loads(encrypted_arishem)
                            else:
                                raise ValueError("Invalid arishem format")
                    else:
                        payload = encrypted_arishem

                    iv = base64.b64decode(payload["iv"])
                    ciphertext = base64.b64decode(payload["value"])
                    key = (idn_config.get("aes_key") or "").encode("utf-8")

                    # Decrypt using AES-256-CBC
                    cipher = Cipher(
                        algorithms.AES(key), modes.CBC(iv), backend=default_backend()
                    )
                    decryptor = cipher.decryptor()
                    decrypted_padded = (
                        decryptor.update(ciphertext) + decryptor.finalize()
                    )

                    # Remove PKCS7 padding
                    padding_len = decrypted_padded[-1]
                    decrypted = decrypted_padded[:-padding_len].decode("utf-8")

                    return decrypted
                except Exception as e:
                    logger.error(f"Failed to decrypt IDN arishem token for {slug}: {e}")
                    return None
        except Exception as e:
            logger.exception(f"Failed to fetch IDN playback token for {slug}: {e}")
            return None

    async def get_streaming_url(
        self, platform: str, id: str, current_user: Optional[UserCurrent] = None
    ) -> LiveStreamInfo:
        """Get streaming URL and room info for a specific platform and ID"""
        if platform == "showroom":
            actual_room_id = id.split("-")[0] if "-" in id else id
            urls = await self.fetch_showroom_streaming_url(actual_room_id)
            profile = await self.fetch_showroom_profile(actual_room_id)
            if not urls:
                raise StreamingUrlNotFoundError()
            # Get view_num and start_at from unified list
            view_num = 0
            start_at = None
            image = None
            lives = await self.fetch_showroom_lives()
            for live in lives:
                if live.room_id == actual_room_id:
                    view_num = live.view_num
                    start_at = live.start_at
                    image = live.image
                    break

            return LiveStreamInfo(
                streaming_urls=urls,
                view_num=view_num,
                start_at=start_at,
                image=image,
                member=profile,
                live_type="public",  # Showroom is always public
                live_id=None,
                room_url_key=None,
            )
        elif platform == "idn":
            lives = await self.fetch_idn_lives()
            for live in lives:
                if live.live_id == id:
                    room_id = live.room_identifier

                    # For IDN Live+, we use the detail API to get the AWS IVS Chat Room ARN
                    if live.live_type == "idnliveplus":
                        if not current_user or not current_user.isAdmin:
                            raise StreamingUrlNotFoundError()

                        if not room_id or not str(room_id).startswith("arn:"):
                            try:
                                detail_url = (
                                    f"https://api.idn.app/api/v4/livestream/{id}?n=1"
                                )
                                async with httpx.AsyncClient(timeout=10.0) as client:
                                    headers = {}
                                    idn_config = await self._get_idn_config()
                                    if idn_config.get("api_key"):
                                        headers["x-api-key"] = idn_config.get("api_key")
                                    res = await client.get(detail_url, headers=headers)
                                    if res.status_code == 200:
                                        data = res.json().get("data", {})
                                        api_chat_room_id = data.get("chat_room_id")
                                        if api_chat_room_id:
                                            room_id = api_chat_room_id
                                    else:
                                        logger.warning(
                                            f"Failed to fetch IDN chat room ID. Status: {res.status_code}, Body: {res.text}"
                                        )
                            except Exception as api_err:
                                logger.exception(
                                    f"Failed to fetch IDN chat room ID from detail API for {id}: {api_err}"
                                )

                    # For regular IDN Live streams, fallback to scraping HTML for the UUID
                    elif (
                        live.live_type != "idnliveplus"
                        and not room_id
                        and live.room_url_key
                    ):
                        try:
                            username = live.room_url_key
                            slug = id
                            scrape_url = f"https://www.idn.app/{username}/live/{slug}"

                            async with httpx.AsyncClient(
                                follow_redirects=True, timeout=30.0
                            ) as client:
                                res = await client.get(scrape_url)
                                html = res.text

                                import re

                                match = re.search(
                                    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                                    html,
                                )
                                if match:
                                    data = json.loads(match.group(1))
                                    livestream = (
                                        data.get("props", {})
                                        .get("pageProps", {})
                                        .get("livestream", {})
                                    )
                                    room_id = livestream.get("chat_room_id")
                        except Exception as scrape_err:
                            logger.exception(
                                f"Failed to scrape IDN chat room ID for {id}: {scrape_err}"
                            )

                    # For premium streams, fetch and append the playback auth token
                    streaming_urls = live.streaming_url
                    if (
                        live.live_type == "idnliveplus"
                        and live.streamer_uuid
                        and streaming_urls
                    ):
                        token = await self.get_idn_playback_token(
                            live.streamer_uuid, id
                        )
                        if token:
                            # Append the token to the URL
                            base_url = streaming_urls[0].url
                            separator = "&" if "?" in base_url else "?"
                            streaming_urls[
                                0
                            ].url = f"{base_url}{separator}token={token}"

                    return LiveStreamInfo(
                        streaming_urls=streaming_urls,
                        room_identifier=room_id,
                        view_num=live.view_num,
                        start_at=live.start_at,
                        image=live.image,
                        member=live.member,
                        live_type=live.live_type,
                        live_id=live.live_id,
                        room_url_key=live.room_url_key,
                    )
        raise StreamingUrlNotFoundError()

    async def fetch_showroom_profile(self, room_id: str) -> Optional[LiveMember]:
        """Fetch Showroom room profile to get member name and image"""
        url = f"https://www.showroom-live.com/api/room/profile?room_id={room_id}"
        try:
            async with httpx.AsyncClient(headers=self.showroom_headers) as client:
                res = await client.get(url, timeout=10.0)
                if res.status_code == 200:
                    data = res.json()
                    return LiveMember(
                        id=str(data.get("room_id")),
                        name=data.get("main_name", "Unknown Member"),
                        nickname=data.get("nickname"),
                        img=data.get("image"),
                    )
        except Exception as e:
            logger.exception(f"Failed to fetch showroom profile for {room_id}: {e}")
            return None

    async def fetch_showroom_streaming_url(
        self, room_id: str
    ) -> List[LiveStreamingURL]:
        """Fetch streaming URL from official Showroom API"""
        url = f"https://www.showroom-live.com/api/live/streaming_url?room_id={room_id}"
        try:
            async with httpx.AsyncClient(headers=self.showroom_headers) as client:
                res = await client.get(url, timeout=10.0)
                res.raise_for_status()
                data = res.json()

                streaming_urls = []
                for stream in data.get("streaming_url_list", []):
                    stream_url = stream.get("url")
                    if not stream_url or not stream_url.startswith(
                        ("http://", "https://")
                    ):
                        continue

                    streaming_urls.append(
                        LiveStreamingURL(
                            url=stream_url,
                            label=stream.get("label"),
                            quality=stream.get("quality", 0),
                        )
                    )
                return streaming_urls
        except Exception as e:
            logger.exception(
                f"Error fetching Showroom streaming URL for {room_id}: {e}"
            )
            return []

    async def get_showroom_comments(self, room_id: str) -> Dict[Any, Any]:
        """Fetch Showroom comment log via proxy to bypass CORS"""
        url = f"https://www.showroom-live.com/api/live/comment_log?room_id={room_id}"
        try:
            async with httpx.AsyncClient(
                headers=self.showroom_headers, timeout=10.0
            ) as client:
                res = await client.get(url)
                return res.json()
        except Exception as e:
            logger.exception(f"Error fetching showroom comments for {room_id}: {e}")
            raise CommentsFetchError()

    async def get_showroom_gifts(self, room_id: str) -> Dict[Any, Any]:
        """Fetch Showroom gift log via proxy to bypass CORS"""
        url = f"https://www.showroom-live.com/api/live/gift_log?room_id={room_id}"
        try:
            async with httpx.AsyncClient(
                headers=self.showroom_headers, timeout=10.0
            ) as client:
                res = await client.get(url)
                return res.json()
        except Exception as e:
            logger.exception(f"Error fetching showroom gifts for {room_id}: {e}")
            raise GiftsFetchError()

    async def proxy_hls_request(self, url: str) -> Dict[str, Any]:
        """Proxy HLS playlist and segments to bypass CORS"""
        try:
            if "showroom-live.com" in url:
                headers = self.showroom_headers
            elif "live-video.net" in url or "idn.app" in url:
                headers = {"Origin": "https://www.idn.app"}
            else:
                headers = {}
            async with httpx.AsyncClient(
                headers=headers, follow_redirects=True, timeout=30.0
            ) as client:
                resp = await client.get(url)

            if resp.status_code != 200:
                return {
                    "content": resp.content,
                    "media_type": None,
                    "status_code": resp.status_code,
                }

            content_type = resp.headers.get("content-type", "")

            # If it's an m3u8 playlist, rewrite internal URLs
            if url.endswith(".m3u8") or "mpegurl" in content_type.lower():
                content = resp.text
                lines = content.splitlines()
                rewritten_lines = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("#"):
                        # Handle tags that might contain URIs (e.g., #EXT-X-KEY, #EXT-X-MAP, #EXT-X-MEDIA)
                        if "URI=" in line:
                            # Simple replacement for URI="url"
                            import re

                            def replace_uri(match):
                                original_uri = match.group(1).strip("\"'")
                                absolute_uri = urljoin(url, original_uri)
                                prefix = "/api" if self.config.is_env_dev else ""
                                proxied_uri = f"{prefix}/jkt48/live/proxy?url={quote_plus(absolute_uri)}"
                                return f'URI="{proxied_uri}"'

                            line = re.sub(
                                r'URI=(["\']?)([^"\',]+)\1', replace_uri, line
                            )

                        rewritten_lines.append(line)
                    else:
                        # This is a URL (variant playlist or segment)
                        absolute_url = urljoin(url, line)
                        prefix = "/api" if self.config.is_env_dev else ""
                        proxied_url = (
                            f"{prefix}/jkt48/live/proxy?url={quote_plus(absolute_url)}"
                        )
                        rewritten_lines.append(proxied_url)

                return {
                    "content": "\n".join(rewritten_lines),
                    "media_type": "application/vnd.apple.mpegurl",
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "no-cache",
                    },
                }

            # For segments (.ts), just return the content
            return {
                "content": resp.content,
                "media_type": content_type,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=3600",
                },
            }

        except Exception as e:
            logger.exception(f"Error proxying HLS request for {url}: {e}")
            raise ProxyError()

    async def get_scheduled_premium_lives(self) -> LiveResponse:
        """Fetch scheduled IDN Live+ streams"""
        streams = await self._fetch_premium_idn_raw_streams(status_filter=["SCHEDULED"])

        results = []
        for stream in streams:
            scheduled_at_ts = stream.get("scheduled_at")
            scheduled_at = (
                datetime.fromtimestamp(scheduled_at_ts, tz=timezone.utc)
                if scheduled_at_ts
                else None
            )

            results.append(
                LiveStatus(
                    platform="idn",
                    live_id=stream.get("slug"),
                    title=stream.get("title"),
                    image=stream.get("image_url"),
                    view_num=stream.get("view_count") or 0,
                    start_at=scheduled_at,
                    scheduled_at=scheduled_at,
                    streaming_url=[],
                    room_identifier=stream.get("room_identifier"),
                    room_url_key=stream.get("creator", {}).get("username"),
                    member=LiveMember(
                        id=stream.get("creator", {}).get("username") or "",
                        name=stream.get("creator", {}).get("name") or "",
                        nickname=str(
                            stream.get("creator", {}).get("username") or ""
                        ).split(" ")[0],
                        img=stream.get("creator", {}).get("image_url")
                        or stream.get("creator", {}).get("avatar")
                        or "/media/news/migrated/jkt48logo.jpg",
                    ),
                    live_type="idnliveplus",
                    streamer_uuid=stream.get("streamer_uuid"),
                )
            )

        return LiveResponse(
            data=results,
            total=len(results),
            updated_at=datetime.now(timezone.utc),
        )
