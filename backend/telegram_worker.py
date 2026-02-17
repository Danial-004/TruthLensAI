# telegram_worker.py
import logging
import os
import httpx
import re
import io
import redis # ✅ Добавлен импорт Redis
# ✅ Добавлены timezone, timedelta для лимитов Redis
from typing import List, Optional
from backend.database import Database
# ✅✅✅ ДОБАВЛЕНЫ ИМПОРТЫ ✅✅✅
import psycopg2
import psycopg2.extras
import asyncio # ✅ Добавлен asyncio для sleep
# ✅ Добавлен Optional из typing
from typing import List, Optional
from enum import Enum
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from telegram import Update, InputFile
from telegram.constants import ChatType
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Настройка ---
load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") # Берем из .env или дефолт
TELEGRAM_USER_DAILY_LIMIT = int(os.getenv("TELEGRAM_USER_DAILY_LIMIT", 10)) # Лимит для Telegram юзеров
REDIS_URL = os.getenv("REDIS_URL") # URL для Redis
# ✅ Чтение SILENT_MODE
SILENT_MODE = os.getenv("SILENT_MODE", "False").lower() in ('true', '1', 't')
# ✅ Чтение ADMIN_CHAT_ID (Опционально, для уведомлений)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env!")
    exit()

# --- Подключение к БД и Redis ---
try:
    db = Database()
    logger.info("✅ Worker подключился к базе данных.")
except Exception as e:
    logger.error(f"❌ Worker НЕ СМОГ подключиться к базе данных: {e}", exc_info=True)
    exit()

# --- Настройка Redis ---
redis_client: Optional[redis.Redis] = None
try:
    if REDIS_URL:
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    else:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        redis_db_num = int(os.getenv("REDIS_DB", 0))
        redis_client = redis.Redis(
            host=redis_host, port=redis_port, password=redis_password,
            db=redis_db_num, decode_responses=True
        )
    redis_client.ping()
    logger.info("✅ Worker подключился к Redis.")
except Exception as e:
    logger.error(f"❌ Worker НЕ СМОГ подключиться к Redis: {e}. Лимиты для Telegram работать не будут.")
    redis_client = None
# --- Конец настройки Redis ---

KEYWORDS = [ # Ключевые слова
    'новость', 'новости', 'событие', 'происшествие', 'заявил', 'сообщил',
    'сказал', 'аким', 'президент', 'министр', 'депутат',
    'Астана', 'Алматы', 'Казахстан', 'Правительство', 'МВД', 'КНБ',
    'жаңалық', 'оқиға', 'мәлімдеді', 'хабарлады', 'депутат', 'министр', 'әкім'
]
KEYWORDS_LOWER = [kw.lower() for kw in KEYWORDS]

# --- Вспомогательная функция для лимитов ---
def check_telegram_limit(user_id: int) -> tuple[bool, int, int]:
    """
    Проверяет и инкрементирует лимит запросов для Telegram user_id в Redis.
    Возвращает (разрешено_ли, текущее_количество, лимит).
    """
    if not redis_client:
        return True, 0, TELEGRAM_USER_DAILY_LIMIT # Если Redis не работает, разрешаем

    key = f"tg_limit:{user_id}"
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key) # Увеличиваем счетчик
        pipe.ttl(key) # Проверяем, есть ли у ключа время жизни
        count, ttl = pipe.execute()

        if ttl == -2 or ttl == -1:
             now = datetime.now(timezone.utc)
             end_of_day = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
             seconds_until_eod = int((end_of_day - now).total_seconds())
             if seconds_until_eod > 0:
                 redis_client.expire(key, seconds_until_eod)
             logger.info(f"Установлен TTL для ключа {key} на {seconds_until_eod} секунд.")

        if count > TELEGRAM_USER_DAILY_LIMIT:
            logger.warning(f"Превышен Telegram лимит ({TELEGRAM_USER_DAILY_LIMIT}) для user_id {user_id}. Текущий счет: {count}.")
            return False, count, TELEGRAM_USER_DAILY_LIMIT
        else:
            return True, count, TELEGRAM_USER_DAILY_LIMIT
    except Exception as e:
        logger.error(f"Ошибка Redis при проверке лимита для user_id {user_id}: {e}")
        return True, 0, TELEGRAM_USER_DAILY_LIMIT # В случае ошибки разрешаем

