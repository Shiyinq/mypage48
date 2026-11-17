"""Offline contract tests for the metered publication API client."""

import copy
import json
import socket
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import httplib2
import pytest
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from recorder.src.ytpublic import client as module
from recorder.src.ytpublic.client import (
    APIRequestError,
    AuthorizationError,
    QuotaExceededError,
    YouTubeClient,
)
from recorder.src.ytpublic.state import (
    DailyLimitError,
    PublicationState,
    SpacingError,
    StateError,
)

VIDEO = "abcdefgh_-1"
OTHER = "12345678901"
CHANNEL = "authorized-channel"
SECRET = "private-refresh-token"
URL = "https://youtube.invalid/private?access_token=" + SECRET


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Live network access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(httplib2.Http, "request", forbidden)


@pytest.fixture
def env(tmp_path):
    config = SimpleNamespace(logs_dir=tmp_path)
    now = [datetime(2026, 1, 10, 20, tzinfo=timezone.utc).timestamp()]
    state = PublicationState(config, clock=lambda: now[0])
    service = Mock(spec=["channels", "playlistItems", "videos", "close"])
    client = YouTubeClient(service, state)
    client.channel_id = CHANNEL
    return SimpleNamespace(
        config=config, now=now, state=state, service=service, client=client
    )


def video(**status):
    return {
        "id": VIDEO,
        "snippet": {"channelId": CHANNEL, "title": "Keep this title"},
        "status": {"privacyStatus": "private", **status},
    }


def queue(env, resource, method, result=None, error=None, inspect=None):
    request = Mock(spec=["execute"])

    def execute(*, num_retries):
        assert num_retries == 0
        if inspect:
            inspect()
        if error is not None:
            raise error
        return result

    request.execute.side_effect = execute
    getattr(getattr(env.service, resource).return_value, method).return_value = request
    return request


def http_error(status, reason):
    return HttpError(
        httplib2.Response({"status": str(status)}),
        json.dumps(
            {"error": {"message": URL, "errors": [{"reason": reason}]}}
        ).encode(),
        uri=URL,
    )


def assert_usage(env, units, updates):
    # Reopen the actual ledger, rather than checking an in-memory reservation mock.
    state = PublicationState(env.config, clock=lambda: env.now[0])
    status = state.status()
    assert status["used_units"] == units
    assert status["update_attempts"] == updates
    return status


@pytest.mark.parametrize("operation", ["channel", "playlist", "videos"])
def test_reads_reserve_one_before_execute(env, operation):
    if operation == "channel":
        resource = "channels"
        result = {
            "items": [
                {
                    "id": CHANNEL,
                    "contentDetails": {"relatedPlaylists": {"uploads": "uploads"}},
                }
            ]
        }
        call = env.client.discover_channel
        kwargs = {"part": "contentDetails", "mine": True, "maxResults": 50}
    elif operation == "playlist":
        resource, result = "playlistItems", {"items": []}

        def call():
            return env.client.list_upload_page("uploads", "cursor")
        kwargs = dict(
            part="contentDetails",
            playlistId="uploads",
            maxResults=50,
            pageToken="cursor",
        )
    else:
        resource, result = "videos", {"items": [video()]}

        def call():
            return env.client.get_videos([VIDEO])
        kwargs = {"part": "snippet,status", "id": VIDEO}
    request = queue(
        env, resource, "list", result, inspect=lambda: assert_usage(env, 1, 0)
    )
    call()
    request.execute.assert_called_once_with(num_retries=0)
    getattr(env.service, resource).return_value.list.assert_called_once_with(**kwargs)
    assert_usage(env, 1, 0)


@pytest.mark.parametrize("failure", [None, "http", "callback"])
def test_update_reservation_callback_dispatch_order_and_no_refund(env, failure):
    events = []

    def callback():
        status = assert_usage(env, 50, 1)
        assert status["next_update_at"] == env.now[0] + 30
        events.append("callback")
        if failure == "callback":
            raise RuntimeError("receipt failed")

    def dispatch():
        assert_usage(env, 50, 1)
        assert events == ["callback"]
        events.append("execute")

    request = queue(
        env,
        "videos",
        "update",
        {"id": VIDEO},
        error=http_error(500, "backendError") if failure == "http" else None,
        inspect=dispatch,
    )
    if failure:
        with pytest.raises(APIRequestError if failure == "http" else RuntimeError):
            env.client.make_public(video(), callback)
    else:
        assert env.client.make_public(video(), callback) == {"id": VIDEO}
    assert events == (
        ["callback"] if failure == "callback" else ["callback", "execute"]
    )
    assert request.execute.call_count == (0 if failure == "callback" else 1)
    assert_usage(env, 50, 1)


