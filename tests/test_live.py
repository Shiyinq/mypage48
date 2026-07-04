import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

@pytest.fixture
async def seed_member_socials(db):
    """Seed member with socials to match in live status."""
    member_data = {
        "id": "member_1",
        "name": "Feni Fitriyanti",
        "nickname": "Feni",
        "socials": {
            "showroom": "https://www.showroom-live.com/48_Feni_Fitriyanti",
            "idn_app": "https://www.idn.app/@jkt48-feni"
        }
    }
    await db["members"].insert_one(member_data)
    return member_data

@pytest.mark.asyncio
async def test_get_live_status_success(client: AsyncClient, seed_member_socials):
    # Mock Showroom API
    mock_showroom_resp = MagicMock()
    mock_showroom_resp.status_code = 200
    mock_showroom_resp.raise_for_status = MagicMock()
    mock_showroom_resp.json.return_value = {
        "onlives": [
            {
                "lives": [
                    {
                        "room_id": 318227,
                        "room_url_key": "48_Feni_Fitriyanti",
                        "main_name": "Feni JKT48",
                        "view_num": 1000,
                        "started_at": int(datetime.now().timestamp())
                    }
                ]
            }
        ]
    }
    
    # Mock IDN API
    mock_idn_resp = MagicMock()
    mock_idn_resp.status_code = 200
    mock_idn_resp.raise_for_status = MagicMock()
    mock_idn_resp.json.return_value = {
        "data": {
            "getLivestreams": [
                {
                    "slug": "idn-live-slug",
                    "title": "IDN Live Feni",
                    "playback_url": "https://example.com/stream.m3u8",
                    "room_identifier": "feni_room",
                    "status": "live",
                    "live_at": datetime.now().isoformat() + "Z",
                    "creator": {
                        "name": "Feni JKT48",
                        "username": "@jkt48-feni"
                    }
                }
            ]
        }
    }

    # We use a side_effect to handle different URLs
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    async def mock_get(url, *args, **kwargs):
        if "showroom-live.com" in str(url):
            return mock_showroom_resp
        if "idn.app" in str(url):
            return mock_idn_resp
        return MagicMock(status_code=404)

    mock_client.get = AsyncMock(side_effect=mock_get)
    mock_client.post = AsyncMock(side_effect=mock_get)

    with patch("src.live.service.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/jkt48/live")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["total"] >= 2 # 1 SR + 1 IDN
        
        platforms = [item["platform"] for item in data["data"]]
        assert "showroom" in platforms
        assert "idn" in platforms

@pytest.mark.asyncio
async def test_get_streaming_url_showroom(client: AsyncClient):
    mock_stream_resp = MagicMock()
    mock_stream_resp.status_code = 200
    mock_stream_resp.raise_for_status = MagicMock()
    mock_stream_resp.json.return_value = {
        "streaming_url_list": [
            {"url": "https://example.com/live.m3u8", "label": "Original", "quality": 1}
        ]
    }
    
    mock_profile_resp = MagicMock()
    mock_profile_resp.status_code = 200
    mock_profile_resp.raise_for_status = MagicMock()
    mock_profile_resp.json.return_value = {
        "room_id": 318227,
        "main_name": "Feni JKT48",
        "nickname": "Feni",
        "image": "https://example.com/feni.jpg"
    }

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    async def mock_get(url, *args, **kwargs):
        if "streaming_url" in str(url):
            return mock_stream_resp
        return mock_profile_resp

    mock_client.get = AsyncMock(side_effect=mock_get)

    with patch("src.live.service.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/jkt48/live/showroom/318227/streaming-url")
        assert response.status_code == 200
        data = response.json()
        assert "streaming_urls" in data
        assert len(data["streaming_urls"]) == 1
        assert data["streaming_urls"][0]["url"] == "https://example.com/live.m3u8"
        assert data["member"]["name"] == "Feni JKT48"

@pytest.mark.asyncio
async def test_proxy_streaming_data(client: AsyncClient):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\nchunk.m3u8"
    mock_resp.text = "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\nchunk.m3u8"
    mock_resp.headers = {"content-type": "application/vnd.apple.mpegurl"}

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("src.live.service.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/jkt48/live/proxy?url=https://example.com/master.m3u8")
        assert response.status_code == 200
        assert "application/vnd.apple.mpegurl" in response.headers["content-type"]
        # Check rewriting (our proxy rewrites URLs to /api/jkt48/live/proxy?url=...)
        assert "/api/jkt48/live/proxy?url=" in response.text

@pytest.mark.asyncio
async def test_get_showroom_comments(client: AsyncClient):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"comment_log": [{"user_id": 1, "comment": "Hello"}]}

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("src.live.service.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/jkt48/live/showroom/comments?room_id=318227")
        assert response.status_code == 200
        data = response.json()
        assert len(data["comment_log"]) == 1
        assert data["comment_log"][0]["comment"] == "Hello"

@pytest.mark.asyncio
async def test_get_streaming_url_not_found(client: AsyncClient):
    # Mock showroom streaming URL to be empty or fail
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("src.live.service.httpx.AsyncClient", return_value=mock_client):
        # We also need to mock fetch_idn_lives to return empty or avoid it
        with patch("src.live.service.LiveService.fetch_idn_lives", return_value=[]):
            response = await client.get("/api/jkt48/live/showroom/invalid/streaming-url")
            # Should be 404 with our new StreamingUrlNotFound exception
            assert response.status_code == 404
            assert response.json()["detail"] == "No streaming URL found for this room."


@pytest.mark.asyncio
async def test_get_showroom_gifts_success(client: AsyncClient):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "gift_log": [
            {
                "gift_id": 31,
                "gift_name": "Star",
                "num": 1,
                "total_point": 10,
                "free": False,
                "image": "https://image.showroom-live.com/star.png",
                "name": "Alice",
                "avatar_url": "https://avatar.showroom-live.com/alice.jpg",
                "created_at": 1234567890,
            }
        ]
    }

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("src.live.service.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/jkt48/live/showroom/gifts?room_id=318227")
        assert response.status_code == 200
        data = response.json()
        assert len(data["gift_log"]) == 1
        assert data["gift_log"][0]["gift_name"] == "Star"
        assert data["gift_log"][0]["total_point"] == 10
        assert data["gift_log"][0]["free"] is False


@pytest.mark.asyncio
async def test_get_showroom_gifts_error(client: AsyncClient):
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=Exception("Connection error"))

    with patch("src.live.service.httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/jkt48/live/showroom/gifts?room_id=318227")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch showroom gifts."
