from datetime import datetime
from typing import List

from src.achievements.constants import AchievementConfig, RankConfig
from src.achievements.exceptions import AchievementsFetchError
from src.achievements.schemas import AchievementItem, AchievementsResponse, RankInfo
from src.config import Settings
from src.logging_config import create_logger
from src.tickets.service import TicketsService

logger = create_logger("achievements_service", __name__)


class AchievementsService:
    def __init__(
        self,
        tickets_service: TicketsService,
        config: Settings,
    ):
        self.tickets_service = tickets_service
        self.config = config

    def calculate_rank(self, total_shows: int) -> RankInfo:
        """Calculate rank/level based on total shows (XP)."""
        xp = total_shows
        current_rank = RankConfig.MILESTONES[0]
        next_rank = (
            RankConfig.MILESTONES[1]
            if len(RankConfig.MILESTONES) > 1
            else {"xp": 1000, "title": "Beyond Legend"}
        )

        for i, milestone in enumerate(RankConfig.MILESTONES):
            if xp >= milestone["xp"]:
                current_rank = milestone
                next_rank = (
                    RankConfig.MILESTONES[i + 1]
                    if i + 1 < len(RankConfig.MILESTONES)
                    else {"xp": 1000, "title": "Beyond Legend"}
                )

        return RankInfo(
            current=current_rank["title"],
            xp=xp,
            nextLevelXp=next_rank["xp"],
            nextRankTitle=next_rank["title"],
        )

    def _parse_ticket_stats(self, tickets: list) -> dict:
        """Parse tickets and extract statistics for achievement calculation."""
        if not tickets:
            return {
                "total_shows": 0,
                "time_span_days": 0,
                "max_same_show": 0,
                "has_row_a": False,
                "has_row_j": False,
                "unique_rows_count": 0,
                "total_spent": 0,
            }

        total_shows = len(tickets)

        # Date calculations
        sorted_dates = sorted([t.event.date for t in tickets])
        first_date = sorted_dates[0] if sorted_dates else None
        last_date = sorted_dates[-1] if sorted_dates else None

        time_span_days = 0
        if first_date and last_date:
            try:
                first_dt = (
                    datetime.strptime(str(first_date), "%Y-%m-%d")
                    if isinstance(first_date, str)
                    else first_date
                )
                last_dt = (
                    datetime.strptime(str(last_date), "%Y-%m-%d")
                    if isinstance(last_date, str)
                    else last_date
                )
                time_span_days = (last_dt - first_dt).days
            except (ValueError, TypeError):
                pass

        # Show counts
        show_counts = {}
        for t in tickets:
            title = t.event.title.strip() if t.event and t.event.title else ""
            if title:
                show_counts[title] = show_counts.get(title, 0) + 1
        max_same_show = max(show_counts.values()) if show_counts else 0

        # Row calculations
        has_row_a = any(
            t.seat and t.seat.section and t.seat.section.upper().startswith("A")
            for t in tickets
        )
        has_row_j = any(
            t.seat and t.seat.section and t.seat.section.upper().startswith("J")
            for t in tickets
        )

        collected_rows = set()
        for t in tickets:
            if t.seat and t.seat.section:
                row = (
                    t.seat.section.strip().upper()[0] if t.seat.section.strip() else ""
                )
                if row:
                    collected_rows.add(row)
        target_rows = {"A", "B", "C", "D", "E", "F", "G", "H", "I", "J"}
        unique_rows_count = len(collected_rows.intersection(target_rows))

        # Spending
        total_spent = sum(t.price for t in tickets if t.price)

        return {
            "total_shows": total_shows,
            "time_span_days": time_span_days,
            "max_same_show": max_same_show,
            "has_row_a": has_row_a,
            "has_row_j": has_row_j,
            "unique_rows_count": unique_rows_count,
            "total_spent": total_spent,
        }

    def calculate_achievements_count(self, tickets: list) -> int:
        """Calculate total unlocked achievements count from tickets."""
        stats = self._parse_ticket_stats(tickets)

        unlocked = 0

        # Attendance milestones
        for ach in AchievementConfig.ATTENDANCE:
            if stats["total_shows"] >= ach.threshold:
                unlocked += 1

        # Same show milestones
        for ach in AchievementConfig.SAME_SHOW:
            if stats["max_same_show"] >= ach.threshold:
                unlocked += 1

        # Anniversary milestones
        for ach in AchievementConfig.ANNIVERSARY:
            if stats["time_span_days"] >= ach.threshold:
                unlocked += 1

        # Row milestones
        if stats["has_row_a"]:
            unlocked += 1  # Elite Seat
        if stats["has_row_j"]:
            unlocked += 1  # Back Row Warrior
        if stats["unique_rows_count"] >= 10:
            unlocked += 1  # Seat Explorer

        # Spending milestone
        if stats["total_spent"] >= 5000000:
            unlocked += 1  # Top Supporter

        return unlocked

    def calculate_achievements_full(self, tickets: list) -> List[dict]:
        """Calculate all achievements with unlock status and progress."""
        stats = self._parse_ticket_stats(tickets)
        achievements = []

        # Attendance milestones
        for ach in AchievementConfig.ATTENDANCE:
            current = stats["total_shows"]
            is_unlocked = current >= ach.threshold
            achievements.append(
                {
                    "id": ach.id,
                    "title": ach.title,
                    "description": ach.description,
                    "icon": ach.icon,
                    "color": ach.color,
                    "isUnlocked": is_unlocked,
                    "progress": f"{min(current, ach.threshold)}/{ach.threshold}"
                    if ach.threshold > 1
                    else None,
                }
            )

        # Same show milestones
        for ach in AchievementConfig.SAME_SHOW:
            current = stats["max_same_show"]
            is_unlocked = current >= ach.threshold
            achievements.append(
                {
                    "id": ach.id,
                    "title": ach.title,
                    "description": ach.description,
                    "icon": ach.icon,
                    "color": ach.color,
                    "isUnlocked": is_unlocked,
                    "progress": f"{min(current, ach.threshold)}/{ach.threshold}",
                }
            )

        # Anniversary milestones
        for ach in AchievementConfig.ANNIVERSARY:
            current = stats["time_span_days"]
            is_unlocked = current >= ach.threshold
            achievements.append(
                {
                    "id": ach.id,
                    "title": ach.title,
                    "description": ach.description,
                    "icon": ach.icon,
                    "color": ach.color,
                    "isUnlocked": is_unlocked,
                    "progress": f"{int(current)}/{ach.threshold} days",
                }
            )

        # Row milestones
        # Elite Seat
        achievements.append(
            {
                "id": "elite_row",
                "title": "Elite Seat",
                "description": "Sat in the legendary Row A",
                "icon": "crown",
                "color": "purple",
                "isUnlocked": stats["has_row_a"],
                "progress": None,
            }
        )
        # Back Row Warrior
        achievements.append(
            {
                "id": "back_row_warrior",
                "title": "Back Row Warrior",
                "description": "Watched from the furthest row (Row J)",
                "icon": "binoculars",
                "color": "indigo",
                "isUnlocked": stats["has_row_j"],
                "progress": None,
            }
        )
        # Seat Explorer
        achievements.append(
            {
                "id": "seat_explorer",
                "title": "Seat Explorer",
                "description": "Collected a ticket for every row (A-J)",
                "icon": "armchair",
                "color": "pink",
                "isUnlocked": stats["unique_rows_count"] >= 10,
                "progress": f"{stats['unique_rows_count']}/10",
            }
        )

        # Spending milestone
        total_spent = stats["total_spent"]
        achievements.append(
            {
                "id": "supporter",
                "title": "Top Supporter",
                "description": "Spent over 5 Million IDR on tickets",
                "icon": "wallet",
                "color": "emerald",
                "isUnlocked": total_spent >= 5000000,
                "progress": f"{(min(total_spent, 5000000) / 1000000):.1f}/5M",
            }
        )

        return achievements

    async def get_achievements(self, user_id: str) -> AchievementsResponse:
        """
        Get all achievements with unlock status and progress for Achievements page.
        """
        try:
            tickets = await self.tickets_service.get_my_tickets(
                user_id, None, resolve_images=False
            )
            achievements_data = self.calculate_achievements_full(tickets)

            # Convert to AchievementItem models
            achievements = [AchievementItem(**ach) for ach in achievements_data]

            unlocked_count = sum(1 for ach in achievements if ach.isUnlocked)

            return AchievementsResponse(
                achievements=achievements,
                unlockedCount=unlocked_count,
                totalCount=len(achievements),
            )
        except Exception as e:
            logger.error(f"Error fetching achievements: {str(e)}")
            raise AchievementsFetchError(str(e)) from e