# --- Функции-обработчики ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ✅ Исправлено: user определяется до использования
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет, {user.mention_html()}! 👋 Я бот для проверки новостей."
        rf"\n\nДля проверки отправь мне:"
        rf"\n• <b>Текст</b> с <b>ключевым словом</b> (например, <i>новость, событие, аким, жаңалық</i>)." # Изменено
        rf"\n• <b>Текст</b> с <b>ключевым словом</b> и <b>ссылкой</b> на изображение." # Добавлено пояснение про ссылку
        rf"\n• <b>Фото</b> с <b>ключевым словом</b> в подписи."
        rf"\n\nЯ проанализирую информацию и дам вердикт. Используй команду /limit, чтобы узнать остаток запросов.",
    )


async def limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает пользователю о его текущем лимите запросов."""
    user_id = update.effective_user.id
    if not redis_client:
        await update.message.reply_text("Не могу проверить лимит, сервис временно недоступен.")
        return

    key = f"tg_limit:{user_id}"
    current_count = 0
    try:
        value = redis_client.get(key)
        if value:
            current_count = int(value)
    except Exception as e:
        logger.error(f"Ошибка Redis при получении лимита для user_id {user_id}: {e}")
        await update.message.reply_text("Ошибка при проверке лимита.")
        return

    remaining = TELEGRAM_USER_DAILY_LIMIT - current_count
    await update.message.reply_text(
        f"Использовано запросов сегодня: {current_count}/{TELEGRAM_USER_DAILY_LIMIT}\n"
        f"Осталось: {max(0, remaining)}"
    )

async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, message_link: str, verdict: str, explanation: str):
    """Отправляет уведомление администратору о найденном фейке."""
    if ADMIN_CHAT_ID:
        try:
            admin_chat_id = int(ADMIN_CHAT_ID)
            text = (
                f"🚨 Обнаружен потенциальный фейк!\n\n"
                f"🔗 Сообщение: {message_link}\n"
                f"⚖️ Вердикт: {verdict}\n"
                f"💬 Пояснение: {explanation}"
            )
            await context.bot.send_message(chat_id=admin_chat_id, text=text)
            logger.info(f"Отправлено уведомление администратору в чат {admin_chat_id}")
        except ValueError:
            logger.error(f"Неверный ADMIN_CHAT_ID в .env: {ADMIN_CHAT_ID}. Должно быть число.")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администратору: {e}", exc_info=True)


async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет текстовое сообщение на ключи, вызывает /analyze или /analyze_url."""

    # Игнорируем свои сообщения и сообщения от других ботов
    if update.message and update.message.from_user and update.message.from_user.is_bot: return

    message = update.message
    if not message or not message.text: return # Проверка на None

    message_text = message.text
    chat_id = message.chat_id
    message_id = message.message_id
    user_id = message.from_user.id if message.from_user else 0 # Handle cases where from_user might be None (rare)
    message_timestamp = message.date.replace(tzinfo=timezone.utc) if message.date else datetime.now(timezone.utc) # Handle None date

    logger.debug(f"Получено сообщение {message_id} из чата {chat_id} от user {user_id}")

    # --- Проверка лимита ---
    allowed, count, limit = check_telegram_limit(user_id)
    if not allowed:
        if not SILENT_MODE and message.chat.type == ChatType.PRIVATE:
             await message.reply_text(f"❌ Вы превысили дневной лимит ({limit}) запросов. Попробуйте завтра.")
        return
    # --- Конец проверки лимита ---

    message_db_id = db.save_telegram_message(
        chat_id=chat_id, message_id=message_id, user_id=user_id,
        message_text=message_text, media_type='text', url_found=None,
        caption=None, message_timestamp=message_timestamp
    )
    if message_db_id is None: return

    message_text_lower = message_text.lower()
    has_keyword = any(keyword in message_text_lower for keyword in KEYWORDS_LOWER)
    if not has_keyword:
        db.update_telegram_message_status(message_db_id, status='ignored_no_keyword')
        return

    # --- ✅✅✅ ИЗМЕНЕННАЯ ЛОГИКА: URL ИЛИ ТОЛЬКО ТЕКСТ ✅✅✅ ---
    url_match = re.search(r'https?://[^\s]+', message_text)
    endpoint = ""
    payload = {}
    action_description = "" # Для сообщения пользователю

    if url_match:
        # --- Если НАЙДЕНА ссылка ---
        url_to_check = url_match.group(0)
        action_description = "ссылку"

        # Проверяем дубликат URL
        if db.check_if_url_analyzed(url_to_check):
            db.update_telegram_message_status(message_db_id, status='ignored_duplicate_url')
            logger.info(f"Сообщение [{chat_id}/{message_id}] проигнорировано: URL {url_to_check} уже анализировался.")
            # if not SILENT_MODE and message.chat.type == ChatType.PRIVATE:
            #    await message.reply_text("ℹ️ Эта ссылка уже была проверена ранее.")
            return

        # Обновляем URL в БД
        try:
             with db._get_connection() as conn:
                 with conn.cursor() as cur:
                     cur.execute("UPDATE telegram_monitored_messages SET url_found = %s WHERE id = %s", (url_to_check, message_db_id))
                 conn.commit()
        except Exception as e_upd:
             logger.error(f"Ошибка обновления URL для сообщения {message_db_id}: {e_upd}")

        logger.info(f"Найдено сообщение [{chat_id}/{message_id}] с ключом и УНИКАЛЬНОЙ ссылкой: {url_to_check}. Вызов /analyze_url.")
        endpoint = "/analyze_url"
        payload = {"url": url_to_check, "text": message_text[:1000]} # Используем /analyze_url

    else:
        # --- Если ссылка НЕ НАЙДЕНА ---
        db.update_telegram_message_status(message_db_id, status='pending_text_only')
        logger.info(f"Найдено сообщение [{chat_id}/{message_id}] с ключом, но БЕЗ ссылки. Вызов /analyze.")
        action_description = "текст"
        endpoint = "/analyze"
        payload = {"text": message_text} # Используем /analyze
    # --- ✅✅✅ КОНЕЦ ИЗМЕНЕННОЙ ЛОГИКИ ✅✅✅ ---


    thinking_message = None
    if not SILENT_MODE and message.chat.type == ChatType.PRIVATE:
         thinking_message = await message.reply_text(f"✅ Нашел ключевое слово и {action_description}! Начинаю проверку...")

    api_analysis_id = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}{endpoint}", # ✅ Используем endpoint
                json=payload,              # ✅ Используем payload
                timeout=60.0,
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Получен результат от API ({endpoint}) для [{chat_id}/{message_id}]: {result.get('verdict')}")

            api_analysis_id = result.get('analysis_id')
            db.update_telegram_message_status(message_db_id, status='analyzed', analysis_id=api_analysis_id)

            # --- Отправка результата в чат ---
            if not SILENT_MODE:
                verdict = result.get("verdict", "Неизвестно")
                confidence_pct = (result.get("confidence") or 0) * 100
                explanation = result.get("detailed_explanation") or result.get("explanation") or "Нет объяснения."

                icon = "❓"; is_fake = False
                if isinstance(verdict, str):
                    v_lower = verdict.lower()
                    if "подлинное" in v_lower or "real" in v_lower: icon = "✅"
                    elif "фейк" in v_lower or "fake" in v_lower: icon = "❌"; is_fake = True
                    elif "манипуляц" in v_lower: icon = "⚠️"; is_fake = True
                    elif "спорн" in v_lower or "controversial" in v_lower: icon = "🤔"

                reply_text = f"{icon} <b>Вердикт:</b> {verdict} (Уверенность: {confidence_pct:.0f}%)\n\n" \
                             f"<i>Объяснение:</i> {explanation}"

                # Добавляем источники и предложения от /analyze
                sources = result.get("sources")
                suggestions = result.get("search_suggestions")
                if sources:
                    reply_text += "\n\n<b>Источники:</b>"
                    for src in sources[:3]: # Показываем не больше 3
                        title = src.get('title', 'Без названия')
                        url = src.get('url')
                        if url and title:
                           reply_text += f"\n• <a href='{url}'>{title}</a>"
                if suggestions:
                    reply_text += "\n\n<b>Попробуйте поискать:</b> " + ", ".join(f"<i>{s}</i>" for s in suggestions[:3])

                await message.reply_html(reply_text, disable_web_page_preview=True)
                if thinking_message: await thinking_message.delete()

                # Уведомление администратору
                if is_fake and message.link:
                     await send_admin_notification(context, message.link, verdict, explanation)


    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка API (HTTP {e.response.status_code}) для [{chat_id}/{message_id}]: {e.request.url} - {e.response.text}")
        db.update_telegram_message_status(message_db_id, status='error_api')
        if not SILENT_MODE:
            if message.chat.type == ChatType.PRIVATE:
                await message.reply_text(f"❌ Ошибка при проверке: API вернул {e.response.status_code}")
            if thinking_message: await thinking_message.delete()
    except Exception as e:
        logger.error(f"Неизвестная ошибка при обработке сообщения [{chat_id}/{message_id}]: {e}", exc_info=True)
        db.update_telegram_message_status(message_db_id, status='error_worker')
        if not SILENT_MODE:
            if message.chat.type == ChatType.PRIVATE:
                await message.reply_text("❌ Внутренняя ошибка worker'а при проверке.")
            if thinking_message: await thinking_message.delete()


