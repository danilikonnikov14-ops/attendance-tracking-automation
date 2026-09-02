"""
API для дашборда админ-панели
"""

from flask import Blueprint, jsonify
from app.models.database import get_db_connection
from app.models.group import get_all_groups
from app.models.student import get_students_by_group
from app.models.attendance import get_attendance_stats
from app.services.face_recognition import recognition_model
from app.utils.logger import get_logger
from datetime import datetime, timedelta
from app.config import config

logger = get_logger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Получение общей статистики для дашборда"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) as total FROM groups")
        total_groups = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) as total FROM students")
        total_students = cur.fetchone()['total']

        cur.execute("""
            SELECT COUNT(DISTINCT (group_name, date, pair_number)) as total
            FROM attendance
        """)
        total_pairs = cur.fetchone()['total'] or 0

        cur.execute("SELECT COUNT(*) as total FROM attendance WHERE status = 'present'")
        total_present = cur.fetchone()['total'] or 0

        if total_students > 0 and total_pairs > 0:
            overall_attendance = round((total_present / (total_students * total_pairs)) * 100, 1)
        else:
            overall_attendance = 0

        cur.close()
        conn.close()

        return jsonify({
            'total_groups': total_groups,
            'total_students': total_students,
            'total_pairs': total_pairs,
            'total_present': total_present,
            'overall_attendance': overall_attendance
        })
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/dashboard/charts', methods=['GET'])
def get_chart_data():
    """Получение данных для графиков"""
    try:
        groups = get_all_groups()
        if not groups:
            return jsonify({
                'bar': {'labels': [], 'data': []},
                'line': {'labels': [], 'data': []},
                'pie': {'labels': [], 'data': []}
            })

        bar_labels = []
        bar_data = []
        for group in groups:
            students = get_students_by_group(group)
            if not students:
                continue
            total_percent = 0
            count = 0
            for s in students:
                stats = get_attendance_stats(group, s['student_name'])
                if stats and len(stats) > 0:
                    stat = stats[0]
                    total_pairs = stat['total_pairs'] or 0
                    present = stat['present_count'] or 0
                    if total_pairs > 0:
                        percent = (present / total_pairs) * 100
                        total_percent += percent
                        count += 1
            if count > 0:
                avg_percent = round(total_percent / count, 1)
                bar_labels.append(group)
                bar_data.append(avg_percent)

        line_labels = []
        line_data = []
        today = datetime.now().date()
        start_date = today - timedelta(days=29)
        conn = get_db_connection()
        cur = conn.cursor()
        for i in range(30):
            day = start_date + timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')
            cur.execute("""
                SELECT DISTINCT group_name FROM attendance WHERE date = %s
            """, (date_str,))
            groups_with_att = [row['group_name'] for row in cur.fetchall()]
            if not groups_with_att:
                line_labels.append(day.strftime('%d.%m'))
                line_data.append(0)
                continue
            total_day_percent = 0
            count_groups = 0
            for g in groups_with_att:
                students = get_students_by_group(g)
                if not students:
                    continue
                cur.execute("""
                    SELECT student_name, status FROM attendance
                    WHERE group_name = %s AND date = %s
                """, (g, date_str))
                records = cur.fetchall()
                if not records:
                    continue
                student_status = {}
                for r in records:
                    student_status[r['student_name']] = r['status']
                present_count = sum(1 for st in students if student_status.get(st['student_name']) == 'present')
                if len(students) > 0:
                    percent = (present_count / len(students)) * 100
                    total_day_percent += percent
                    count_groups += 1
            if count_groups > 0:
                avg_day_percent = round(total_day_percent / count_groups, 1)
            else:
                avg_day_percent = 0
            line_labels.append(day.strftime('%d.%m'))
            line_data.append(avg_day_percent)

        cur.close()
        conn.close()

        pie_labels = []
        pie_data = []
        for group in groups:
            students = get_students_by_group(group)
            if students:
                pie_labels.append(group)
                pie_data.append(len(students))

        return jsonify({
            'bar': {'labels': bar_labels, 'data': bar_data},
            'line': {'labels': line_labels, 'data': line_data},
            'pie': {'labels': pie_labels, 'data': pie_data}
        })
    except Exception as e:
        logger.error(f"Ошибка получения данных для графиков: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/dashboard/system_status', methods=['GET'])
def system_status():
    """Статус системы: БД, API, модель"""
    try:
        db_ok = False
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            db_ok = cur.fetchone() is not None
            cur.close()
            conn.close()
        except:
            db_ok = False

        model_ok = recognition_model is not None

        return jsonify({
            'database': db_ok,
            'api': True,  
            'model': model_ok,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/schedule_interval', methods=['GET'])
def get_schedule_interval():
    """Получение интервала обновления расписания"""
    return jsonify({
        'interval': config.SCHEDULE_UPDATE_INTERVAL
    })

@dashboard_bp.route('/system_status', methods=['GET'])
def system_status_short():
    """Дублирующий маршрут без /dashboard/"""
    return system_status()

@dashboard_bp.route('/dashboard/student_ratings', methods=['GET'])
def get_student_ratings():
    """Получение топ-3 студентов с лучшей и худшей посещаемостью"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                student_name,
                COUNT(*) as total_pairs,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count,
                ROUND(100.0 * SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) / COUNT(*), 1) as percent
            FROM attendance
            GROUP BY student_name
            HAVING COUNT(*) >= 3
            ORDER BY percent DESC
        """)
        
        all_students = cur.fetchall()
        cur.close()
        conn.close()
        
        best = all_students[:3] if all_students else []
        worst = all_students[-3:] if len(all_students) >= 3 else []
        
        return jsonify({
            'best': [
                {
                    'name': s['student_name'],
                    'percent': s['percent'],
                    'total_pairs': s['total_pairs'],
                    'present_count': s['present_count']
                }
                for s in best
            ],
            'worst': [
                {
                    'name': s['student_name'],
                    'percent': s['percent'],
                    'total_pairs': s['total_pairs'],
                    'present_count': s['present_count']
                }
                for s in worst
            ]
        })
    except Exception as e:
        logger.error(f"Ошибка получения рейтинга студентов: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/dashboard/day_time_stats', methods=['GET'])
def get_day_time_stats():
    """Получение статистики по дням недели и парам"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                EXTRACT(DOW FROM date::date) as day_of_week,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present
            FROM attendance
            WHERE date ~ '^\d{4}-\d{2}-\d{2}$'
            GROUP BY day_of_week
            ORDER BY day_of_week
        """)
        
        day_names = {
            0: 'Вс', 1: 'Пн', 2: 'Вт', 3: 'Ср', 
            4: 'Чт', 5: 'Пт', 6: 'Сб'
        }
        
        day_stats = []
        for row in cur.fetchall():
            total = row['total']
            present = row['present']
            percent = round((present / total * 100), 1) if total > 0 else 0
            day_stats.append({
                'day': day_names.get(row['day_of_week'], '—'),
                'percent': percent,
                'total': total,
                'present': present
            })
        
        cur.execute("""
            SELECT 
                pair_number,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present
            FROM attendance
            WHERE pair_number IN ('1', '2', '3', '4', '5', '6')
            GROUP BY pair_number
            ORDER BY pair_number::int
        """)
        
        pair_stats = []
        for row in cur.fetchall():
            total = row['total']
            present = row['present']
            percent = round((present / total * 100), 1) if total > 0 else 0
            pair_stats.append({
                'pair': row['pair_number'],
                'percent': percent,
                'total': total,
                'present': present
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'days': day_stats,
            'pairs': pair_stats
        })
    except Exception as e:
        logger.error(f"Ошибка получения статистики по дням/парам: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/last_update', methods=['GET'])
def get_last_update():
    """Получение времени последнего обновления расписания"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(updated_at) as last_update 
            FROM schedule_cache
        """)
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            'last_update': result['last_update'].isoformat() if result and result['last_update'] else None
        })
    except Exception as e:
        logger.error(f"Ошибка получения времени обновления: {e}")
        return jsonify({'last_update': None}), 500

@dashboard_bp.route('/force_update', methods=['POST'])
def force_update_schedule():
    """Принудительное обновление расписания"""
    try:
        from app.services.schedule_updater import force_update
        from app.models.group import get_all_groups
        groups = get_all_groups()
        if not groups:
            return jsonify({'success': False, 'error': 'Нет групп для обновления'}), 400
        total = force_update()
        return jsonify({'success': True, 'saved': total})
    except Exception as e:
        logger.error(f"Ошибка принудительного обновления: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/dashboard/last_update', methods=['GET'])
def get_last_update_with_dashboard():
    """Дублирующий маршрут с /dashboard/ для совместимости"""
    return get_last_update()