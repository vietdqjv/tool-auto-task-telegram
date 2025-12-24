# src/bot/middlewares/__init__.py
"""Middleware exports."""
import importlib

from .auth import AuthMiddleware

# Import kebab-case file using importlib
_rate_limit = importlib.import_module(".rate-limit", package=__name__)
RateLimitMiddleware = _rate_limit.RateLimitMiddleware

__all__ = ["AuthMiddleware", "RateLimitMiddleware"]
