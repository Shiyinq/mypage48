import asyncio
import pytest
import bcrypt
from datetime import datetime
# Monkeypatch bcrypt to fix passlib incompatibility with bcrypt >= 4.0.0
bcrypt.__about__ = type("about", (object,), {"__version__": bcrypt.__version__})

from httpx import AsyncClient, ASGITransport
from src.config import config

# Override configuration BEFORE importing main app
config.DB_NAME = "mypage48_test"
config.AUTH_REQUESTS_PER_MINUTE = 10000
config.DEFAULT_REQUESTS_PER_MINUTE = 10000

from src.main import app, limiter
from src.database import database_instance
from src.dependencies import require_csrf_protection


# Disable rate limiter during testing
limiter.enabled = False

# Mock CSRF protection to always pass
app.dependency_overrides[require_csrf_protection] = lambda: True


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db():
    """
    Connect to MongoDB, yield the database, and drop it after the test.
    This ensures each test runs in isolation with a clean database.
    """
    # Ensure we are connected
    await database_instance.connect()
    
    yield database_instance.database
    
    # Clean up: Drop the test database
    if database_instance.client:
        await database_instance.client.drop_database(config.DB_NAME)
    
    # We generally don't close the connection here if we want to reuse the pool,
    # but for strict isolation we could. For now, just dropping DB is enough.

@pytest.fixture(scope="function")
async def client(db):
    """
    Create a new FastAPI TestClient that uses the `db` fixture.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 12345)), base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture(autouse=True)
def mock_resend_email(monkeypatch):
    """
    Mock resend.Emails.send to prevent sending actual emails.
    """
    class MockResponse:
        def __init__(self):
            self.id = "mock_id"

    mock_calls = []

    def mock_send(params):
        mock_calls.append(params)
        return MockResponse()

    monkeypatch.setattr("resend.Emails.send", mock_send)
    return mock_calls


@pytest.fixture
def create_user(client, db):
    """
    Factory fixture to create, verify, and authenticate a user.
    Returns an async function that creates users on demand.
    """
    async def _create(
        username: str,
        email: str = None,
        full_name: str = "Test User",
        member_id: str = None,
        is_admin: bool = False
    ) -> tuple[str, str, dict]:
        """
        Create and authenticate a user.
        
        Returns:
            tuple: (token, user_id, headers)
        """
        if email is None:
            email = f"{username}@example.com"
        if member_id is None:
            member_id = username[:10]
        
        register_payload = {
            "fullName": full_name,
            "memberId": member_id,
            "username": username,
            "email": email,
            "password": "Password123!",
            "confirmPassword": "Password123!",
            "ofcStatus": "Active"
        }
        await client.post("/api/users/signup", json=register_payload)
        
        # Verify user and optionally make admin
        update_fields = {"isEmailVerified": True}
        if is_admin:
            update_fields["isAdmin"] = True
        
        await db["users"].update_one(
            {"username": username},
            {"$set": update_fields}
        )
        
        # Login
        login_data = {"username": username, "password": "Password123!"}
        login_res = await client.post("/api/auth/signin", data=login_data)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user_id from profile
        profile_res = await client.get("/api/users/profile", headers=headers)
        user_id = profile_res.json()["profile"]["userId"]
        
        return token, user_id, headers
    
    return _create


@pytest.fixture
def create_ticket(db):
    """
    Factory fixture to create test tickets directly in the database.
    Returns an async function that creates tickets on demand.
    """
    async def _create(user_id: str, ticket_data: dict) -> str:
        """
        Create a test ticket.
        
        Args:
            user_id: The user ID who owns the ticket
            ticket_data: Dict with optional keys: title, date, time, day, 
                        section, number, price, two_shot
        
        Returns:
            str: The ticket's ObjectId as string
        """
        from bson import ObjectId
        
        ticket = {
            "_id": ObjectId(),
            "ticket_id": f"TKT-{user_id[-4:]}-{datetime.now().timestamp()}",
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "currency": "IDR",
            "rules": {"refund_allowed": False, "exchange_allowed": False},
            "event": {
                "title": ticket_data.get("title", "Pajama Drive"),
                "date": ticket_data.get("date", "2024-06-15"),
                "time": ticket_data.get("time", "14:00"),
                "day": ticket_data.get("day", "Saturday"),
                "venue": "JKT48 Theater", 
            },
            "seat": {
                "section": ticket_data.get("section", "A1"),
                "number": ticket_data.get("number", "5"),
            },
            "price": ticket_data.get("price", 50000),
            "two_shot": ticket_data.get("two_shot", None),
        }
        await db["tickets"].insert_one(ticket)
        return str(ticket["_id"])
    
    return _create
