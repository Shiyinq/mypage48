from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src import dependencies
from src.auth.schemas import UserCurrent, OshiResponse
from src.dependencies import (
    get_user_service,
    get_member_service,
    get_theater_service,
)
from src.logging_config import create_logger
from src.users.schemas import (
    UserCreatedWithEmail,
    UserCreateRequest,
    UserCreateResponse,
)
from src.users.service import UserService
from src.members.service import MemberService
from src.users.schemas import (
    UserCreatedWithEmail,
    UserCreateRequest,
    UserCreateResponse,
    PublicUserResponse,
    UserStats,
    PublicShowEntry,
)
from src.users.service import UserService
from src.members.service import MemberService
from src.theater.service import TheaterService
from fastapi import HTTPException

router = APIRouter()

logger = create_logger("users", __name__)


@router.post("/users/signup", status_code=201, response_model=UserCreateResponse)
async def signup(
    user: UserCreateRequest, user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user account.
    """

    result = await user_service.create_user(user)

    if isinstance(result, UserCreatedWithEmail):
        logger.info("User created successfully and verification email sent")
    else:
        logger.info("User created successfully")

    return result


@router.get("/users/profile", response_model=UserCurrent)
async def user_profile(
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    member_service: MemberService = Depends(get_member_service),
):
    """
    Get the profile information of the currently logged-in user.

    Returns:
        UserCurrent: The current user's profile data.
    """

    oshi_response = None

    if current_user.oshiId:
        try:
            member_detail = await member_service.get_member_by_id(current_user.oshiId)
            member = member_detail.member
            oshi_response = OshiResponse(
                name=member.name,
                nickname=member.nickname,
                generation=member.generation or "-",
                profilePicture=member.img or "https://upload.wikimedia.org/wikipedia/commons/8/82/JKT48.svg",
                catchphrase=member.jiko or "-",
                socials=member.socials.model_dump() if member.socials else None
            )
        except Exception as e:
            logger.warning(f"Failed to fetch oshi data for id {current_user.oshiId}: {e}")

    current_user.oshi = oshi_response
    return current_user


class UpdateOshiRequest(BaseModel):
    oshiId: int


@router.post("/users/oshi", status_code=200)
async def update_oshi(
    request: UpdateOshiRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the user's Oshi.
    """
    await user_service.update_oshi(current_user.userId, request.oshiId)
    return {"message": "Oshi updated successfully"}


class UpdatePublicStatusRequest(BaseModel):
    isPublic: bool
    publicYear: int | None = None # None means "All Time"


@router.post("/users/public-status", status_code=200)
async def update_public_status(
    request: UpdatePublicStatusRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the user's public profile status.
    """
    await user_service.update_public_status(current_user.userId, request.isPublic, request.publicYear)
    return {"message": "Public status updated successfully"}


@router.get("/u/{username}", response_model=PublicUserResponse)
async def get_public_profile(
    username: str,
    user_service: UserService = Depends(get_user_service),
    member_service: MemberService = Depends(get_member_service),
    theater_service: TheaterService = Depends(get_theater_service),
):
    """
    Get a user's public profile by username.
    """
    user = await user_service.get_public_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found or private")

    oshi_response = None
    if user.oshiId:
        try:
            member_detail = await member_service.get_member_by_id(user.oshiId)
            member = member_detail.member
            oshi_response = OshiResponse(
                name=member.name,
                nickname=member.nickname,
                generation=member.generation or "-",
                profilePicture=member.img or "https://upload.wikimedia.org/wikipedia/commons/8/82/JKT48.svg",
                catchphrase=member.jiko or "-",
                socials=member.socials.model_dump() if member.socials else None
            )
        except Exception as e:
            logger.warning(f"Failed to fetch oshi data for id {user.oshiId}: {e}")

    # Calculate Stats
    stats = None
    try:
        # Respect user's public year setting if set
        tickets = await theater_service.get_my_tickets(user.userId, user.publicYear)
        total_shows = len(tickets)
        total_spent = sum(t.price for t in tickets)
        total_2shots = sum(1 for t in tickets if t.two_shot is not None)
        
        # Add 2-shot spending to total spent
        total_spent += sum(t.two_shot.price for t in tickets if t.two_shot and t.two_shot.price)

        # Calculate Seat Stats & Top Show
        row_counts = {}
        seat_counts = {}
        show_counts = {}

        for t in tickets:
            # Row stats
            if t.seat and t.seat.section:
                row = t.seat.section.strip().upper()[0]
                row_counts[row] = row_counts.get(row, 0) + 1
                
                # Seat stats
                seat_key = f"{row}-{t.seat.number}"
                seat_counts[seat_key] = seat_counts.get(seat_key, 0) + 1
            
            # Show stats
            if t.event and t.event.title:
                show_counts[t.event.title] = show_counts.get(t.event.title, 0) + 1

        top_row = '-'
        top_row_count = 0
        if row_counts:
            # Sort by count desc
            top_row = max(row_counts, key=row_counts.get)
            top_row_count = row_counts[top_row]
            
        top_show = '-'
        top_show_count = 0
        if show_counts:
            top_show = max(show_counts, key=show_counts.get)
            top_show_count = show_counts[top_show]

        # Recent Activity (Top 5 sorted by date descending)
        sorted_tickets = sorted(tickets, key=lambda x: x.event.date, reverse=True)
        recent_activity = []
        for t in sorted_tickets[:5]:
            recent_activity.append(
                PublicShowEntry(
                    title=t.event.title,
                    date=t.event.date,
                    type="2-Shot" if t.two_shot else "Theater"
                )
            )

        # Create Stats Object
        stats = UserStats(
            totalShows=total_shows,
            totalTwoShots=total_2shots,
            totalSpent=total_spent,
            topRow=top_row,
            topShow=top_show,
            topRowCount=top_row_count,
            topShowCount=top_show_count,
            rowCounts=row_counts,
            seatCounts=seat_counts,
            recentActivity=recent_activity
        )
    except Exception as e:
        logger.warning(f"Failed to calculate stats for user {user.userId}: {e}")

    return PublicUserResponse(
        name=user.name,
        username=user.username,
        profilePicture=user.profilePicture,
        oshi=oshi_response,
        createdAt=user.createdAt,
        publicYear=user.publicYear,
        stats=stats
    )
