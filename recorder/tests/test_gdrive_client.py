"""Offline regression tests for the synchronous Drive transport."""

import copy
import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from recorder.src.gdrive import client as drive_module
from recorder.src.gdrive.client import (
    APP_PROPERTIES,
    FOLDER_MIME,
    DriveClient,
    DriveSafetyError,
    validate_filename,
)


def metadata(payload=b"video", **overrides):
    result = {
        "id": "asset",
        "name": "video.mp4",
        "mimeType": "video/mp4",
        "parents": ["archive"],
        "size": str(len(payload)),
        "md5Checksum": hashlib.md5(payload).hexdigest(),
        "sha256Checksum": hashlib.sha256(payload).hexdigest(),
        "appProperties": {
            "app": "mypage48",
            "role": "asset",
            "archive_key": "recording-123",
            "file_key": "video.mp4",
        },
    }
    result.update(overrides)
    return result


@pytest.fixture
def fake():
    service = MagicMock()
    files = service.files.return_value
    root = {
        "id": "managed-root",
        "name": "JKT48Live",
        "mimeType": FOLDER_MIME,
        "parents": ["my-drive"],
        "appProperties": APP_PROPERTIES.copy(),
        "shared": False,
        "ownedByMe": True,
        "trashed": False,
    }
    archive = {
        "id": "archive",
        "name": "recording",
        "mimeType": FOLDER_MIME,
        "parents": [root["id"]],
        "shared": False,
        "ownedByMe": True,
        "appProperties": {
            "app": "mypage48",
            "role": "archive",
            "archive_key": "recording-123",
        },
    }
    state = SimpleNamespace(
        service=service,
        files=files,
        root=root,
        archive=archive,
        roots=[root],
        children=[],
        objects={root["id"]: root, "archive": archive},
        client=DriveClient(service),
    )

    def get(**kwargs):
        value = (
            {"id": "my-drive"}
            if kwargs["fileId"] == "root"
            else state.objects[kwargs["fileId"]]
        )
        request = MagicMock()
        request.execute.return_value = copy.deepcopy(value)
        return request

    def listing(**kwargs):
        request = MagicMock()
        values = state.roots if "value = 'root'" in kwargs["q"] else state.children
        if "'root' in parents" in kwargs["q"]:
            values = [item for item in values if item.get("parents") == ["my-drive"]]
        request.execute.return_value = {"files": copy.deepcopy(values)}
        return request

    files.get.side_effect = get
    files.list.side_effect = listing

    def create_root():
        state.roots.append(root)
        return {"id": root["id"]}

    files.create.return_value.execute.side_effect = create_root
    service.permissions.return_value.list.return_value.execute.return_value = {
        "permissions": [{"id": "owner", "role": "owner", "type": "user"}]
    }
    return state


def test_root_reused_by_tags_not_display_name(fake):
    fake.root["name"] = "Renamed by owner"
    assert fake.client.ensure_root()["id"] == fake.root["id"]
    fake.files.create.assert_not_called()
    query = fake.files.list.call_args.kwargs["q"]
    assert "appProperties" in query and "value = 'root'" in query
    assert "name =" not in query


def test_root_created_private_in_my_drive_and_refetched(fake):
    fake.roots = []
    assert fake.client.ensure_root()["id"] == fake.root["id"]
    body = fake.files.create.call_args.kwargs["body"]
    assert body == {
        "name": "JKT48Live",
        "mimeType": FOLDER_MIME,
        "parents": ["root"],
        "appProperties": APP_PROPERTIES,
    }
    assert fake.files.get.call_args_list[0].kwargs["fileId"] == fake.root["id"]
    fake.service.permissions.return_value.create.assert_not_called()


@pytest.mark.parametrize("create", [False, True])
def test_drive_file_root_404_does_not_block_managed_folder(fake, create):
    from googleapiclient.errors import HttpError
    from httplib2 import Response

    if create:
        fake.roots = []
    original_get = fake.files.get.side_effect

    def scoped_get(**kwargs):
        if kwargs["fileId"] == "root":
            raise HttpError(
                Response({"status": "404"}), b'{"error":{"message":"File not found"}}'
            )
        return original_get(**kwargs)

    fake.files.get.side_effect = scoped_get
    assert fake.client.ensure_root()["id"] == fake.root["id"]
    assert all(
        call.kwargs["fileId"] != "root" for call in fake.files.get.call_args_list
    )
    assert any(
        "'root' in parents" in call.kwargs["q"]
        for call in fake.files.list.call_args_list
    )
    assert fake.client.authorization_failed is False
    assert fake.files.create.call_count == int(create)


