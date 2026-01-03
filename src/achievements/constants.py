from typing import Optional

from src.achievements.schemas import AchievementDef


class ErrorCode:
    FETCH_FAILED = "Failed to fetch achievements"


class DomainErrorCode:
    FETCH_FAILED = "Error fetching achievements data"


class AchievementConfig:
    """Achievement definitions - mirrors frontend achievements.ts."""

    # Attendance milestones
    ATTENDANCE = [
        AchievementDef("first_show", "First Step", "Attended your first theater show", "heart", "red", 1),
        AchievementDef("regular_visitor", "Regular Visitor", "Attended 10 shows", "ticket", "orange", 10),
        AchievementDef("dedicated_fan_50", "Dedicated Fan", "Attended 50 shows", "award", "cyan", 50),
        AchievementDef("century_club_100", "Century Club", "Attended 100 shows", "medal", "violet", 100),
        AchievementDef("theater_icon_150", "Theater Icon", "Attended 150 shows", "zap", "fuchsia", 150),
        AchievementDef("legendary_wota_200", "Legendary Wota", "Attended 200 shows", "crown", "rose", 200),
        AchievementDef("theater_kami_300", "Theater Kami", "Attended 300 shows", "sparkles", "purple", 300),
        AchievementDef("absolute_legend_500", "Absolute Legend", "Attended 500 shows", "trophy", "amber", 500),
    ]

    # Same show milestones
    SAME_SHOW = [
        AchievementDef("super_fan", "Super Fan", "Watched the same event 10 times", "star", "yellow", 10),
        AchievementDef("mega_fan", "Mega Fan", "Watched the same event 20 times", "sparkles", "orange", 20),
        AchievementDef("ultra_fan", "Ultra Fan", "Watched the same event 30 times", "flame", "red", 30),
    ]

    # Anniversary milestones
    ANNIVERSARY = [
        AchievementDef("theater_enthusiast", "Theater Enthusiast", "1 year anniversary since first show", "calendar", "blue", 365),
        AchievementDef("theater_veteran", "Theater Veteran", "2 year anniversary since first show", "history", "indigo", 730),
        AchievementDef("theater_legend", "Theater Legend", "3 year anniversary since first show", "crown", "violet", 1095),
    ]

    # Row milestones (no threshold, boolean)
    ROW = [
        AchievementDef("elite_row", "Elite Seat", "Sat in the legendary Row A", "crown", "purple"),
        AchievementDef("back_row_warrior", "Back Row Warrior", "Watched from the furthest row (Row J)", "binoculars", "indigo"),
        AchievementDef("seat_explorer", "Seat Explorer", "Collected a ticket for every row (A-J)", "armchair", "pink", 10),
    ]

    # Spending milestones
    SPENDING = [
        AchievementDef("supporter", "Top Supporter", "Spent over 5 Million IDR on tickets", "wallet", "emerald", 5000000),
    ]


class RankConfig:
    """Configuration for user rank/level calculation."""
    MILESTONES = [
        {"xp": 0, "title": "Newcomer"},
        {"xp": 1, "title": "First Step"},
        {"xp": 10, "title": "Regular Visitor"},
        {"xp": 50, "title": "Dedicated Fan"},
        {"xp": 100, "title": "Century Club"},
        {"xp": 150, "title": "Theater Icon"},
        {"xp": 200, "title": "Legendary Wota"},
        {"xp": 300, "title": "Theater Kami"},
        {"xp": 500, "title": "Absolute Legend"},
    ]
