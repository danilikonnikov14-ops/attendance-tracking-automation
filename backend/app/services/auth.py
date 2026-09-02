"""
Сервис аутентификации - хеширование и проверка паролей
"""

import hashlib
import os
import hmac
import time


def hash_password(password: str) -> str:
    """
    Хеширование пароля с использованием SHA-256 + соль
    
    Формат: salt$hash
    """
    salt = os.urandom(32).hex()
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Проверка пароля
    
    Args:
        password: Пароль в открытом виде
        hashed: Хеш в формате salt$hash или старый формат (без соли)
    """
    try:
        salt, password_hash = hashed.split('$')
        computed_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return hmac.compare_digest(computed_hash, password_hash)
    except (ValueError, TypeError):
        return hashlib.sha256(password.encode()).hexdigest() == hashed


def hash_password_legacy(password: str) -> str:
    """Устаревший метод хеширования (без соли)"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(user_id: int, username: str) -> str:
    """Генерация простого токена (для будущего использования)"""
    secret = os.getenv('SECRET_KEY', 'dev-secret-key')
    data = f"{user_id}:{username}:{int(time.time())}"
    token = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    return token