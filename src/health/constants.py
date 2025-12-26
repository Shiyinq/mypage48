from enum import Enum


class HealthStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class DatabaseStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNKNOWN = "unknown"
    ERROR = "error"
