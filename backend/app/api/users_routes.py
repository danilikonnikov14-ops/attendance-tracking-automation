"""
API эндпоинты для управления пользователями (только для админов)
"""

from flask import Blueprint, request, jsonify
from app.models.user import get_user_by_username, create_user, delete_user, update_user
from app.models.group import group_exists
from app.utils.logger import get_logger
from app.utils.auth_decorator import admin_required
from app.models.database import get_db_connection

logger = get_logger(__name__)
users_bp = Blueprint('users', __name__)


@users_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """Получение списка всех пользователей"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, full_name, group_name, role, created_at
            FROM users
            ORDER BY id
        """)
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        logger.error(f"Ошибка получения пользователей: {e}")
        return jsonify({'error': str(e)}), 500


@users_bp.route('/users', methods=['POST'])
@admin_required
def create_new_user():
    """Создание нового пользователя"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        group_name = data.get('group_name', '').strip() or None
        role = data.get('role', 'teacher')

        if not username or not password:
            return jsonify({'error': 'Логин и пароль обязательны'}), 400
        if len(password) < 4:
            return jsonify({'error': 'Пароль должен быть не менее 4 символов'}), 400

        if get_user_by_username(username):
            return jsonify({'error': f'Пользователь {username} уже существует'}), 409

        if group_name and not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404

        user = create_user(username, password, group_name, full_name, role)
        if user:
            return jsonify({'success': True, 'user': user})
        else:
            return jsonify({'error': 'Ошибка создания пользователя'}), 500
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")
        return jsonify({'error': str(e)}), 500


@users_bp.route('/users/<username>', methods=['DELETE'])
@admin_required
def remove_user(username):
    """Удаление пользователя"""
    try:
        if username == 'admin':
            return jsonify({'error': 'Нельзя удалить администратора'}), 403
        if delete_user(username):
            return jsonify({'success': True, 'message': f'Пользователь {username} удалён'})
        else:
            return jsonify({'error': 'Пользователь не найден'}), 404
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя: {e}")
        return jsonify({'error': str(e)}), 500