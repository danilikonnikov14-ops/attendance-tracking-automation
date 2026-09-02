"""
Инициализация API Blueprints
"""

from app.api.auth_routes import auth_bp
from app.api.schedule_routes import schedule_bp
from app.api.students_routes import students_bp
from app.api.attendance_routes import attendance_bp
from app.api.stats_routes import stats_bp
from app.api.groups_routes import groups_bp
from app.api.dashboard_routes import dashboard_bp
from app.api.users_routes import users_bp

__all__ = [
    'auth_bp',
    'schedule_bp',
    'students_bp',
    'attendance_bp',
    'stats_bp',
    'groups_bp',
    'dashboard_bp',
    'users_bp'
]