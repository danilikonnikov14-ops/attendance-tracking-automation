"""
Маршруты для групп и расписания
"""

from flask import Blueprint, render_template
from config.config import config
from services.api_client import APIClient
from services.schedule_service import ScheduleService

group_bp = Blueprint('group', __name__)
api_client = APIClient()
schedule_service = ScheduleService(api_client)


@group_bp.route('/<group_name>.html')
def group_schedule(group_name):
    """Расписание группы"""
    if group_name not in config.GROUPS:
        return render_template('404.html'), 404
    
    schedule = schedule_service.get_schedule(group_name)
    return render_template('group.html', group_name=group_name, schedule=schedule)


@group_bp.route('/lesson/<group_name>/<date>/<pair_number>')
def lesson_details(group_name, date, pair_number):
    """Детали пары с посещаемостью"""
    if group_name not in config.GROUPS:
        return render_template('404.html'), 404
    
    schedule = schedule_service.get_schedule(group_name)
    
    lesson = None
    day_name = ""
    
    for day in schedule:
        for cls in day.get('classes', []):
            if cls.get('number') == pair_number:
                lesson = cls
                day_name = day.get('name', '')
                break
        if lesson:
            break
    
    if not lesson:
        return render_template('404.html'), 404
    
    stats_data = api_client.get_attendance_stats(group_name, date, pair_number) or {}
    
    lesson_data = {
        'subject': lesson.get('subject', '—'),
        'group_name': group_name,
        'pair_number': pair_number,
        'time': lesson.get('time', ''),
        'date': date,
        'day_name': day_name,
        'room': lesson.get('room', '—'),
        'teacher': lesson.get('teacher', '—')
    }
    
    return render_template('lesson_details.html',
        lesson=lesson_data,
        present_list=stats_data.get('presentList', []),
        absent_list=stats_data.get('absentList', []),
        stats={
            'total': stats_data.get('total', 0),
            'present': stats_data.get('present', 0),
            'absent': stats_data.get('absent', 0)
        }
    )