"""Offline-safe by default consumer Drive ownership migration.

Run plan, propose --execute, accept --execute, then verify, with the same explicit
root/source/target arguments. Each phase requests separate broad Drive consent;
recorder drive.file tokens are never read. Stop every writer for the entire
migration. Google consumer accounts only (not Workspace/shared drives); quota,
sharing policy and Google consent restrictions still apply. No content is copied.
Ownership does NOT validate recorder drive.file access or worker compatibility.
"""

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

FOLDER = "application/vnd.google-apps.folder"
SHORTCUT = "application/vnd.google-apps.shortcut"
SCOPES = ["https://www.googleapis.com/auth/drive"]
BASE = Path(__file__).resolve().parent
FIELDS = (
    "id,name,mimeType,parents,size,md5Checksum,sha1Checksum,sha256Checksum,"
    "appProperties,trashed,driveId,owners(emailAddress,permissionId)"
)
KEYS = (
    "id name mimeType parents size md5Checksum sha1Checksum sha256Checksum "
    "appProperties"
).split()


class SafetyError(RuntimeError):
    """A deliberately non-secret diagnostic."""


def require(condition, message):
    if not condition:
        raise SafetyError(message)


def call(request):
    try:
        return request.execute()
    except Exception:
        raise SafetyError(
            "Drive request failed; reauthorize/check access and retry"
        ) from None


def pages(resource, key, **kwargs):
    token, seen = None, set()
    while True:
        page = call(resource.list(pageToken=token, **kwargs))
        require(not page.get("incompleteSearch"), "Incomplete Drive search")
        require(isinstance(page.get(key), list), "Incomplete API response")
        yield from page[key]
        token = page.get("nextPageToken")
        if not token:
            break
        require(token not in seen, "Repeated pagination token")
        seen.add(token)


def identity(service, email):
    user = call(service.about().get(fields="user(emailAddress,permissionId)"))["user"]
    require(user.get("emailAddress", "").lower() == email, "Wrong OAuth account")
    require(bool(user.get("permissionId")), "Missing account permission identity")
    return user["permissionId"]


def validate_properties(properties):
    require(isinstance(properties, dict), "Invalid private property snapshot")
    require(len(properties) <= 30, "Too many private properties")
    for key, value in properties.items():
        require(
            isinstance(key, str) and isinstance(value, str),
            "Private properties must map strings to strings",
        )
        try:
            valid = bool(key) and len(key.encode()) + len(value.encode()) <= 124
        except UnicodeError:
            valid = False
        require(valid, "Invalid private property size")


def permanent_marker(properties):
    # Direct script execution puts recorder/, not its package parent, on sys.path.
    # Limit the import-path adjustment to loading the existing validator.
    root = str(BASE.parent)
    added = root not in sys.path
    if added:
        sys.path.insert(0, root)
    try:
        from recorder.src.gdrive.permanent import decode_marker

        return decode_marker(properties)
    except Exception:
        raise SafetyError("Invalid permanent archive marker") from None
    finally:
        if added:
            sys.path.remove(root)


def validate_permanent_tree(items, root):
    def tagged(item, **tags):
        return all(item["appProperties"].get(k) == v for k, v in tags.items())

    containers = set()
    for file_id, item in items.items():
        props = item["appProperties"]
        if tagged(item, app="mypage48", role="permanent"):
            require(
                item["mimeType"] == FOLDER
                and item["name"] == "permanent"
                and item["parents"] == [root]
                and tagged(items[root], app="mypage48", role="root"),
                "Invalid permanent container identity",
            )
            containers.add(file_id)
        if not any(k.startswith("keep_") for k in props):
            continue
        marker = permanent_marker(props)
        require(marker["state"] == "finalized", "Permanent finalization incomplete")
        require(
            item["mimeType"] == FOLDER
            and tagged(item, app="mypage48", role="archive")
            and re.fullmatch(r"[0-9a-f]{64}", props.get("archive_key", ""))
            and item["name"] == marker["name"],
            "Invalid permanent archive identity",
        )
        parent = items.get(item["parents"][0]) if len(item["parents"]) == 1 else None
        require(
            parent is not None
            and tagged(parent, app="mypage48", role="permanent")
            and parent["parents"] == [root],
            "Invalid finalized archive location",
        )
        assets = {
            a["id"]: a for a in marker["assets"] if a["name"].lower().endswith(".mp4")
        }
        children = {k: v for k, v in items.items() if v["parents"] == [file_id]}
        require(set(children) == set(assets), "Permanent archive asset set mismatch")
        for child_id, child in children.items():
            asset = assets[child_id]
            require(
                child["name"] == asset["name"]
                and child["mimeType"] != FOLDER
                and not child["mimeType"].startswith("application/vnd.google-apps.")
                and child["size"] == str(asset["size"])
                and isinstance(child["md5Checksum"], str)
                and child["md5Checksum"].lower() == asset["md5Checksum"].lower()
                and tagged(
                    child,
                    app="mypage48",
                    role="asset",
                    archive_key=props["archive_key"],
                    file_key=asset["name"],
                ),
                "Permanent asset identity or integrity mismatch",
            )
    require(len(containers) <= 1, "Ambiguous permanent containers")
    for item in items.values():
        if any(parent in containers for parent in item["parents"]):
            require(
                any(k.startswith("keep_") for k in item["appProperties"]),
                "Permanent archive missing finalization marker",
            )


