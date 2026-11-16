"""Shared, deliberately strict Drive archive format."""

import hashlib
import json
import re
from pathlib import Path

from .client import DriveSafetyError, validate_filename

SCHEMA_VERSION = 1
MANIFEST_NAME = "archive_manifest.json"
READY_NAME = ".drive_ready"
ROLES = {"video", "metadata", "thumbnail", "notification"}


def archive_key_for(folder, meta):
    """Identity survives relocation of the recordings root, not folder renames."""
    identity = [
        Path(folder).name,
        meta.get("live_id"),
        meta.get("platform"),
        meta.get("start_at"),
        meta.get("recording_started_at"),
    ]
    if not all(isinstance(value, str) and value for value in identity[:3]):
        raise DriveSafetyError("Incomplete recording identity")
    validate_filename(identity[0])
    validate_filename(identity[1])
    if any(value is not None and not isinstance(value, str) for value in identity[3:]):
        raise DriveSafetyError("Invalid recording start identity")
    if not any(value and value.strip() for value in identity[3:]):
        raise DriveSafetyError("Missing recording start identity")
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def normalize_member_nickname(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise DriveSafetyError("Invalid member_nickname")
    return value.strip()


def validate_manifest(value) -> dict:
    """Validate untrusted remote data before any staging paths are constructed."""
    if not isinstance(value, dict):
        raise DriveSafetyError("Manifest must be an object")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise DriveSafetyError("Unsupported manifest schema")
    if not isinstance(value.get("archive_key"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", value["archive_key"]
    ):
        raise DriveSafetyError("Invalid archive key")
    for field in ("live_id", "platform", "recording_folder"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise DriveSafetyError(f"Invalid {field}")
    value = {
        **value,
        "member_nickname": normalize_member_nickname(value.get("member_nickname")),
    }
    validate_filename(value["live_id"])
    validate_filename(value["recording_folder"])
    metadata = validate_filename(value.get("metadata_filename"))
    if metadata != f"{value['live_id']}.json":
        raise DriveSafetyError("Metadata must be the explicit live ID JSON")
    files = value.get("files")
    if not isinstance(files, list) or not files:
        raise DriveSafetyError("Missing archive files")
    names, ids, roles = set(), set(), []
    for item in files:
        if not isinstance(item, dict):
            raise DriveSafetyError("Invalid file entry")
        name = validate_filename(item.get("name"))
        role, file_id = item.get("role"), item.get("id")
        if not isinstance(role, str) or role not in ROLES:
            raise DriveSafetyError("Invalid file role")
        if not isinstance(file_id, str) or not file_id.strip():
            raise DriveSafetyError("Invalid file ID")
        if name in names or file_id in ids:
            raise DriveSafetyError("Duplicate file name or ID")
        if name in {MANIFEST_NAME, READY_NAME, ".yt_done", ".r2_done"}:
            raise DriveSafetyError("Reserved archive filename")
        if type(item.get("size")) is not int or item["size"] < 0:
            raise DriveSafetyError("Invalid file size")
        if not isinstance(item.get("md5Checksum"), str) or not re.fullmatch(
            r"[0-9a-fA-F]{32}", item["md5Checksum"]
        ):
            raise DriveSafetyError("Invalid file checksum")
        if (role == "metadata") != (name == metadata):
            raise DriveSafetyError("Metadata role mismatch")
        if role == "video" and (name != f"{value['live_id']}.mp4" or item["size"] == 0):
            raise DriveSafetyError("Invalid final video")
        if role == "thumbnail" and name != f"{value['live_id']}_yt_thumb.jpg":
            raise DriveSafetyError("Invalid thumbnail")
        names.add(name)
        ids.add(file_id)
        roles.append(role)
    if roles.count("metadata") != 1 or roles.count("video") != 1:
        raise DriveSafetyError("Exactly one metadata file and video required")
    for field in ("youtube_id", "youtube_title"):
        if field in value and not isinstance(value[field], str):
            raise DriveSafetyError(f"Invalid {field}")
    return value
