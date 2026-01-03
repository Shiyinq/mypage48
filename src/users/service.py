import asyncio
from datetime import datetime

from pymongo.errors import DuplicateKeyError

from src.auth.email_service import EmailService
from src.auth.schemas import OshiResponse
from src.auth.security_service import SecurityService
from src.config import Settings
from src.image_validation import (
    validate_base64_image,
    ImageValidationError,
    ImageTooLargeError as ImageTooLargeValidationError,
    InvalidImageTypeError as InvalidImageTypeValidationError,
)
from src.logging_config import create_logger
from src.users.constants import Info, RankConfig
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
    UserUpdateError,
    UsernameAlreadyExistsError,
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
    RankInfo,
    UserCreated,
    UserCreatedWithEmail,
    UserCreateRequest,
    UserInDB,
    UserStats,
)
from src.theater.service import TheaterService
from src.members.service import MemberService

logger = create_logger("users_service", __name__)


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        security_service: SecurityService,
        email_service: EmailService,
        config: Settings,
        theater_service: TheaterService,
        member_service: MemberService,
    ):
        self.repository = repository
        self.security_service = security_service
        self.email_service = email_service
        self.config = config
        self.theater_service = theater_service
        self.member_service = member_service

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

    async def create_user(self, request: UserCreateRequest) -> UserCreated:
        """
        Create a new user from registration request.
        Sensitive fields are set explicitly by this service, not from user input.
        """
        try:
            hashed_password = await asyncio.to_thread(
                self.security_service.get_password_hash, request.password
            )

            user_in_db = UserInDB(
                name=request.fullName,
                memberId=request.memberId,
                username=request.username.lower(),
                email=request.email.lower(),
                ofcStatus=request.ofcStatus,
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

    async def update_oshi(self, user_id: str, oshi_id: int) -> "MessageResponse":
        """Update the user's Oshi ID"""
        try:
            await self.repository.set_oshi_id(user_id, oshi_id)
            return MessageResponse(detail=Info.OSHI_UPDATED)
        except Exception as e:
            logger.exception(f"Error updating oshi: {str(e)}")
            raise OshiUpdateError()

    async def update_public_status(self, user_id: str, is_public: bool, public_year: int | None = None) -> "MessageResponse":
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

    async def update_profile_picture(self, user_id: str, profile_picture: str) -> MessageResponse:
        """Update the user's profile picture"""
        try:
            # Validate the image before saving
            validate_base64_image(profile_picture)
            
            await self.repository.set_profile_picture(user_id, profile_picture)
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
                member_detail = await self.member_service.get_member_by_id(user.oshiId)
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

        # Handle "This Year" option (-1) by converting to current year
        query_year = user.publicYear
        display_year = user.publicYear

        if user.publicYear == -1:
            query_year = datetime.now().year
            display_year = query_year  # Show the actual year in the UI

        try:
            # Respect user's public year setting if set
            tickets = await self.theater_service.get_my_tickets(user.userId, query_year)
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
            publicYear=display_year,  # Show actual year for "This Year" option
            stats=stats
        )

    @staticmethod
    def _calculate_rank(total_shows: int) -> RankInfo:
        """Calculate rank/level based on total shows (XP)."""
        xp = total_shows
        current_rank = RankConfig.MILESTONES[0]
        next_rank = RankConfig.MILESTONES[1] if len(RankConfig.MILESTONES) > 1 else {"xp": 1000, "title": "Beyond Legend"}

        for i, milestone in enumerate(RankConfig.MILESTONES):
            if xp >= milestone["xp"]:
                current_rank = milestone
                next_rank = RankConfig.MILESTONES[i + 1] if i + 1 < len(RankConfig.MILESTONES) else {"xp": 1000, "title": "Beyond Legend"}

        return RankInfo(
            current=current_rank["title"],
            xp=xp,
            nextLevelXp=next_rank["xp"],
            nextRankTitle=next_rank["title"]
        )

    @staticmethod
    def _calculate_achievements(tickets: list) -> int:
        """Calculate total unlocked achievements from tickets."""
        if not tickets:
            return 0

        total_shows = len(tickets)

        # Date calculations
        sorted_dates = sorted([t.event.date for t in tickets])
        first_date = sorted_dates[0] if sorted_dates else None
        last_date = sorted_dates[-1] if sorted_dates else None

        time_span_days = 0
        if first_date and last_date:
            try:
                first_dt = datetime.strptime(str(first_date), "%Y-%m-%d") if isinstance(first_date, str) else first_date
                last_dt = datetime.strptime(str(last_date), "%Y-%m-%d") if isinstance(last_date, str) else last_date
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
        has_row_a = any(t.seat and t.seat.section and t.seat.section.upper().startswith("A") for t in tickets)
        has_row_j = any(t.seat and t.seat.section and t.seat.section.upper().startswith("J") for t in tickets)

        collected_rows = set()
        for t in tickets:
            if t.seat and t.seat.section:
                row = t.seat.section.strip().upper()[0] if t.seat.section.strip() else ""
                if row:
                    collected_rows.add(row)
        target_rows = {"A", "B", "C", "D", "E", "F", "G", "H", "I", "J"}
        unique_rows_count = len(collected_rows.intersection(target_rows))

        # Spending
        total_spent = sum(t.price for t in tickets if t.price)

        # Count unlocked achievements (same as frontend achievements.ts)
        unlocked = 0

        # Attendance milestones
        if total_shows >= 1:
            unlocked += 1  # First Step
        if total_shows >= 10:
            unlocked += 1  # Regular Visitor
        if total_shows >= 50:
            unlocked += 1  # Dedicated Fan
        if total_shows >= 100:
            unlocked += 1  # Century Club
        if total_shows >= 150:
            unlocked += 1  # Theater Icon
        if total_shows >= 200:
            unlocked += 1  # Legendary Wota
        if total_shows >= 300:
            unlocked += 1  # Theater Kami
        if total_shows >= 500:
            unlocked += 1  # Absolute Legend

        # Same show milestones
        if max_same_show >= 10:
            unlocked += 1  # Super Fan
        if max_same_show >= 20:
            unlocked += 1  # Mega Fan
        if max_same_show >= 30:
            unlocked += 1  # Ultra Fan

        # Anniversary milestones
        if time_span_days >= 365:
            unlocked += 1  # Theater Enthusiast
        if time_span_days >= 730:
            unlocked += 1  # Theater Veteran
        if time_span_days >= 1095:
            unlocked += 1  # Theater Legend

        # Row milestones
        if has_row_a:
            unlocked += 1  # Elite Seat
        if has_row_j:
            unlocked += 1  # Back Row Warrior
        if unique_rows_count >= 10:
            unlocked += 1  # Seat Explorer

        # Spending milestone
        if total_spent >= 5000000:
            unlocked += 1  # Top Supporter

        return unlocked

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
                    member_detail = await self.member_service.get_member_by_id(current_user.oshiId)
                    member = member_detail.member
                    oshi_name = member.name
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

            # Get tickets for stats calculation
            tickets = await self.theater_service.get_my_tickets(current_user.userId, None)

            # Calculate rank
            total_shows = len(tickets)
            rank = self._calculate_rank(total_shows)

            # Calculate achievements
            total_achievements = self._calculate_achievements(tickets)

            # Calculate oshi 2-shot counts
            roulette_count = 0
            birthday_count = 0
            if oshi_name:
                for t in tickets:
                    if t.two_shot and t.two_shot.member_name == oshi_name:
                        if t.two_shot.type == "Roulette":
                            roulette_count += 1
                        elif t.two_shot.type == "Birthday":
                            birthday_count += 1

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
                        twoShotMember=t.two_shot.member_name if t.two_shot else None
                    )
                )

            # Build profile dict from current_user
            profile_dict = {
                "userId": current_user.userId,
                "profilePicture": current_user.profilePicture,
                "name": current_user.name,
                "email": current_user.email,
                "username": current_user.username,
                "memberId": current_user.memberId,
                "oshiId": current_user.oshiId,
                "ofcStatus": current_user.ofcStatus,
                "isPublic": current_user.isPublic,
                "publicYear": current_user.publicYear,
            }

            return ProfileFullResponse(
                profile=profile_dict,
                oshi=oshi_response,
                rank=rank,
                stats=ProfileStats(
                    totalShows=total_shows,
                    totalAchievements=total_achievements
                ),
                oshiTwoShots=OshiTwoShotCounts(
                    roulette=roulette_count,
                    birthday=birthday_count
                ),
                recentActivity=recent_activity
            )

        except Exception as e:
            logger.exception(f"Error fetching profile stats: {str(e)}")
            raise ProfileStatsFetchError()
