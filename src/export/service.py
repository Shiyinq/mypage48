import asyncio
import base64
import hashlib
import io
import zipfile
from datetime import datetime, timedelta

import pandas as pd
import requests

from src.config import Settings
from src.export.constants import ExportStatus
from src.export.exceptions import ExportInProgressError, ExportNotFoundError
from src.export.repository import ExportRepository
from src.export.schemas import ExportResponse
from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger
from src.members.repository import MemberRepository
from src.memories.repository import MemoriesRepository
from src.storage.repository import StorageRepository
from src.tickets.repository import TicketsRepository
from src.users.repository import UserRepository

logger = create_logger("export_service", __name__)


class ExportService:
    def __init__(
        self,
        export_repo: ExportRepository,
        tickets_repo: TicketsRepository,
        memories_repo: MemoriesRepository,
        storage_repo: StorageRepository,
        users_repo: UserRepository,
        members_repo: MemberRepository,
        background_tasks: BackgroundTaskRunner,
        config: Settings,
    ):
        self.export_repo = export_repo
        self.tickets_repo = tickets_repo
        self.memories_repo = memories_repo
        self.storage_repo = storage_repo
        self.users_repo = users_repo
        self.members_repo = members_repo
        self.background_tasks = background_tasks
        self.config = config

    async def get_status(self, user_id: str) -> ExportResponse:
        job = await self.export_repo.get_job(user_id)
        if not job:
            return ExportResponse(status=ExportStatus.IDLE)

        # Check if job is stale (e.g. processing for > 1 hour)
        if job.status == ExportStatus.PROCESSING:
            if datetime.utcnow() - job.updated_at > timedelta(hours=1):
                await self.export_repo.update_status(
                    user_id, ExportStatus.FAILED, error="Timeout"
                )
                return ExportResponse(
                    status=ExportStatus.FAILED, message="Job timed out"
                )

        response = ExportResponse(status=job.status)
        if job.status == ExportStatus.COMPLETED and job.updated_at:
            # Expire after 24 hours
            expires_at = job.updated_at + timedelta(hours=24)
            response.expires_at = expires_at
            if datetime.utcnow() > expires_at:
                # Clean up expired job lazily
                await self.export_repo.delete_job(user_id)
                if job.file_path:
                    await self.storage_repo.delete_file(job.file_path)
                return ExportResponse(status=ExportStatus.IDLE)

        return response

    async def initiate_export(self, user_id: str) -> ExportResponse:
        job = await self.export_repo.get_job(user_id)

        # If job exists and is valid/processing, return status
        if job:
            if job.status == ExportStatus.PROCESSING:
                raise ExportInProgressError()

            if job.status == ExportStatus.COMPLETED:
                # Check expiry
                expires_at = job.updated_at + timedelta(hours=24)
                if datetime.utcnow() < expires_at:
                    return ExportResponse(
                        status=ExportStatus.COMPLETED, expires_at=expires_at
                    )
                else:
                    # Expired, allow new
                    pass

        # Create new job
        await self.export_repo.create_job(user_id)

        # Add background task
        self.background_tasks.add_task(self._process_export, user_id)

        return ExportResponse(status=ExportStatus.PROCESSING)

    async def _process_export(self, user_id: str):
        try:
            logger.info(f"Starting export for user {user_id}")

            # 1. Fetch Data
            tickets, _ = await self.tickets_repo.get_tickets(user_id, limit=9999)

            # Fetch user profile picture and Oshi
            user_doc = await self.users_repo.get_user_by_id(user_id)
            if not user_doc:
                user_doc = {}

            # Try multiple keys for profile picture (User reported 'avatar')
            profile_pic_url = user_doc.get("profilePicture")

            oshi_img_url = None
            # Try multiple keys for Oshi ID
            oshi_id = user_doc.get("oshiId")

            if oshi_id:
                # Oshi ID is stored as string in user doc, matches 'id' in members collection
                oshi_doc = await self.members_repo.find_by_id(str(oshi_id))
                if oshi_doc:
                    oshi_img_url = oshi_doc.get("img")

            # 2. Generate Excel (Merged Data)
            export_data = []
            for t in tickets:
                evt = t.get("event", {})
                seat = t.get("seat", {})

                # Base Ticket Data
                row = {
                    "Date": evt.get("date"),
                    "Time": evt.get("time"),
                    "Title": evt.get("title"),
                    "Venue": evt.get("venue"),
                    "Seat": f"{seat.get('section', '')} - {seat.get('number', '')}",
                    "Price": t.get("price"),
                    "Currency": t.get("currency"),
                    "Ticket Image": "YES" if t.get("imageUrl") else "NO",
                }

                # 2-Shot Data (if available)
                if t.get("two_shot"):
                    ts = t["two_shot"]
                    row.update(
                        {
                            "2-Shot Member": ts.get("member_name"),
                            "2-Shot Type": ts.get("type"),
                            "2-Shot Price": ts.get("price"),
                            "2-Shot Image": "YES" if ts.get("imageUrl") else "NO",
                        }
                    )
                else:
                    row.update(
                        {
                            "2-Shot Member": "",
                            "2-Shot Type": "",
                            "2-Shot Price": "",
                            "2-Shot Image": "NO",
                        }
                    )

                export_data.append(row)

            df_merged = pd.DataFrame(export_data)

            # 3. Create Zip
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add Excel
                with io.BytesIO() as excel_buffer:
                    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                        df_merged.to_excel(writer, sheet_name="Data", index=False)
                    excel_buffer.seek(0)
                    zip_file.writestr("data.xlsx", excel_buffer.getvalue())

                # Helper to safely download and add file
                async def add_file_to_zip(
                    path: str, zip_path_prefix: str, custom_name: str = None
                ):
                    if not path:
                        return

                    # Avoid logging long strings (likely base64)
                    if len(path) > 256:
                        logger.info(
                            f"Processing image (len={len(path)}) for {zip_path_prefix}"
                        )
                    else:
                        logger.info(
                            f"Attempting to add file: {path} -> {zip_path_prefix}"
                        )

                    file_data = None
                    fname = custom_name or "image.png"

                    try:
                        # Case 1: Data URI or Long String (Base64)
                        if path.startswith("data:") or len(path) > 500:
                            try:
                                encoded = path
                                if "base64," in path:
                                    header, encoded = path.split("base64,", 1)
                                    if "image/png" in header:
                                        fname = custom_name or "image.png"
                                    elif "image/jpeg" in header:
                                        fname = custom_name or "image.jpg"

                                file_data = base64.b64decode(encoded)

                                if not custom_name:
                                    # Generate name hash if no custom name
                                    # Use .png as default safe extension for base64
                                    name_hash = hashlib.md5(
                                        encoded.encode()
                                    ).hexdigest()[:10]
                                    fname = f"{name_hash}.png"
                            except Exception as b64e:
                                logger.warning(f"Failed to decode base64 image: {b64e}")
                                return

                        # Case 2: External URL (HTTP/HTTPS)
                        elif path.startswith(("http", "https")):
                            logger.info(f"Downloading external image")
                            res = await asyncio.to_thread(
                                requests.get, path, timeout=10
                            )
                            if res.status_code == 200:
                                file_data = res.content
                                if not custom_name:
                                    fname = path.split("/")[-1].split("?")[0]
                            else:
                                logger.warning(
                                    f"Failed to download {path}: {res.status_code}"
                                )
                                return

                        # Case 3: Internal MinIO Path OR Fallback
                        # If it has a slash or looks like a filename, try MinIO
                        elif "/" in path or (len(path) < 256 and "." in path):
                            logger.info(f"Downloading MinIO image: {path}")
                            file_data = await self.storage_repo.get_file(path)

                            if not custom_name and "/" in path:
                                fname = path.split("/")[-1]

                        if file_data:
                            # Ensure we have a valid filename
                            if not fname or fname == ".":
                                fname = "image.png"

                            zip_file.writestr(f"{zip_path_prefix}/{fname}", file_data)
                        else:
                            # logger.warning(f"No file data retrieved") # Reduce noise
                            pass

                    except Exception as e:
                        logger.error(f"Error adding file to export: {e}")

                # Add Profile Picture
                await add_file_to_zip(profile_pic_url, "images/profile", "profile.jpg")

                # Add Oshi Image
                await add_file_to_zip(oshi_img_url, "images/oshi", "oshi.jpg")

                # Add Images
                for t in tickets:
                    # Ticket Image
                    if t.get("imageUrl"):
                        # Use ticket ID in name to avoid collisions if path is messy
                        t_id = t.get("ticket_id", "unknown")
                        name = None
                        if len(t["imageUrl"]) < 500 and "/" in t["imageUrl"]:
                            name = t["imageUrl"].split("/")[-1]
                        else:
                            name = f"ticket_{t_id}.jpg"
                        await add_file_to_zip(t["imageUrl"], "images/tickets", name)

                    # 2Shot Image
                    if t.get("two_shot") and t["two_shot"].get("imageUrl"):
                        # Use member name or ID for 2shot
                        val = t["two_shot"].get("imageUrl")
                        ts_name = None
                        if len(val) < 500 and "/" in val:
                            ts_name = val.split("/")[-1]
                        else:
                            member = (
                                t["two_shot"]
                                .get("member_name", "member")
                                .replace(" ", "_")
                            )
                            ts_name = f"2shot_{member}_{t.get('ticket_id', 'id')}.jpg"

                        await add_file_to_zip(val, "images/2shots", ts_name)

            zip_buffer.seek(0)

            # 4. Upload Zip
            zip_filename = (
                f"exports/{user_id}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
            )
            await self.storage_repo.upload_file(
                zip_buffer.getvalue(), zip_filename, content_type="application/zip"
            )

            # 5. Update Status
            await self.export_repo.update_status(
                user_id, ExportStatus.COMPLETED, file_path=zip_filename
            )
            logger.info(f"Export completed for user {user_id}")

        except Exception as e:
            logger.exception(f"Export failed for user {user_id}: {e}")
            await self.export_repo.update_status(
                user_id, ExportStatus.FAILED, error=str(e)
            )

    async def download_export(
        self, user_id: str
    ):  # Returns tuple: (stream, filename, cleanup_func)
        job = await self.export_repo.get_job(user_id)

        if not job or job.status != ExportStatus.COMPLETED or not job.file_path:
            raise ExportNotFoundError(message="Export file not available.")

        # Check expiry
        expires_at = job.updated_at + timedelta(hours=24)
        if datetime.utcnow() > expires_at:
            await self.export_repo.delete_job(user_id)
            await self.storage_repo.delete_file(job.file_path)
            raise ExportNotFoundError(message="Export file expired.")

        # Get stream
        stream = await self.storage_repo.get_file_stream(job.file_path)
        if not stream:
            raise ExportNotFoundError(message="File not found in storage.")

        # Define cleanup
        async def cleanup():
            try:
                # Use close on stream if needed? MinIO response usually needs close.
                stream.close()
                stream.release_conn()
            except:
                pass

            # Delete file and job
            logger.info(f"Cleaning up export for user {user_id}")
            await self.storage_repo.delete_file(job.file_path)
            await self.export_repo.delete_job(user_id)

        filename = "mypage48_export.zip"
        return stream, filename, cleanup
