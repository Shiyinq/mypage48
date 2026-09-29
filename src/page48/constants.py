class Info:
    POST_CREATED = "Post created successfully."
    POST_UPDATED = "Post updated successfully."
    POST_DELETED = "Post deleted successfully."
    LIKE_TOGGLED = "Like status toggled."
    REPOST_TOGGLED = "Repost status toggled."
    BOOKMARK_TOGGLED = "Bookmark status toggled."

class ErrorCode:
    POST_NOT_FOUND = "Post not found."
    POST_CREATE_ERROR = "Failed to create post."
    UNAUTHORIZED_ACTION = "You are not authorized to perform this action."
    MAX_MEDIA_EXCEEDED = "Maximum number of media allowed per post is 4."
    REPLY_NOT_FOUND = "The post you are trying to reply to does not exist."
    USER_NOT_FOUND = "User not found."

class DomainErrorCode:
    POST_NOT_FOUND = "Post not found."
    POST_CREATION_FAILED = "Failed to create post."
    UNAUTHORIZED = "Unauthorized."
    USER_NOT_FOUND = "User not found."
