"""
Модель расписания 
"""

from app.models.database import get_db_connection
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

def save_schedule(group_name, days):
    """Сохранение расписания"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM schedule_cache WHERE group_name = %s", (group_name,))
        
        inserted = 0
        for day in days:
            day_name = day.get('name', '')
            day_date = day.get('date', '')
            for cls in day.get('classes', []):
                time_str = cls.get('time', '')
                start_time = ''
                end_time = ''
                if '-' in time_str:
                    parts = time_str.split('-')
                    start_time = parts[0].strip() if len(parts) > 0 else ''
                    end_time = parts[1].strip() if len(parts) > 1 else ''
                
                cur.execute("""
                    INSERT INTO schedule_cache (
                        group_name, day_name, day_date, pair_number, 
                        subject, teacher, room, time, start_time, end_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    group_name, day_name, day_date, cls.get('number', ''),
                    cls.get('subject', ''), cls.get('teacher', '—'),
                    cls.get('room', '—'), time_str, start_time, end_time
                ))
                inserted += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Сохранено {inserted} пар для группы {group_name}")
        return inserted
        
    except Exception as e:
        logger.error(f"Ошибка сохранения расписания: {e}")
        return 0

def get_schedule(group_name):
    """Получение расписания группы"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT day_name, day_date, pair_number, subject, teacher, room, time, start_time, end_time
            FROM schedule_cache
            WHERE group_name = %s
            ORDER BY day_date, pair_number
        """, (group_name,))
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        days = {}
        for row in rows:
            day_key = row['day_date'] or row['day_name']
            if day_key not in days:
                days[day_key] = {
                    'name': row['day_name'],
                    'date': row['day_date'] or '',
                    'classes': []
                }
            days[day_key]['classes'].append({
                'number': row['pair_number'],
                'time': row['time'] or '',
                'subject': row['subject'] or '',
                'teacher': row['teacher'] or '—',
                'room': row['room'] or '—'
            })
        
        return list(days.values())
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения расписания: {e}")
        return []

def get_schedule_for_date(group_name, date):
    """Получение расписания на конкретную дату"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT day_name, day_date, pair_number, subject, teacher, room, time, start_time, end_time
            FROM schedule_cache
            WHERE group_name = %s AND day_date = %s
            ORDER BY pair_number
        """, (group_name, date))
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        logger.error(f"Ошибка получения расписания на дату: {e}")
        return []

def get_schedule_for_today(group_name):
    """Получение расписания на сегодня"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        return get_schedule_for_date(group_name, today)
        
    except Exception as e:
        logger.error(f"Ошибка получения расписания на сегодня: {e}")
        return []

def get_schedule_for_week(group_name):
    """Получение расписания на неделю"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT day_date
            FROM schedule_cache
            WHERE group_name = %s AND day_date != ''
            ORDER BY day_date
        """, (group_name,))
        
        dates = [row['day_date'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        schedule = {}
        for date in dates:
            schedule[date] = get_schedule_for_date(group_name, date)
        
        return schedule
        
    except Exception as e:
        logger.error(f"Ошибка получения расписания на неделю: {e}")
        return {}

def clear_schedule(group_name=None):
    """Очистка кэша расписания"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if group_name:
            cur.execute("DELETE FROM schedule_cache WHERE group_name = %s", (group_name,))
        else:
            cur.execute("DELETE FROM schedule_cache")
        
        affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Очищено {affected} записей расписания")
        return affected
        
    except Exception as e:
        logger.error(f"Ошибка очистки расписания: {e}")
        return 0

def get_all_groups_with_schedule():
    """Получение всех групп, у которых есть расписание"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT DISTINCT group_name FROM schedule_cache ORDER BY group_name")
        groups = [row['group_name'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return groups
        
    except Exception as e:
        logger.error(f"Ошибка получения групп с расписанием: {e}")
        return []

def get_schedule_stats(group_name):
    """Получение статистики по расписанию"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_pairs,
                COUNT(DISTINCT day_date) as total_days,
                MIN(day_date) as first_date,
                MAX(day_date) as last_date
            FROM schedule_cache
            WHERE group_name = %s AND day_date != ''
        """, (group_name,))
        
        stats = cur.fetchone()
        cur.close()
        conn.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики расписания: {e}")
        return None