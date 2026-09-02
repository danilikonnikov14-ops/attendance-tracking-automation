"""
Клиент для работы с API бэкенда
"""

import requests
from config.config import config
from datetime import datetime
import time
from flask import session


class APIClient:
    """Клиент для API бэкенда"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.timeout = config.API_TIMEOUT
    
    def _get_headers(self):
        """Получение заголовков с токеном"""
        headers = {}
        from flask import session
        token = session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers
    
    def _get(self, endpoint, params=None):
        """GET запрос к API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                from flask import session
                session.clear()
                return None
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except requests.exceptions.Timeout:
            print(f"Таймаут API: {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Ошибка соединения с API: {endpoint}")
            return None
        except Exception as e:
            print(f"Ошибка API: {e}")
            return None
    
    def get_schedule(self, group_name):
        """Получение расписания группы"""
        return self._get(f"/schedule/{group_name}") or []
    
    def get_attendance_stats(self, group_name, date, pair_number):
        """Получение статистики посещаемости"""
        return self._get(f"/attendance_stats/{group_name}/{date}/{pair_number}")
    
    def get_attendance_trend(self, group_name, period='week', year='', month='', semester=''):
        """Получение динамики посещаемости"""
        params = {'period': period}
        if year: params['year'] = year
        if month: params['month'] = month
        if semester: params['semester'] = semester
        
        return self._get(f"/attendance_trend/{group_name}", params) or {'dates': [], 'rates': []}
    
    def get_student_stats(self, group_name):
        """Получение статистики студентов"""
        return self._get(f"/student_stats/{group_name}") or []
    
    def get_day_attendance(self, group_name, date):
        """Получение посещаемости за день"""
        return self._get(f"/day_attendance/{group_name}/{date}") or {}
    
    def get_groups(self):
        """Получение списка групп"""
        return config.GROUPS
    
    def health_check(self):
        """Проверка доступности API"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False