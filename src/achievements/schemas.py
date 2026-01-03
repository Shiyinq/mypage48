from typing import Optional, List, NamedTuple
from pydantic import BaseModel


class AchievementDef(NamedTuple):
    """Definition of an achievement."""
    id: str
    title: str
    description: str
    icon: str
    color: str
    threshold: Optional[int] = None  # For progress-based achievements


class RankInfo(BaseModel):
    """Rank/level information based on total shows (XP)."""
    current: str
    xp: int
    nextLevelXp: int
    nextRankTitle: str


class AchievementItem(BaseModel):
    """Single achievement with unlock status and progress."""
    id: str
    title: str
    description: str
    icon: str
    color: str
    isUnlocked: bool
    progress: Optional[str] = None


class AchievementsResponse(BaseModel):
    """Response with all achievements and counts."""
    achievements: List[AchievementItem]
    unlockedCount: int
    totalCount: int