def metadata(service, file_id, source, target):
    item = call(service.files().get(fileId=file_id, fields=FIELDS))
    require(item.get("id") == file_id, "File identity mismatch")
    require(item.get("trashed") is False, "Trashed or inaccessible item")
    require(not item.get("driveId"), "Shared drives are unsupported")
    require(item.get("mimeType") not in (None, SHORTCUT), "Shortcut/unknown MIME type")
    owners = item.get("owners", [])
    require(len(owners) == 1, "Ambiguous owner")
    owner = owners[0].get("emailAddress", "").lower()
    require(owner in (source, target), "Unexpected owner")
    require(bool(owners[0].get("permissionId")), "Missing owner permission identity")
    require(isinstance(item.get("parents"), list), "Missing parents")
    require(isinstance(item.get("name"), str), "Missing name")
    properties = item.get("appProperties", {})
    validate_properties(properties)
    snapshot = {k: item.get(k) for k in KEYS}
    snapshot["appProperties"] = properties
    return snapshot, owner, owners[0]["permissionId"]


def inventory(service, root, source, target):
    result, order, stack = {}, [], [(root, None, False)]
    while stack:
        file_id, parent, visited = stack.pop()
        if visited:
            order.append(file_id)
            continue
        require(file_id not in result, "Duplicate ID or cycle")
        item, owner, _ = metadata(service, file_id, source, target)
        if parent:
            require(item["parents"] == [parent], "Unexpected parent edge")
        result[file_id] = item
        stack.append((file_id, parent, True))
        if item["mimeType"] == FOLDER:
            children = list(
                pages(
                    service.files(),
                    "files",
                    q=f"'{file_id}' in parents",
                    fields="nextPageToken,incompleteSearch,files(id)",
                    pageSize=1000,
                    spaces="drive",
                )
            )
            stack.extend((child["id"], file_id, False) for child in children)
    require(result[root]["mimeType"] == FOLDER, "Root must be a folder")
    validate_permanent_tree(result, root)
    return result, order


