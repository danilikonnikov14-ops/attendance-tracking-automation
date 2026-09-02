"""
Валидаторы данных
"""

import re
from datetime import datetime

def validate_group_name(group_name):
    """Валидация названия группы"""
    if not group_name or not isinstance(group_name, str):
        return False
    return len(group_name) > 0

def validate_date(date_str):
    """Валидация даты"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except:
        return False

def validate_pair_number(pair_number):
    """Валидация номера пары"""
    try:
        num = int(pair_number)
        return num > 0
    except:
        return False

def validate_student_name(name):
    """Валидация имени студента"""
    if not name or not isinstance(name, str):
        return False
    return len(name.strip()) > 0

def validate_password(password):
    """Валидация пароля"""
    if not password or len(password) < 4:
        return False
    return True

def sanitize_string(text):
    """Очистка строки от опасных символов"""
    if not text:
        return ''
    return re.sub(r'[;\'"]', '', text)