def test_root_ambiguity_fails_without_creation(fake):
    fake.roots.append(dict(fake.root, id="duplicate"))
    with pytest.raises(DriveSafetyError, match="Multiple managed"):
        fake.client.ensure_root()
    fake.files.create.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"shared": True},
        {"shared": None},
        {"ownedByMe": False},
        {"driveId": "shared-drive"},
        {"trashed": True},
        {"parents": ["foreign-folder"]},
        {"mimeType": "text/plain"},
        {"appProperties": {"app": "other", "role": "root"}},
    ],
)
def test_unsafe_root_rejected(fake, changes):
    fake.root.update(changes)
    with pytest.raises(DriveSafetyError):
        fake.client.ensure_root()
    fake.service.permissions.return_value.delete.assert_not_called()


@pytest.mark.parametrize(
    "permissions",
    [
        [],
        [{"role": "reader", "type": "anyone"}],
        [{"role": "owner", "type": "user", "deleted": True}],
        [{"role": "owner", "type": "user"}, {"role": "writer", "type": "user"}],
    ],
)
def test_unexpected_root_permissions_rejected(fake, permissions):
    fake.service.permissions.return_value.list.return_value.execute.return_value = {
        "permissions": permissions
    }
    with pytest.raises(DriveSafetyError):
        fake.client.ensure_root()


@pytest.mark.parametrize("method", ["list_children", "list_archives"])
def test_paginated_listing(fake, monkeypatch, method):
    if method == "list_archives":
        monkeypatch.setattr(fake.client, "ensure_root", lambda: fake.root)
    requests = []

    def listing(**kwargs):
        requests.append(kwargs)
        request = MagicMock()
        request.execute.return_value = (
            {"files": [{"id": "first"}], "nextPageToken": "page-2"}
            if kwargs["pageToken"] is None
            else {"files": [{"id": "second"}]}
        )
        return request

    fake.files.list.side_effect = listing
    result = (
        fake.client.list_archives()
        if method == "list_archives"
        else fake.client.list_children("parent's\\folder")
    )
    assert [f["id"] for f in result] == ["first", "second"]
    assert [r["pageToken"] for r in requests] == [None, "page-2"]
    assert all("trashed = false" in r["q"] for r in requests)
    if method == "list_archives":
        assert "value = 'archive'" in requests[0]["q"]
        assert "'managed-root' in parents" in requests[0]["q"]
    else:
        assert "parent\\'s\\\\folder" in requests[0]["q"]


@pytest.mark.parametrize(
    "page, message",
    [
        ({"incompleteSearch": True}, "incomplete"),
        ({"nextPageToken": "repeated", "files": []}, "pagination"),
    ],
)
def test_incomplete_or_repeated_pagination_rejected(fake, page, message):
    fake.files.list.side_effect = None
    fake.files.list.return_value.execute.return_value = page
    with pytest.raises(DriveSafetyError, match=message):
        fake.client.list_children("archive")


@pytest.fixture
def local_video(tmp_path):
    path = tmp_path / "video.mp4"
    path.write_bytes(b"video")
    return path


def prepare_upload(fake, result):
    fake.objects["asset"] = result
    request = fake.files.create.return_value
    request.next_chunk.side_effect = [(MagicMock(), None), (None, {"id": "asset"})]
    fake.files.update.return_value.next_chunk.return_value = (None, {"id": "asset"})


def test_upload_resumable_and_verified(fake, local_video):
    prepare_upload(fake, metadata())
    assert fake.client.upload_file("archive", local_video)["id"] == "asset"
    kwargs = fake.files.create.call_args.kwargs
    assert kwargs["body"]["parents"] == ["archive"]
    assert kwargs["body"]["appProperties"] == metadata()["appProperties"]
    assert kwargs["media_body"].resumable()
    assert fake.files.create.return_value.next_chunk.call_count == 2
    fake.files.update.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"size": "999"},
        {"md5Checksum": "0" * 32},
        {"sha256Checksum": "0" * 64},
        {"md5Checksum": None, "sha256Checksum": None},
    ],
)
def test_upload_rejects_unverified_remote_file(fake, local_video, changes):
    prepare_upload(fake, metadata(**changes))
    with pytest.raises(DriveSafetyError):
        fake.client.upload_file("archive", local_video)
    assert local_video.read_bytes() == b"video"