def digest(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()


def save(path, state):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".migration-")
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(state, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked(path):
    require(not path.parent.is_symlink(), "Symlink state directory")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(stat.S_IMODE(path.parent.stat().st_mode) == 0o700, "State dir must be 0700")
    fd = os.open(str(path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SafetyError("Migration checkpoint is locked") from None
        yield
    finally:
        os.close(fd)


def load(path, expected):
    try:
        require(not path.is_symlink(), "Symlink checkpoint")
        require(stat.S_IMODE(path.stat().st_mode) == 0o600, "Checkpoint must be 0600")
        state = json.loads(path.read_text())
        plan = state["plan"]
        require(state["seal"] == digest(plan), "Checkpoint inventory corrupted")
        require(all(plan[k] == v for k, v in expected.items()), "Checkpoint mismatch")
        fresh = (
            "Checkpoint lacks a trusted private-property baseline; stop writers and "
            "use a fresh plan at a new checkpoint path after reconciling ownership; "
            "existing checkpoint not overwritten"
        )
        require(plan["version"] == 2, fresh)
        for item in plan["items"].values():
            require("appProperties" in item, fresh)
            validate_properties(item["appProperties"])
        validate_permanent_tree(plan["items"], plan["root"])
        require(set(plan["order"]) == set(plan["items"]), "Invalid checkpoint order")
        require(len(plan["order"]) == len(plan["items"]), "Duplicate checkpoint IDs")
        require(plan["order"][-1] == plan["root"], "Invalid root order")
        return state
    except SafetyError:
        raise
    except Exception:
        raise SafetyError("Checkpoint unreadable or corrupt; not overwritten") from None


def permissions(service, file_id):
    return list(
        pages(
            service.permissions(),
            "permissions",
            fileId=file_id,
            fields=(
                "nextPageToken,permissions("
                "id,type,emailAddress,role,pendingOwner,deleted)"
            ),
            pageSize=100,
        )
    )


def inspect(service, file_id, plan, actor_id, phase):
    item, owner, owner_id = metadata(service, file_id, plan["source"], plan["target"])
    require(item == plan["items"][file_id], "Tree metadata changed since plan")
    if (phase == "propose" and owner == plan["source"]) or (
        phase in ("accept", "verify") and owner == plan["target"]
    ):
        require(owner_id == actor_id, "Owner permission identity mismatch")
    perms = permissions(service, file_id)
    matches = [p for p in perms if p.get("emailAddress", "").lower() == plan["target"]]
    require(len(matches) <= 1, "Ambiguous target permission")
    target = matches[0] if matches else None
    if target:
        require(
            target.get("type") == "user" and not target.get("deleted"),
            "Unsafe target permission",
        )
        if phase in ("accept", "verify"):
            require(target["id"] == actor_id, "Target permission identity mismatch")
    if owner == plan["target"]:
        require(target and target["role"] == "owner", "Target ownership not confirmed")
    elif phase == "accept":
        require(
            target
            and target.get("role") == "writer"
            and target.get("pendingOwner") is True,
            "No pending ownership proposal",
        )
    return owner, target


def run(service, phase, path, root, source, target, execute=False):
    expected = dict(root=root, source=source, target=target)
    actor = identity(service, source if phase in ("plan", "propose") else target)
    with locked(path):
        if path.exists() or path.is_symlink():
            state = load(path, expected)
        else:
            require(phase == "plan", "Plan checkpoint required")
            items, order = inventory(service, root, source, target)
            for file_id in order:
                item, owner, owner_id = metadata(service, file_id, source, target)
                require(item == items[file_id], "Tree changed while planning")
                require(
                    owner == source and owner_id == actor,
                    "Initial plan requires source ownership",
                )
            plan = dict(version=2, items=items, order=order, **expected)
            state = dict(plan=plan, seal=digest(plan), progress={})
            save(path, state)
        plan = state["plan"]
        current, _ = inventory(service, root, source, target)
        require(current == plan["items"], "Complete tree changed since plan")
        folders = sum(item["mimeType"] == FOLDER for item in plan["items"].values())
        summary = dict(folders=folders, files=len(plan["items"]) - folders)
        if phase == "plan":
            return summary
        # Validate every item before the first mutation, including pending proposals.
        for file_id in plan["order"]:
            owner, _ = inspect(service, file_id, plan, actor, phase)
            if phase == "verify":
                require(owner == target, "Ownership migration incomplete")
        if phase == "verify" or not execute:
            return summary
        for file_id in plan["order"]:
            owner, permission = inspect(service, file_id, plan, actor, phase)
            if owner == target or (
                phase == "propose"
                and permission
                and permission.get("role") == "writer"
                and permission.get("pendingOwner") is True
            ):
                continue
            state["progress"][file_id] = dict(phase=phase, status="intent")
            save(path, state)
            try:
                if phase == "propose":
                    body = dict(role="writer", pendingOwner=True)
                    if permission:
                        call(
                            service.permissions().update(
                                fileId=file_id, permissionId=permission["id"], body=body
                            )
                        )
                    else:
                        body.update(type="user", emailAddress=target)
                        call(
                            service.permissions().create(
                                fileId=file_id, body=body, sendNotificationEmail=True
                            )
                        )
                else:
                    call(
                        service.permissions().update(
                            fileId=file_id,
                            permissionId=actor,
                            body={"role": "owner"},
                            transferOwnership=True,
                        )
                    )
                owner, permission = inspect(service, file_id, plan, actor, phase)
                require(
                    owner == target
                    if phase == "accept"
                    else permission and permission.get("pendingOwner") is True,
                    "Remote operation not confirmed",
                )
            except Exception:
                state["progress"][file_id] = dict(phase=phase, status="failed")
                save(path, state)
                raise SafetyError(
                    "Migration operation failed; resume checks remote state"
                ) from None
            state["progress"][file_id] = dict(phase=phase, status="confirmed")
            save(path, state)
        current, _ = inventory(service, root, source, target)
        require(current == plan["items"], "Complete tree changed during transfer")
        return summary


def oauth():
    from dotenv import load_dotenv
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    load_dotenv(BASE / ".env")
    load_dotenv(BASE.parent / ".env")
    client_id = os.environ.get("REC_GOOGLE_CLIENT_ID")
    secret = os.environ.get("REC_GOOGLE_CLIENT_SECRET")
    require(client_id and secret, "Shared OAuth client environment settings required")
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": dict(
                client_id=client_id,
                client_secret=secret,
                auth_uri="https://accounts.google.com/o/oauth2/auth",
                token_uri="https://oauth2.googleapis.com/token",
                redirect_uris=["http://localhost"],
            )
        },
        SCOPES,
    )
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        open_browser=True,
        prompt="consent select_account",
        access_type="online",
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def run_stages(phases, role, path, root, source, target, execute):
    print(f"Authorize the {role} account in the browser for {' + '.join(phases)}.")
    service = oauth()
    try:
        for phase in phases:
            print(f"Starting stage: {phase}.")
            summary = run(
                service,
                phase,
                path,
                root,
                source,
                target,
                execute and phase in ("propose", "accept"),
            )
            print(
                f"{phase}: {summary['folders']} folders (including root), "
                f"{summary['files']} files. Phase complete. "
                "Worker compatibility and drive.file access were NOT validated."
            )
    finally:
        service.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase",
        nargs="?",
        default="plan",
        choices=("plan", "propose", "accept", "verify", "all"),
    )
    parser.add_argument("--root-id", required=True)
    parser.add_argument("--source-email", required=True)
    parser.add_argument("--target-email", required=True)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=BASE / "logs" / "ownership-migration" / "checkpoint.json",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-root")
    parser.add_argument("--workers-stopped", action="store_true")
    args = parser.parse_args(argv)
    try:
        source, target = args.source_email.lower(), args.target_email.lower()
        require(source != target, "Accounts must differ")
        require(
            all(
                re.fullmatch(r"[^@\s]+@(gmail\.com|googlemail\.com)", e)
                for e in (source, target)
            ),
            "Only consumer Gmail accounts supported",
        )
        require(bool(re.fullmatch(r"[A-Za-z0-9_-]+", args.root_id)), "Invalid root ID")
        require(
            not args.execute or args.phase in ("propose", "accept", "all"),
            "Read-only phase cannot execute",
        )
        require(args.phase != "all" or args.execute, "All requires explicit execution")
        if args.execute:
            require(
                args.confirm_root == args.root_id and args.workers_stopped,
                "Execution requires root confirmation and stopped workers",
            )
        require(
            ".." not in args.checkpoint.parts, "Parent traversal in checkpoint path"
        )
        path = args.checkpoint.absolute()
        require(
            not any(p.is_symlink() for p in (path, *path.parents)),
            "Symlink checkpoint path",
        )
        require(
            path.is_relative_to(BASE / "logs"), "Checkpoint must be under recorder/logs"
        )
        groups = (
            [("source", ("plan", "propose")), ("target", ("accept", "verify"))]
            if args.phase == "all"
            else [
                (
                    "source" if args.phase in ("plan", "propose") else "target",
                    (args.phase,),
                )
            ]
        )
        for role, phases in groups:
            run_stages(phases, role, path, args.root_id, source, target, args.execute)
    except Exception:
        # Never echo OAuth/HTTP errors, tokens, URLs, or remote metadata.
        parser.exit(
            1,
            "Migration stopped safely; check identity, checkpoint and remote tree. "
            "No secrets logged.\n",
        )


if __name__ == "__main__":
    main()
