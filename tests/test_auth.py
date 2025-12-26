import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from src.config import config
from src.auth.constants import Info, ErrorCode
from src.utils import hash_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password) -> str:
    return pwd_context.hash(password)


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    response = await client.post("/api/users/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_login_user_success(client: AsyncClient, db):
    # Register first
    register_payload = {
        "name": "Login User",
        "username": "loginuser",
        "email": "login@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)

    # Manually verify user in DB to allow login
    await db["users"].update_one(
        {"username": "loginuser"}, 
        {"$set": {"isEmailVerified": True}}
    )

    # Login
    login_data = {
        "username": "loginuser",
        "password": "Password123!"
    }
    response = await client.post("/api/auth/signin", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    login_data = {
        "username": "nonexistent",
        "password": "WrongPassword123!"
    }
    response = await client.post("/api/auth/signin", data=login_data)
    assert response.status_code in [400, 401] 

@pytest.mark.asyncio
async def test_refresh_token_flow(client: AsyncClient, db):
    # Register and login to get refresh token
    register_payload = {
        "name": "Refresh User",
        "username": "refreshuser",
        "email": "refresh@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    # Manually verify
    await db["users"].update_one(
        {"username": "refreshuser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_data = {
        "username": "refreshuser",
        "password": "Password123!"
    }
    response = await client.post("/api/auth/signin", data=login_data)
    assert response.status_code == 200
    
    # Refresh token should be in cookies
    cookies = response.cookies
    assert "refresh_token" in cookies
    
    # Refresh using the cookie
    response = await client.post("/api/auth/refresh", cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_logout(client: AsyncClient, db):
    # Register and login
    register_payload = {
        "name": "Logout User",
        "username": "logoutuser",
        "email": "logout@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    # Manually verify
    await db["users"].update_one(
        {"username": "logoutuser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_data = {
        "username": "logoutuser",
        "password": "Password123!"
    }
    response = await client.post("/api/auth/signin", data=login_data)
    cookies = response.cookies
    
    # Logout
    response = await client.post("/api/auth/logout", cookies=cookies)
    assert response.status_code == 200
    assert response.json()["message"] == Info.LOGOUT_SUCCESS

@pytest.mark.asyncio
async def test_send_verification_email(client: AsyncClient, db, mock_resend_email):
    # Register user (unverified)
    register_payload = {
        "name": "Verify User",
        "username": "verifyuser",
        "email": "verify@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    # Send verification email
    response = await client.post("/api/auth/send-verification", json={"email": "verify@example.com"})
    assert response.status_code == 200
    assert response.json()["message"] == Info.EMAIL_VERIFICATION_SENT
    
    # Check if email was "sent" via mock
    assert len(mock_resend_email) > 0
    assert mock_resend_email[-1]["to"] == "verify@example.com"
    assert "Verify Your Email" in mock_resend_email[-1]["subject"]

@pytest.mark.asyncio
async def test_verify_email(client: AsyncClient, db):
    user_id = str(uuid.uuid4())
    # Create user
    user_data = {
        "userId": user_id,
        "name": "To Verify",
        "username": "toverify",
        "email": "toverify@example.com",
        "password": get_password_hash("Password123!"),
        "isEmailVerified": False,
        "failedLoginAttempts": 0,
        "isAccountLocked": False
    }
    await db["users"].insert_one(user_data)
    
    # Insert verification token
    token = "valid_token_123"
    token_hash = hash_token(token)
    token_data = {
        "userId": user_id,
        "hashToken": token_hash,
        "tokenType": "email_verification",
        "expiresAt": datetime.now(timezone.utc) + timedelta(hours=1),
        "createdAt": datetime.now(timezone.utc)
    }
    await db["verification_tokens"].insert_one(token_data)
    
    response = await client.post("/api/auth/verify-email", json={"token": token})
    assert response.status_code == 200
    assert response.json()["message"] == ErrorCode.EMAIL_VERIFIED_SUCCESS
    
    # Verify in DB
    user = await db["users"].find_one({"email": "toverify@example.com"})
    assert user["isEmailVerified"] is True
    # Token should be deleted
    token_in_db = await db["verification_tokens"].find_one({"hashToken": token_hash, "tokenType": "email_verification"})
    assert token_in_db is None

@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient, db, mock_resend_email):
    # Create verified user
    user_data = {
        "userId": str(uuid.uuid4()),
        "name": "Forgot Pass",
        "username": "forgotpass",
        "email": "forgot@example.com",
        "password": get_password_hash("OldPassword123!"),
        "isEmailVerified": True,
        "failedLoginAttempts": 0,
        "isAccountLocked": False
    }
    await db["users"].insert_one(user_data)
    
    response = await client.post("/api/auth/forgot-password", json={"email": "forgot@example.com"})
    assert response.status_code == 200
    assert response.json()["message"] == ErrorCode.PASSWORD_RESET_SENT
    
    # Check mock
    assert len(mock_resend_email) > 0
    assert mock_resend_email[-1]["to"] == "forgot@example.com"
    assert "Reset Your Password" in mock_resend_email[-1]["subject"]

@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient, db):
    user_id = str(uuid.uuid4())
    # Create user with reset token
    user_data = {
        "userId": user_id,
        "name": "Reset Pass",
        "username": "resetpass",
        "email": "reset@example.com",
        "password": get_password_hash("OldPassword123!"),
        "isEmailVerified": True,
        "failedLoginAttempts": 0,
        "isAccountLocked": False
    }
    await db["users"].insert_one(user_data)
    
    # Insert reset token
    token = "reset_token_123"
    token_hash = hash_token(token)
    token_data = {
        "userId": user_id,
        "hashToken": token_hash,
        "tokenType": "password_reset",
        "expiresAt": datetime.now(timezone.utc) + timedelta(hours=1),
        "createdAt": datetime.now(timezone.utc)
    }
    await db["verification_tokens"].insert_one(token_data)
    
    payload = {
        "token": token,
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    }
    response = await client.post("/api/auth/reset-password", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == ErrorCode.PASSWORD_RESET_SUCCESS
    
    # Verify login with new password
    login_data = {
        "username": "resetpass",
        "password": "NewPassword123!"
    }
    response = await client.post("/api/auth/signin", data=login_data)
    assert response.status_code == 200
