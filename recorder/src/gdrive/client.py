"""Synchronous, serialized Drive transport; call from async workers via to_thread.

Tags are a discovery mechanism, not a distributed lock. Callers must serialize
archive ownership and enforce completion/retention policy before deletion.
"""

import hashlib
import io
import json
import mimetypes
import os
import tempfile
import threading
from functools import wraps
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
APP_PROPERTIES = {"app": "mypage48", "role": "root"}
FOLDER_MIME = "application/vnd.google-apps.folder"
FILE_FIELDS = (
    "id,name,mimeType,parents,appProperties,size,md5Checksum,sha256Checksum,"
    "trashed,shared,ownedByMe,driveId"
)


class DriveSafetyError(RuntimeError):
    """Ambiguous identity, unsafe sharing, or failed integrity verification."""


def _serialized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapped


def _quote(value):
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def validate_filename(name):
    """Return a single safe filename, rejecting remote path traversal."""
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or any(c in name for c in "/\\:")
        or any(ord(c) < 32 or ord(c) == 127 for c in name)
        or name != name.strip()
    ):
        raise DriveSafetyError("Unsafe archive filename")
    return name


def _hashes(path):
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


class DriveClient:
    """One account's Drive client. No network work happens on import.

    Pass RecorderConfig to from_config, or inject an API service for tests/OAuth.
    All returned file objects include id, name, tags, size and available hashes.
    """

    def __init__(self, service):
        self.service = service
        self._lock = threading.RLock()

    @classmethod
    def from_config(cls, config):
        values = [
            getattr(config, name, "")
            for name in (
                "google_client_id",
                "google_client_secret",
                "gdrive_refresh_token",
            )
        ]
        if not all(values):
            raise ValueError(
                "Drive requires shared Google credentials and its own refresh token"
            )
        credentials = Credentials(
            token=None,
            client_id=values[0],
            client_secret=values[1],
            refresh_token=values[2],
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
        return cls(build("drive", "v3", credentials=credentials, cache_discovery=False))

    def _list(self, query):
        result = []
        token = None
        seen = set()
        while True:
            page = (
                self.service.files()
                .list(
                    q=f"trashed = false and ({query})",
                    spaces="drive",
                    pageSize=1000,
                    pageToken=token,
                    fields=f"nextPageToken,incompleteSearch,files({FILE_FIELDS})",
                )
                .execute(num_retries=3)
            )
            if page.get("incompleteSearch"):
                raise DriveSafetyError("Drive returned an incomplete search")
            result.extend(page.get("files", []))
            token = page.get("nextPageToken")
            if not token:
                return result
            if token in seen:
                raise DriveSafetyError("Drive repeated a pagination token")
            seen.add(token)

    @staticmethod
    def _tag_query(tags):
        return " and ".join(
            "appProperties has { key = '%s' and value = '%s' }"
            % (_quote(key), _quote(value))
            for key, value in tags.items()
        )

    @_serialized
    def get_file(self, file_id):
        return (
            self.service.files()
            .get(fileId=file_id, fields=FILE_FIELDS)
            .execute(num_retries=3)
        )

    def _validate_root(self, root):
        if (
            root.get("mimeType") != FOLDER_MIME
            or root.get("trashed", False)
            or root.get("shared") is not False
            or root.get("ownedByMe") is not True
            or root.get("driveId")
            or any(
                root.get("appProperties", {}).get(k) != v
                for k, v in APP_PROPERTIES.items()
            )
        ):
            raise DriveSafetyError(
                "Managed Drive root is not private and owned in My Drive"
            )
        my_root = (
            self.service.files()
            .get(fileId="root", fields="id")
            .execute(num_retries=3)["id"]
        )
        if root.get("parents") != [my_root]:
            raise DriveSafetyError("Managed Drive root must be directly in My Drive")
        token = None
        seen = set()
        owners = 0
        while True:
            page = (
                self.service.permissions()
                .list(
                    fileId=root["id"],
                    pageToken=token,
                    fields="nextPageToken,permissions(id,type,role,deleted)",
                )
                .execute(num_retries=3)
            )
            if any(
                p.get("role") != "owner"
                or p.get("type") != "user"
                or p.get("deleted", False)
                for p in page.get("permissions", [])
            ):
                raise DriveSafetyError("Managed Drive root has unexpected permissions")
            owners += len(page.get("permissions", []))
            token = page.get("nextPageToken")
            if not token:
                break
            if token in seen:
                raise DriveSafetyError("Drive repeated a permissions pagination token")
            seen.add(token)
        if owners != 1:
            raise DriveSafetyError("Managed Drive root must have exactly one owner")
        return root

    @_serialized
    def ensure_root(self):
        roots = self._list(self._tag_query(APP_PROPERTIES))
        if len(roots) > 1:
            raise DriveSafetyError("Multiple managed Drive roots; resolve manually")
        if not roots:
            root = (
                self.service.files()
                .create(
                    body={
                        "name": "JKT48Live",
                        "mimeType": FOLDER_MIME,
                        "parents": ["root"],
                        "appProperties": APP_PROPERTIES.copy(),
                    },
                    fields=FILE_FIELDS,
                )
                .execute()
            )
        else:
            root = roots[0]
        return self._validate_root(self.get_file(root["id"]))

    @_serialized
    def list_children(self, parent_id):
        return self._list(f"'{_quote(parent_id)}' in parents")

    def _archive_tags(self, archive_key):
        if not isinstance(archive_key, str) or not archive_key.strip():
            raise ValueError("archive_key must be nonempty")
        return {"app": "mypage48", "role": "archive", "archive_key": archive_key}

    def _validate_archive(self, archive_id, archive_key=None):
        root = self.ensure_root()
        archive = self.get_file(archive_id)
        tags = archive.get("appProperties", {})
        if (
            archive_id == root["id"]
            or archive.get("mimeType") != FOLDER_MIME
            or archive.get("trashed", False)
            or archive.get("parents") != [root["id"]]
            or tags.get("app") != "mypage48"
            or tags.get("role") != "archive"
            or not tags.get("archive_key")
            or (archive_key is not None and tags.get("archive_key") != archive_key)
            or archive.get("shared") is not False
            or archive.get("ownedByMe") is not True
        ):
            raise DriveSafetyError(
                "Not a private managed archive under the managed root"
            )
        return archive

    @_serialized
    def list_archives(self):
        root = self.ensure_root()
        return self._list(
            f"'{_quote(root['id'])}' in parents and mimeType = '{FOLDER_MIME}' and "
            + self._tag_query({"app": "mypage48", "role": "archive"})
        )

    @_serialized
    def ensure_archive(self, archive_key, name):
        validate_filename(name)
        tags = self._archive_tags(archive_key)
        root = self.ensure_root()
        matches = self._list(
            f"'{_quote(root['id'])}' in parents and " + self._tag_query(tags)
        )
        if len(matches) > 1:
            raise DriveSafetyError("Multiple folders for archive key")
        if matches:
            return self._validate_archive(matches[0]["id"], archive_key)
        result = (
            self.service.files()
            .create(
                body={
                    "name": name,
                    "mimeType": FOLDER_MIME,
                    "parents": [root["id"]],
                    "appProperties": tags,
                },
                fields=FILE_FIELDS,
            )
            .execute()
        )
        return self._validate_archive(result["id"], archive_key)

    def _find_child(self, parent_id, name, tags):
        children = self.list_children(parent_id)
        matches = [
            f
            for f in children
            if f.get("name") == name
            or all(f.get("appProperties", {}).get(k) == v for k, v in tags.items())
        ]
        if len(matches) > 1:
            raise DriveSafetyError("Ambiguous archive file identity")
        if matches:
            item = matches[0]
            if (
                item.get("name") != name
                or item.get("mimeType") == FOLDER_MIME
                or any(
                    item.get("appProperties", {}).get(k) != v for k, v in tags.items()
                )
            ):
                raise DriveSafetyError("Archive filename collides with unmanaged file")
            return item
        return None

    def _file_tags(self, parent_id, name):
        archive = self._validate_archive(parent_id)
        return {
            "app": "mypage48",
            "role": "asset",
            "archive_key": archive["appProperties"]["archive_key"],
            "file_key": name,
        }

    @staticmethod
    def _verify(metadata, size, md5, sha256):
        if int(metadata.get("size", -1)) != size:
            raise DriveSafetyError("Drive file size mismatch")
        available = False
        for key, expected in (("md5Checksum", md5), ("sha256Checksum", sha256)):
            if metadata.get(key):
                available = True
                if metadata[key].lower() != expected:
                    raise DriveSafetyError("Drive file checksum mismatch")
        if not available:
            raise DriveSafetyError("Drive file has no verifiable checksum")

    def _write(self, parent_id, name, media, tags, existing=None):
        body = {"name": name, "appProperties": tags}
        if existing:
            request = self.service.files().update(
                fileId=existing["id"], body=body, media_body=media, fields=FILE_FIELDS
            )
        else:
            body["parents"] = [parent_id]
            request = self.service.files().create(
                body=body, media_body=media, fields=FILE_FIELDS
            )
        result = None
        while result is None:
            _, result = request.next_chunk(num_retries=3)
        return self.get_file(result["id"])

    @_serialized
    def upload_file(self, parent_id, local_path, name=None):
        path = Path(local_path)
        name = validate_filename(name if name is not None else path.name)
        tags = self._file_tags(parent_id, name)
        before = path.stat()
        md5, sha256 = _hashes(path)
        existing = self._find_child(parent_id, name, tags)
        if existing:
            try:
                self._verify(existing, before.st_size, md5, sha256)
            except DriveSafetyError:
                pass
            else:
                if path.stat() != before:
                    raise DriveSafetyError("Local file changed during verification")
                return existing
        media = MediaFileUpload(
            str(path),
            mimetype=mimetypes.guess_type(name)[0] or "application/octet-stream",
            chunksize=8 * 1024 * 1024,
            resumable=True,
        )
        try:
            result = self._write(parent_id, name, media, tags, existing)
        finally:
            media.stream().close()
        if path.stat() != before:
            raise DriveSafetyError("Local file changed during upload")
        self._verify(result, before.st_size, md5, sha256)
        return result

    @_serialized
    def upsert_json(self, parent_id, name, value):
        name = validate_filename(name)
        tags = self._file_tags(parent_id, name)
        payload = json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True
        ).encode("utf-8")
        existing = self._find_child(parent_id, name, tags)
        result = self._write(
            parent_id,
            name,
            MediaIoBaseUpload(
                io.BytesIO(payload), mimetype="application/json", resumable=True
            ),
            tags,
            existing,
        )
        self._verify(
            result,
            len(payload),
            hashlib.md5(payload, usedforsecurity=False).hexdigest(),
            hashlib.sha256(payload).hexdigest(),
        )
        return result

    @_serialized
    def get_json(self, file_id, max_bytes=4 * 1024 * 1024):
        metadata = self.get_file(file_id)
        if int(metadata.get("size", -1)) not in range(max_bytes + 1):
            raise DriveSafetyError("JSON file exceeds size limit or has no size")
        stream = io.BytesIO()
        download = MediaIoBaseDownload(
            stream,
            self.service.files().get_media(fileId=file_id),
            chunksize=min(max_bytes + 1, 1024 * 1024),
        )
        done = False
        while not done:
            _, done = download.next_chunk(num_retries=3)
            if stream.tell() > max_bytes:
                raise DriveSafetyError("JSON file exceeds size limit")
        payload = stream.getvalue()
        self._verify(
            metadata,
            len(payload),
            hashlib.md5(payload, usedforsecurity=False).hexdigest(),
            hashlib.sha256(payload).hexdigest(),
        )
        return json.loads(payload.decode("utf-8"))

    @_serialized
    def download_file(
        self,
        file_id,
        destination,
        *,
        expected_size=None,
        expected_md5=None,
        expected_sha256=None,
    ):
        """Download to an explicit local path, verify, then atomically replace.

        Optional expected values are manifest values, checked in addition to Drive.
        The caller owns the destination directory; remote names never form paths.
        """
        metadata = self.get_file(file_id)
        validate_filename(metadata["name"])
        destination = Path(destination)
        validate_filename(destination.name)
        fd, temporary = tempfile.mkstemp(
            prefix=".drive-", suffix=".part", dir=destination.parent
        )
        try:
            with os.fdopen(fd, "wb") as stream:
                download = MediaIoBaseDownload(
                    stream,
                    self.service.files().get_media(fileId=file_id),
                    chunksize=8 * 1024 * 1024,
                )
                done = False
                while not done:
                    _, done = download.next_chunk(num_retries=3)
                stream.flush()
                os.fsync(stream.fileno())
            size = Path(temporary).stat().st_size
            md5, sha256 = _hashes(temporary)
            self._verify(metadata, size, md5, sha256)
            if (
                (expected_size is not None and size != int(expected_size))
                or (expected_md5 is not None and md5 != expected_md5.lower())
                or (expected_sha256 is not None and sha256 != expected_sha256.lower())
            ):
                raise DriveSafetyError("Downloaded file differs from archive manifest")
            os.replace(temporary, destination)
            return destination
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @_serialized
    def delete_archive(self, archive_id, archive_key):
        """Permanently delete a managed archive, NOT trash it.

        Caller MUST first validate the completion receipt, retention policy and
        exclusive job ownership. This transport only validates identity/ancestry.
        """
        self._validate_archive(archive_id, archive_key)
        self.service.files().delete(fileId=archive_id).execute(num_retries=3)
