"""
Server Face Attendance
Точка входа в приложение
"""

import threading
import logging
import os
from app import create_app
from app.config import config
from app.models.database import init_database
from app.models.group import get_all_groups  
from app.services.face_recognition import load_recognition_model
from app.services.schedule_updater import run_initial_update, start_updater_thread

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Запуск приложения"""
    logger.info("Запуск сервера")
    logger.info(f"Версия: {config.VERSION}")
    
    logger.info("Проверка базы данных...")
    if not init_database():
        logger.error("Критическая ошибка инициализации БД")
        return
    
    groups = get_all_groups()
    if groups:
        logger.info(f"Группы: {', '.join(groups)}")
    else:
        logger.info("Группы: Нет групп в базе данных")
    
    logger.info("Загрузка модели распознавания лиц...")
    load_recognition_model()
    
    logger.info("Обновление расписания...")
    run_initial_update()
    
    logger.info("Запуск фонового обновления расписания...")
    start_updater_thread()
    
    app = create_app()
    logger.info(f"Сервер готов на http://{config.HOST}:{config.PORT}")
    
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        use_reloader=False
    )


if __name__ == '__main__':
    main()