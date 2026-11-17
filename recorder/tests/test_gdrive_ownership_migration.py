"""Entirely offline fake Drive protocol and safety tests."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "migration", Path(__file__).parents[1] / "migrate_gdrive_ownership.py"
)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
SOURCE, TARGET = "source@gmail.com", "target@gmail.com"


class Request:
    def __init__(self, fn):
        self.fn = fn

    def execute(self):
        return self.fn()


class Fake:
    def __init__(self):
        self.email = SOURCE
        self.writes = []
        self.fail = False
        self.repeat = False
        self.nodes = {}
        self.perms = {}
        for key, parent, mime in [
            ("root", "outside", m.FOLDER),
            ("folder", "root", m.FOLDER),
            ("file", "folder", "video/mp4"),
        ]:
            self.nodes[key] = dict(
                id=key,
                parents=[parent],
                name=key,
                mimeType=mime,
                trashed=False,
                owners=[dict(emailAddress=SOURCE, permissionId="source")],
            )
            self.perms[key] = [
                dict(id="source", type="user", emailAddress=SOURCE, role="owner")
            ]
        self.nodes["file"].update(size="4", md5Checksum="abcd")

    def close(self):
        pass

    def about(self):
        fake = self

        class About:
            def get(self, **kwargs):
                return Request(
                    lambda: {
                        "user": dict(
                            emailAddress=fake.email,
                            permissionId=fake.email.split("@")[0],
                        )
                    }
                )

        return About()

    def files(self):
        fake = self

        class Files:
            def get(self, fileId, **kwargs):
                return Request(lambda: copy.deepcopy(fake.nodes[fileId]))

            def list(self, q, pageToken=None, **kwargs):
                parent = q.split("'")[1]
                children = [
                    dict(id=k) for k, v in fake.nodes.items() if parent in v["parents"]
                ]
                page = dict(files=children if not pageToken else [])
                if fake.repeat or (children and not pageToken):
                    page["nextPageToken"] = "next"
                return Request(lambda: page)

        return Files()

    def permissions(self):
        fake = self

        class Permissions:
            def list(self, fileId, **kwargs):
                return Request(
                    lambda: dict(permissions=copy.deepcopy(fake.perms[fileId]))
                )

            def create(self, **kwargs):
                def apply():
                    fake.writes.append(("create", kwargs))
                    fake.perms[kwargs["fileId"]].append(
                        dict(id="target", **kwargs["body"])
                    )
                    if fake.fail:
                        fake.fail = False
                        raise RuntimeError("SECRET_TOKEN")
                    return {}

                return Request(apply)

            def update(self, **kwargs):
                def apply():
                    fake.writes.append(("update", kwargs))
                    p = next(
                        p
                        for p in fake.perms[kwargs["fileId"]]
                        if p["id"] == kwargs["permissionId"]
                    )
                    p.update(kwargs["body"])
                    if kwargs.get("transferOwnership"):
                        fake.nodes[kwargs["fileId"]]["owners"] = [
                            dict(emailAddress=TARGET, permissionId="target")
                        ]
                    if fake.fail:
                        fake.fail = False
                        raise RuntimeError("SECRET_TOKEN")
                    return {}

                return Request(apply)

        return Permissions()


@pytest.fixture
def setup(tmp_path):
    fake = Fake()
    path = tmp_path / "state" / "checkpoint.json"

    def run(phase="plan", execute=False):
        return m.run(fake, phase, path, "root", SOURCE, TARGET, execute)

    return fake, path, run


def test_protocol_preview_resume_and_verify(setup):
    fake, path, run = setup
    run()
    run("propose")
    assert not fake.writes
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    fake.fail = True
    with pytest.raises(m.SafetyError, match="resume") as error:
        run("propose", True)
    assert "SECRET_TOKEN" not in str(error.value) + path.read_text()
    run("propose", True)
    assert [kw["fileId"] for _, kw in fake.writes] == ["file", "folder", "root"]
    for method, kw in fake.writes:
        assert method == "create"
        assert kw["sendNotificationEmail"] is True
        assert kw["body"] == dict(
            type="user", role="writer", emailAddress=TARGET, pendingOwner=True
        )
    fake.email = TARGET
    run("accept")
    assert len(fake.writes) == 3
    run("accept", True)
    assert [kw["fileId"] for _, kw in fake.writes[3:]] == ["file", "folder", "root"]
    for _, kw in fake.writes[3:]:
        assert kw["body"] == {"role": "owner"}
        assert kw["permissionId"] == "target"
        assert kw["transferOwnership"] is True
    run("accept", True)
    run("verify")
    assert len(fake.writes) == 6


@pytest.mark.parametrize(
    "change",
    ["size", "addition", "trash", "shortcut", "shared", "owner", "parent", "missing"],
)
def test_changed_tree_no_writes(setup, change):
    fake, _, run = setup
    run()
    if change == "addition":
        fake.nodes["new"] = dict(fake.nodes["file"], id="new")
    elif change == "missing":
        del fake.nodes["file"]
    else:
        key, value = {
            "size": ("size", "5"),
            "trash": ("trashed", True),
            "shortcut": ("mimeType", m.SHORTCUT),
            "shared": ("driveId", "drive"),
            "owner": ("owners", []),
            "parent": ("parents", ["outside"]),
        }[change]
        fake.nodes["file"][key] = value
    with pytest.raises(m.SafetyError):
        run("propose", True)
    assert not fake.writes


def test_identity_corruption_and_lock(setup):
    fake, path, run = setup
    run()
    fake.email = TARGET
    with pytest.raises(m.SafetyError, match="account"):
        run("propose", True)
    fake.email = SOURCE
    with m.locked(path):
        with pytest.raises(m.SafetyError, match="locked"):
            run()
    original = path.read_text()
    state = json.loads(original)
    state["plan"]["items"]["file"]["size"] = "999"
    path.write_text(json.dumps(state))
    with pytest.raises(m.SafetyError, match="corrupted"):
        run()
    assert path.read_text() != original
    assert not fake.writes


def test_repeated_pagination_and_cycle(setup):
    fake, _, run = setup
    fake.repeat = True
    with pytest.raises(m.SafetyError, match="pagination"):
        run()
    fake.repeat = False
    fake.nodes["root"]["parents"] = ["folder"]
    with pytest.raises(m.SafetyError, match="cycle"):
        run()


def test_accept_requires_proposal(setup):
    fake, _, run = setup
    run()
    fake.email = TARGET
    with pytest.raises(m.SafetyError, match="pending"):
        run("accept", True)
    assert not fake.writes


def test_existing_permission_and_accept_crash_recovery(setup):
    fake, path, run = setup
    fake.perms["file"].append(
        dict(id="target", type="user", emailAddress=TARGET, role="reader")
    )
    run()
    run("propose", True)
    method, kwargs = fake.writes[0]
    assert method == "update"
    assert kwargs["body"] == dict(role="writer", pendingOwner=True)
    assert "transferOwnership" not in kwargs
    fake.email = TARGET
    fake.fail = True
    with pytest.raises(m.SafetyError):
        run("accept", True)
    assert "SECRET_TOKEN" not in path.read_text()
    run("accept", True)
    run("verify")
    accepted = [kw["fileId"] for _, kw in fake.writes if kw.get("transferOwnership")]
    assert accepted == ["file", "folder", "root"]


def test_main_gates_before_oauth(monkeypatch, capsys):
    monkeypatch.setattr(m, "oauth", lambda: pytest.fail("OAuth must not run"))
    with pytest.raises(SystemExit):
        m.main(
            [
                "propose",
                "--root-id",
                "root",
                "--source-email",
                SOURCE,
                "--target-email",
                TARGET,
                "--execute",
            ]
        )
    assert "SECRET" not in capsys.readouterr().err


@pytest.mark.parametrize(
    "kind", ["traversal", "relative-traversal", "outside", "symlink"]
)
def test_main_rejects_invalid_checkpoint_before_oauth(
    monkeypatch, tmp_path, capsys, kind
):
    base = tmp_path / "recorder"
    logs = base / "logs"
    logs.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setattr(m, "BASE", base)
    calls = []
    monkeypatch.setattr(m, "oauth", lambda: calls.append("oauth"))
    if kind == "traversal":
        checkpoint = logs / ".." / ".." / "outside" / "checkpoint.json"
    elif kind == "relative-traversal":
        monkeypatch.chdir(tmp_path)
        checkpoint = Path("recorder/logs/../../outside/checkpoint.json")
    elif kind == "outside":
        checkpoint = outside / "checkpoint.json"
    else:
        (logs / "link").symlink_to(outside, target_is_directory=True)
        checkpoint = logs / "link" / "checkpoint.json"
    with pytest.raises(SystemExit) as error:
        m.main(
            [
                "--root-id",
                "root",
                "--source-email",
                SOURCE,
                "--target-email",
                TARGET,
                "--checkpoint",
                str(checkpoint),
            ]
        )
    assert error.value.code == 1
    assert calls == []
    assert not (outside / "checkpoint.json").exists()
    assert "stopped safely" in capsys.readouterr().err


@pytest.mark.parametrize("phase", ["plan", "propose", "accept", "verify"])
def test_main_inventory_summary(setup, monkeypatch, capsys, phase):
    fake, path, run = setup
    run()
    if phase in ("accept", "verify"):
        run("propose", True)
        fake.email = TARGET
        if phase == "verify":
            run("accept", True)
    monkeypatch.setattr(m, "BASE", path.parent.parent)
    monkeypatch.setattr(m, "oauth", lambda: fake)
    original_run = m.run

    def run_checkpoint(service, requested_phase, checkpoint, *args):
        return original_run(service, requested_phase, path, *args)

    monkeypatch.setattr(m, "run", run_checkpoint)
    before = len(fake.writes)
    m.main(
        [phase, "--root-id", "root", "--source-email", SOURCE, "--target-email", TARGET]
    )
    output = capsys.readouterr().out
    assert f"{phase}: 2 folders (including root), 1 files." in output
    assert "were NOT validated" in output
    assert SOURCE not in output and TARGET not in output
    assert "SECRET_TOKEN" not in output
    assert len(fake.writes) == before


def test_all_real_stages_and_partial_transfer_recovery(monkeypatch, tmp_path):
    monkeypatch.setattr(m, "BASE", tmp_path / "recorder")
    fake = Fake()
    sessions = []

    def oauth():
        fake.email = SOURCE if len(sessions) % 2 == 0 else TARGET
        sessions.append(fake.email)
        return fake

    monkeypatch.setattr(m, "oauth", oauth)
    m.main(all_args())
    assert sessions == [SOURCE, TARGET]
    assert len(fake.writes) == 6
    # Recover with an existing checkpoint and already-target-owned descendants.
    m.main(all_args())
    assert sessions == [SOURCE, TARGET, SOURCE, TARGET]
    assert len(fake.writes) == 6


def all_args():
    return [
        "all",
        "--root-id",
        "root",
        "--source-email",
        SOURCE,
        "--target-email",
        TARGET,
        "--execute",
        "--confirm-root",
        "root",
        "--workers-stopped",
    ]


@pytest.mark.parametrize("failure", [None, "plan", "propose", "accept", "verify"])
def test_all_stage_order_auth_and_cleanup(monkeypatch, tmp_path, capsys, failure):
    monkeypatch.setattr(m, "BASE", tmp_path / "recorder")
    events = []
    services = []

    class Service:
        def __init__(self, role):
            self.role = role
            self.closed = False

        def close(self):
            self.closed = True
            events.append(("close", self.role))

    def oauth():
        role = "source" if not services else "target"
        events.append(("oauth", role))
        service = Service(role)
        services.append(service)
        return service

    def run(service, phase, path, root, source, target, execute):
        assert not service.closed
        assert execute == (phase in ("propose", "accept"))
        assert (root, source, target) == ("root", SOURCE, TARGET)
        events.append((phase, service.role))
        if phase == failure:
            raise RuntimeError("SECRET_TOKEN")
        return dict(folders=85, files=425)

    monkeypatch.setattr(m, "oauth", oauth)
    monkeypatch.setattr(m, "run", run)
    if failure:
        with pytest.raises(SystemExit) as error:
            m.main(all_args())
        assert error.value.code == 1
    else:
        m.main(all_args())
    stages = ["plan", "propose", "accept", "verify"]
    completed = stages if failure is None else stages[: stages.index(failure) + 1]
    expected = [("oauth", "source")]
    for stage in completed:
        if stage == "accept":
            expected.extend([("close", "source"), ("oauth", "target")])
        expected.append((stage, "source" if stage in stages[:2] else "target"))
    expected.append(("close", services[-1].role))
    assert events == expected
    assert all(service.closed for service in services)
    output = capsys.readouterr()
    assert "SECRET_TOKEN" not in output.out + output.err
    assert SOURCE not in output.out and TARGET not in output.out
    for stage in completed:
        assert f"Starting stage: {stage}." in output.out
    assert "Authorize the source account" in output.out
    if "accept" in completed:
        assert "Authorize the target account" in output.out


@pytest.mark.parametrize("missing", ["execute", "confirm", "workers", "wrong-root"])
def test_all_confirmations_before_oauth(monkeypatch, capsys, missing):
    calls = []
    monkeypatch.setattr(m, "oauth", lambda: calls.append("oauth"))
    args = all_args()
    if missing == "execute":
        args.remove("--execute")
    elif missing == "workers":
        args.remove("--workers-stopped")
    elif missing == "confirm":
        index = args.index("--confirm-root")
        del args[index : index + 2]
    else:
        args[args.index("--confirm-root") + 1] = "wrong"
    with pytest.raises(SystemExit) as error:
        m.main(args)
    assert error.value.code == 1
    assert calls == []
    assert "stopped safely" in capsys.readouterr().err
