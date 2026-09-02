"""
Модели данных
"""

from app.models.database import get_db_connection, init_database
from app.models.user import (
    create_user,
    get_user_by_username,
    authenticate_user,
    update_user,
    delete_user
)
from app.models.student import (
    add_student,
    get_students_by_group,
    get_student_by_name,
    delete_student,
    delete_students_by_group,
    get_all_groups
)
from app.models.attendance import (
    save_attendance_record,
    save_attendance_records,
    get_attendance_by_date,
    get_attendance_by_student,
    get_attendance_stats,
    delete_attendance_records
)
from app.models.schedule import (
    save_schedule,
    get_schedule,
    get_schedule_for_date,
    get_schedule_for_today,
    get_schedule_for_week,
    clear_schedule,
    get_all_groups_with_schedule,
    get_schedule_stats
)

__all__ = [
    'get_db_connection',
    'init_database',
    'create_user',
    'get_user_by_username',
    'authenticate_user',
    'update_user',
    'delete_user',
    'add_student',
    'get_students_by_group',
    'get_student_by_name',
    'delete_student',
    'delete_students_by_group',
    'get_all_groups',
    'save_attendance_record',
    'save_attendance_records',
    'get_attendance_by_date',
    'get_attendance_by_student',
    'get_attendance_stats',
    'delete_attendance_records',
    'save_schedule',
    'get_schedule',
    'get_schedule_for_date',
    'get_schedule_for_today',
    'get_schedule_for_week',
    'clear_schedule',
    'get_all_groups_with_schedule',
    'get_schedule_stats'
]