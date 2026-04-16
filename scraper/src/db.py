"""Database utility for JKT48 scraper."""
import os
from datetime import datetime
from typing import Any, Dict, List

from pymongo import MongoClient
from pymongo.collection import Collection


class MongoDB:
    def __init__(self):
        # Support both MONGODB_URI and MONGO_URI env variables
        self.uri = (
            os.environ.get("MONGODB_URI")
            or os.environ.get("MONGO_URI")
            or "mongodb://localhost:27017"
        )
        self.db_name = os.environ.get("DB_NAME", "mypage48")
        self.client = None
        self.db = None

    def connect(self):
        """Connect to MongoDB."""
        if self.client is None:
            try:
                self.client = MongoClient(self.uri)
                # Test connection
                self.client.admin.command("ping")
                self.db = self.client[self.db_name]
                return True
            except Exception as e:
                print(f"❌ Failed to connect to MongoDB: {e}")
                return False
        return True

    def get_collection(self, name: str) -> Collection:
        """Get a collection by name."""
        if self.db is None:
            self.connect()
        return self.db[name]

    def close(self):
        """Close the connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None


def parse_date(date_value) -> datetime:
    """Parse date string or datetime to datetime object."""
    if isinstance(date_value, datetime):
        return date_value

    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        except ValueError:
            pass

        formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_value, fmt)
            except ValueError:
                continue
    return datetime.now()  # Fallback


def upsert_data(
    collection: Collection, data_list: List[Dict[str, Any]], id_field: str = "id"
) -> Dict[str, int]:
    """Generic upsert function for any collection."""
    stats = {"inserted": 0, "updated": 0, "errors": 0}

    for item in data_list:
        try:
            db_item = item.copy()

            # Special handling for dates
            if "date" in db_item:
                db_item["date"] = parse_date(db_item["date"])

            for date_field in ["valid_date_from", "valid_date_to"]:
                if db_item.get(date_field):
                    db_item[date_field] = parse_date(db_item[date_field])
            if "birthdate" in db_item and db_item["birthdate"]:
                # birthdate in members is string "DD Month YYYY", might need special parsing if we want it as Date
                # but for now let's keep it as is or handle if needed.
                pass

            identifier = db_item.get(id_field)
            if not identifier:
                stats["errors"] += 1
                continue

            result = collection.update_one(
                {id_field: identifier}, {"$set": db_item}, upsert=True
            )

            if result.upserted_id:
                stats["inserted"] += 1
            elif result.modified_count > 0:
                stats["updated"] += 1

        except Exception as e:
            stats["errors"] += 1
            print(f"  ❌ Error syncing item: {e}")

    return stats
