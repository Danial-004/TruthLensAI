# backend/tasks.py - ФИНАЛЬНАЯ ВЕРСИЯ
import logging
# Используем относительные импорты (с точкой)
from .celery_worker import celery_app
from .database import Database

logger = logging.getLogger(__name__)

@celery_app.task(name="save_analysis_to_db")
def save_analysis_task(analysis_data: dict):
    """Задача Celery для асинхронного сохранения анализа в БД."""
    db_task = Database()
    db_task.initialize()
    logger.info(f"Celery task started for user: {analysis_data.get('user_id')}")
    db_task.save_analysis(analysis_data)
    db_task.close()
    logger.info(f"Celery task finished successfully.")
    return {"status": "success", "classification": analysis_data["classification"]}