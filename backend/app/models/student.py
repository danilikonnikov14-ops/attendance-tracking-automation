"""
Модель студента
"""

from app.models.database import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)

def add_student(student_name, group_name):
    """Добавление студента"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO students (student_name, group_name)
            VALUES (%s, %s)
            RETURNING id, student_name, group_name
        """, (student_name, group_name))
        
        student = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Добавлен студент: {student_name} ({group_name})")
        return student
        
    except Exception as e:
        logger.error(f"Ошибка добавления студента: {e}")
        raise

def get_students_by_group(group_name):
    """Получение студентов группы"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, student_name, group_name, created_at
            FROM students
            WHERE group_name = %s
            ORDER BY student_name
        """, (group_name,))
        
        students = cur.fetchall()
        cur.close()
        conn.close()
        
        return students
        
    except Exception as e:
        logger.error(f"Ошибка получения студентов: {e}")
        return []

def get_student_by_name(student_name, group_name):
    """Получение студента по имени и группе"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, student_name, group_name
            FROM students
            WHERE student_name = %s AND group_name = %s
        """, (student_name, group_name))
        
        student = cur.fetchone()
        cur.close()
        conn.close()
        
        return student
        
    except Exception as e:
        logger.error(f"Ошибка получения студента: {e}")
        return None

def delete_student(student_name, group_name):
    """Удаление студента"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM students
            WHERE student_name = %s AND group_name = %s
            RETURNING id
        """, (student_name, group_name))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Ошибка удаления студента: {e}")
        return False

def delete_students_by_group(group_name):
    """Удаление всех студентов группы"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM students WHERE group_name = %s", (group_name,))
        affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Удалено {affected} студентов из группы {group_name}")
        return affected
        
    except Exception as e:
        logger.error(f"Ошибка удаления студентов: {e}")
        return 0

def get_all_groups():
    """Получение всех групп"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT DISTINCT group_name FROM students ORDER BY group_name")
        groups = [row['group_name'] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return groups
        
    except Exception as e:
        logger.error(f"Ошибка получения групп: {e}")
        return []