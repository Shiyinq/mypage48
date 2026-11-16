"""OAuth setup tests without real browser, network, credentials or .env reads."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv

from recorder import auth_gdrive
from recorder.src.gdrive.client import SCOPES, DriveSafetyError


@pytest.fixture
def oauth(monkeypatch):
    monkeypatch.setenv("REC_GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("REC_GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("REC_YOUTUBE_REFRESH_TOKEN", "unchanged-youtube-token")
    loader = MagicMock()
    monkeypatch.setattr(auth_gdrive, "load_dotenv", loader)
    flow = MagicMock()
    credentials = SimpleNamespace(refresh_token="test-drive-token")
    flow.run_local_server.return_value = credentials
    factory = MagicMock(return_value=flow)
    monkeypatch.setattr(auth_gdrive.InstalledAppFlow, "from_client_config", factory)
    build = MagicMock()
    monkeypatch.setattr(auth_gdrive, "build", build)
    client = MagicMock()
    client.ensure_root.return_value = {"id": "private-root"}
    client_factory = MagicMock(return_value=client)
    monkeypatch.setattr(auth_gdrive, "DriveClient", client_factory)
    return SimpleNamespace(
        loader=loader,
        flow=flow,
        factory=factory,
        credentials=credentials,
        build=build,
        client=client,
        client_factory=client_factory,
    )


def test_oauth_requests_drive_only_offline_and_account_selection(
    oauth, capsys, monkeypatch
):
    auth_gdrive.main()
    config, scopes = oauth.factory.call_args.args
    assert scopes == SCOPES == ["https://www.googleapis.com/auth/drive.file"]
    assert config["installed"]["client_id"] == "test-client"
    assert config["installed"]["client_secret"] == "test-secret"
    oauth.flow.run_local_server.assert_called_once_with(
        host="localhost",
        port=0,
        open_browser=True,
        access_type="offline",
        prompt="consent select_account",
    )
    oauth.build.assert_called_once_with(
        "drive", "v3", credentials=oauth.credentials, cache_discovery=False
    )
    oauth.client_factory.assert_called_once_with(oauth.build.return_value)
    oauth.client.ensure_root.assert_called_once_with()
    output = capsys.readouterr().out
    assert "REC_GDRIVE_REFRESH_TOKEN=test-drive-token" in output
    assert "private-root" in output
    assert "test-secret" not in output
    assert "unchanged-youtube-token" not in output
    assert (
        auth_gdrive.os.environ["REC_YOUTUBE_REFRESH_TOKEN"] == "unchanged-youtube-token"
    )


def test_oauth_without_refresh_token_never_prints_success(oauth, capsys):
    oauth.credentials.refresh_token = None
    with pytest.raises(SystemExit, match="No refresh token"):
        auth_gdrive.main()
    oauth.build.assert_not_called()
    oauth.client.ensure_root.assert_not_called()
    assert "REC_GDRIVE_REFRESH_TOKEN=" not in capsys.readouterr().out


def test_oauth_unsafe_root_does_not_print_token(oauth, capsys):
    oauth.client.ensure_root.side_effect = DriveSafetyError("Unsafe root")
    with pytest.raises(DriveSafetyError, match="Unsafe root"):
        auth_gdrive.main()
    assert "test-drive-token" not in capsys.readouterr().out


def test_oauth_interactive_credentials_use_hidden_secret_prompt(oauth, monkeypatch):
    monkeypatch.delenv("REC_GOOGLE_CLIENT_ID")
    monkeypatch.delenv("REC_GOOGLE_CLIENT_SECRET")
    prompt = MagicMock(return_value=" prompted-client ")
    secret = MagicMock(return_value=" prompted-secret ")
    monkeypatch.setattr("builtins.input", prompt)
    monkeypatch.setattr(auth_gdrive, "getpass", secret)
    auth_gdrive.main()
    config = oauth.factory.call_args.args[0]["installed"]
    assert config["client_id"] == "prompted-client"
    assert config["client_secret"] == "prompted-secret"
    prompt.assert_called_once()
    secret.assert_called_once()


def test_oauth_missing_client_credentials_fails_before_browser(oauth, monkeypatch):
    monkeypatch.delenv("REC_GOOGLE_CLIENT_ID")
    monkeypatch.setattr("builtins.input", lambda _: " ")
    with pytest.raises(SystemExit, match="credentials are required"):
        auth_gdrive.main()
    oauth.factory.assert_not_called()


def test_oauth_loads_recorder_then_root_defaults(oauth):
    auth_gdrive.main()
    base = auth_gdrive.Path(auth_gdrive.__file__).resolve().parent
    assert [call.args[0] for call in oauth.loader.call_args_list] == [
        base / ".env",
        base.parent / ".env",
    ]


def test_recorder_env_overrides_root_defaults(oauth, monkeypatch, tmp_path):
    """Recorder-local values take precedence over repository-root defaults."""
    recorder_dir = tmp_path / "recorder"
    recorder_dir.mkdir()
    (tmp_path / ".env").write_text(
        "REC_GOOGLE_CLIENT_ID=root-client\nREC_GOOGLE_CLIENT_SECRET=root-secret\n"
    )
    (recorder_dir / ".env").write_text(
        "REC_GOOGLE_CLIENT_ID=recorder-client\n"
        "REC_GOOGLE_CLIENT_SECRET=recorder-secret\n"
    )
    monkeypatch.delenv("REC_GOOGLE_CLIENT_ID")
    monkeypatch.delenv("REC_GOOGLE_CLIENT_SECRET")
    monkeypatch.setattr(auth_gdrive, "__file__", str(recorder_dir / "auth_gdrive.py"))
    monkeypatch.setattr(auth_gdrive, "load_dotenv", load_dotenv)
    auth_gdrive.main()
    config = oauth.factory.call_args.args[0]["installed"]
    assert config["client_id"] == "recorder-client"
    assert config["client_secret"] == "recorder-secret"
