from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DataUsersStats(BaseModel):
    total_users: int
    verified_users: int
    unverified_users: int
    total_admins: int
    total_feedback: int
    active_users_last_days: int
    public_profiles: int
    users_joined_today: int


class DataMyPageStats(BaseModel):
    total_tickets: int
    total_2shot: int
    total_journal: int
    total_favorites: int
    total_sorter: int
    total_money_spent_idr: float


class DataTheaterStats(BaseModel):
    total_members_jkt: int
    active_members_count: int
    graduated_members_count: int
    total_setlists: int
    active_setlists_count: int
    inactive_setlists_count: int
    total_events: int
    total_show_setlist: int
    total_upcoming_events_and_shows: int
    total_upcoming_events: int
    total_upcoming_shows: int
    upcoming_birthdays_count: int
    total_news: int
    total_live_member: int
    showroom_live_count: int
    idn_live_count: int
    total_replay_live: int
    showroom_replay_count: int
    idn_replay_count: int


class IDNLivePlusConfig(BaseModel):
    auth_token: Optional[str] = None
    access_token: Optional[str] = None
    session_id: Optional[str] = None
    api_key: Optional[str] = None
    aes_key: Optional[str] = None
    refresh_token: Optional[str] = None
    cognito_client_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    enabled: Optional[bool] = None


class IDNLivePlusConfigResponse(BaseModel):
    data: IDNLivePlusConfig
    detail: str
