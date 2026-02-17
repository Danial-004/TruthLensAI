# backend/celery_worker.py
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_BROKER_URL"),
    # Указываем, что наши задачи находятся в модуле backend.tasks
    include=['backend.tasks']
)