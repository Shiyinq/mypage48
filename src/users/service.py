import asyncio
import math
import time
from datetime import datetime, timezone
from typing import Optional

from pymongo.errors import DuplicateKeyError

from src.achievements.service import AchievementsService
from src.auth.email_service import EmailService
from src.auth.schemas import OshiResponse, OshiShowResponse
from src.auth.security_service import SecurityService
from src.config import Settings
from src.events.service import EventsService
from src.image_validation import ImageTooLargeError as ImageTooLargeValidationError
from src.image_validation import ImageValidationError
from src.image_validation import (
    InvalidImageTypeError as InvalidImageTypeValidationError,
)
from src.image_validation import validate_base64_image
from src.logging_config import create_logger
from src.members.service import MemberService
from src.storage.service import StorageService
from src.tickets.service import TicketsService
from src.users.constants import Info
from src.users.exceptions import (
    EmailAlreadyExistsError,
    ImageTooLargeError,
    InvalidImageError,
    InvalidImageTypeError,
    OshiUpdateError,
    ProfileStatsFetchError,
    ProviderUserCreationError,
    PublicStatusUpdateError,
    PublicUserNotFoundError,
    UserCreationError,
    UserFetchError,
    UsernameAlreadyExistsError,
    UserUpdateError,
)
from src.users.repository import UserRepository
from src.users.schemas import (
    MessageResponse,
    OshiTwoShotCounts,
    ProfileFullResponse,
    ProfileRecentActivity,
    ProfileStats,
    ProviderUserCreateRequest,
    PublicShowEntry,
    PublicUserResponse,
    UpdateProfileRequest,
    UserCreated,
    UserCreatedWithEmail,
    UserCreateRequest,
    UserInDB,
    UserListItem,
    UserListResponse,
    UserPaginationMeta,
    UserStats,
)

