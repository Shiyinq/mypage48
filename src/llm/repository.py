from motor.motor_asyncio import AsyncIOMotorDatabase


class LLMRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        # LLM service might not store data, but we keep the structure consistent.
        # Maybe log analysis history? For now, we don't strictly need a collection access.
        self.collection = db["llm_logs"]

    async def log_analysis(self, user_id: str, success: bool):
        # Optional: log usage
        pass
