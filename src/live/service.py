import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from urllib.parse import urljoin, quote_plus
from src.config import Settings
from src.live.exceptions import (
    FetchShowroomError,
    FetchIdnError,
    StreamingUrlNotFoundError,
    ProxyError,
    CommentsFetchError,
)
from src.live.schemas import (
    LiveMember,
    LiveResponse,
    LiveStatus,
    LiveStreamingURL,
    LiveStreamInfo,
)
from src.logging_config import create_logger
from src.members.repository import MemberRepository

logger = create_logger("live_service", __name__)


class LiveService:
    def __init__(
        self,
        member_repository: MemberRepository,
        config: Settings,
    ):
        self.member_repository = member_repository
        self.config = config
        self._cache = {}
        self._cache_ttl = 60  # seconds cache
        self.showroom_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.showroom-live.com/",
        }

    async def get_live_status(self) -> LiveResponse:
        """Get unified live status from Showroom and IDN"""
        now = datetime.now()
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
        response = LiveResponse(
            data=all_lives, total=len(all_lives), updated_at=now
        )

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
                    if key in member_map:
                        member = member_map[key]
                        results.append(
                            LiveStatus(
                                platform="showroom",
                                room_id=str(room.get("room_id")),
                                room_url_key=key,
                                title=room.get("main_name"),
                                view_num=room.get("view_num", 0),
                                start_at=datetime.fromtimestamp(room.get("started_at"))
                                if room.get("started_at")
                                else None,
                                member=LiveMember(
                                    id=member["id"],
                                    name=member["name"],
                                    nickname=member.get("nickname"),
                                    img=member.get("img"),
                                ),
                            )
                        )
                
                # DEBUG MOCK: If no JKT48 members are live, take up to 8 Showroom lives for testing multi-view
                if not results and all_rooms:
                    for room in all_rooms[:8]:
                        results.append(
                            LiveStatus(
                                platform="showroom",
                                room_id=str(room.get("room_id")),
                                room_url_key=room.get("room_url_key"),
                                title=f"[DEBUG] {room.get('main_name')}",
                                view_num=room.get("view_num", 0),
                                start_at=datetime.fromtimestamp(room.get("started_at"))
                                if room.get("started_at")
                                else datetime.now(),
                                member=LiveMember(
                                    id=f"debug_{room.get('room_id')}",
                                    name=room.get("main_name"),
                                    nickname=room.get("nickname") or room.get("main_name"),
                                    img=""
                                ),
                            )
                        )
                
                return results
        except Exception as e:
            logger.exception(f"Exception in fetch_showroom_lives: {str(e)}")
            raise FetchShowroomError()

    async def fetch_idn_lives(self) -> List[LiveStatus]:
        """Fetch active JKT48 streams from official IDN GraphQL"""
        url = "https://api.idn.app/graphql"
        query = """
        query GetLivestream($page: Int) {
          getLivestreams(page: $page) {
            slug
            title
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
        variables = {"page": 1}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    url, json={"query": query, "variables": variables}, timeout=30.0
                )
                res.raise_for_status()
                data = res.json()

                streams = data.get("data", {}).get("getLivestreams", [])
                if not streams:
                    return []

                # Fetch all members to match
                active_members = await self.member_repository.find_all(limit=500)
                member_map = {}
                for m in active_members:
                    idn_url = m.get("socials", {}).get("idn_app", "")
                    if idn_url:
                        # Normalize username: remove trailing slash, take last part, remove @
                        username = idn_url.rstrip("/").split("/")[-1].replace("@", "").strip().lower()
                        if username:
                            member_map[username] = m

                results = []
                for stream in streams:
                    # IDN status can be "live" (lowercase) or "ON_LIVE"
                    status = str(stream.get("status", "")).upper()
                    if status not in ["LIVE", "ON_LIVE"]:
                        continue

                    username = str(stream.get("creator", {}).get("username") or "").replace("@", "").strip().lower()
                    if username in member_map:
                        member = member_map[username]
                        playback_url = stream.get("playback_url")
                        streaming_urls = []
                        if playback_url:
                            streaming_urls.append(
                                LiveStreamingURL(url=playback_url, label="HLS", quality=0)
                            )

                        results.append(
                            LiveStatus(
                                platform="idn",
                                live_id=stream.get("slug"),
                                title=stream.get("title"),
                                view_num=0,
                                start_at=datetime.fromisoformat(
                                    stream.get("live_at").replace("Z", "+00:00")
                                )
                                if stream.get("live_at")
                                else None,
                                streaming_url=streaming_urls,
                                room_identifier=stream.get("room_identifier"),
                                room_url_key=stream.get("creator", {}).get("username"),
                                member=LiveMember(
                                    id=member["id"],
                                    name=member["name"],
                                    nickname=member.get("nickname"),
                                    img=member.get("img"),
                                ),
                            )
                        )
                    else:
                        # Fallback for IDN JKT48 members not in DB
                        creator_name = str(stream.get("creator", {}).get("name") or "")
                        if "JKT48" in creator_name.upper() or "JKT48" in str(stream.get("title") or "").upper():
                            playback_url = stream.get("playback_url")
                            streaming_urls = []
                            if playback_url:
                                streaming_urls.append(LiveStreamingURL(url=playback_url, label="HLS", quality=0))

                            results.append(
                                LiveStatus(
                                    platform="idn",
                                    live_id=stream.get("slug"),
                                    title=stream.get("title"),
                                    view_num=0,
                                    start_at=datetime.fromisoformat(stream.get("live_at").replace("Z", "+00:00")) if stream.get("live_at") else None,
                                    streaming_url=streaming_urls,
                                    room_identifier=stream.get("room_identifier"),
                                    room_url_key=stream.get("creator", {}).get("username"),
                                    member=LiveMember(
                                        id=f"temp_{username}",
                                        name=creator_name,
                                        nickname=creator_name.split(" ")[0],
                                        img=stream.get("creator", {}).get("avatar") or "https://www.jkt48.com/images/ogp.png",
                                    ),
                                )
                            )
 
                # DEBUG MOCK: If no JKT48 members are live, take the first available IDN live for testing
                if not results and streams:
                    stream = streams[0]
                    room_id = stream.get("room_identifier") or stream.get("creator", {}).get("username")
                    results.append(
                        LiveStatus(
                            platform="idn",
                            live_id=stream.get("slug"),
                            title=f"[DEBUG] {stream.get('title')}",
                            view_num=0,
                            start_at=datetime.fromisoformat(stream.get("live_at").replace("Z", "+00:00")) if stream.get("live_at") else datetime.now(),
                            streaming_url=[
                                LiveStreamingURL(url=stream.get("playback_url"), label="HLS", quality=0)
                            ] if stream.get("playback_url") else [],
                            room_identifier=room_id,
                            room_url_key=stream.get("creator", {}).get("username"),
                            member=LiveMember(
                                id=f"debug_{stream.get('slug')}",
                                name=stream.get("creator", {}).get("name") or "DEBUG TEST STREAM",
                                nickname=stream.get("creator", {}).get("username") or "Debug",
                                img=""
                            ),
                        )
                    )

                return results
        except Exception as e:
            logger.exception(f"Exception in fetch_idn_lives: {str(e)}")
            raise FetchIdnError()

    async def get_streaming_url(self, platform: str, id: str) -> LiveStreamInfo:
        """Get streaming URL and room info for a specific platform and ID"""
        if platform == "showroom":
            urls = await self.fetch_showroom_streaming_url(id)
            profile = await self.fetch_showroom_profile(id)
            if not urls:
                raise StreamingUrlNotFoundError()
            return LiveStreamInfo(
                streaming_urls=urls,
                member=profile
            )
        elif platform == "idn":
            lives = await self.fetch_idn_lives()
            for live in lives:
                if live.live_id == id:
                    room_id = live.room_identifier
                    
                    # If room_id is None, try scraping from the live page
                    if not room_id and live.room_url_key:
                        try:
                            # IDN Live URL: https://www.idn.app/{username}/live/{slug}
                            username = live.room_url_key
                            slug = id
                            scrape_url = f"https://www.idn.app/{username}/live/{slug}"
                            
                            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                                res = await client.get(scrape_url)
                                html = res.text
                                
                                import re
                                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
                                if match:
                                    data = json.loads(match.group(1))
                                    livestream = data.get("props", {}).get("pageProps", {}).get("livestream", {})
                                    room_id = livestream.get("chat_room_id")
                        except Exception as scrape_err:
                            logger.exception(f"Failed to scrape IDN chat room ID for {id}: {scrape_err}")

                    return LiveStreamInfo(
                        streaming_urls=live.streaming_url,
                        room_identifier=room_id,
                        member=live.member
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
                        img=data.get("image")
                    )
        except Exception as e:
            logger.exception(f"Failed to fetch showroom profile for {room_id}: {e}")
            return None

    async def fetch_showroom_streaming_url(self, room_id: str) -> List[LiveStreamingURL]:
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
                    if not stream_url or not stream_url.startswith(("http://", "https://")):
                        continue
                        
                    streaming_urls.append(
                        LiveStreamingURL(
                            url=stream_url,
                            label=stream.get("label"),
                            quality=stream.get("quality", 0)
                        )
                    )
                return streaming_urls
        except Exception as e:
            logger.exception(f"Error fetching Showroom streaming URL for {room_id}: {e}")
            return []

    async def get_showroom_comments(self, room_id: str) -> Dict[Any, Any]:
        """Fetch Showroom comment log via proxy to bypass CORS"""
        url = f"https://www.showroom-live.com/api/live/comment_log?room_id={room_id}"
        try:
            async with httpx.AsyncClient(headers=self.showroom_headers, timeout=10.0) as client:
                res = await client.get(url)
                return res.json()
        except Exception as e:
            logger.exception(f"Error fetching showroom comments for {room_id}: {e}")
            raise CommentsFetchError()

    async def proxy_hls_request(self, url: str) -> Dict[str, Any]:
        """Proxy HLS playlist and segments to bypass CORS"""
        try:
            headers = self.showroom_headers if "showroom-live.com" in url else {}
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
                resp = await client.get(url)
                
            if resp.status_code != 200:
                return {
                    "content": resp.content,
                    "media_type": None,
                    "status_code": resp.status_code
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
                                proxied_uri = f"/api/jkt48/live/proxy?url={quote_plus(absolute_uri)}"
                                return f'URI="{proxied_uri}"'
                            
                            line = re.sub(r'URI=(["\']?)([^"\',]+)\1', replace_uri, line)
                        
                        rewritten_lines.append(line)
                    else:
                        # This is a URL (variant playlist or segment)
                        absolute_url = urljoin(url, line)
                        proxied_url = f"/api/jkt48/live/proxy?url={quote_plus(absolute_url)}"
                        rewritten_lines.append(proxied_url)
                
                return {
                    "content": "\n".join(rewritten_lines),
                    "media_type": "application/vnd.apple.mpegurl",
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "no-cache"
                    }
                }
            
            # For segments (.ts), just return the content
            return {
                "content": resp.content,
                "media_type": content_type,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=3600"
                }
            }
            
        except Exception as e:
            logger.exception(f"Error proxying HLS request for {url}: {e}")
            raise ProxyError()
