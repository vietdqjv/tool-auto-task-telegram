# src/bot/middlewares/__init__.py
"""Middleware exports."""
import importlib

from .auth import AuthMiddleware

# Import kebab-case files using importlib
_rate_limit = importlib.import_module(".rate-limit", package=__name__)
RateLimitMiddleware = _rate_limit.RateLimitMiddleware

_group_rate_limit = importlib.import_module(".group-rate-limit", package=__name__)
GroupRateLimitMiddleware = _group_rate_limit.GroupRateLimitMiddleware

__all__ = ["AuthMiddleware", "RateLimitMiddleware", "GroupRateLimitMiddleware"]
