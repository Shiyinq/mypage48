from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from src.setlists.schemas import SetlistBase
from src.members.schemas import MemberBase


class EventTeam(BaseModel):
    id: str
    img: str


class Event(BaseModel):
    id: str
    title: str
    date: datetime
    url: str
    label: str
    
    # Optional fields from 'detail' event type
    # List View Fields
    imageUrl: Optional[str] = None
    totalMembers: int = 0
    
    # Detail fields (excluded from list view by default in repository projection, but kept here if we want to reuse schema for detail later, 
    # though user asked to remove them. For now, let's keep them optional but defaulting to None/Empty so they don't show up if not populated)
    # Actually, user said "hilangkan juga...". Pydantic will show them if they are in schema unless we use response_model_exclude_unset.
    # But usually it's cleaner to have a separate List schema. 
    # Given the codebase simplifies things, I will make them Optional and default to None.
    # And I will NOT populate them in the repository list query.
    
    # However, for totalMembers, we need it.
    
    # Refactoring based on user request "hilangkan juga graduationIds... gantikan dengan totalMember"
    
    setlistId: Optional[str] = None
    team: Optional[EventTeam] = None
    
    # We will remove these from the output if they are None/Empty? 
    # The user said "hilangkan juga", implying he doesn't want to see them in the JSON response.
    # I will comment them out or remove them for now. If needed for detail, we can add a DetailSchema.
    # memberIds: Optional[List[str]] = Field(default_factory=list)
    # seitansaiIds: Optional[List[str]] = Field(default_factory=list)
    # graduationIds: Optional[List[str]] = Field(default_factory=list)

    # Aggregated fields - removing as per request for list view
    # setlist: Optional[SetlistBase] = None
    # members: Optional[List[MemberBase]] = Field(default_factory=list)
    # graduations: Optional[List[MemberBase]] = Field(default_factory=list)
    # seitansais: Optional[List[MemberBase]] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class PaginationMeta(BaseModel):
    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class EventPaginationResponse(BaseModel):
    data: List[Event]
    meta: PaginationMeta
