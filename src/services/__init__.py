# src/services/__init__.py
"""Services module exports."""
import importlib

# Import using importlib for kebab-case files
_task_service = importlib.import_module("src.services.task-service")
_api_client = importlib.import_module("src.services.api-client")
from .notification import NotificationService

TaskService = _task_service.TaskService
APIClient = _api_client.APIClient

__all__ = ["TaskService", "APIClient", "NotificationService"]
