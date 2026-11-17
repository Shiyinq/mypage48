"""Offline permanent archive state-machine and safety tests."""

import copy
from unittest.mock import MagicMock

import pytest

from recorder.src.gdrive.client import FOLDER_MIME, DriveClient, DriveSafetyError
from recorder.src.gdrive.permanent import decode_marker, display_name, encode_marker

KEY = "a" * 64
TAGS = {"app": "mypage48", "role": "archive", "archive_key": KEY}


def record():
    return {
        "version": 1,
        "state": "pending",
        "name": "erine 13 Agustus 2026 20:15 WIB",
        "receipt": {
            "schema_version": 1,
            "archive_key": KEY,
            "live_id": "live",
            "member_nickname": "Erine",
            "youtube_id": "yt",
            "completed_at": "2026-08-13T14:00:00+00:00",
            "retention": "keep",
            "retention_reason": "member_exception",
        },
        "assets": [
            {"id": "video", "name": "live.mp4", "size": 5, "md5Checksum": "b" * 32},
            {
                "id": "meta",
                "name": "live.json",
                "role": "metadata",
                "size": 12,
                "md5Checksum": "c" * 32,
            },
            {"id": "done", "name": ".yt_done"},
        ],
    }


@pytest.fixture
def drive(monkeypatch):
    service = MagicMock()
    client = DriveClient(service)
    objects = {
        "root": {"id": "root"},
        "permanent": {"id": "permanent"},
        "archive": {
            "id": "archive",
            "parents": ["root"],
            "name": "old",
            "appProperties": TAGS.copy(),
            "mimeType": FOLDER_MIME,
            "shared": False,
            "ownedByMe": True,
        },
    }
    for asset in record()["assets"]:
        objects[asset["id"]] = {
            **asset,
            "parents": ["archive"],
            "mimeType": "application/octet-stream",
            "shared": False,
            "ownedByMe": True,
            "appProperties": {**TAGS, "role": "asset", "file_key": asset["name"]},
        }
    monkeypatch.setattr(client, "ensure_root", lambda: objects["root"])
    monkeypatch.setattr(client, "get_file", lambda id: copy.deepcopy(objects[id]))
    monkeypatch.setattr(
        client, "_permanent_folder", lambda create=False: objects["permanent"]
    )
    monkeypatch.setattr(
        client,
        "list_children",
        lambda id: [
            copy.deepcopy(o) for o in objects.values() if o.get("parents") == [id]
        ],
    )
    events = []

    def update(**kwargs):
        def execute():
            events.append(("update", copy.deepcopy(kwargs)))
            obj = objects[kwargs["fileId"]]
            obj.update(copy.deepcopy(kwargs.get("body", {})))
            if "addParents" in kwargs:
                obj["parents"] = [kwargs["addParents"]]
            return copy.deepcopy(obj)

        return MagicMock(execute=execute)

    def delete(**kwargs):
        def execute(**unused):
            events.append(("delete", kwargs["fileId"]))
            del objects[kwargs["fileId"]]

        return MagicMock(execute=execute)

    service.files.return_value.update.side_effect = update
    service.files.return_value.delete.side_effect = delete
    return client, objects, events


def test_name_utc_to_wib_and_colon():
    assert (
        display_name({"start_at": "2026-08-13T13:15:00Z"}, "Erine") == record()["name"]
    )


@pytest.mark.parametrize(
    "value", [None, "", "invalid", "2026-08-13", "2026-02-30T12:00:00Z"]
)
def test_invalid_dates(value):
    with pytest.raises(DriveSafetyError):
        display_name({"start_at": value}, "erine")


def test_marker_roundtrip_and_limits():
    tags = encode_marker(TAGS, record())
    assert decode_marker(tags) == record()
    assert all(len(k.encode()) + len(v.encode()) <= 124 for k, v in tags.items())
    assert all(tags[k] == v for k, v in TAGS.items())
    oversized = record()
    oversized["receipt"]["youtube_title"] = "長" * 3000
    with pytest.raises(DriveSafetyError):
        encode_marker(TAGS, oversized)


