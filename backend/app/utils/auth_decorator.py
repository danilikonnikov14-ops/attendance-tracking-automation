"""
Декоратор для проверки JWT токена
"""

import jwt
from functools import wraps
from flask import request, jsonify
from app.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)
SECRET_KEY = config.SECRET_KEY


def jwt_required(f):
    """Декоратор для проверки JWT токена"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.path == '/groups':
            return f(*args, **kwargs)
        
        token = request.headers.get('Authorization')

        if not token:
            logger.warning("Токен не предоставлен")
            return jsonify({'error': 'Токен не предоставлен'}), 401

        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]

            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user = payload
            logger.debug(f"Токен валиден для пользователя: {payload.get('username')}")

        except jwt.ExpiredSignatureError:
            logger.warning("Токен истёк")
            return jsonify({'error': 'Токен истёк'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Недействительный токен: {e}")
            return jsonify({'error': 'Недействительный токен'}), 401
        except Exception as e:
            logger.error(f"Ошибка проверки токена: {e}")
            return jsonify({'error': 'Ошибка аутентификации'}), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Токен не предоставлен'}), 401

        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]

            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            if payload.get('role') != 'admin':
                logger.warning(f"Доступ запрещён для пользователя: {payload.get('username')}")
                return jsonify({'error': 'Недостаточно прав'}), 403

            request.user = payload

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Токен истёк'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Недействительный токен'}), 401

        return f(*args, **kwargs)
    return decorated