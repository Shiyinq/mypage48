import io
import json
from datetime import datetime, timezone
from typing import Optional

from src.config import Settings
from src.logging_config import create_logger
from src.replay.exceptions import ReplayUploadError
from src.replay.repository import ReplayRepository
from src.replay.schemas import ReplayFilesInfo, ReplayResponse
from src.storage.repository import StorageRepository

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


class ReplayService:
    def __init__(
        self,
        repository: ReplayRepository,
        storage_repository: StorageRepository,
        config: Settings,
    ):
        self.repository = repository
        self.storage = storage_repository
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
                f"Cannot upload replay with status '{status}'. Only 'completed' allowed."
            )

        if await self.repository.exists(live_id):
            logger.warning(f"Replay {live_id} already exists, skipping")
            raise ReplayUploadError(f"Replay {live_id} already exists")

        r2_base = f"replay/{live_id}"

        files = {}
        files["json_file"] = await self._upload_bytes(
            metadata_bytes, f"{r2_base}/{live_id}.json", "application/json"
        )
        if thumbnail_bytes:
            files["thumbnail"] = await self._upload_bytes(
                thumbnail_bytes, f"{r2_base}/{live_id}.jpg", "image/jpeg"
            )
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
            path = f"{r2_base}/screenshots/{filename}"
            await self._upload_bytes(data, path, "image/jpeg")
            screenshot_paths.append(filename)

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

        logger.info(f"Replay uploaded: {live_id} ({len(chats)} chats, {len(screenshot_paths)} screenshots)")
        return ReplayResponse(**doc)

    async def _upload_bytes(
        self, data: bytes, path: str, content_type: str
    ) -> str:
        await self.storage.upload_file(data, path, content_type=content_type)
        return path

    async def find_by_live_id(self, live_id: str) -> Optional[ReplayResponse]:
        doc = await self.repository.find_by_live_id(live_id)
        if doc:
            doc["_id"] = str(doc["_id"])
            return ReplayResponse(**doc)
        return None

    async def list_all(self) -> list[dict]:
        docs = await self.repository.find_all()
        result = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            doc["member"] = doc.pop("member_name", "")
            result.append(doc)
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
