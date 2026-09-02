"""
Фоновое обновление расписания
"""

import time
import threading
from app.config import config
from app.services.schedule_parser import update_all_schedules
from app.utils.logger import get_logger
from app.models.group import get_all_groups

logger = get_logger(__name__)

_running = True


def schedule_updater():
    """Фоновый поток для периодического обновления расписания"""
    global _running
    
    logger.info(f"Фоновый поток обновления расписания запущен (интервал: {config.SCHEDULE_UPDATE_INTERVAL}с)")
    
    while _running:
        try:
            time.sleep(config.SCHEDULE_UPDATE_INTERVAL)
            if _running:
                logger.info("Плановое обновление расписания")
                update_all_schedules(get_all_groups())
                logger.info("Плановое обновление завершено")
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
            break
        except Exception as e:
            logger.error(f"Ошибка в фоновом обновлении: {e}")
    
    logger.info("Фоновый поток обновления остановлен")


def start_updater_thread():
    """Запуск фонового потока"""
    thread = threading.Thread(target=schedule_updater, daemon=True)
    thread.start()
    return thread


def stop_updater():
    """Остановка фонового потока"""
    global _running
    _running = False
    logger.info("Отправлен сигнал остановки обновления")


def run_initial_update():
    """Первичное обновление расписания при запуске"""
    try:
        logger.info("Первичное обновление расписания...")
        total = update_all_schedules(get_all_groups())
        logger.info(f"Первичное обновление завершено. Сохранено {total} пар")
        return total
    except Exception as e:
        logger.error(f"Ошибка при первичном обновлении: {e}")
        return 0


def force_update():
    """Принудительное обновление расписания"""
    logger.info("Принудительное обновление расписания...")
    return update_all_schedules(get_all_groups())