async def check_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет фото на ключи в подписи и вызывает /analyze_image."""

    if update.message and update.message.from_user and update.message.from_user.is_bot: return
    if not update.message or not update.message.photo: return

    message = update.message
    chat_id = message.chat_id
    message_id = message.message_id
    user_id = message.from_user.id if message.from_user else 0
    message_timestamp = message.date.replace(tzinfo=timezone.utc) if message.date else datetime.now(timezone.utc)
    caption = message.caption or ""

    logger.debug(f"Получено фото {message_id} из чата {chat_id} от user {user_id}")

    # --- Проверка лимита ---
    allowed, count, limit = check_telegram_limit(user_id)
    if not allowed:
        if not SILENT_MODE and message.chat.type == ChatType.PRIVATE:
             await message.reply_text(f"❌ Вы превысили дневной лимит ({limit}) запросов. Попробуйте завтра.")
        return
    # --- Конец проверки лимита ---

    message_db_id = db.save_telegram_message(
        chat_id=chat_id, message_id=message_id, user_id=user_id,
        message_text=None, media_type='photo', url_found=None,
        caption=caption, message_timestamp=message_timestamp
    )
    if message_db_id is None: return

    caption_lower = caption.lower()
    if not caption or not any(keyword in caption_lower for keyword in KEYWORDS_LOWER):
        db.update_telegram_message_status(message_db_id, status='ignored_no_keyword')
        return

    logger.info(f"Найдено фото [{chat_id}/{message_id}] с ключевым словом в подписи. Начинаю анализ.")

    thinking_message = None
    if not SILENT_MODE and message.chat.type == ChatType.PRIVATE:
        thinking_message = await message.reply_text("✅ Нашел фото с ключевым словом! Начинаю анализ...")

    photo_file_id = message.photo[-1].file_id
    api_analysis_id = None

    try:
        photo_file = await context.bot.get_file(photo_file_id)
        photo_bytes = await photo_file.download_as_bytearray()

        photo_input_file = io.BytesIO(photo_bytes)
        files_data = {'file': ('image.jpg', photo_input_file, 'image/jpeg')}
        form_data = {'text': caption} # Используем подпись

        logger.info(f"Отправка запроса на /analyze_image для [{chat_id}/{message_id}]")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/analyze_image",
                files=files_data,
                data=form_data,
                timeout=60.0
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Получен результат от API (Image) для [{chat_id}/{message_id}]: {result.get('verdict')}")

            api_analysis_id = result.get('analysis_id')
            db.update_telegram_message_status(message_db_id, status='analyzed', analysis_id=api_analysis_id)

            # --- Отправка результата в чат ---
            if not SILENT_MODE:
                verdict = result.get("verdict", "Неизвестно")
                confidence_pct = (result.get("confidence") or 0) * 100
                explanation = result.get("explanation") or "Нет объяснения."

                icon = "❓"; is_fake = False
                if isinstance(verdict, str):
                    v_lower = verdict.lower()
                    if "подлинное" in v_lower or "real" in v_lower: icon = "✅"
                    elif "фейк" in v_lower or "fake" in v_lower: icon = "❌"; is_fake = True
                    elif "манипуляц" in v_lower: icon = "⚠️"; is_fake = True
                    elif "спорн" in v_lower or "controversial" in v_lower: icon = "🤔"

                reply_text = f"{icon} <b>Вердикт по фото:</b> {verdict} (Уверенность: {confidence_pct:.0f}%)\n\n" \
                             f"<i>Объяснение:</i> {explanation}"

                await message.reply_html(reply_text)
                if thinking_message: await thinking_message.delete()

                # Уведомление администратору
                if is_fake and message.link:
                     await send_admin_notification(context, message.link, verdict, explanation)


    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка API (HTTP {e.response.status_code}) для фото [{chat_id}/{message_id}]: {e.request.url} - {e.response.text}")
        db.update_telegram_message_status(message_db_id, status='error_api')
        if not SILENT_MODE:
            if message.chat.type == ChatType.PRIVATE:
                await message.reply_text(f"❌ Ошибка при анализе изображения: API вернул {e.response.status_code}")
            if thinking_message: await thinking_message.delete()
    except Exception as e:
        logger.error(f"Неизвестная ошибка при обработке фото [{chat_id}/{message_id}]: {e}", exc_info=True)
        db.update_telegram_message_status(message_db_id, status='error_worker')
        if not SILENT_MODE:
            if message.chat.type == ChatType.PRIVATE:
                await message.reply_text("❌ Внутренняя ошибка worker'а при анализе изображения.")
            if thinking_message: await thinking_message.delete()


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику обработки сообщений за последние 24 часа."""
    try:
        with db._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Считаем статусы за последние 24 часа
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM telegram_monitored_messages
                    WHERE processed_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY status;
                """)
                stats_raw = cur.fetchall()

                # Считаем общее количество полученных сообщений за 24 часа
                cur.execute("""
                    SELECT COUNT(*) as total
                    FROM telegram_monitored_messages
                    WHERE message_timestamp >= NOW() - INTERVAL '24 hours';
                """)
                total_messages = cur.fetchone()['total']

        stats = {row['status']: row['count'] for row in stats_raw}
        analyzed = stats.get('analyzed', 0)
        pending_url = stats.get('pending', 0) # Сообщения с URL, ожидающие анализа
        pending_text = stats.get('pending_text_only', 0) # Сообщения без URL, ожидающие анализа
        pending = pending_url + pending_text # Общее число ожидающих

        ignored_kw = stats.get('ignored_no_keyword', 0)
        ignored_url = stats.get('ignored_no_url', 0) # Текст с ключом, но без URL (если ты решишь их игнорировать, а не анализировать)
        ignored_dup = stats.get('ignored_duplicate_url', 0)
        ignored = ignored_kw + ignored_url + ignored_dup # Сумма игнорированных

        error_api = stats.get('error_api', 0)
        error_worker = stats.get('error_worker', 0)
        errors = error_api + error_worker # Сумма ошибок

        total_processed_in_period = analyzed + ignored + errors + pending # Сумма всех записей за период

        # Формируем текст статистики
        stats_text_lines = [
            f"📊 **Статистика за последние 24 часа:**\n",
            f"📨 Всего получено сообщений (текст+фото): {total_messages}",
            f"⚙️ Обработано воркером (записи в БД): {total_processed_in_period}",
            f"⏳ В ожидании анализа: {pending}",
            f"✅ Проанализировано успешно: {analyzed}",
            f"🤷 Проигнорировано (нет ключей): {ignored_kw}",
            # f"🤷 Проигнорировано (нет URL): {ignored_url}", # Раскомментируй, если решишь их не анализировать
            f"🤷 Проигнорировано (дубль URL): {ignored_dup}",
            f"🔥 Ошибок API: {error_api}",
            f"🔥 Ошибок воркера: {error_worker}"
        ]
        stats_text = "\n".join(stats_text_lines)

        # Экранируем символы для MarkdownV2
        safe_chars = '_*[]()~`>#+-=|{}.!' # Символы, которые нужно экранировать
        for char in safe_chars:
            stats_text = stats_text.replace(char, f'\\{char}')

        await update.message.reply_markdown_v2(stats_text)

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}", exc_info=True)
        await update.message.reply_text("❌ Не удалось получить статистику.")


# --- Основная функция ---

def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("limit", limit_command))
    application.add_handler(CommandHandler("stats", stats_command)) # ✅ Добавили команду /stats

    application.add_handler(MessageHandler(
        # Слушаем текст ИЛИ фото, везде КРОМЕ команд
        (filters.TEXT | filters.PHOTO) & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP | filters.ChatType.CHANNEL | filters.ChatType.PRIVATE) & ~filters.COMMAND,
        # Вызываем разные функции в зависимости от типа
        # Добавили проверку update.message на None
        lambda update, context: check_photo(update, context) if update.message and update.message.photo else check_message(update, context)
    ))

    logger.info("🚀 Запуск Telegram Worker (v_text_analysis + db_index + silent_mode + stats)...")
    application.run_polling()

if __name__ == "__main__":
    main()

