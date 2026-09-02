"""
Модель посещаемости
"""

from app.models.database import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)

def save_attendance_record(group_name, student_name, date, pair_number, status):
    """Сохранение записи посещаемости"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO attendance (group_name, student_name, date, pair_number, status)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (group_name, student_name, date, pair_number)
            DO UPDATE SET status = EXCLUDED.status, recognized_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (group_name, student_name, date, pair_number, status))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Ошибка сохранения посещаемости: {e}")
        return False

def save_attendance_records(group_name, date, pair_number, records):
    """Сохранение нескольких записей посещаемости"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM attendance
            WHERE group_name = %s AND date = %s AND pair_number = %s
        """, (group_name, date, pair_number))
        
        for record in records:
            cur.execute("""
                INSERT INTO attendance (group_name, student_name, date, pair_number, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (group_name, record['student_name'], date, pair_number, record['status']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Сохранено {len(records)} записей посещаемости")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка сохранения посещаемости: {e}")
        return False

def get_attendance_by_date(group_name, date, pair_number=None):
    """Получение посещаемости по дате"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if pair_number:
            cur.execute("""
                SELECT student_name, status, recognized_at
                FROM attendance
                WHERE group_name = %s AND date = %s AND pair_number = %s
            """, (group_name, date, pair_number))
        else:
            cur.execute("""
                SELECT student_name, pair_number, status, recognized_at
                FROM attendance
                WHERE group_name = %s AND date = %s
                ORDER BY pair_number, student_name
            """, (group_name, date))
        
        records = cur.fetchall()
        cur.close()
        conn.close()
        
        return records
        
    except Exception as e:
        logger.error(f"Ошибка получения посещаемости: {e}")
        return []

def get_attendance_by_student(group_name, student_name):
    """Получение посещаемости студента"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT date, pair_number, status, recognized_at
            FROM attendance
            WHERE group_name = %s AND student_name = %s
            ORDER BY date, pair_number
        """, (group_name, student_name))
        
        records = cur.fetchall()
        cur.close()
        conn.close()
        
        return records
        
    except Exception as e:
        logger.error(f"Ошибка получения посещаемости студента: {e}")
        return []

def get_attendance_stats(group_name, student_name=None):
    """Получение статистики посещаемости"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if student_name:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_pairs,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count
                FROM attendance
                WHERE group_name = %s AND student_name = %s
            """, (group_name, student_name))
        else:
            cur.execute("""
                SELECT 
                    student_name,
                    COUNT(*) as total_pairs,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count
                FROM attendance
                WHERE group_name = %s
                GROUP BY student_name
                ORDER BY student_name
            """, (group_name,))
        
        stats = cur.fetchall()
        cur.close()
        conn.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return []

def delete_attendance_records(group_name, date=None, pair_number=None):
    """Удаление записей посещаемости"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if date and pair_number:
            cur.execute("""
                DELETE FROM attendance
                WHERE group_name = %s AND date = %s AND pair_number = %s
            """, (group_name, date, pair_number))
        elif date:
            cur.execute("""
                DELETE FROM attendance
                WHERE group_name = %s AND date = %s
            """, (group_name, date))
        else:
            cur.execute("DELETE FROM attendance WHERE group_name = %s", (group_name,))
        
        affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Удалено {affected} записей посещаемости")
        return affected
        
    except Exception as e:
        logger.error(f"Ошибка удаления посещаемости: {e}")
        return 0