def test_transition_and_remote_only_restart(drive):
    client, objects, events = drive
    client.finalize_permanent("archive", KEY, record())
    assert objects["archive"]["parents"] == ["permanent"]
    assert objects["archive"]["name"] == record()["name"]
    assert set(objects) == {"root", "permanent", "archive", "video"}
    assert events[0][1]["body"].get("appProperties")
    assert events[1][1]["addParents"] == "permanent"
    assert [e[1] for e in events if e[0] == "delete"] == ["meta", "done"]
    assert decode_marker(objects["archive"]["appProperties"])["state"] == "finalized"
    client.finalize_permanent("archive", KEY)
    assert objects["video"]["id"] == "video"


@pytest.mark.parametrize("crash_after", [1, 2, 3, 4])
def test_crash_recovery(drive, crash_after):
    client, objects, events = drive
    files = client.service.files()
    original_update, original_delete = (
        files.update.side_effect,
        files.delete.side_effect,
    )

    def wrap(factory):
        def request(**kwargs):
            req = factory(**kwargs)
            execute = req.execute

            def run(**options):
                result = execute(**options)
                if len(events) == crash_after:
                    raise RuntimeError("power loss")
                return result

            req.execute = run
            return req

        return request

    files.update.side_effect = wrap(original_update)
    files.delete.side_effect = wrap(original_delete)
    with pytest.raises(RuntimeError):
        client.finalize_permanent("archive", KEY, record())
    files.update.side_effect, files.delete.side_effect = (
        original_update,
        original_delete,
    )
    client.finalize_permanent("archive", KEY)
    assert set(objects) == {"root", "permanent", "archive", "video"}


@pytest.mark.parametrize(
    "corruption",
    [
        "foreign",
        "shortcut",
        "folder",
        "checksum",
        "size",
        "extra",
        "metadata_checksum",
        "metadata_size",
        "metadata_missing",
    ],
)
def test_preflight_refuses_before_any_writes(drive, corruption):
    client, objects, events = drive
    if corruption == "foreign":
        objects["meta"]["appProperties"] = {}
    elif corruption in {"shortcut", "folder"}:
        objects["meta"]["mimeType"] = "application/vnd.google-apps." + corruption
    elif corruption == "checksum":
        objects["video"]["md5Checksum"] = "c" * 32
    elif corruption == "size":
        objects["video"]["size"] = 6
    elif corruption == "metadata_checksum":
        objects["meta"]["md5Checksum"] = "d" * 32
    elif corruption == "metadata_size":
        objects["meta"]["size"] = 13
    elif corruption == "metadata_missing":
        del objects["meta"]
    else:
        objects["extra"] = {**objects["meta"], "id": "extra", "name": "surprise"}
    with pytest.raises(DriveSafetyError):
        client.finalize_permanent("archive", KEY, record())
    assert not events


def test_permanent_without_marker_is_never_initialized(drive):
    client, objects, events = drive
    objects["archive"]["parents"] = ["permanent"]
    with pytest.raises(DriveSafetyError):
        client.finalize_permanent("archive", KEY, record())
    assert not events


def test_malformed_marker_refused(drive):
    client, objects, events = drive
    objects["archive"]["appProperties"]["keep_00"] = "{}"
    with pytest.raises(DriveSafetyError):
        client.finalize_permanent("archive", KEY, record())
    assert not events


def test_migrated_key_cannot_be_duplicated(drive, monkeypatch):
    client, objects, events = drive
    objects["archive"]["parents"] = ["permanent"]
    monkeypatch.setattr(client, "_list", lambda query: [objects["archive"]])
    with pytest.raises(DriveSafetyError):
        client.ensure_archive(KEY, "local_name")
    client.service.files().create.assert_not_called()


@pytest.mark.parametrize(
    "start, expected",
    [
        ("2026-08-13T18:15:00Z", "erine 14 Agustus 2026 01:15 WIB"),
        ("2026-12-31T18:15:00Z", "erine 1 Januari 2027 01:15 WIB"),
    ],
)
def test_name_wib_date_rollover(start, expected):
    assert display_name({"start_at": start}, "Erine") == expected


