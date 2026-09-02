"""
Сервисы приложения
"""

from app.services.auth import hash_password, verify_password, generate_token
from app.services.face_recognition import (
    load_recognition_model,
    process_face,
    recognize_face,
    detect_faces,
    get_face_database_stats,
    add_face_to_database,
    remove_face_from_database,
    save_face_database
)
from app.services.schedule_parser import (
    parse_schedule_from_site,
    update_schedule_for_group,
    update_all_schedules
)
from app.services.schedule_updater import (
    schedule_updater,
    start_updater_thread,
    stop_updater,
    run_initial_update,
    force_update
)

__all__ = [
    'hash_password',
    'verify_password',
    'generate_token',
    'load_recognition_model',
    'process_face',
    'recognize_face',
    'detect_faces',
    'get_face_database_stats',
    'add_face_to_database',
    'remove_face_from_database',
    'save_face_database',
    'parse_schedule_from_site',
    'update_schedule_for_group',
    'update_all_schedules',
    'schedule_updater',
    'start_updater_thread',
    'stop_updater',
    'run_initial_update',
    'force_update'
]