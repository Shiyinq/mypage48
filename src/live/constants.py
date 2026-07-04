class Info:
    LIVE_FETCH_SUCCESS = "Live status fetched successfully."


class ErrorCode:
    FETCH_SHOWROOM_FAILED = "Failed to fetch lives from Showroom."
    FETCH_IDN_FAILED = "Failed to fetch lives from IDN."
    STREAMING_URL_NOT_FOUND = "No streaming URL found for this room."
    PROXY_FAILED = "Live streaming proxy failed."
    COMMENTS_FETCH_FAILED = "Failed to fetch showroom comments."
    GIFTS_FETCH_FAILED = "Failed to fetch showroom gifts."


class DomainErrorCode:
    FETCH_SHOWROOM_ERROR = "Live fetch from Showroom failed."
    FETCH_IDN_ERROR = "Live fetch from IDN failed."
    STREAMING_URL_NOT_FOUND = "Streaming URL not found."
    PROXY_ERROR = "Failed to proxy stream request."
    COMMENTS_FETCH_ERROR = "Failed to fetch showroom comments."
    GIFTS_FETCH_ERROR = "Failed to fetch showroom gifts."