def test_finalized_poll_is_read_only_without_child_or_sibling_requests(
    drive, monkeypatch
):
    client, objects, events = drive
    client.finalize_permanent("archive", KEY, record())
    events.clear()
    get_file = MagicMock(wraps=client.get_file)
    list_children = MagicMock(
        side_effect=AssertionError("deep audit on finalized poll")
    )
    monkeypatch.setattr(client, "get_file", get_file)
    monkeypatch.setattr(client, "list_children", list_children)
    for _ in range(3):
        assert client.finalize_permanent("archive", KEY) == record()["receipt"]
    assert get_file.call_count == 3
    assert all(call.args == ("archive",) for call in get_file.call_args_list)
    list_children.assert_not_called()
    assert not events


@pytest.mark.parametrize("change", ["marker", "parent", "name"])
def test_finalized_fast_path_fails_closed(drive, change):
    client, objects, events = drive
    client.finalize_permanent("archive", KEY, record())
    events.clear()
    if change == "marker":
        objects["archive"]["appProperties"]["keep_00"] = "invalid"
    elif change == "parent":
        objects["archive"]["parents"] = ["root"]
    else:
        objects["archive"]["name"] = "renamed"
    with pytest.raises(DriveSafetyError):
        client.finalize_permanent("archive", KEY)
    assert not events


@pytest.mark.parametrize("ignored", ["pending_marker", "move", "finalized_marker"])
def test_silent_update_noop_fails_readback(drive, ignored):
    client, objects, events = drive
    files = client.service.files()
    original_update = files.update.side_effect

    def update(**kwargs):
        properties = kwargs.get("body", {}).get("appProperties")
        marker = decode_marker(properties) if properties else None
        ignore = (
            (ignored == "move" and "addParents" in kwargs)
            or (ignored == "pending_marker" and marker and marker["state"] == "pending")
            or (
                ignored == "finalized_marker"
                and marker
                and marker["state"] == "finalized"
            )
        )
        if ignore:
            # Even an apparently successful response must not be trusted.
            response = {**copy.deepcopy(objects["archive"]), **kwargs.get("body", {})}
            return MagicMock(execute=MagicMock(return_value=response))
        return original_update(**kwargs)

    files.update.side_effect = update
    with pytest.raises(DriveSafetyError):
        client.finalize_permanent("archive", KEY, record())
    if ignored in {"pending_marker", "move"}:
        assert not any(event[0] == "delete" for event in events)
        assert {"meta", "done", "video"} <= objects.keys()
        assert objects["archive"]["parents"] == ["root"]
    if ignored == "pending_marker":
        assert decode_marker(objects["archive"]["appProperties"]) is None
        assert not events
    else:
        assert decode_marker(objects["archive"]["appProperties"])["state"] == "pending"
    # Retrying with a functioning API recovers from every observed remote state.
    files.update.side_effect = original_update
    client.finalize_permanent("archive", KEY, record())
    assert decode_marker(objects["archive"]["appProperties"])["state"] == "finalized"


@pytest.mark.parametrize("remaining", ["meta", "done"])
def test_silent_delete_noop_never_finalizes(drive, remaining):
    client, objects, events = drive
    files = client.service.files()
    original_delete = files.delete.side_effect

    def delete(**kwargs):
        if kwargs["fileId"] == remaining:
            return MagicMock(execute=MagicMock(return_value=None))
        return original_delete(**kwargs)

    files.delete.side_effect = delete
    with pytest.raises(DriveSafetyError, match="nonvideo"):
        client.finalize_permanent("archive", KEY, record())
    assert remaining in objects
    assert decode_marker(objects["archive"]["appProperties"])["state"] == "pending"
    files.delete.side_effect = original_delete
    client.finalize_permanent("archive", KEY)
    assert set(objects) == {"root", "permanent", "archive", "video"}
    assert decode_marker(objects["archive"]["appProperties"])["state"] == "finalized"


@pytest.mark.parametrize("corruption", ["parent", "name", "private", "tags", "marker"])
def test_move_readback_checks_full_folder_identity_before_delete(drive, corruption):
    client, objects, events = drive
    files = client.service.files()
    original_update = files.update.side_effect

    def update(**kwargs):
        request = original_update(**kwargs)
        if "addParents" not in kwargs:
            return request
        execute = request.execute

        def move():
            response = execute()
            archive = objects["archive"]
            if corruption == "parent":
                archive["parents"] = ["permanent", "foreign"]
            elif corruption == "name":
                archive["name"] = "incorrect"
            elif corruption == "private":
                archive["shared"] = True
            elif corruption == "tags":
                archive["appProperties"]["archive_key"] = "b" * 64
            else:
                archive["appProperties"] = TAGS.copy()
            return response

        request.execute = move
        return request

    files.update.side_effect = update
    with pytest.raises(DriveSafetyError):
        client.finalize_permanent("archive", KEY, record())
    assert not any(event[0] == "delete" for event in events)
    assert {"meta", "done", "video"} <= objects.keys()


