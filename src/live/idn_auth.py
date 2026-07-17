import base64
import json
from typing import Optional

import httpx

from src.logging_config import create_logger

logger = create_logger("idn_auth", __name__)

COGNITO_REGION = "ap-southeast-1"
COGNITO_ENDPOINT = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"


def extract_session_id(id_token: str) -> str:
    _, payload_b64, _ = id_token.split(".")
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding

    payload = json.loads(base64.b64decode(payload_b64))
    return payload.get("username", "")


async def cognito_refresh_tokens(refresh_token: str, client_id: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                COGNITO_ENDPOINT,
                headers={
                    "Content-Type": "application/x-amz-json-1.1",
                    "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Referer": "https://www.idn.app",
                    "Origin": "https://www.idn.app",
                },
                json={
                    "AuthFlow": "REFRESH_TOKEN_AUTH",
                    "AuthParameters": {"REFRESH_TOKEN": refresh_token},
                    "ClientId": client_id,
                },
                timeout=15.0,
            )
            res.raise_for_status()
            data = res.json()
            auth_result = data.get("AuthenticationResult")
            if not auth_result:
                logger.error("Cognito refresh: no AuthenticationResult in response")
                return None
            return {
                "id_token": auth_result["IdToken"],
                "access_token": auth_result["AccessToken"],
                "expires_in": auth_result.get("ExpiresIn", 86400),
            }
    except Exception as e:
        logger.exception(f"Cognito refresh failed: {e}")
        return None
