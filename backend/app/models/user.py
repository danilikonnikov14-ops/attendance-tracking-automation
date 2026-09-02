"""
Модель пользовател
"""

from app.models.database import get_db_connection
from app.services.auth import hash_password, verify_password
from app.utils.logger import get_logger

logger = get_logger(__name__)

def create_user(username, password, group_name, full_name, role='teacher'):
    """Создание нового пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    password_hash = hash_password(password)
    
    cur.execute("""
        INSERT INTO users (username, password_hash, group_name, full_name, role)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, username, group_name, full_name, role
    """, (username, password_hash, group_name, full_name, role))
    
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return user

def get_user_by_username(username):
    """Получение пользователя по имени"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, username, password_hash, group_name, full_name, role, created_at
        FROM users WHERE username = %s
    """, (username,))
    
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    return user

def authenticate_user(username, password):
    """Аутентификация пользователя"""
    user = get_user_by_username(username)
    if not user:
        return None
    
    if verify_password(password, user['password_hash']):
        return user
    
    return None

def update_user(username, **kwargs):
    """Обновление данных пользователя"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key == 'password':
                updates.append("password_hash = %s")
                values.append(hash_password(value))
            elif key in ['group_name', 'full_name']:
                updates.append(f"{key} = %s")
                values.append(value)
        
        if not updates:
            return None
        
        values.append(username)
        query = f"UPDATE users SET {', '.join(updates)} WHERE username = %s RETURNING id, username, group_name, full_name"
        
        cur.execute(query, values)
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return user
        
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя: {e}")
        return None

def delete_user(username):
    """Удаление пользователя"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM users WHERE username = %s RETURNING id", (username,))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя: {e}")
        return False