@pytest.mark.parametrize("block", ["attempts", "budget", "spacing", "pause"])
def test_limits_block_dispatch_and_callback_without_charge(env, block):
    if block == "attempts":
        env.state.max_updates = 1
        env.state.reserve(50, update=True)
        env.now[0] += 30
    elif block == "budget":
        env.state.reserve(4951)
    elif block == "spacing":
        env.state.reserve(50, update=True)
    else:
        env.state.mark_quota_exhausted()
    before = env.state.status()
    request = queue(env, "videos", "update")
    callback = Mock()
    with pytest.raises(SpacingError if block == "spacing" else DailyLimitError):
        env.client.make_public(video(), callback)
    callback.assert_not_called()
    request.execute.assert_not_called()
    assert env.state.status() == before


def test_budget_blocks_reads(env):
    env.state.reserve(5000)
    request = queue(env, "videos", "list")
    with pytest.raises(DailyLimitError):
        env.client.get_videos([VIDEO])
    request.execute.assert_not_called()
    assert_usage(env, 5000, 0)


def test_spacing_allows_reads_and_update_at_exact_deadline(env):
    queue(env, "videos", "update", {})
    env.client.make_public(video(), lambda: None)
    queue(env, "videos", "list", {"items": []})
    assert env.client.get_videos([VIDEO]) == []
    env.now[0] += 30
    env.client.make_public(video(), lambda: None)
    assert_usage(env, 101, 2)


def test_update_preserves_only_writable_status_and_does_not_mutate_input(env):
    writable = dict(
        embeddable=False,
        license="creativeCommon",
        publicStatsViewable=False,
        selfDeclaredMadeForKids=False,
        containsSyntheticMedia=True,
    )
    original = video(
        **writable,
        uploadStatus="processed",
        failureReason="none",
        rejectionReason="none",
        madeForKids=True,
    )
    snapshot = copy.deepcopy(original)
    queue(env, "videos", "update", {})
    env.client.make_public(original, lambda: None)
    env.service.videos.return_value.update.assert_called_once_with(
        part="status",
        body={"id": VIDEO, "status": {**writable, "privacyStatus": "public"}},
    )
    assert original == snapshot


@pytest.mark.parametrize(
    "patch",
    [
        {"status": {"privacyStatus": "unlisted"}},
        {"status": {"privacyStatus": "public"}},
        {"status": {"privacyStatus": "private", "publishAt": "2027-01-01T00:00:00Z"}},
        {"snippet": {"channelId": "other"}},
        {"id": "invalid"},
    ],
)
def test_unsafe_publication_refused_before_building_request(env, patch):
    callback = Mock()
    with pytest.raises(StateError):
        env.client.make_public({**video(), **patch}, callback)
    env.service.videos.assert_not_called()
    callback.assert_not_called()
    assert_usage(env, 0, 0)


def test_publication_requires_discovered_channel(env):
    env.client.channel_id = None
    with pytest.raises(StateError):
        env.client.make_public(video(), Mock())
    env.service.videos.assert_not_called()


@pytest.mark.parametrize(
    "result",
    [
        {"items": []},
        {"items": [{}, {}]},
        {"items": [{"id": CHANNEL}]},
        {
            "items": [
                {
                    "id": CHANNEL,
                    "contentDetails": {"relatedPlaylists": {"uploads": "p"}},
                }
            ],
            "nextPageToken": "more",
        },
        {
            "items": [
                {"id": 123, "contentDetails": {"relatedPlaylists": {"uploads": "p"}}}
            ]
        },
    ],
)
def test_discovery_requires_exactly_one_complete_channel(env, result):
    env.client.channel_id = None
    queue(env, "channels", "list", result)
    with pytest.raises(StateError):
        env.client.discover_channel()
    assert env.client.channel_id is None
    assert_usage(env, 1, 0)


def test_discovery_sets_channel_and_uploads_playlist(env):
    queue(
        env,
        "channels",
        "list",
        {
            "items": [
                {
                    "id": "new-channel",
                    "contentDetails": {"relatedPlaylists": {"uploads": "playlist"}},
                }
            ]
        },
    )
    assert env.client.discover_channel() == {
        "channel_id": "new-channel",
        "playlist_id": "playlist",
    }
    assert env.client.channel_id == "new-channel"


def test_playlist_deduplicates_and_preserves_cursor(env):
    queue(
        env,
        "playlistItems",
        "list",
        {
            "items": [
                {"contentDetails": {"videoId": value}}
                for value in [VIDEO, OTHER, VIDEO]
            ],
            "nextPageToken": "next-page",
        },
    )
    assert env.client.list_upload_page("uploads") == {
        "ids": [VIDEO, OTHER],
        "next_page_token": "next-page",
    }


@pytest.mark.parametrize(
    "result",
    [
        {"items": [{"contentDetails": {"videoId": value}}]}
        for value in [None, "", "a" * 12, "é" * 11, "a" * 10 + "\n"]
    ]
    + [{"nextPageToken": value} for value in ["", 1, [], False]],
)
def test_playlist_validates_ids_and_pagination(env, result):
    queue(env, "playlistItems", "list", result)
    with pytest.raises(StateError):
        env.client.list_upload_page("uploads")
    assert_usage(env, 1, 0)


