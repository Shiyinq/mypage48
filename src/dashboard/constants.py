class DashboardConstants:
    """Constants used in Dashboard Service."""

    # Days of the week for day preference statistics
    DAYS = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    # Theater rows for seat statistics
    THEATER_ROWS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]


class Info:
    """Informational messages."""

    STATS_FETCHED = "Dashboard statistics fetched successfully."


class ErrorCode:
    """Error codes for HTTP exceptions."""

    STATS_FETCH_ERROR = "Failed to fetch dashboard statistics."


class DomainErrorCode:
    """Error codes for Domain exceptions."""

    STATS_FETCH_FAILED = "Failed to fetch dashboard statistics."
