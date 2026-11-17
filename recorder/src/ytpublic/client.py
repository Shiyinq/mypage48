"""Metered YouTube reads and privacy updates; no video upload operations."""

import json
import re

import httplib2
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .state import PublicationState, StateError

VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}", re.ASCII)
WRITABLE_STATUS = (
    "embeddable",
    "license",
    "publicStatsViewable",
    "selfDeclaredMadeForKids",
    "containsSyntheticMedia",
)
AUTH_CODES = {
    "invalid_grant",
    "invalid_client",
    "unauthorized_client",
    "invalid_scope",
    "invalid_token",
}


class AuthorizationError(RuntimeError):
    pass


class QuotaExceededError(RuntimeError):
    pass


class APIRequestError(RuntimeError):
    """Safe error context without request URLs or credential contents."""


def _translate_error(exc):
    if isinstance(exc, RefreshError):
        if not exc.retryable and any(code in str(exc) for code in AUTH_CODES):
            raise AuthorizationError("YouTube OAuth credentials rejected") from exc
        raise APIRequestError("YouTube token refresh temporarily failed") from exc
    if isinstance(exc, HttpError):
        reasons = []
        try:
            payload = json.loads(exc.content)
            reasons = [
                item.get("reason", "")
                for item in payload.get("error", {}).get("errors", [])
            ]
        except (ValueError, TypeError, AttributeError):
            pass
        status = exc.resp.status
        if status == 401:
            raise AuthorizationError("YouTube authorization rejected") from exc
        if any(reason in {"quotaExceeded", "dailyLimitExceeded"} for reason in reasons):
            raise QuotaExceededError("YouTube daily API quota exhausted") from exc
        safe_reasons = ",".join(
            reason for reason in reasons if re.fullmatch(r"[A-Za-z0-9_-]+", reason)
        )
        raise APIRequestError(
            f"YouTube HTTP {status}: {safe_reasons or 'request failed'}"
        ) from exc
    raise exc


class YouTubeClient:
    """Use from one executor thread; all network attempts are charged explicitly."""

    def __init__(self, service, state: PublicationState):
        self.service = service
        self.state = state
        self.channel_id = None

    @classmethod
    def from_config(cls, config, state):
        if not all(
            (
                config.google_client_id,
                config.google_client_secret,
                config.youtube_refresh_token,
            )
        ):
            raise AuthorizationError("YouTube OAuth credentials are missing")
        credentials = Credentials(
            None,
            refresh_token=config.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=config.google_client_id,
            client_secret=config.google_client_secret,
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube",
            ],
        )
        try:
            credentials.refresh(Request())
        except Exception as exc:
            _translate_error(exc)
        # Separate transport avoids changing the uploader's builder. Disable
        # automatic 401 replay as well as SDK retries so every API attempt is metered.
        http = AuthorizedHttp(
            credentials, http=httplib2.Http(timeout=60), max_refresh_attempts=0
        )
        return cls(build("youtube", "v3", http=http, cache_discovery=False), state)

    def _execute(self, request, *, update=False, before_update=None):
        self.state.reserve(50 if update else 1, update=update)
        if before_update is not None:
            before_update()
        try:
            return request.execute(num_retries=0)
        except (HttpError, RefreshError) as exc:
            _translate_error(exc)

    def discover_channel(self):
        result = self._execute(
            self.service.channels().list(
                part="contentDetails", mine=True, maxResults=50
            )
        )
        items = result.get("items", [])
        if len(items) != 1 or result.get("nextPageToken"):
            raise StateError("Expected exactly one authorized YouTube channel")
        channel_id = items[0].get("id")
        playlist_id = (
            items[0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
        if (
            not isinstance(channel_id, str)
            or not channel_id
            or not isinstance(playlist_id, str)
            or not playlist_id
        ):
            raise StateError("Authorized channel lacks an uploads playlist")
        self.channel_id = channel_id
        return {"channel_id": channel_id, "playlist_id": playlist_id}

    def list_upload_page(self, playlist_id, page_token=None):
        result = self._execute(
            self.service.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
        )
        ids = []
        for item in result.get("items", []):
            video_id = item.get("contentDetails", {}).get("videoId")
            if not isinstance(video_id, str) or VIDEO_ID.fullmatch(video_id) is None:
                raise StateError("Uploads playlist contains an invalid video ID")
            if video_id not in ids:
                ids.append(video_id)
        token = result.get("nextPageToken")
        if token is not None and (not isinstance(token, str) or not token):
            raise StateError("Invalid uploads pagination token")
        return {"ids": ids, "next_page_token": token}

    def get_videos(self, ids):
        if not ids:
            return []
        if len(ids) > 50 or any(
            not isinstance(value, str) or VIDEO_ID.fullmatch(value) is None
            for value in ids
        ):
            raise StateError("Invalid YouTube video batch")
        result = self._execute(
            self.service.videos().list(part="snippet,status", id=",".join(ids))
        )
        resources = result.get("items", [])
        seen = set()
        for video in resources:
            if (
                not isinstance(video, dict)
                or video.get("id") not in ids
                or video["id"] in seen
            ):
                raise StateError("Unexpected or duplicate video resource")
            if video.get("snippet", {}).get("channelId") != self.channel_id:
                raise StateError("Video does not belong to authorized channel")
            seen.add(video["id"])
        return resources

    def make_public(self, video, before_update):
        video_id = video.get("id")
        if not isinstance(video_id, str) or VIDEO_ID.fullmatch(video_id) is None:
            raise StateError("Invalid publication video ID")
        status = video.get("status", {})
        if (
            video.get("snippet", {}).get("channelId") != self.channel_id
            or self.channel_id is None
        ):
            raise StateError("Refusing to publish a video outside authorized channel")
        if status.get("privacyStatus") != "private" or status.get("publishAt"):
            raise StateError("Refusing to override current video privacy/schedule")
        writable = {
            field: status[field] for field in WRITABLE_STATUS if field in status
        }
        writable["privacyStatus"] = "public"
        request = self.service.videos().update(
            part="status", body={"id": video_id, "status": writable}
        )
        return self._execute(request, update=True, before_update=before_update)

    def close(self):
        self.service.close()
