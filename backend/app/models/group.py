"""
Модель группы
"""

from app.models.database import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_all_groups():
    """Получение списка всех групп (только имена)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM groups ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [row['name'] for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения групп: {e}")
        return []


def get_all_groups_with_id():
    """Получение списка групп с id и name"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM groups ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Ошибка получения групп: {e}")
        return []


def group_exists(group_name):
    """Проверка существования группы"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM groups WHERE name = %s", (group_name,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"Ошибка проверки группы: {e}")
        return False


def add_group(group_name):
    """Добавление новой группы"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO groups (name) VALUES (%s) RETURNING id, name", (group_name,))
        new_group = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Группа добавлена: {group_name}")
        return new_group
    except Exception as e:
        logger.error(f"Ошибка добавления группы: {e}")
        return None


def delete_group(group_name):
    """Удаление группы и всех связанных данных (каскадно)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE group_name = %s", (group_name,))
        cur.execute("DELETE FROM attendance WHERE group_name = %s", (group_name,))
        cur.execute("DELETE FROM schedule_cache WHERE group_name = %s", (group_name,))
        cur.execute("UPDATE users SET group_name = NULL WHERE group_name = %s", (group_name,))
        cur.execute("DELETE FROM groups WHERE name = %s RETURNING id", (group_name,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if deleted:
            logger.info(f"Группа {group_name} удалена каскадно")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка удаления группы: {e}")
        return False