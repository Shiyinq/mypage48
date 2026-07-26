from fastapi import APIRouter

from src.achievements.route import router as achievements_router
from src.admin.route import router as admin_router
from src.api_keys.route import router as api_keys_router
from src.auth.route import router as auth_router
from src.concerts.route import router as concerts_router
from src.dashboard.route import router as dashboard_router
from src.events.route import router as events_router
from src.export.router import router as export_router
from src.feedback.route import router as feedback_router
from src.health.route import router as health_router
from src.live.route import router as live_router
from src.live_history.route import router as live_history_router
from src.llm.route import router as llm_router
from src.members.route import router as members_router
from src.memories.route import router as memories_router
from src.news.route import router as news_router
from src.playground.route import router as playground_router
from src.replay.route import router as replay_router
from src.setlists.route import router as setlists_router
from src.sorter.route import router as sorter_router
from src.storage.route import router as storage_router
from src.tickets.route import router as theater_router
from src.users.route import router as user_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"])
router.include_router(api_keys_router, tags=["API Keys"])
router.include_router(admin_router, prefix="/admin", tags=["Admin"])
router.include_router(user_router, tags=["Users"])
router.include_router(health_router, tags=["Health"])
router.include_router(llm_router, prefix="/llm", tags=["LLM"])
router.include_router(theater_router, prefix="/theater", tags=["Theater"])
router.include_router(sorter_router, prefix="/theater/sorter", tags=["Sorter"])
router.include_router(members_router, prefix="/members", tags=["Members"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(
    achievements_router, prefix="/achievements", tags=["Achievements"]
)
router.include_router(memories_router, prefix="/memories", tags=["Memories"])
router.include_router(setlists_router, prefix="/theater/setlists", tags=["Setlists"])
router.include_router(storage_router, tags=["Storage"])
router.include_router(events_router, prefix="/events", tags=["Events"])
router.include_router(export_router, prefix="/export", tags=["Export"])
router.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])
router.include_router(news_router, prefix="/theater/news", tags=["News"])
router.include_router(live_router, prefix="/jkt48/live", tags=["Live"])
router.include_router(
    live_history_router, prefix="/history/lives", tags=["Live History"]
)
router.include_router(playground_router, prefix="/playground", tags=["Playground"])
router.include_router(replay_router, tags=["Replay"])
router.include_router(concerts_router, prefix="/theater/concerts", tags=["Concerts"])
