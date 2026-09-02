"""
API эндпоинты для расписания
"""

from flask import Blueprint, jsonify
from app.models.schedule import get_schedule, get_schedule_for_today, get_schedule_stats
from app.config import config
from app.utils.logger import get_logger
from app.utils.auth_decorator import jwt_required
from datetime import datetime
from app.models.group import group_exists, get_all_groups

logger = get_logger(__name__)
schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/schedule/<group_name>', methods=['GET'])
@jwt_required
def get_schedule_by_group(group_name):
    """
    Получение расписания группы
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        schedule = get_schedule(group_name)
        
        if not schedule:
            return jsonify({'error': 'Расписание не найдено'}), 404
        
        for day in schedule:
            day_date = day.get('date', '')
            if day_date and day_date.isdigit() and len(day_date) >= 10:
                try:
                    timestamp_ms = int(day_date)
                    date_obj = datetime.fromtimestamp(timestamp_ms / 1000)
                    day['date'] = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
        
        return jsonify(schedule)
        
    except Exception as e:
        logger.error(f"Ошибка получения расписания: {e}")
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/schedule/<group_name>/today', methods=['GET'])
@jwt_required
def get_today_schedule(group_name):
    """
    Получение расписания на сегодня
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        schedule = get_schedule_for_today(group_name)
        return jsonify(schedule)
        
    except Exception as e:
        logger.error(f"Ошибка получения расписания на сегодня: {e}")
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/schedule/<group_name>/stats', methods=['GET'])
@jwt_required
def get_schedule_statistics(group_name):
    """
    Получение статистики расписания
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        stats = get_schedule_stats(group_name)
        return jsonify(stats or {})
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики расписания: {e}")
        return jsonify({'error': str(e)}), 500