logger = create_logger("users_service", __name__)


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        security_service: SecurityService,
        email_service: EmailService,
        config: Settings,
        tickets_service: TicketsService,
        member_service: MemberService,
        achievements_service: AchievementsService,
        events_service: EventsService,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.security_service = security_service
        self.email_service = email_service
        self.config = config
        self.tickets_service = tickets_service
        self.member_service = member_service
        self.achievements_service = achievements_service
        self.events_service = events_service
        self.storage_service = storage_service

    def _handle_duplicate_key_error(self, dk: DuplicateKeyError):
        """Handle DuplicateKeyError and raise appropriate domain exception."""
        if dk.details and "keyPattern" in dk.details:
            keys = dk.details["keyPattern"]
            if "username" in keys:
                raise UsernameAlreadyExistsError()
            elif "email" in keys:
                raise EmailAlreadyExistsError()

        dk_str = str(dk)
        if "username" in dk_str:
            raise UsernameAlreadyExistsError()
        elif "email" in dk_str:
            raise EmailAlreadyExistsError()

    async def _generate_unique_member_id(self) -> str:
        """Generate a member ID based on registration timestamp."""
        return f"MYP48-{int(time.time() * 1000)}"

    async def create_user(self, request: UserCreateRequest) -> UserCreated:
        """
        Create a new user from registration request.
        Sensitive fields are set explicitly by this service, not from user input.
        """
        try:
            hashed_password = await asyncio.to_thread(
                self.security_service.get_password_hash, request.password
            )

            member_id = await self._generate_unique_member_id()

            user_in_db = UserInDB(
                name=request.fullName,
                memberId=member_id,
                username=request.username.lower(),
                email=request.email.lower(),
                ofcStatus="Active",
                password=hashed_password,
                isEmailVerified=False,
                failedLoginAttempts=0,
                isAccountLocked=False,
                accountLockedUntil=None,
            )

            await self.repository.insert_user(user_in_db.model_dump())

            try:
                token = await self.security_service.create_and_save_token(
                    user_in_db.userId,
                    "email_verification",
                    self.config.email_verification_expire_hours,
                )

                await self.email_service.send_email_verification(
                    user_in_db.email, token, user_in_db.username
                )
                return UserCreatedWithEmail()
            except Exception as e:
                logger.warning(
                    f"User created but error sending verification email: {e}"
                )
                return UserCreated()

        except DuplicateKeyError as dk:
            self._handle_duplicate_key_error(dk)
        except (UsernameAlreadyExistsError, EmailAlreadyExistsError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in create_user: {str(e)}")
            raise UserCreationError()

    async def create_user_provider(
        self, request: ProviderUserCreateRequest
    ) -> UserCreated:
        """
        Create a new user from OAuth provider.
        Provider users are automatically email verified.
        """
        try:
            user_in_db = UserInDB(
                profilePicture=request.profilePicture,
                name=request.name,
                username=request.username.lower(),
                email=request.email.lower(),
                password=None,
                provider=request.provider,
                isEmailVerified=True,
                failedLoginAttempts=0,
                isAccountLocked=False,
                accountLockedUntil=None,
            )

            await self.repository.insert_user(user_in_db.model_dump())
            return UserCreated()

        except DuplicateKeyError as dk:
            self._handle_duplicate_key_error(dk)
        except (UsernameAlreadyExistsError, EmailAlreadyExistsError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in create_user_provider: {str(e)}")
            raise ProviderUserCreationError()

    async def update_oshi(self, user_id: str, oshi_id: str) -> "MessageResponse":
        """Update the user's Oshi ID"""
        try:
            await self.repository.set_oshi_id(user_id, oshi_id)
            return MessageResponse(detail=Info.OSHI_UPDATED)
        except Exception as e:
            logger.exception(f"Error updating oshi: {str(e)}")
            raise OshiUpdateError()

    async def update_public_status(
        self, user_id: str, is_public: bool, public_year: int | None = None
    ) -> "MessageResponse":
        """Update the user's public profile status"""
        try:
            await self.repository.set_public_status(user_id, is_public, public_year)
            return MessageResponse(detail=Info.PUBLIC_STATUS_UPDATED)
        except Exception as e:
            logger.exception(f"Error updating public status: {str(e)}")
            raise PublicStatusUpdateError()

    async def get_public_user_by_username(self, username: str) -> UserInDB | None:
        """Get a user by username if they are public"""
        try:
            user_data = await self.repository.find_one({"username": username.lower()})
            if not user_data:
                return None

            user = UserInDB(**user_data)
            if not user.isPublic:
                return None

            return user
        except Exception as e:
            logger.exception(f"Error fetching public user: {str(e)}")
            raise UserFetchError()

    async def update_profile_picture(
        self, user_id: str, profile_picture: str, blur_hash: Optional[str] = None
    ) -> MessageResponse:
        """Update the user's profile picture"""
        try:
            # Fetch current user to get old profile picture for cleanup
            current_user = await self.repository.get_user_by_id(user_id)
            if not current_user:
                raise UserFetchError()

            # Only validate if it's a base64 image (legacy upload)
            # Storage filenames (category/user_id/filename) skip validation
            if profile_picture.startswith("data:"):
                validate_base64_image(profile_picture)

            await self.repository.set_profile_picture(
                user_id, profile_picture, blur_hash
            )

            # Cleanup old profile picture from R2 if it changed
            old_pic = current_user.get("profilePicture")
            if old_pic and old_pic != profile_picture:
                await self.storage_service.delete_image(old_pic)

            return MessageResponse(detail=Info.PROFILE_PICTURE_UPDATED)
        except ImageTooLargeValidationError:
            raise ImageTooLargeError()
        except InvalidImageTypeValidationError:
            raise InvalidImageTypeError()
        except ImageValidationError:
            raise InvalidImageError()
        except Exception as e:
            logger.exception(f"Error updating profile picture: {str(e)}")
            raise UserUpdateError()

    async def update_profile(
        self, user_id: str, request: UpdateProfileRequest
    ) -> MessageResponse:
        """Update user profile information (name, username, email)"""
        try:
            # Get current user data
            user_data = await self.repository.get_user_by_id(user_id)
            if not user_data:
                raise UserFetchError()

            current_user = UserInDB(**user_data)
            update_data = {"updatedAt": datetime.now()}

            # Handle Name Update
            if request.name is not None:
                update_data["name"] = request.name

            # Handle Username Update
            if request.username is not None:
                new_username = request.username.lower()
                if new_username != current_user.username:
                    # Duplicate check is handled by repository unique index + our _handle_duplicate_key_error
                    update_data["username"] = new_username

            # Handle Email Update
            email_changed = False
            if request.email is not None:
                new_email = request.email.lower()
                if new_email != current_user.email:
                    update_data["email"] = new_email
                    update_data["isEmailVerified"] = False
                    email_changed = True

            if len(update_data) > 1:  # More than just updatedAt
                try:
                    await self.repository.update_one(
                        {"userId": user_id}, {"$set": update_data}
                    )
                except DuplicateKeyError as dk:
                    self._handle_duplicate_key_error(dk)

            # Send verification email if changed
            if email_changed:
                try:
                    token = await self.security_service.create_and_save_token(
                        user_id,
                        "email_verification",
                        self.config.email_verification_expire_hours,
                    )
                    await self.email_service.send_email_verification(
                        update_data["email"],
                        token,
                        update_data.get("username", current_user.username),
                    )
                except Exception as e:
                    logger.warning(
                        f"Profile updated but error sending verification email: {e}"
                    )

            return MessageResponse(detail=Info.PROFILE_UPDATED)

        except (UsernameAlreadyExistsError, EmailAlreadyExistsError):
            raise
        except Exception as e:
            logger.exception(f"Error updating profile: {str(e)}")
            raise UserUpdateError()

    async def get_public_profile(
        self,
        username: str,
    ) -> "PublicUserResponse":
        """
        Get a user's public profile by username.
        Raises PublicUserNotFoundError if user not found or is private.
        """

        user = await self.get_public_user_by_username(username)
        if not user:
            raise PublicUserNotFoundError()

        oshi_response = None
        if user.oshiId:
            try:
                # Ensure oshiId is string provided to MemberService
                member_detail = await self.member_service.get_member_by_id(
                    str(user.oshiId)
                )
                member = member_detail.member
                oshi_response = OshiResponse(
                    name=member.name,
                    nickname=member.nickname,
                    generation=member.generation or "-",
                    profilePicture=member.img,
                    profilePicture_medium=member.img_medium,
                    profilePicture_small=member.img_small,
                    blurHash=member.blurHash,
                    catchphrase=member.jiko or "-",
                    socials=member.socials.model_dump() if member.socials else None,
                )
            except Exception as e:
                logger.warning(f"Failed to fetch oshi data for id {user.oshiId}: {e}")

        # Calculate Stats
        stats = None

        # Handle "This Year" option (-1) by converting to current year
        query_year = user.publicYear
        display_year = user.publicYear

        if user.publicYear == -1:
            query_year = datetime.now().year
            display_year = query_year  # Show the actual year in the UI

        try:
            # Respect user's public year setting if set
            tickets = await self.tickets_service.get_my_tickets(user.userId, query_year)
            total_shows = len(tickets)
            total_spent = sum(t.price for t in tickets)
            total_2shots = sum(1 for t in tickets if t.two_shot is not None)

            # Add 2-shot spending to total spent
            total_spent += sum(
                t.two_shot.price for t in tickets if t.two_shot and t.two_shot.price
            )

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

            top_row = "-"
            top_row_count = 0
            if row_counts:
                # Sort by count desc
                top_row = max(row_counts, key=row_counts.get)
                top_row_count = row_counts[top_row]

            top_show = "-"
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
                        type="2-Shot" if t.two_shot else "Theater",
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
                recentActivity=recent_activity,
            )
        except Exception as e:
            logger.warning(f"Failed to calculate stats for user {user.userId}: {e}")

        profile_picture = user.profilePicture
        if profile_picture:
            variants = await self.storage_service.resolve_image_variants(
                profile_picture
            )
            profile_picture = variants["url"]
            profile_picture_medium = variants["url_medium"]
            profile_picture_small = variants["url_small"]
            blur_hash = variants["blurHash"]
        else:
            profile_picture_medium = None
            profile_picture_small = None
            blur_hash = None

        return PublicUserResponse(
            name=user.name,
            username=user.username,
            profilePicture=profile_picture,
            profilePicture_medium=profile_picture_medium,
            profilePicture_small=profile_picture_small,
            blurHash=blur_hash,
            oshi=oshi_response,
            createdAt=user.createdAt,
            publicYear=display_year,  # Show actual year for "This Year" option
            stats=stats,
        )

    async def get_profile_full(
        self,
        current_user,
    ) -> ProfileFullResponse:
        """
        Get complete profile with all stats for Profile page.
        Returns profile, oshi, rank, stats, oshi 2-shots, and recent activity.
        """
        try:
            # Get oshi data
            oshi_response = None
            oshi_name = None
            if current_user.oshiId:
                try:
                    member_detail = await self.member_service.get_member_by_id(
                        str(current_user.oshiId)
                    )
                    member = member_detail.member
                    oshi_name = member.name
                    oshi_response = OshiResponse(
                        name=member.name,
                        nickname=member.nickname,
                        generation=member.generation or "-",
                        profilePicture=member.img,
                        profilePicture_medium=member.img_medium,
                        profilePicture_small=member.img_small,
                        blurHash=member.blurHash,
                        catchphrase=member.jiko or "-",
                        socials=member.socials.model_dump() if member.socials else None,
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch oshi data for id {current_user.oshiId}: {e}"
                    )

            # Get tickets for stats calculation
            tickets = await self.tickets_service.get_my_tickets(
                current_user.userId, None
            )

            total_shows = len(tickets)
            rank = self.achievements_service.calculate_rank(total_shows)

            total_achievements = self.achievements_service.calculate_achievements_count(
                tickets
            )

            # Calculate oshi 2-shot counts and meetings
            roulette_count = 0
            birthday_count = 0
            oshi_meetings = 0

            if oshi_name:
                # 1. 2-Shot Counts
                for t in tickets:
                    if t.two_shot and t.two_shot.member_name == oshi_name:
                        if t.two_shot.type == "Roulette":
                            roulette_count += 1
                        elif t.two_shot.type == "Birthday":
                            birthday_count += 1

                # 2. Oshi Meetings (Attendance at events where Oshi was present)
                # Fetch all events where Oshi was a member
                oshi_events = await self.events_service.get_events_for_member(
                    str(current_user.oshiId)
                )
                # Create a set of unique event identifiers (title + date) for O5 events
                oshi_event_keys = set()
                for e in oshi_events:
                    # e is a dict from find_events_by_member_id projection
                    # key format: "Title|YYYY-MM-DD"
                    # Ensure date is string YYYY-MM-DD if it's datetime
                    d = e.get("date")
                    if isinstance(d, datetime):
                        d = d.strftime("%Y-%m-%d")
                    elif isinstance(d, str):
                        # If date includes time, take only YYYY-MM-DD part
                        d = d.split("T")[0]

                    oshi_event_keys.add(f"{e.get('title')}|{d}")

                # Check user tickets against these events
                for t in tickets:
                    # t.event.date is "YYYY-MM-DD" string
                    ticket_key = f"{t.event.title}|{t.event.date}"
                    if ticket_key in oshi_event_keys:
                        oshi_meetings += 1

                # 3. Calculate oshi total shows
                oshi_total_shows = len(oshi_events)

                if oshi_response:
                    oshi_response.totalShows = oshi_total_shows

                    # Split oshi_events into upcoming and history
                    now = datetime.now()
                    upcoming_events = []
                    past_events = []

                    for e in oshi_events:
                        event_date = e.get("date")
                        if not isinstance(event_date, datetime):
                            try:
                                event_date = datetime.fromisoformat(str(event_date))
                            except:
                                continue

                        show_data = OshiShowResponse(
                            title=e.get("title", "Unknown"),
                            date=event_date,
                            url=e.get("url"),
                        )

                        if event_date >= now:
                            upcoming_events.append(show_data)
                        else:
                            past_events.append(show_data)

                    # Sort and limit
                    # Upcoming: Ascending (soonest first) - No limit
                    # History: Descending (most recent first) - Limit 5
                    oshi_response.upcomingSchedule = sorted(
                        upcoming_events, key=lambda x: x.date
                    )
                    oshi_response.pastSchedule = sorted(
                        past_events, key=lambda x: x.date, reverse=True
                    )[:5]

            # Get recent activity (5 most recent shows)
            sorted_tickets = sorted(tickets, key=lambda x: x.event.date, reverse=True)
            recent_activity = []
            for t in sorted_tickets[:5]:
                recent_activity.append(
                    ProfileRecentActivity(
                        ticketId=t.ticket_id,
                        title=t.event.title,
                        date=str(t.event.date),
                        section=t.seat.section if t.seat else "",
                        number=str(t.seat.number) if t.seat else "",
                        hasTwoShot=t.two_shot is not None,
                        twoShotMember=t.two_shot.member_name if t.two_shot else None,
                    )
                )

            # Resolve profile picture if it's a storage path
            profile_pic = current_user.profilePicture
            profile_pic_medium = None
            profile_pic_small = None
            if profile_pic:
                variants = await self.storage_service.resolve_image_variants(
                    profile_pic
                )
                profile_pic = variants["url"]
                profile_pic_medium = variants["url_medium"]
                profile_pic_small = variants["url_small"]
                blur_hash = variants["blurHash"]
            else:
                blur_hash = getattr(current_user, "blurHash", None)

            # Build profile dict from current_user
            profile_dict = {
                "userId": current_user.userId,
                "profilePicture": profile_pic,
                "profilePicture_medium": profile_pic_medium,
                "profilePicture_small": profile_pic_small,
                "blurHash": blur_hash,
                "name": current_user.name,
                "email": current_user.email,
                "username": current_user.username,
                "memberId": current_user.memberId,
                "oshiId": current_user.oshiId,
                "ofcStatus": current_user.ofcStatus,
                "isPublic": current_user.isPublic,
                "publicYear": current_user.publicYear,
                "isAdmin": current_user.isAdmin,
                "isEmailVerified": current_user.isEmailVerified,
                "createdAt": current_user.createdAt,
            }

            return ProfileFullResponse(
                profile=profile_dict,
                oshi=oshi_response,
                rank=rank,
                stats=ProfileStats(
                    totalShows=total_shows,
                    totalAchievements=total_achievements,
                    oshiMeetings=oshi_meetings,
                ),
                oshiTwoShots=OshiTwoShotCounts(
                    roulette=roulette_count, birthday=birthday_count
                ),
                recentActivity=recent_activity,
            )

        except Exception as e:
            logger.exception(f"Error fetching profile stats: {str(e)}")
            raise ProfileStatsFetchError()

    async def get_all_users(
        self, page: int, limit: int, search: str | None = None
    ) -> "UserListResponse":
        """
        Get paginated list of users (admin only).
        Returns user list with pagination metadata.
        """
        try:
            users = await self.repository.get_all_paginated(page, limit, search)
            total = await self.repository.count_all(search)

            async def _resolve_user(u):
                profile_pic = u.get("profilePicture")
                profile_pic_medium = None
                profile_pic_small = None
                if profile_pic:
                    variants = await self.storage_service.resolve_image_variants(
                        profile_pic
                    )
                    profile_pic = variants["url"]
                    profile_pic_medium = variants["url_medium"]
                    profile_pic_small = variants["url_small"]
                    blur_hash = variants["blurHash"]
                else:
                    blur_hash = u.get("blurHash")

                last_active = u.get("lastActiveAt")
                if last_active and last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)

                created_at = u.get("createdAt")
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                return UserListItem(
                    userId=u.get("userId", ""),
                    name=u.get("name", ""),
                    username=u.get("username", ""),
                    email=u.get("email", ""),
                    profilePicture=profile_pic,
                    profilePicture_medium=profile_pic_medium,
                    profilePicture_small=profile_pic_small,
                    blurHash=blur_hash,
                    isAdmin=u.get("isAdmin", False),
                    isEmailVerified=u.get("isEmailVerified", False),
                    isAccountLocked=u.get("isAccountLocked", False),
                    createdAt=created_at,
                    lastActiveAt=last_active,
                )

            if users:
                user_list = list(
                    await asyncio.gather(*(_resolve_user(u) for u in users))
                )
            else:
                user_list = []

            last_page = math.ceil(total / limit) if total > 0 else 1
            next_page = page + 1 if page < last_page else None

            return UserListResponse(
                data=user_list,
                meta=UserPaginationMeta(
                    current_page=page,
                    last_page=last_page,
                    total_data=total,
                    per_page=limit,
                    next_page=next_page,
                ),
            )
        except Exception as e:
            logger.exception(f"Error fetching users list: {str(e)}")
            raise UserFetchError()
