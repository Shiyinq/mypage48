import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_analyze_ticket_success(client: AsyncClient, db, monkeypatch):
    # Mock GenAI response
    class MockGenResponse:
        text = '{"title": "Mock Show", "date": "2024-01-01", "time": "19:00", "gate_open": "18:00", "day": "Monday", "section": "A", "number": "10", "price": 150000, "ticket_id": "MOCK-123"}'

    class MockModel:
        async def generate_content_async(self, contents, generation_config):
            return MockGenResponse()

    # Apply Mock
    # We need to mock 'src.llm.service.genai.GenerativeModel' instantiation
    # OR we can mock the `GenerativeModel` class itself in `src.llm.service`.
    
    # Strategy: Mock `src.llm.service.genai.GenerativeModel` to return our MockModel
    monkeypatch.setattr("src.llm.service.genai.GenerativeModel", lambda model_name: MockModel())

    # Register and Login
    register_payload = {
        "fullName": "LLM User",
        "memberId": "llm123",
        "username": "llmuser",
        "email": "llm@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "llmuser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "llmuser", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Analyze Ticket
    payload = {
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
    }
    response = await client.post("/api/llm/analyze-ticket", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Mock Show"
    assert data["ticket_id"] == "MOCK-123"
