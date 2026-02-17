import redis
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True  # <── важно для Upstash
)

try:
    print("Pinging Redis...")
    response = r.ping()
    print("✅ Connected! Redis replied:", response)
except Exception as e:
    print("❌ Connection failed:", e)