@pytest.mark.parametrize("ids", [[VIDEO] * 51, [None], ["bad"], ["é" * 11]])
def test_invalid_batches_never_dispatch(env, ids):
    with pytest.raises(StateError):
        env.client.get_videos(ids)
    env.service.videos.assert_not_called()
    assert_usage(env, 0, 0)


def test_empty_batch_and_omitted_ids_are_valid(env):
    assert env.client.get_videos([]) == []
    env.service.videos.assert_not_called()
    ids = [f"{index:011d}" for index in range(50)]
    resource = {**video(), "id": ids[0]}
    queue(env, "videos", "list", {"items": [resource]})
    assert env.client.get_videos(ids) == [resource]
    env.service.videos.return_value.list.assert_called_once_with(
        part="snippet,status", id=",".join(ids)
    )
    assert_usage(env, 1, 0)


@pytest.mark.parametrize(
    "items",
    [
        [video(), video()],
        [{**video(), "id": OTHER}],
        [{**video(), "snippet": {"channelId": "other"}}],
        [None],
    ],
)
def test_unexpected_duplicate_or_outside_channel_resources_refused(env, items):
    queue(env, "videos", "list", {"items": items})
    with pytest.raises(StateError):
        env.client.get_videos([VIDEO])
    assert_usage(env, 1, 0)


@pytest.mark.parametrize(
    "status,reason,expected",
    [
        (401, "authError", AuthorizationError),
        (403, "quotaExceeded", QuotaExceededError),
        (403, "dailyLimitExceeded", QuotaExceededError),
        (403, "rateLimitExceeded", APIRequestError),
        (500, URL, APIRequestError),
    ],
)
def test_http_errors_are_classified_sanitized_and_charged(
    env, status, reason, expected
):
    request = queue(env, "videos", "list", error=http_error(status, reason))
    with pytest.raises(expected) as caught:
        env.client.get_videos([VIDEO])
    assert URL not in str(caught.value)
    assert SECRET not in str(caught.value)
    assert "https://" not in str(caught.value)
    request.execute.assert_called_once_with(num_retries=0)
    assert_usage(env, 1, 0)


@pytest.mark.parametrize(
    "message,retryable,expected",
    [
        ("invalid_grant", False, AuthorizationError),
        ("invalid_client", False, AuthorizationError),
        ("temporarily_unavailable", True, APIRequestError),
    ],
)
def test_refresh_errors_are_safe_and_charged(env, message, retryable, expected):
    queue(
        env,
        "videos",
        "list",
        error=RefreshError(f"{message}: {URL}", retryable=retryable),
    )
    with pytest.raises(expected) as caught:
        env.client.get_videos([VIDEO])
    assert SECRET not in str(caught.value)
    assert URL not in str(caught.value)
    assert_usage(env, 1, 0)


def test_from_config_uses_existing_youtube_credentials_and_no_401_replay(
    env, monkeypatch
):
    config = SimpleNamespace(
        google_client_id="client-id",
        google_client_secret="client-secret",
        youtube_refresh_token=SECRET,
        gdrive_refresh_token="different-account-token",
    )
    credentials = Mock()
    factory = Mock(return_value=credentials)
    refresh_request = Mock()
    http = Mock()
    authorized = Mock()
    build = Mock(return_value=env.service)
    monkeypatch.setattr(module, "Credentials", factory)
    monkeypatch.setattr(module, "Request", Mock(return_value=refresh_request))
    monkeypatch.setattr(module.httplib2, "Http", Mock(return_value=http))
    transport = Mock(return_value=authorized)
    monkeypatch.setattr(module, "AuthorizedHttp", transport)
    monkeypatch.setattr(module, "build", build)
    result = YouTubeClient.from_config(config, env.state)
    factory.assert_called_once_with(
        None,
        refresh_token=SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
        ],
    )
    credentials.refresh.assert_called_once_with(refresh_request)
    module.httplib2.Http.assert_called_once_with(timeout=60)
    transport.assert_called_once_with(credentials, http=http, max_refresh_attempts=0)
    build.assert_called_once_with(
        "youtube", "v3", http=authorized, cache_discovery=False
    )
    assert result.service is env.service
    assert result.state is env.state
    assert result.channel_id is None
    assert_usage(env, 0, 0)


@pytest.mark.parametrize(
    "missing", ["google_client_id", "google_client_secret", "youtube_refresh_token"]
)
def test_missing_credentials_fail_without_refresh_or_build(env, monkeypatch, missing):
    config = SimpleNamespace(
        google_client_id="id",
        google_client_secret="secret",
        youtube_refresh_token=SECRET,
    )
    setattr(config, missing, "")
    factory, build = Mock(), Mock()
    monkeypatch.setattr(module, "Credentials", factory)
    monkeypatch.setattr(module, "build", build)
    with pytest.raises(AuthorizationError):
        YouTubeClient.from_config(config, env.state)
    factory.assert_not_called()
    build.assert_not_called()


def test_close_closes_service(env):
    env.client.close()
    env.service.close.assert_called_once_with()
