"""
Подключение к базе данных и инициализация таблиц
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import config
from app.utils.logger import get_logger
from app.utils.hash_utils import hash_password  

logger = get_logger(__name__)


def get_db_connection():
    """Получение подключения к БД"""
    return psycopg2.connect(**config.DB_CONFIG, cursor_factory=RealDictCursor)


def init_database():
    """Создание таблиц, если они не существуют"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                group_name VARCHAR(50),
                full_name VARCHAR(200),
                role VARCHAR(20) DEFAULT 'teacher',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(200) NOT NULL,
                group_name VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_name, group_name)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS schedule_cache (
                id SERIAL PRIMARY KEY,
                group_name VARCHAR(50) NOT NULL,
                day_name VARCHAR(50) NOT NULL,
                day_date VARCHAR(20),
                pair_number VARCHAR(10) NOT NULL,
                subject VARCHAR(500),
                teacher VARCHAR(200),
                room VARCHAR(50),
                time VARCHAR(50),
                start_time VARCHAR(10),
                end_time VARCHAR(10),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_name, day_date, pair_number)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                group_name VARCHAR(50) NOT NULL,
                student_name VARCHAR(200) NOT NULL,
                date VARCHAR(20) NOT NULL,
                pair_number VARCHAR(10) NOT NULL,
                status VARCHAR(20) NOT NULL,
                recognized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_name, student_name, date, pair_number)
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_attendance_group ON attendance(group_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_schedule_group ON schedule_cache(group_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_schedule_date ON schedule_cache(day_date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(name)")

        conn.commit()
        logger.info("Таблицы успешно созданы/проверены")


        if config.GROUPS_RAW:
            for g in config.GROUPS:
                cur.execute("INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (g,))
            conn.commit()
            logger.info(f"Добавлены начальные группы из конфига: {config.GROUPS}")

        cur.execute("SELECT COUNT(*) FROM users WHERE username = %s", ("admin",))
        if cur.fetchone()['count'] == 0:
            password_hash = hash_password("admin123")
            first_group = config.GROUPS[0] if config.GROUPS else ""
            cur.execute("""
                INSERT INTO users (username, password_hash, group_name, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
            """, ("admin", password_hash, first_group, "Администратор", "admin"))
            conn.commit()
            logger.info("Создан тестовый пользователь: admin / admin123")

        cur.execute("SELECT COUNT(*) FROM users WHERE username = %s", ("teacher",))
        if cur.fetchone()['count'] == 0:
            password_hash = hash_password("teacher123")
            first_group = config.GROUPS[0] if config.GROUPS else ""
            cur.execute("""
                INSERT INTO users (username, password_hash, group_name, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
            """, ("teacher", password_hash, first_group, "Преподаватель", "teacher"))
            conn.commit()
            logger.info("Создан тестовый пользователь: teacher / teacher123")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return False