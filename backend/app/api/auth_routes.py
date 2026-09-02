"""
API эндпоинты для аутентификации
"""

from flask import Blueprint, request, jsonify
from app.models.user import authenticate_user
from app.utils.logger import get_logger
from app.config import config
import jwt
import datetime

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)

SECRET_KEY = config.SECRET_KEY


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Вход в систему — возвращает JWT токен
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Логин и пароль обязательны'
            }), 400

        user = authenticate_user(username, password)

        if user:
            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'role': user.get('role', 'teacher'),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, SECRET_KEY, algorithm='HS256')

            logger.info(f"Успешный вход: {username}")
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'groupName': user['group_name'],
                    'fullName': user['full_name'],
                    'role': user.get('role', 'teacher')
                }
            })

        logger.warning(f"Неудачная попытка входа: {username}")
        return jsonify({
            'success': False,
            'message': 'Неверный логин или пароль'
        }), 401

    except Exception as e:
        logger.error(f"Ошибка при входе: {e}")
        return jsonify({
            'success': False,
            'message': 'Внутренняя ошибка сервера'
        }), 500