"""
API прокси - передача запросов к бэкенду
"""

from flask import Blueprint, request, jsonify, session
from services.api_client import APIClient
from datetime import datetime

api_bp = Blueprint('api', __name__)
api_client = APIClient()


def get_headers():
    """Получение заголовков с токеном"""
    headers = {}
    token = session.get('token')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


@api_bp.route('/attendance_stats/<group_name>/<date>/<pair_number>')
def attendance_stats_proxy(group_name, date, pair_number):
    """Прокси для статистики посещаемости"""
    try:
        formatted_date = date
        if date and date.isdigit() and len(date) >= 10:
            try:
                timestamp_ms = int(date)
                date_obj = datetime.fromtimestamp(timestamp_ms / 1000)
                formatted_date = date_obj.strftime('%Y-%m-%d')
            except:
                pass
        
        data = api_client.get_attendance_stats(group_name, formatted_date, pair_number)
        
        if data and data.get('total', 0) > 0:
            return jsonify({
                'has_data': True,
                'total': data.get('total', 0),
                'present': data.get('present', 0),
                'absent': data.get('absent', 0),
                'presentList': data.get('presentList', []),
                'absentList': data.get('absentList', [])
            })
        
        return jsonify({'has_data': False, 'total': 0, 'present': 0, 'absent': 0})
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'has_data': False, 'total': 0, 'present': 0, 'absent': 0})


@api_bp.route('/attendance_trend/<group_name>')
def attendance_trend_proxy(group_name):
    """Прокси для динамики посещаемости"""
    period = request.args.get('period', 'week')
    year = request.args.get('year', '')
    month = request.args.get('month', '')
    semester = request.args.get('semester', '')
    
    try:
        data = api_client.get_attendance_trend(group_name, period, year, month, semester)
        return jsonify(data)
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'dates': [], 'rates': []}), 500


@api_bp.route('/student_stats/<group_name>')
def student_stats_proxy(group_name):
    """Прокси для статистики студентов"""
    try:
        data = api_client.get_student_stats(group_name)
        return jsonify(data)
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify([]), 500


@api_bp.route('/day_attendance/<group_name>/<date>')
def day_attendance_proxy(group_name, date):
    """Прокси для посещаемости за день"""
    try:
        data = api_client.get_day_attendance(group_name, date)
        return jsonify(data)
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500