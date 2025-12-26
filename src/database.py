import motor.motor_asyncio

from src.config import config


class Database:
    _instance = None

    def __init__(self):
        self.client = None
        self.database = None

    async def connect(self):
        """Create database connection."""
        from src.logging_config import create_logger

        self.logger = create_logger("database", __name__)

        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                config.mongo_uri, maxPoolSize=config.db_max_pool_size
            )
            self.database = self.client[config.db_name]
            self.logger.info(f"Connected to database: {config.db_name}")
        except Exception as e:
            self.logger.exception(
                f"An error occurred while connecting to the database: {str(e)}"
            )
            raise e

    async def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            self.logger.info("Database connection closed.")


database_instance = Database()
