import time
from typing import List, Optional, Tuple

import httpx

from ..models import LiveInfo


class LiveDetector:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=15.0)
        self._last_live_ids: set[str] = set()

    async def poll(self) -> Tuple[List[LiveInfo], bool]:
        try:
            resp = await self.client.get(
                f"{self.api_base_url}/jkt48/live", params={"t": int(time.time() * 1000)}
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[live_detector] Failed to poll live status: {e}")
            return [], False

        lives: List[LiveInfo] = []
        for item in data.get("data", []):
            platform: str = item.get("platform", "")
            live_id: Optional[str] = item.get("live_id")
            if not live_id:
                continue

            member = item.get("member") or {}
            member_name = member.get("name", "unknown")
            member_nickname = member.get("nickname") or member_name

            room_id: str = ""
            if platform == "showroom":
                room_id = str(item.get("room_id", ""))
            elif platform == "idn":
                room_id = str(item.get("live_id", ""))

            hls_url: Optional[str] = None
            streaming_urls = item.get("streaming_url", [])
            if streaming_urls:
                hls_url = streaming_urls[0].get("url")

            live_info = LiveInfo(
                live_id=live_id,
                platform=platform,
                member_name=member_name,
                member_nickname=member_nickname,
                room_id=room_id,
                room_identifier=item.get("room_identifier"),
                hls_url=hls_url,
                title=item.get("title", ""),
                member_image=member.get("img", ""),
                start_at=item.get("start_at", ""),
            )
            lives.append(live_info)

        return lives, True

    def diff(self, current_lives: List[LiveInfo]) -> Tuple[List[LiveInfo], set[str]]:
        current_ids = {l.live_id for l in current_lives}
        new_lives = [l for l in current_lives if l.live_id not in self._last_live_ids]
        ended_ids = self._last_live_ids - current_ids
        self._last_live_ids = current_ids
        return new_lives, ended_ids

    async def get_streaming_url(
        self, platform: str, room_id: str, live_id: str = ""
    ) -> Optional[dict]:
        identifier = room_id if platform == "showroom" else (live_id or room_id)
        try:
            resp = await self.client.get(
                f"{self.api_base_url}/jkt48/live/{platform}/{identifier}/streaming-url"
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(
                f"[live_detector] Failed to get streaming URL for {platform}/{identifier}: {e}"
            )
            return None

    @staticmethod
    def pick_best_url(stream_info: dict) -> Optional[str]:
        urls = stream_info.get("streaming_urls", [])
        if not urls:
            return None
        platform = stream_info.get("platform", "")
        if platform == "showroom":
            best = max(urls, key=lambda u: u.get("quality", 0))
            return best.get("url")
        return urls[0].get("url")

    async def close(self):
        await self.client.aclose()
