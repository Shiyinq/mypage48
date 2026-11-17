"""Bounded, self-contained permanent archive recovery records."""

import json
import re
from datetime import datetime, timedelta, timezone

from .client import DriveSafetyError

MONTHS = (
    "Januari Februari Maret April Mei Juni Juli Agustus "
    "September Oktober November Desember"
).split()
PREFIX = "keep_"


def display_name(metadata, nickname):
    try:
        start = datetime.fromisoformat(metadata["start_at"].replace("Z", "+00:00"))
        if start.tzinfo is None:
            raise ValueError("Missing timezone")
        start = start.astimezone(timezone(timedelta(hours=7)))
        nickname = nickname.strip().lower()
        if not nickname or any(c in nickname for c in "/\\:_"):
            raise ValueError("Invalid nickname")
        name = (
            f"{nickname} {start.day} {MONTHS[start.month - 1]} {start.year} "
            f"{start:%H:%M} WIB"
        )
        if any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise ValueError("Invalid display name")
        return name
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise DriveSafetyError(
            "Missing or invalid permanent archive date/name"
        ) from exc


def encode_marker(tags, record):
    payload = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    # Split by UTF-8 bytes, never through a Unicode codepoint.
    chunks = [""]
    for char in payload:
        if len((chunks[-1] + char).encode()) > 110:
            chunks.append("")
        chunks[-1] += char
    result = {k: v for k, v in tags.items() if not k.startswith(PREFIX)}
    result.update({f"{PREFIX}{i:02d}": chunk for i, chunk in enumerate(chunks)})
    if len(result) > 30 or any(
        len(k.encode()) + len(v.encode()) > 124 for k, v in result.items()
    ):
        raise DriveSafetyError("Permanent marker exceeds Drive appProperty limits")
    return result


def decode_marker(tags):
    keys = sorted(k for k in tags if k.startswith(PREFIX))
    if not keys:
        return None
    if keys != [f"{PREFIX}{i:02d}" for i in range(len(keys))]:
        raise DriveSafetyError("Incomplete permanent marker")
    try:
        record = json.loads("".join(tags[k] for k in keys))
        if record["version"] != 1 or record["state"] not in {"pending", "finalized"}:
            raise ValueError("Unsupported marker")
        if not isinstance(record["name"], str) or not re.fullmatch(
            r"[^/\\\\:_\x00-\x1f\x7f]+ [1-9][0-9]? (?:"
            + "|".join(MONTHS)
            + r") [0-9]{4} [0-2][0-9]:[0-5][0-9] WIB",
            record["name"],
        ):
            raise ValueError("Invalid permanent name")
        from .youtube_worker import validate_receipt

        receipt = validate_receipt(record["receipt"], tags.get("archive_key"))
        if receipt["retention"] != "keep" or receipt["retention_reason"] not in {
            "member_exception",
            "deletion_disabled",
        }:
            raise ValueError("Not a kept archive")
        if not isinstance(record["assets"], list) or not record["assets"]:
            raise ValueError("Missing assets")
        ids, names = set(), set()
        for asset in record["assets"]:
            from .client import validate_filename

            validate_filename(asset["name"])
            if not isinstance(asset["id"], str) or not asset["id"]:
                raise ValueError("Invalid asset ID")
            if asset["name"].lower().endswith(".mp4") and (
                type(asset.get("size")) is not int
                or asset["size"] <= 0
                or not isinstance(asset.get("md5Checksum"), str)
                or not re.fullmatch(r"[0-9a-fA-F]{32}", asset["md5Checksum"])
            ):
                raise ValueError("Invalid video integrity")
            if asset["id"] in ids or asset["name"] in names:
                raise ValueError("Duplicate assets")
            ids.add(asset["id"])
            names.add(asset["name"])
        if not any(a["name"].lower().endswith(".mp4") for a in record["assets"]):
            raise ValueError("Missing video")
        encode_marker(tags, record)
        return record
    except (KeyError, TypeError, ValueError) as exc:
        raise DriveSafetyError("Malformed permanent archive marker") from exc
