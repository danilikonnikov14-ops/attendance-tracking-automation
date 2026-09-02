"""
API эндпоинты для статистики
"""

from flask import Blueprint, request, jsonify
from app.models.student import get_students_by_group
from app.models.attendance import get_attendance_stats, get_attendance_by_date
from app.config import config
from app.utils.logger import get_logger
from app.utils.auth_decorator import jwt_required
from app.models.group import group_exists, get_all_groups
from datetime import datetime, timedelta
from app.models.database import get_db_connection

logger = get_logger(__name__)
stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/attendance_trend/<group_name>', methods=['GET'])
@jwt_required
def get_attendance_trend(group_name):
    """
    Получение динамики посещаемости по дням
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        period = request.args.get('period', 'week')
        year = request.args.get('year', None)
        month = request.args.get('month', None)
        semester = request.args.get('semester', None)
        
        # Получение всех студентов группы
        students = get_students_by_group(group_name)
        total_students = len(students)
        
        logger.info(f"Группа {group_name}: {total_students} студентов")
        
        if total_students == 0:
            return jsonify({'dates': [], 'rates': []})
        
        today = datetime.now().date()
        dates_list = []
        
        if period == 'week':
            day_count = 0
            current = today
            while day_count < 7:
                if current.weekday() != 6:  # не воскресенье
                    dates_list.insert(0, current.strftime('%Y-%m-%d'))
                    day_count += 1
                current -= timedelta(days=1)
        
        elif period == 'month':
            try:
                y = int(year) if year and year not in ('null', 'undefined', '') else today.year
                m = int(month) if month and month not in ('null', 'undefined', '') else today.month
            except:
                y, m = today.year, today.month
            
            first_day = datetime(y, m, 1).date()
            if m == 12:
                last_day = datetime(y+1, 1, 1).date() - timedelta(days=1)
            else:
                last_day = datetime(y, m+1, 1).date() - timedelta(days=1)
            
            current_date = first_day
            while current_date <= last_day:
                if current_date.weekday() != 6:
                    dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
        
        elif period == 'semester':
            try:
                y = int(year) if year and year not in ('null', 'undefined', '') else today.year
                s = int(semester) if semester and semester not in ('null', 'undefined', '') else 1
            except:
                y, s = today.year, 1
            
            if s == 1:  
                first_day = datetime(y, 9, 1).date()
                last_day = datetime(y, 12, 31).date()
            else:  # Весенний семестр (январь-июнь)
                first_day = datetime(y, 1, 1).date()
                last_day = datetime(y, 6, 30).date()
            
            current_date = first_day
            while current_date <= last_day:
                if current_date.weekday() != 6:
                    dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
        
        else:
            return jsonify({'error': 'Неизвестный период'}), 400
        
        if not dates_list:
            return jsonify({'dates': [], 'rates': []})
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        attendance_by_day = {}
        
        for date_str in dates_list:
            
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT student_name) as present_count
                FROM attendance
                WHERE group_name = %s 
                    AND date = %s 
                    AND status = 'present'
            """, (group_name, date_str))
            
            result = cur.fetchone()
            present_count = result['present_count'] if result else 0
            
            rate = round((present_count / total_students) * 100, 1) if total_students > 0 else 0
            attendance_by_day[date_str] = rate
        
        cur.close()
        conn.close()
        
        dates = []
        rates = []
        for date_str in dates_list:
            rates.append(attendance_by_day.get(date_str, 0))
            try:
                d = datetime.strptime(date_str, '%Y-%m-%d')
                dates.append(d.strftime('%d.%m'))
            except:
                dates.append(date_str)
        
        logger.info(f"Тренд для {group_name}: {len(dates)} дней")
        
        return jsonify({
            'dates': dates,
            'rates': rates,
            'period': period
        })
        
    except Exception as e:
        logger.error(f"Ошибка в attendance_trend: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/student_stats/<group_name>', methods=['GET'])
@jwt_required
def get_student_stats(group_name):
    """
    Получение статистики по каждому студенту группы
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        stats = get_attendance_stats(group_name)
        
        students = get_students_by_group(group_name)
        all_students = {s['student_name']: {'total_pairs': 0, 'present_count': 0} for s in students}
        
        for stat in stats:
            if stat['student_name'] in all_students:
                all_students[stat['student_name']]['total_pairs'] = stat['total_pairs'] or 0
                all_students[stat['student_name']]['present_count'] = stat['present_count'] or 0
        
        result = []
        for name, data in all_students.items():
            total = data['total_pairs']
            present = data['present_count']
            absent = total - present
            percent = round((present / total * 100), 1) if total > 0 else 0
            
            result.append({
                'name': name,
                'total_pairs': total,
                'absent': absent,
                'percent': percent
            })
        
        result.sort(key=lambda x: x['percent'], reverse=True)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики студентов: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/day_attendance/<group_name>/<date>', methods=['GET'])
@jwt_required
def get_day_attendance(group_name, date):
    """
    Получение статистики посещаемости за день по всем парам
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        students = get_students_by_group(group_name)
        total_students = len(students)
        
        records = get_attendance_by_date(group_name, date)
        
        pairs = {}
        for record in records:
            pair_num = record['pair_number']
            if pair_num not in pairs:
                pairs[pair_num] = {'present': 0, 'total': 0}
            pairs[pair_num]['total'] += 1
            if record['status'] == 'present':
                pairs[pair_num]['present'] += 1
        
        pair_stats = []
        for pair_num in sorted(pairs.keys()):
            pair_data = pairs[pair_num]
            present = pair_data['present']
            percent = round((present / total_students * 100), 1) if total_students > 0 else 0
            pair_stats.append({
                'pair_number': pair_num,
                'present_count': present,
                'total': total_students,
                'percent': percent
            })
        
        if pair_stats:
            avg_percent = sum(p['percent'] for p in pair_stats) / len(pair_stats)
        else:
            avg_percent = 0
        
        return jsonify({
            'date': date,
            'total_students': total_students,
            'pairs': pair_stats,
            'day_percent': round(avg_percent, 1)
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики за день: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/group_stats/<group_name>', methods=['GET'])
@jwt_required
def get_group_stats(group_name):
    """
    Общая статистика по группе
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        students = get_students_by_group(group_name)
        total_students = len(students)
        
        stats = get_attendance_stats(group_name)
        
        total_pairs = 0
        total_present = 0
        
        for stat in stats:
            total_pairs += stat['total_pairs'] or 0
            total_present += stat['present_count'] or 0
        
        total_absent = total_pairs - total_present
        overall_percent = round((total_present / total_pairs * 100), 1) if total_pairs > 0 else 0
        
        return jsonify({
            'group_name': group_name,
            'students_count': total_students,
            'total_pairs': total_pairs,
            'total_present': total_present,
            'total_absent': total_absent,
            'overall_percent': overall_percent
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики группы: {e}")
        return jsonify({'error': str(e)}), 500