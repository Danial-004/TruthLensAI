# backend/database.py
import os
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime # ✅ Импортируем datetime для message_timestamp
from dotenv import load_dotenv

import psycopg2
import psycopg2.extras
import bcrypt  # безопасное хеширование

load_dotenv()
logger = logging.getLogger(__name__)

class Database:
    """
    Класс для управления подключением к PostgreSQL и выполнения операций.
    """

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL не найден в .env! Убедитесь, что он задан.")
        # Fix for SQLAlchemy/psycopg2 which might expect postgresql://
        if self.db_url.startswith("postgres://"):
            self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)

    def _get_connection(self):
        """Создает и возвращает новое соединение."""
        try:
            # Увеличим таймаут на всякий случай
            return psycopg2.connect(self.db_url, connect_timeout=15)
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise RuntimeError("Соединение с базой данных недоступно.") from e

    # -----------------------------------------------------------------------
    # ИНИЦИАЛИЗАЦИЯ ТАБЛИЦ
    # -----------------------------------------------------------------------
    def initialize(self):
        """Создает таблицы и индексы, если они не существуют."""
        commands = (
            # --- Существующие таблицы ---
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                requests_today INTEGER DEFAULT 0,
                last_request_date DATE DEFAULT CURRENT_DATE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                verdict TEXT NOT NULL,
                confidence REAL NOT NULL,
                full_response JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS user_votes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                analysis_id INTEGER NOT NULL,
                vote INTEGER NOT NULL, -- 1 = согласен, -1 = не согласен
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE,
                UNIQUE (user_id, analysis_id)
            );
            """,
            # --- Новая таблица для мониторинга ---
            """
            CREATE TABLE IF NOT EXISTS telegram_monitored_messages (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                user_id BIGINT, -- Может быть null в каналах
                message_text TEXT,
                media_type TEXT, -- 'text', 'photo'
                url_found TEXT, -- Ссылка, если найдена
                caption TEXT, -- Подпись к фото
                message_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                analysis_id INTEGER, -- Ссылка на результат анализа (если был)
                status TEXT DEFAULT 'pending', -- 'pending', 'analyzed', 'ignored_no_keyword', 'ignored_no_url', 'ignored_duplicate_url', 'error_api', 'error_worker'
                FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE SET NULL,
                UNIQUE (chat_id, message_id) -- Гарантируем уникальность сообщений
            );
            """,
             # --- Индексы ---
            """
            CREATE INDEX IF NOT EXISTS idx_telegram_chat_message ON telegram_monitored_messages (chat_id, message_id);
            """,
            # ✅✅✅ ДОБАВЛЕН ИНДЕКС ДЛЯ ПРОВЕРКИ URL ✅✅✅
            """
            CREATE INDEX IF NOT EXISTS idx_telegram_url_analyzed ON telegram_monitored_messages (url_found) WHERE status = 'analyzed';
            """
            # ✅✅✅ КОНЕЦ ДОБАВЛЕНИЯ ИНДЕКСА ✅✅✅
        )
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for command in commands:
                        cur.execute(command)
                conn.commit()
                logger.info("✅ Таблицы и индексы (включая 'idx_telegram_url_analyzed') проверены/созданы.")
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации БД: {e}", exc_info=True)
            raise

    # -----------------------------------------------------------------------
    # ПОЛЬЗОВАТЕЛИ
    # -----------------------------------------------------------------------
    def create_user(self, email: str, password_hash: str) -> Optional[int]:
        """Создает нового пользователя. Принимает УЖЕ хэшированный пароль."""
        try:
            with self._get_connection() as conn:
                # ТҮЗЕТУ: Біз мұнда қайта хэштемейміз! 
                # password_hash - бұл app.py-дан келген дайын хэш.
                sql = "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id;"
                with conn.cursor() as cur:
                    cur.execute(sql, (email, password_hash))
                    user_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"✅ Пользователь {email} создан с ID {user_id}.")
                return user_id
        except psycopg2.IntegrityError:
            logger.info(f"⚠️ Пользователь с email {email} уже существует.")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при создании пользователя {email}: {e}", exc_info=True)
            return None

    def verify_user(self, email: str, password: str) -> Optional[Dict]:
        """Проверяет логин/пароль."""
        try:
            with self._get_connection() as conn:
                sql = "SELECT id, email, password_hash FROM users WHERE email = %s;"
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, (email,))
                    row = cur.fetchone()
                    if row:
                        stored_hash = row["password_hash"].encode('utf-8')
                        # Используем bcrypt для проверки
                        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                            logger.info(f"✅ Пользователь {email} успешно верифицирован.")
                            return {"id": row["id"], "email": row["email"]}
                        else:
                            logger.warning(f"⚠️ Неверный пароль для пользователя {email}.")
                    else:
                        logger.warning(f"⚠️ Попытка входа для несуществующего email: {email}.")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка проверки пользователя {email}: {e}", exc_info=True)
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Возвращает пользователя по email."""
        try:
            with self._get_connection() as conn:
                # FIX: Alias password_hash as hashed_password
                sql = "SELECT id, email, password_hash AS hashed_password FROM users WHERE email = %s;"
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, (email,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Ошибка get_user_by_email для {email}: {e}", exc_info=True)
            return None

    def get_user_status(self, user_id: int) -> Optional[Dict]:
        """Возвращает email и текущее количество запросов пользователя."""
        sql = """
            WITH updated AS (
                UPDATE users
                SET requests_today = 0, last_request_date = CURRENT_DATE
                WHERE id = %s AND last_request_date < CURRENT_DATE
                RETURNING id
            )
            SELECT email, requests_today FROM users WHERE id = %s;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, (user_id, user_id))
                    row = cur.fetchone()
                conn.commit() # Сохраняем сброс счетчика, если он произошел
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Ошибка get_user_status для user_id {user_id}: {e}", exc_info=True)
            return None

    # -----------------------------------------------------------------------
    # АНАЛИЗЫ
    # -----------------------------------------------------------------------
    def save_analysis(self, user_id: int, text: str, verdict: str, confidence: float, full_response: dict) -> Optional[int]:
        """Сохраняет результат анализа и возвращает его ID."""
        sql = "INSERT INTO analyses (user_id, text, verdict, confidence, full_response) VALUES (%s, %s, %s, %s, %s) RETURNING id;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Преобразуем dict в JSON строку для JSONB
                    cur.execute(sql, (user_id, text, verdict, confidence, json.dumps(full_response)))
                    analysis_id = cur.fetchone()[0]
                conn.commit()
            logger.info(f"✅ Анализ {analysis_id} для пользователя {user_id} сохранен.")
            return analysis_id
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения анализа для user_id {user_id}: {e}", exc_info=True)
            return None

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Возвращает историю анализов."""
        sql = "SELECT id, text, verdict, confidence, created_at, full_response FROM analyses WHERE user_id = %s ORDER BY created_at DESC LIMIT %s;"
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, (user_id, limit))
                    # Преобразуем строки в словари
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории для user_id {user_id}: {e}", exc_info=True)
            return []

    # -----------------------------------------------------------------------
    # ГОЛОСОВАНИЯ
    # -----------------------------------------------------------------------
    def save_vote(self, user_id: int, analysis_id: int, vote: int) -> bool:
        """Сохраняет или обновляет голос пользователя за анализ."""
        # ON CONFLICT обновляет голос, если пользователь уже голосовал за этот анализ
        sql = "INSERT INTO user_votes (user_id, analysis_id, vote) VALUES (%s, %s, %s) ON CONFLICT (user_id, analysis_id) DO UPDATE SET vote = EXCLUDED.vote;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (user_id, analysis_id, vote))
                conn.commit()
            logger.info(f"✅ Голос ({vote}) от пользователя {user_id} за анализ {analysis_id} сохранён.")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения голоса ({user_id}/{analysis_id}/{vote}): {e}", exc_info=True)
            return False

    # -----------------------------------------------------------------------
    # ОГРАНИЧЕНИЕ ЗАПРОСОВ (RATE LIMITING)
    # -----------------------------------------------------------------------
    def check_and_update_rate_limit(self, user_id: int, limit: int = 30) -> bool:
        """
        Атомарно проверяет и обновляет лимит запросов для пользователя.
        Возвращает True, если запрос разрешен, иначе False.
        """
        sql = """
            UPDATE users
            SET
                requests_today = CASE
                    WHEN last_request_date < CURRENT_DATE THEN 1
                    ELSE requests_today + 1
                END,
                last_request_date = CURRENT_DATE
            WHERE id = %s
            RETURNING requests_today;
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (user_id,))
                    result = cur.fetchone()
                    conn.commit() # Сохраняем изменения (счетчик запросов)

                    if not result:
                        logger.warning(f"Попытка проверить лимит для несуществующего user_id: {user_id}")
                        return False

                    new_requests_count = result[0]

                    if new_requests_count > limit:
                        logger.warning(f"Превышен лимит ({limit}) для user_id {user_id}. Текущий счет: {new_requests_count}.")
                        return False

            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке лимита запросов для user_id {user_id}: {e}", exc_info=True)
            return False

    # -----------------------------------------------------------------------
    # TELEGRAM МОНИТОРИНГ
    # -----------------------------------------------------------------------

    # ✅✅✅ НОВАЯ ФУНКЦИЯ ДЛЯ СОХРАНЕНИЯ СООБЩЕНИЯ ИЗ TELEGRAM ✅✅✅
    def save_telegram_message(
        self, chat_id: int, message_id: int, user_id: Optional[int],
        message_text: Optional[str], media_type: str, url_found: Optional[str],
        caption: Optional[str], message_timestamp: datetime
    ) -> Optional[int]:
        """Сохраняет информацию об исходном сообщении Telegram."""
        sql = """
            INSERT INTO telegram_monitored_messages
            (chat_id, message_id, user_id, message_text, media_type, url_found, caption, message_timestamp, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chat_id, message_id) DO NOTHING -- Не перезаписывать, если уже есть
            RETURNING id;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        chat_id, message_id, user_id, message_text, media_type,
                        url_found, caption, message_timestamp, 'pending' # Начальный статус
                    ))
                    result = cur.fetchone()
                    conn.commit()
                    if result:
                        logger.debug(f"Сообщение {message_id} из чата {chat_id} сохранено с ID {result[0]}.")
                        return result[0]
                    else:
                        logger.debug(f"Сообщение {message_id} из чата {chat_id} уже существует.")
                        return None # Сообщение уже было
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сообщения Telegram ({chat_id}/{message_id}): {e}", exc_info=True)
            return None

    # ✅✅✅ НОВАЯ ФУНКЦИЯ ДЛЯ ОБНОВЛЕНИЯ СТАТУСА СООБЩЕНИЯ ✅✅✅
    def update_telegram_message_status(self, message_db_id: int, status: str, analysis_id: Optional[int] = None):
        """Обновляет статус обработанного сообщения и ID анализа."""
        # Допустимые статусы: 'pending', 'analyzed', 'ignored_no_keyword', 'ignored_no_url', 'ignored_duplicate_url', 'error_api', 'error_worker'
        sql = """
            UPDATE telegram_monitored_messages
            SET status = %s, analysis_id = %s, processed_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (status, analysis_id, message_db_id))
                conn.commit()
            logger.debug(f"Статус сообщения {message_db_id} обновлен на '{status}'.")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статуса сообщения {message_db_id} на '{status}': {e}", exc_info=True)


    # ✅✅✅ НОВАЯ ФУНКЦИЯ ДЛЯ ПРОВЕРКИ URL ✅✅✅
    def check_if_url_analyzed(self, url: str) -> bool:
        """Проверяет, был ли этот URL уже успешно проанализирован."""
        # Ищем запись с таким URL и статусом 'analyzed', используя индекс
        sql = """
            SELECT EXISTS (
                SELECT 1
                FROM telegram_monitored_messages
                WHERE url_found = %s AND status = 'analyzed'
            );
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (url,))
                    exists = cur.fetchone()[0]
                    if exists:
                         logger.debug(f"URL {url} уже был проанализирован ранее.")
                    return exists # Вернет True, если найдена хотя бы одна запись
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке URL {url} в БД: {e}", exc_info=True)
            return False # В случае ошибки считаем, что URL не был проанализирован (лучше перепроверить)
    # ✅✅✅ КОНЕЦ НОВОЙ ФУНКЦИИ ✅✅✅