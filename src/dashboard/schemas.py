"""Schemas for Dashboard Service."""
from typing import Dict, List, Optional

from pydantic import BaseModel


class DayStat(BaseModel):
    """Statistics for a specific day of the week."""

    name: str
    count: int


class DayStatsResponse(BaseModel):
    """Response for day preference statistics."""

    stats: List[DayStat]
    max_count: int


class RowStatsResponse(BaseModel):
    """Response for row statistics."""

    counts: Dict[str, int]
    max_count: int
    unique_visited: int


class MonthlyStat(BaseModel):
    """Statistics for a specific month."""

    name: str
    count: int
    spent: int
    is_active: bool


class MonthlyStatsResponse(BaseModel):
    """Response for monthly attendance statistics."""

    stats: List[MonthlyStat]
    max_count: int


class TopShowResponse(BaseModel):
    """Response for top show statistics."""

    title: str
    count: int
    image: Optional[str] = None


class TopMemberResponse(BaseModel):
    """Response for top 2-shot member."""

    name: str
    count: int
    image: Optional[str] = None


class TwoShotStatsResponse(BaseModel):
    """Response for 2-shot statistics (without extremes)."""

    total_spend: int
    total_count: int
    unique_count: int
    top_2_shot: Optional[TopMemberResponse] = None


class ExtremeItem(BaseModel):
    """Data for first/last show or 2-shot."""

    ticket_id: str
    image: Optional[str] = None
    title: str
    date: str
    time: str
    detail: Optional[str] = None


class ExtremesResponse(BaseModel):
    """Response for first and last extremes."""

    first: Optional[ExtremeItem] = None
    last: Optional[ExtremeItem] = None


# Grouped Stats Classes


class TheaterStatsGroup(BaseModel):
    """Grouped statistics for Theater card."""

    total_visits: int
    total_spent: int
    most_frequent_row: str
    most_frequent_row_count: int
    top_show: TopShowResponse
    extremes: ExtremesResponse


class TwoShotStatsGroup(BaseModel):
    """Grouped statistics for 2-Shot card."""

    total_count: int
    total_spend: int
    unique_count: int
    top_2_shot: Optional[TopMemberResponse] = None
    extremes: ExtremesResponse


class SeatMapStatsGroup(BaseModel):
    """Grouped statistics for Seat Map."""

    row_stats: RowStatsResponse
    seat_stats: Dict[str, int]


class PeriodStatsGroup(BaseModel):
    """Grouped statistics for Periods (Monthly & Day)."""

    monthly_stats: MonthlyStatsResponse
    day_stats: DayStatsResponse


class DashboardStatsResponse(BaseModel):
    """Complete dashboard statistics response grouped by UI sections."""

    available_years: List[int]
    theater: TheaterStatsGroup
    two_shot: TwoShotStatsGroup
    seat_map: SeatMapStatsGroup
    period: PeriodStatsGroup
