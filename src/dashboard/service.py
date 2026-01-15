from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config import Settings
from src.dashboard.constants import DashboardConstants
from src.dashboard.exceptions import StatsFetchError
from src.dashboard.schemas import (
    DashboardStatsResponse,
    DayStat,
    DayStatsResponse,
    ExtremeItem,
    ExtremesResponse,
    MonthlyStat,
    MonthlyStatsResponse,
    PeriodStatsGroup,
    RowStatsResponse,
    SeatMapStatsGroup,
    TheaterStatsGroup,
    TopMemberResponse,
    TopShowResponse,
    TwoShotStatsGroup,
    TwoShotStatsResponse,
)
from src.logging_config import create_logger
from src.tickets.repository import TicketsRepository

logger = create_logger("dashboard_service", __name__)


class DashboardService:
    """Service for generating dashboard statistics from ticket data."""

    def __init__(
        self,
        tickets_repository: TicketsRepository,
        config: Settings,
    ):
        self.tickets_repository = tickets_repository
        self.config = config

    @staticmethod
    def _get_show_image(title: str) -> Optional[str]:
        """Get show image URL based on title."""
        title_lower = title.lower()
        for show in DashboardConstants.SHOW_IMAGES:
            if show["title"].lower() in title_lower:
                return show["image"]
        return None

    @staticmethod
    def _format_date(date_str: str, include_year: bool = False) -> str:
        """Format date string for display."""
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            if include_year:
                return d.strftime("%d %b %Y")
            return d.strftime("%d %b")
        except (ValueError, TypeError):
            return date_str

    def _calculate_day_stats(self, tickets: List[Dict[str, Any]]) -> DayStatsResponse:
        """Calculate day preference statistics."""
        stats = {day: 0 for day in DashboardConstants.DAYS}

        for t in tickets:
            event = t.get("event", {})
            day = event.get("day")
            if not day:
                # Calculate day from date if not stored
                try:
                    date_str = event.get("date", "")
                    d = datetime.strptime(date_str, "%Y-%m-%d")
                    day = d.strftime("%A")
                except (ValueError, TypeError):
                    continue

            if day:
                day_normalized = day.strip().capitalize()
                if day_normalized in stats:
                    stats[day_normalized] += 1

        stats_list = [
            DayStat(name=day, count=stats[day]) for day in DashboardConstants.DAYS
        ]
        max_count = max((s.count for s in stats_list), default=1) or 1
        return DayStatsResponse(stats=stats_list, max_count=max_count)

    def _calculate_row_stats(self, tickets: List[Dict[str, Any]]) -> RowStatsResponse:
        """Calculate row statistics."""
        counts: Dict[str, int] = {}

        for t in tickets:
            seat = t.get("seat", {})
            section = seat.get("section", "").strip().upper()
            if section:
                row = section[0]
                if row in DashboardConstants.THEATER_ROWS:
                    counts[row] = counts.get(row, 0) + 1

        max_count = max(counts.values(), default=1) or 1
        return RowStatsResponse(
            counts=counts,
            max_count=max_count,
            unique_visited=len(counts),
        )

    def _calculate_seat_stats(self, tickets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate seat statistics."""
        stats: Dict[str, int] = {}

        for t in tickets:
            seat = t.get("seat", {})
            section = seat.get("section", "").strip().upper()
            number = seat.get("number")
            if section and number:
                row = section[0]
                key = f"{row}-{number}"
                stats[key] = stats.get(key, 0) + 1

        return stats

    def _calculate_monthly_stats(
        self,
        tickets: List[Dict[str, Any]],
        start_month: int,
        end_month: int,
        is_all_data: bool,
    ) -> MonthlyStatsResponse:
        """Calculate monthly attendance statistics."""
        stats = []
        for i in range(12):
            month_date = datetime(2000, i + 1, 1)
            stats.append(
                {
                    "name": month_date.strftime("%b"),
                    "count": 0,
                    "spent": 0,
                    "is_active": is_all_data or (start_month <= i <= end_month),
                }
            )

        for t in tickets:
            try:
                date_str = t.get("event", {}).get("date", "")
                d = datetime.strptime(date_str, "%Y-%m-%d")
                m = d.month - 1
                stats[m]["count"] += 1
                stats[m]["spent"] += t.get("price", 0)
            except (ValueError, TypeError):
                continue

        stats_list = [
            MonthlyStat(
                name=s["name"],
                count=s["count"],
                spent=s["spent"],
                is_active=s["is_active"],
            )
            for s in stats
        ]
        max_count = max((s.count for s in stats_list), default=1) or 1
        return MonthlyStatsResponse(stats=stats_list, max_count=max_count)

    def _calculate_top_show(self, tickets: List[Dict[str, Any]]) -> TopShowResponse:
        """Calculate top show statistics."""
        if not tickets:
            return TopShowResponse(title="-", count=0, image=None)

        counts: Dict[str, int] = {}
        for t in tickets:
            title = t.get("event", {}).get("title", "").strip()
            if title:
                counts[title] = counts.get(title, 0) + 1

        if not counts:
            return TopShowResponse(title="-", count=0, image=None)

        top_title = max(counts.keys(), key=lambda k: counts[k])
        return TopShowResponse(
            title=top_title,
            count=counts[top_title],
            image=self._get_show_image(top_title),
        )

    def _calculate_two_shot_stats(
        self, tickets: List[Dict[str, Any]]
    ) -> TwoShotStatsResponse:
        """Calculate 2-shot statistics."""
        member_stats: Dict[str, Dict[str, Any]] = {}
        total_spend = 0
        total_count = 0
        unique_members: set = set()

        for t in tickets:
            two_shot = t.get("two_shot")
            if two_shot and two_shot.get("member_name"):
                name = two_shot["member_name"].strip()
                price = two_shot.get("price", 0)
                total_spend += price
                total_count += 1
                unique_members.add(name)

                if name not in member_stats:
                    member_stats[name] = {"count": 0, "image": two_shot.get("imageUrl")}
                member_stats[name]["count"] += 1
                if two_shot.get("imageUrl"):
                    member_stats[name]["image"] = two_shot["imageUrl"]

        top_member = None
        if member_stats:
            top_name = max(member_stats.keys(), key=lambda k: member_stats[k]["count"])
            top_data = member_stats[top_name]
            top_member = TopMemberResponse(
                name=top_name, count=top_data["count"], image=top_data.get("image")
            )

        return TwoShotStatsResponse(
            total_spend=total_spend,
            total_count=total_count,
            unique_count=len(unique_members),
            top_2_shot=top_member,
        )

    def _calculate_show_extremes(
        self, tickets: List[Dict[str, Any]], include_year: bool
    ) -> ExtremesResponse:
        """Calculate first and last show."""
        if not tickets:
            return ExtremesResponse(first=None, last=None)

        sorted_tickets = sorted(
            tickets,
            key=lambda t: (
                t.get("event", {}).get("date", ""),
                t.get("event", {}).get("time", ""),
            ),
        )

        first = sorted_tickets[0]
        last = sorted_tickets[-1]

        def to_extreme_item(t: Dict[str, Any]) -> ExtremeItem:
            event = t.get("event", {})
            seat = t.get("seat", {})
            section = seat.get("section", "").strip().upper()
            row = section[0] if section else ""
            number = seat.get("number", "")
            return ExtremeItem(
                ticket_id=str(t.get("_id", "")),
                image=self._get_show_image(event.get("title", "")),
                title=event.get("title", "-"),
                date=self._format_date(event.get("date", ""), include_year),
                time=event.get("time", ""),
                detail=f"Row {row} - {number}" if row and number else None,
            )

        return ExtremesResponse(
            first=to_extreme_item(first),
            last=to_extreme_item(last),
        )

    def _calculate_two_shot_extremes(
        self, tickets: List[Dict[str, Any]], include_year: bool
    ) -> ExtremesResponse:
        """Calculate first and last 2-shot."""
        with_two_shot = [
            t for t in tickets if (t.get("two_shot") or {}).get("member_name")
        ]

        if not with_two_shot:
            return ExtremesResponse(first=None, last=None)

        sorted_tickets = sorted(
            with_two_shot,
            key=lambda t: (
                t.get("event", {}).get("date", ""),
                t.get("event", {}).get("time", ""),
            ),
        )

        first = sorted_tickets[0]
        last = sorted_tickets[-1]

        def to_extreme_item(t: Dict[str, Any]) -> ExtremeItem:
            event = t.get("event", {})
            two_shot = t.get("two_shot", {})
            return ExtremeItem(
                ticket_id=str(t.get("_id", "")),
                image=two_shot.get("imageUrl"),
                title=two_shot.get("member_name", "-"),
                date=self._format_date(event.get("date", ""), include_year),
                time=event.get("time", ""),
                detail=None,
            )

        return ExtremesResponse(
            first=to_extreme_item(first),
            last=to_extreme_item(last),
        )

    async def get_dashboard_stats(
        self,
        user_id: str,
        year: Optional[int] = None,
        start_month: int = 0,
        end_month: int = 11,
        is_all_data: bool = False,
    ) -> DashboardStatsResponse:
        """Get complete dashboard statistics for a user."""
        try:
            # Get available years (efficient query)
            available_years = await self.tickets_repository.get_available_years(user_id)

            # Ensure current year is always in the list
            current_year = datetime.now().year
            if current_year not in available_years:
                available_years.append(current_year)

            # Sort descending
            available_years.sort(reverse=True)

            # Use current year if not specified
            if year is None:
                year = datetime.now().year

            # Filter tickets based on parameters (efficient query)
            filtered_tickets = await self.tickets_repository.get_tickets_filtered(
                user_id, year, start_month, end_month, is_all_data
            )

            # Calculate all statistics
            total_spent = sum(t.get("price", 0) for t in filtered_tickets)
            total_visits = len(filtered_tickets)

            day_stats = self._calculate_day_stats(filtered_tickets)
            row_stats = self._calculate_row_stats(filtered_tickets)
            seat_stats = self._calculate_seat_stats(filtered_tickets)
            monthly_stats = self._calculate_monthly_stats(
                filtered_tickets, start_month, end_month, is_all_data
            )
            top_show = self._calculate_top_show(filtered_tickets)
            two_shot_stats = self._calculate_two_shot_stats(filtered_tickets)
            show_extremes = self._calculate_show_extremes(filtered_tickets, is_all_data)
            two_shot_extremes = self._calculate_two_shot_extremes(
                filtered_tickets, is_all_data
            )

            # Calculate most frequent row
            most_frequent_row = "-"
            most_frequent_row_count = 0
            if row_stats.counts:
                most_frequent_row = max(
                    row_stats.counts.keys(), key=lambda k: row_stats.counts[k]
                )
                most_frequent_row_count = row_stats.counts[most_frequent_row]

            # Group statistics
            theater_stats = TheaterStatsGroup(
                total_visits=total_visits,
                total_spent=total_spent,
                most_frequent_row=most_frequent_row,
                most_frequent_row_count=most_frequent_row_count,
                top_show=top_show,
                extremes=show_extremes,
            )

            two_shot_stats_group = TwoShotStatsGroup(
                total_count=two_shot_stats.total_count,
                total_spend=two_shot_stats.total_spend,
                unique_count=two_shot_stats.unique_count,
                top_2_shot=two_shot_stats.top_2_shot,
                extremes=two_shot_extremes,
            )

            seat_map_stats = SeatMapStatsGroup(
                row_stats=row_stats,
                seat_stats=seat_stats,
            )

            period_stats = PeriodStatsGroup(
                monthly_stats=monthly_stats,
                day_stats=day_stats,
            )

            return DashboardStatsResponse(
                available_years=available_years,
                theater=theater_stats,
                two_shot=two_shot_stats_group,
                seat_map=seat_map_stats,
                period=period_stats,
            )
        except Exception as e:
            logger.exception(f"Error fetching dashboard stats: {str(e)}")
            raise StatsFetchError() from e
