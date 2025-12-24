# src/core/exceptions.py
"""Custom exceptions for the application."""


class BotError(Exception):
    """Base exception for bot errors."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class TaskNotFoundError(BotError):
    """Raised when task is not found."""

    def __init__(self, task_id: int):
        super().__init__(f"Task {task_id} not found")
        self.task_id = task_id


class UserNotFoundError(BotError):
    """Raised when user is not found."""

    def __init__(self, user_id: int):
        super().__init__(f"User {user_id} not found")
        self.user_id = user_id


class UnauthorizedError(BotError):
    """Raised when user is not authorized."""

    def __init__(self, user_id: int, action: str = "perform this action"):
        super().__init__(f"User {user_id} not authorized to {action}")
        self.user_id = user_id


class RateLimitError(BotError):
    """Raised when rate limit exceeded."""

    def __init__(self, user_id: int, retry_after: int = 60):
        super().__init__(f"Rate limit exceeded, retry after {retry_after}s")
        self.user_id = user_id
        self.retry_after = retry_after


class ExternalAPIError(BotError):
    """Raised when external API call fails."""

    def __init__(self, service: str, status_code: int | None = None):
        msg = f"External API error from {service}"
        if status_code:
            msg += f" (status: {status_code})"
        super().__init__(msg)
        self.service = service
        self.status_code = status_code


class ValidationError(BotError):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str):
        super().__init__(f"Invalid {field}: {reason}")
        self.field = field
        self.reason = reason
