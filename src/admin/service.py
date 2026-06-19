import logging
from datetime import datetime, timedelta, timezone

from src.admin.exceptions import AdminStatsFetchError
from src.admin.repository import AdminRepository
from src.admin.schemas import DataMyPageStats, DataTheaterStats, DataUsersStats

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository

    async def get_users_stats(self, active_days: int = 7) -> DataUsersStats:
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=active_days)
            now = datetime.now()
            start_of_day = datetime(now.year, now.month, now.day)

            total_users = await self.repository.count_documents("users")
            verified_users = await self.repository.count_documents(
                "users", {"isEmailVerified": True}
            )
            unverified_users = await self.repository.count_documents(
                "users", {"isEmailVerified": False}
            )
            total_admins = await self.repository.count_documents(
                "users", {"isAdmin": True}
            )
            public_profiles = await self.repository.count_documents(
                "users", {"isPublic": True}
            )
            active_users_last_days = await self.repository.count_documents(
                "users", {"lastActiveAt": {"$gte": cutoff_date}}
            )

            total_feedback = await self.repository.count_documents("feedback")

            users_joined_today = await self.repository.count_documents(
                "users", {"createdAt": {"$gte": start_of_day}}
            )

            return DataUsersStats(
                total_users=total_users,
                verified_users=verified_users,
                unverified_users=unverified_users,
                total_admins=total_admins,
                total_feedback=total_feedback,
                active_users_last_days=active_users_last_days,
                public_profiles=public_profiles,
                users_joined_today=users_joined_today,
            )
        except Exception:
            logger.exception("Error fetching users stats")
            raise AdminStatsFetchError()

    async def get_mypage_stats(self) -> DataMyPageStats:
        try:
            total_tickets = await self.repository.count_documents("tickets")
            total_2shot = await self.repository.count_documents(
                "tickets", {"two_shot": {"$ne": None}}
            )
            total_journal = await self.repository.count_documents(
                "tickets", {"notes": {"$nin": [None, ""]}}
            )
            total_favorites = await self.repository.count_documents(
                "tickets", {"is_favorite": True}
            )

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total": {
                            "$sum": {
                                "$add": ["$price", {"$ifNull": ["$two_shot.price", 0]}]
                            }
                        },
                    }
                }
            ]
            result = await self.repository.aggregate("tickets", pipeline)
            total_money = result[0]["total"] if result else 0.0

            return DataMyPageStats(
                total_tickets=total_tickets,
                total_2shot=total_2shot,
                total_journal=total_journal,
                total_favorites=total_favorites,
                total_money_spent_idr=float(total_money),
            )
        except Exception:
            logger.exception("Error fetching mypage stats")
            raise AdminStatsFetchError()

    async def get_theater_stats(self) -> DataTheaterStats:
        try:
            total_members_jkt = await self.repository.count_documents("members")
            active_members_count = await self.repository.count_documents(
                "members", {"active": True}
            )
            graduated_members_count = total_members_jkt - active_members_count

            total_setlists = await self.repository.count_documents("setlists")
            active_setlists_count = await self.repository.count_documents(
                "setlists", {"active": True}
            )
            inactive_setlists_count = total_setlists - active_setlists_count

            total_news = await self.repository.count_documents("news")
            total_live_member = await self.repository.count_documents("live_history")
            showroom_live_count = await self.repository.count_documents(
                "live_history", {"platform": "showroom"}
            )
            idn_live_count = await self.repository.count_documents(
                "live_history", {"platform": "idn"}
            )

            # Calculate upcoming birthdays for the rest of the year
            members = await self.repository.find("members", {"active": True})
            upcoming_birthdays_count = 0
            now = datetime.now()
            today = now.date()
            months_map = {
                "Januari": 1,
                "Februari": 2,
                "Maret": 3,
                "April": 4,
                "Mei": 5,
                "Juni": 6,
                "Juli": 7,
                "Agustus": 8,
                "September": 9,
                "Oktober": 10,
                "November": 11,
                "Desember": 12,
            }
            end_of_year = datetime(today.year, 12, 31).date()

            for member in members:
                if not member.get("birthdate"):
                    continue
                try:
                    parts = member["birthdate"].split()
                    if len(parts) != 3:
                        continue
                    day = int(parts[0])
                    month_str = parts[1]
                    if month_str not in months_map:
                        continue
                    month = months_map[month_str]
                    # We check if the birthday in the CURRENT year is upcoming
                    birthday_this_year = datetime(today.year, month, day).date()
                    if today <= birthday_this_year <= end_of_year:
                        upcoming_birthdays_count += 1
                except (ValueError, TypeError):
                    continue

            total_events = await self.repository.count_documents(
                "events", {"setlistId": {"$in": [None, ""]}}
            )
            total_show_setlist = await self.repository.count_documents(
                "events", {"setlistId": {"$nin": [None, ""]}}
            )

            start_of_day = datetime(now.year, now.month, now.day)
            total_upcoming = await self.repository.count_documents(
                "events", {"date": {"$gte": start_of_day}}
            )
            total_upcoming_events = await self.repository.count_documents(
                "events",
                {"date": {"$gte": start_of_day}, "setlistId": {"$in": [None, ""]}},
            )
            total_upcoming_shows = await self.repository.count_documents(
                "events",
                {"date": {"$gte": start_of_day}, "setlistId": {"$nin": [None, ""]}},
            )

            return DataTheaterStats(
                total_members_jkt=total_members_jkt,
                active_members_count=active_members_count,
                graduated_members_count=graduated_members_count,
                total_setlists=total_setlists,
                active_setlists_count=active_setlists_count,
                inactive_setlists_count=inactive_setlists_count,
                total_events=total_events,
                total_show_setlist=total_show_setlist,
                total_upcoming_events_and_shows=total_upcoming,
                total_upcoming_events=total_upcoming_events,
                total_upcoming_shows=total_upcoming_shows,
                upcoming_birthdays_count=upcoming_birthdays_count,
                total_news=total_news,
                total_live_member=total_live_member,
                showroom_live_count=showroom_live_count,
                idn_live_count=idn_live_count,
            )
        except Exception:
            logger.exception("Error fetching theater stats")
            raise AdminStatsFetchError()
