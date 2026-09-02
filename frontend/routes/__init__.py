"""
Маршруты веб-приложения
"""

from routes.api_routes import api_bp
from routes.group_routes import group_bp

__all__ = [
    'main_bp',
    'api_bp',
    'group_bp'
]