"""
Настройка логирования
"""

import logging
import os
from app.config import config

def setup_logging(app=None):
    """Настройка логирования"""
    
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    if app:
        app.logger.handlers = []
        app.logger.addHandler(logging.FileHandler(config.LOG_FILE, encoding='utf-8'))
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)

def get_logger(name):
    """Получить логгер с именем"""
    return logging.getLogger(name)