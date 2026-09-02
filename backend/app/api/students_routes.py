"""
API эндпоинты для студентов
"""

from flask import Blueprint, request, jsonify
from app.models.student import get_students_by_group, add_student, delete_student
from app.config import config
from app.utils.logger import get_logger
from app.utils.validators import validate_student_name
from app.utils.auth_decorator import jwt_required, admin_required
from app.models.group import group_exists, get_all_groups

logger = get_logger(__name__)
students_bp = Blueprint('students', __name__)


@students_bp.route('/students/<group_name>', methods=['GET'])
@jwt_required
def get_students(group_name):
    """
    Получение списка студентов группы
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        students = get_students_by_group(group_name)
        return jsonify([{'name': s['student_name']} for s in students])
        
    except Exception as e:
        logger.error(f"Ошибка получения студентов: {e}")
        return jsonify({'error': str(e)}), 500


@students_bp.route('/students/<group_name>', methods=['POST'])
@admin_required
def add_student_to_group(group_name):
    """
    Добавление студента в группу
    """
    try:
        data = request.get_json()
        student_name = data.get('student_name')
        
        if not student_name or not validate_student_name(student_name):
            return jsonify({'error': 'Некорректное имя студента'}), 400
        
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        result = add_student(student_name, group_name)
        return jsonify({'success': True, 'student': result})
        
    except Exception as e:
        logger.error(f"Ошибка добавления студента: {e}")
        return jsonify({'error': str(e)}), 500


@students_bp.route('/students/<group_name>/<student_name>', methods=['DELETE'])
@admin_required
def delete_student_from_group(group_name, student_name):
    """
    Удаление студента из группы
    """
    try:
        if not group_exists(group_name):
            return jsonify({'error': f'Группа {group_name} не найдена'}), 404
        
        result = delete_student(student_name, group_name)
        
        if result:
            return jsonify({'success': True, 'message': f'Студент {student_name} удален'})
        else:
            return jsonify({'error': 'Студент не найден'}), 404
            
    except Exception as e:
        logger.error(f"Ошибка удаления студента: {e}")
        return jsonify({'error': str(e)}), 500