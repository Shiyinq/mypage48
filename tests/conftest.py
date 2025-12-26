import asyncio
import pytest
import bcrypt
# Monkeypatch bcrypt to fix passlib incompatibility with bcrypt >= 4.0.0
bcrypt.__about__ = type("about", (object,), {"__version__": bcrypt.__version__})

from httpx import AsyncClient, ASGITransport
from src.main import app, limiter
from src.config import config
from src.database import database_instance
from src.dependencies import require_csrf_protection

# Override database name for testing
config.DB_NAME = "fasmo_test"
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

