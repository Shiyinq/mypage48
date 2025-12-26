import secrets


class CSRFService:
    CSRF_TOKEN_COOKIE = "csrf_token"
    CSRF_TOKEN_HEADER = "X-CSRF-Token"

    @staticmethod
    def generate_csrf_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_csrf_token_string(header_token: str, cookie_token: str) -> bool:
        if not header_token or not cookie_token:
            return False
        return secrets.compare_digest(header_token, cookie_token)
