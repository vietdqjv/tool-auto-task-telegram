# src/bot/__init__.py
"""Bot module exports."""
from .app import create_bot, create_dispatcher, on_startup, on_shutdown

__all__ = ["create_bot", "create_dispatcher", "on_startup", "on_shutdown"]
