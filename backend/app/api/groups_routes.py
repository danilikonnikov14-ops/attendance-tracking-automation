"""
API эндпоинты для управления группами (только для админов)
"""

from flask import Blueprint, request, jsonify
from app.models.group import get_all_groups, add_group, delete_group, group_exists
from app.utils.logger import get_logger
from app.utils.auth_decorator import admin_required

logger = get_logger(__name__)
groups_bp = Blueprint('groups', __name__)


@groups_bp.route('/groups', methods=['GET'])
def list_groups():
    """Получение списка всех групп"""
    try:
        groups = get_all_groups()
        return jsonify(groups)
    except Exception as e:
        logger.error(f"Ошибка получения групп: {e}")
        return jsonify({'error': str(e)}), 500


@groups_bp.route('/groups', methods=['POST'])
@admin_required
def create_group():
    """Создание новой группы"""
    try:
        data = request.get_json()
        group_name = data.get('name', '').strip()
        if not group_name:
            return jsonify({'error': 'Название группы обязательно'}), 400
        if group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} уже существует'}), 409
        new_group = add_group(group_name)
        if new_group:
            return jsonify({'success': True, 'group': new_group})
        else:
            return jsonify({'error': 'Ошибка добавления группы'}), 500
    except Exception as e:
        logger.error(f"Ошибка создания группы: {e}")
        return jsonify({'error': str(e)}), 500


@groups_bp.route('/groups/<group_name>', methods=['DELETE'])
@admin_required
def remove_group(group_name):
    """Удаление группы (каскадно)"""
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        if delete_group(group_name):
            return jsonify({'success': True, 'message': f'Группа {group_name} удалена'})
        else:
            return jsonify({'error': 'Ошибка удаления группы'}), 500
    except Exception as e:
        logger.error(f"Ошибка удаления группы: {e}")
        return jsonify({'error': str(e)}), 500