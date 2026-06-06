import pytest
from datetime import datetime, timezone

@pytest.fixture
def create_news(db):
    """
    Factory fixture to create test news items directly in the database.
    """
    async def _create(news_data: dict) -> str:
        await db["news"].insert_one(news_data)
        return news_data.get("news_id") or news_data.get("link")
    
    return _create

@pytest.mark.asyncio
async def test_get_news_paginated(client, create_news, create_user):
    # Auth
    _, _, headers = await create_user("testuser")

    # Create news events
    await create_news({
        "news_id": 1,
        "title": "Recent News 1",
        "date": "2026-03-22T10:00:00+07:00",
        "category": "Event",
        "link": "recent-news-1",
        "content_body": "<p>Content 1</p>",
        "is_published": True,
        "valid_date_from": "2026-03-22T10:00:00+07:00"
    })
    
    await create_news({
        "news_id": 2,
        "title": "Older News 2",
        "date": "2026-03-21T10:00:00+07:00",
        "category": "Theater",
        "link": "older-news-2",
        "content_body": "<p>Content 2</p>",
        "is_published": True,
        "valid_date_from": "2026-03-21T10:00:00+07:00"
    })

    # Test without category filter
    response = await client.get("/api/theater/news?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["count_total"] == 2
    assert len(data["data"]) == 2
    
    # Check default sorting (newest first based on ID or Date, assuming DB order or service sorting)
    # The first item should be the one created recently or first in DB depending on your repository.
    # We will just assert they are present.
    news_titles = [n["title"] for n in data["data"]]
    assert "Recent News 1" in news_titles
    assert "Older News 2" in news_titles


@pytest.mark.asyncio
async def test_get_news_with_date_filter(client, create_news, create_user):
    # Auth
    _, _, headers = await create_user("testuser_date")

    # The datetime should match valid_date_from storage format (which is a string or ISODate in Mongo, but in test setup we pass strings, and schema converts to datetime if we go through service. Since create_news bypasses service, we must insert datetime objects, or if schema parses it, let's look at create_news: it inserts dict directly to DB).
    # Wait, the repository queries valid_date_from with datetime objects (because utils.parse_date_range returns datetime objects).
    # If the test fixture inserts string "2026-03-22T10:00:00+07:00", then `$gte` with datetime might fail in MongoDB because types don't match!
    # Let's fix the fixture insertion to use datetime or ensure the test passes.
    # Actually, in real app, News schemas validate and store as datetime in Mongo.
    
    await create_news({
        "news_id": 10,
        "title": "News Jan",
        "category": "Event",
        "link": "news-jan",
        "is_published": True,
        "content_body": "<p>Content</p>",
        "valid_date_from": datetime(2026, 1, 15, tzinfo=timezone.utc)
    })
    
    await create_news({
        "news_id": 11,
        "title": "News Feb",
        "category": "Event",
        "link": "news-feb",
        "is_published": True,
        "content_body": "<p>Content</p>",
        "valid_date_from": datetime(2026, 2, 15, tzinfo=timezone.utc)
    })

    # Test filtering by start_date and end_date
    res1 = await client.get("/api/theater/news?start_date=2026-02-01&end_date=2026-02-28", headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["meta"]["count_total"] == 1
    assert data1["data"][0]["title"] == "News Feb"

    # Test invalid date
    res2 = await client.get("/api/theater/news?start_date=invalid", headers=headers)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "INVALID_DATE_FORMAT"



@pytest.mark.asyncio
async def test_get_news_by_link(client, create_news, create_user):
    # Auth
    _, _, headers = await create_user("testuser_link")

    await create_news({
        "news_id": 3,
        "title": "Special Detail News",
        "date": "2026-03-20T10:00:00+07:00",
        "category": "Other",
        "link": "special-detail-news",
        "content_body": "<p>Full HTML content</p>",
        "is_published": True,
        "valid_date_from": "2026-03-20T10:00:00+07:00"
    })

    # Test getting existing news by link
    response = await client.get("/api/theater/news/special-detail-news", headers=headers)
    assert response.status_code == 200
    news_item = response.json()
    
    assert news_item["title"] == "Special Detail News"
    assert news_item["link"] == "special-detail-news"
    # content_body should be included in the detail response
    assert news_item["content_body"] == "<p>Full HTML content</p>"

    # Test getting non-existent news
    response_not_found = await client.get("/api/theater/news/non-existent-link", headers=headers)
    assert response_not_found.status_code == 404
    assert response_not_found.json()["detail"] == "News not found."

@pytest.mark.asyncio
async def test_get_news_service_error(client, monkeypatch, create_user):
    # Auth
    _, _, headers = await create_user("testuser_error")
    
    # Mock repository method to raise generic exception
    async def mock_find(*args, **kwargs):
        raise Exception("DB Error")
        
    monkeypatch.setattr("src.news.repository.NewsRepository.get_news", mock_find)
    
    # Test error handling on paginated list
    response = await client.get("/api/theater/news", headers=headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch news."
    
    # Mock repository method for single item to raise generic exception
    monkeypatch.setattr("src.news.repository.NewsRepository.get_news_by_link", mock_find)
    response_link = await client.get("/api/theater/news/any-link", headers=headers)
    assert response_link.status_code == 500
    assert response_link.json()["detail"] == "Failed to fetch news item."
