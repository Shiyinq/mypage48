from fastapi import APIRouter

from src.api_keys.route import router as api_keys_router
from src.auth.route import router as auth_router
from src.health.route import router as health_router
from src.users.route import router as user_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"])
router.include_router(api_keys_router, tags=["API Keys"])
router.include_router(user_router, tags=["Users"])
router.include_router(health_router, tags=["Health"])
