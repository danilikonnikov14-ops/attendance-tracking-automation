"""
Утилиты для хеширования (без циклических импортов)
"""

import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """
    Хеширование пароля с солью
    Формат: salt$hash
    """
    salt = os.urandom(32).hex()
    return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"


def verify_password(password: str, hashed: str) -> bool:
    """Проверка пароля (поддерживает старый формат без соли)"""
    try:
        salt, hash_ = hashed.split('$')
        computed = hashlib.sha256((salt + password).encode()).hexdigest()
        return hmac.compare_digest(computed, hash_)
    except ValueError:
        return hashlib.sha256(password.encode()).hexdigest() == hashed