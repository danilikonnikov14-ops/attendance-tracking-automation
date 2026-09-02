"""
Конфигурация веб-приложения
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс конфигурации"""
    
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://backend:5000')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 10))
    
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5001))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    GROUPS = ["09.07.14п1", "09.07.14п2", "09.07.14р", "09.07.13п1"]
    
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'False').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', 300))  # 5 минут


config = Config()