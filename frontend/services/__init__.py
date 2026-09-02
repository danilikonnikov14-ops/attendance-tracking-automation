"""
Сервисы веб-приложения
"""

from services.api_client import APIClient
from services.schedule_service import ScheduleService

__all__ = [
    'APIClient',
    'ScheduleService'
]