@pytest.mark.parametrize("corruption", ["missing", "checksum", "size", "extra"])
def test_final_listing_validates_exact_video_set_before_finalized_marker(
    drive, corruption
):
    client, objects, events = drive
    files = client.service.files()
    original_delete = files.delete.side_effect

    def delete(**kwargs):
        request = original_delete(**kwargs)
        execute = request.execute

        def remove(**options):
            result = execute(**options)
            if kwargs["fileId"] == "done":
                if corruption == "missing":
                    del objects["video"]
                elif corruption == "checksum":
                    objects["video"]["md5Checksum"] = "c" * 32
                elif corruption == "size":
                    objects["video"]["size"] = 999
                else:
                    objects["extra"] = {**objects["video"], "id": "extra"}
            return result

        request.execute = remove
        return request

    files.delete.side_effect = delete
    with pytest.raises(DriveSafetyError):
        client.finalize_permanent("archive", KEY, record())
    assert decode_marker(objects["archive"]["appProperties"])["state"] == "pending"


@pytest.mark.parametrize("reason", ["member_exception", "deletion_disabled"])
def test_both_keep_reasons_finalize_and_recover(drive, reason):
    client, objects, events = drive
    kept = record()
    kept["receipt"]["retention_reason"] = reason
    assert client.finalize_permanent("archive", KEY, kept) == kept["receipt"]
    assert set(objects) == {"root", "permanent", "archive", "video"}
    assert client.finalize_permanent("archive", KEY) == kept["receipt"]


def test_delete_receipt_cannot_be_permanent_marker():
    deleted = record()
    deleted["receipt"].update(retention="delete", retention_reason="deletion_enabled")
    with pytest.raises(DriveSafetyError):
        decode_marker(encode_marker(TAGS, deleted))


def test_valid_permanent_container_does_not_affect_pending_discovery_or_ensure(
    drive, monkeypatch
):
    import re

    client, objects, events = drive
    objects["permanent"] = {
        "id": "permanent",
        "name": "permanent",
        "mimeType": FOLDER_MIME,
        "parents": ["root"],
        "shared": False,
        "ownedByMe": True,
        "appProperties": {"app": "mypage48", "role": "permanent"},
    }
    client.finalize_permanent("archive", KEY, record())
    pending_key = "c" * 64
    objects["pending"] = {
        "id": "pending",
        "name": "unfinished",
        "mimeType": FOLDER_MIME,
        "parents": ["root"],
        "shared": False,
        "ownedByMe": True,
        "appProperties": {**TAGS, "archive_key": pending_key},
    }

    def listing(query):
        tags = re.findall(r"key = '([^']+)' and value = '([^']+)'", query)
        parent = re.search(r"'([^']+)' in parents", query)
        return [
            copy.deepcopy(obj)
            for obj in objects.values()
            if all(obj.get("appProperties", {}).get(k) == v for k, v in tags)
            and (not parent or obj.get("parents") == [parent.group(1)])
        ]

    monkeypatch.setattr(client, "_list", listing)
    assert [folder["id"] for folder in client.list_archives()] == ["pending"]
    assert client.ensure_archive(pending_key, "unfinished")["id"] == "pending"
    client.service.files().create.assert_not_called()
    # New archive creation likewise remains confined to the managed root.
    new_key = "d" * 64

    def create(**kwargs):
        obj = {"id": "new", "shared": False, "ownedByMe": True, **kwargs["body"]}
        objects["new"] = obj
        return MagicMock(execute=MagicMock(return_value=copy.deepcopy(obj)))

    client.service.files().create.side_effect = create
    assert client.ensure_archive(new_key, "new_recording")["parents"] == ["root"]
    assert {folder["id"] for folder in client.list_archives()} == {"pending", "new"}