def test_upload_reuses_matching_tagged_name_size_and_checksum(fake, local_video):
    fake.children = [metadata()]
    assert fake.client.upload_file("archive", local_video)["id"] == "asset"
    fake.files.create.assert_not_called()
    fake.files.update.assert_not_called()


def test_upload_updates_mismatched_managed_asset_by_id(fake, local_video):
    fake.children = [metadata(md5Checksum="0" * 32)]
    prepare_upload(fake, metadata())
    fake.client.upload_file("archive", local_video)
    assert fake.files.update.call_args.kwargs["fileId"] == "asset"
    fake.files.create.assert_not_called()


@pytest.mark.parametrize(
    "children",
    [
        [metadata(appProperties={})],
        [metadata(), metadata(id="duplicate")],
        [metadata(name="renamed.mp4")],
    ],
)
def test_upload_rejects_unmanaged_collision_or_ambiguous_identity(
    fake, local_video, children
):
    fake.children = children
    with pytest.raises(DriveSafetyError):
        fake.client.upload_file("archive", local_video)
    fake.files.create.assert_not_called()
    fake.files.update.assert_not_called()


def test_upload_detects_local_change(fake, local_video):
    prepare_upload(fake, metadata())

    def upload(**kwargs):
        local_video.write_bytes(b"changed during upload")
        return None, {"id": "asset"}

    fake.files.create.return_value.next_chunk.side_effect = upload
    with pytest.raises(DriveSafetyError, match="Local file changed"):
        fake.client.upload_file("archive", local_video)


def test_delete_managed_archive_is_permanent_not_trash(fake):
    fake.client.delete_archive("archive", "recording-123")
    fake.files.delete.assert_called_once_with(fileId="archive")
    fake.files.delete.return_value.execute.assert_called_once_with(num_retries=3)
    fake.files.update.assert_not_called()


@pytest.mark.parametrize(
    "target, key, changes",
    [
        ("managed-root", "recording-123", {}),
        ("archive", "wrong-key", {}),
        ("archive", "recording-123", {"parents": ["foreign"]}),
        ("archive", "recording-123", {"appProperties": {}}),
        ("archive", "recording-123", {"shared": True}),
        ("archive", "recording-123", {"mimeType": "text/plain"}),
    ],
)
def test_delete_protects_root_and_nonmanaged_targets(fake, target, key, changes):
    fake.archive.update(changes)
    with pytest.raises(DriveSafetyError):
        fake.client.delete_archive(target, key)
    fake.files.delete.assert_not_called()


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../escape",
        "/absolute",
        "a/b",
        "a\\b",
        "C:evil",
        " bad",
        "bad ",
        "bad\x00",
        "bad\n",
        "bad\x7f",
        None,
    ],
)
def test_unsafe_filenames_rejected(name):
    with pytest.raises(DriveSafetyError):
        validate_filename(name)


@pytest.mark.parametrize(
    "name", ["video.mp4", ".yt_done", "archive_manifest.json", "メンバー.jpg"]
)
def test_safe_filenames_accepted(name):
    assert validate_filename(name) == name


def test_download_verifies_and_atomically_preserves_existing_file(
    fake, tmp_path, monkeypatch
):
    payload = b"video"
    fake.objects["asset"] = metadata(payload)

    class Download:
        def __init__(self, stream, request, **kwargs):
            self.stream = stream

        def next_chunk(self, **kwargs):
            self.stream.write(payload)
            return None, True

    monkeypatch.setattr(drive_module, "MediaIoBaseDownload", Download)
    target = tmp_path / "video.mp4"
    assert fake.client.download_file("asset", target).read_bytes() == payload
    target.write_bytes(b"preserve existing")
    with pytest.raises(DriveSafetyError, match="manifest"):
        fake.client.download_file("asset", target, expected_sha256="bad")
    assert target.read_bytes() == b"preserve existing"
    assert list(tmp_path.iterdir()) == [target]


def test_config_uses_drive_token_not_youtube_token(monkeypatch):
    credentials = MagicMock()
    build = MagicMock()
    monkeypatch.setattr(drive_module, "Credentials", credentials)
    monkeypatch.setattr(drive_module, "build", build)
    config = SimpleNamespace(
        google_client_id="client",
        google_client_secret="secret",
        gdrive_refresh_token="drive-token",
        youtube_refresh_token="youtube-token",
    )
    DriveClient.from_config(config)
    assert credentials.call_args.kwargs["refresh_token"] == "drive-token"
    assert credentials.call_args.kwargs["scopes"] == drive_module.SCOPES
    config.gdrive_refresh_token = ""
    with pytest.raises(ValueError):
        DriveClient.from_config(config)
