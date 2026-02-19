# backend/app.py — TruthLens AI v4.6.4 Resilient Vision + STERN Prompt (Full Code)
import asyncio
import logging
import os
import json
import io
import time
import httpx
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, ValidationError, HttpUrl
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import (
    Depends, FastAPI, HTTPException, Request, status,
    File, UploadFile, Form
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis
from PIL import Image
from bs4 import BeautifulSoup

# === Локальные модули ===
from database import Database   
from search_api import WebSearcher
from utils import detect_language, preprocess_text
from datetime import datetime

# Токен 30 минутқа жарамды болады
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# === 1. Настройка ===
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="TruthLens AI v4.6 - Resilient Vision + Fallback", version="4.6.4")

# === 2. Константы и CORS ===
ALGORITHM = "HS256"
USER_DAILY_REQUEST_LIMIT = 30
GUEST_REQUEST_LIMIT = 2
GUEST_WINDOW_SECONDS = 60 * 60 * 24
MAX_RETRIES_GEMINI = 3
URL_DOWNLOAD_TIMEOUT = 10 # 10 секунд

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://truthlens-ai-one.vercel.app",  # <--- ЕҢ МАҢЫЗДЫСЫ ОСЫ (соңында /slash болмасын)
]

# 2. Render-ден келген қосымша сілтемелерді қосамыз
env_origins = os.getenv("CORS_ORIGINS")
if env_origins:
    if env_origins == "*":
        # Егер Render-де жұлдызша тұрса, оны елемейміз (қате шықпауы үшін)
        pass 
    else:
        origins.extend(env_origins.split(","))
# 3. Middleware-ді дұрыс баптаймыз
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # <--- Мұнда ["*"] емес, нақты тізім тұруы шарт!
    allow_credentials=True,     # <--- Бұл True болса, allow_origins-те "*" болмауы керек
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
redis_pool: Optional[redis.ConnectionPool] = None

# === 3. Pydantic схемы ===
class AnalysisRequest(BaseModel):
    text: str

class VoteRequest(BaseModel):
    analysis_id: int
    vote: int
    
class UrlAnalysisRequest(BaseModel):
    url: HttpUrl # Используем HttpUrl для базовой валидации
    text: str

class Verdict(str, Enum):
    REAL = "real"
    FAKE = "fake"
    CONTROVERSIAL = "controversial"

class Source(BaseModel):
    title: str
    url: str
    description: str

class DetailedAnalysisResponse(BaseModel):
    bias_identification: str
    detailed_explanation: str
    sources: List[Source]
    search_suggestions: List[str]

class GeminiFullAnalysisResponse(DetailedAnalysisResponse):
    verdict: Verdict
    confidence: float

class FullAnalysisResponse(DetailedAnalysisResponse):
    verdict: Verdict
    confidence: float
    original_statement: str
    analysis_id: Optional[int] = None

class ImageAnalysisResponse(BaseModel):
    verdict: str
    explanation: str
    original_statement: str
    confidence: Optional[float] = None

class GeminiVisionAnalysisInternal(BaseModel):
    ai_artifact_check: str
    context_check: str
    verdict: str
    explanation: str
    confidence: float

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserStatusResponse(BaseModel):
    email: EmailStr
    requests_today: int
    daily_limit: int

class GuestStatusResponse(BaseModel):
    requests_today: int
    daily_limit: int

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# ==========================================
# ОСЫ КОДТЫ backend/app.py ІШІНЕ ҚОСЫҢЫЗ
# ==========================================

@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register_user(user: UserCreate, request: Request):
    db: Optional[Database] = getattr(request.app.state, 'db', None)
    if not db:
        raise HTTPException(status_code=503, detail="База данных недоступна")

    # 1. Мұндай email бар-жоғын тексереміз ('await' ЖОҚ)
    if db.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Пароль ұзындығын тексереміз
    if len(user.password.encode('utf-8')) > 72:
        raise HTTPException(status_code=400, detail="Пароль слишком длинный (макс. 72 байта).")

    # 3. Парольді хэштейміз (72 символға дейін қысқартып)
    hashed_password = pwd_context.hash(user.password[:72])

    # 4. Пайдаланушыны жасаймыз ('await' ЖОҚ)
    # create_user функциясы database.py ішінде болуы керек
    try:
        db.create_user(user.email, hashed_password)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")

    return {"message": "User created successfully"}

# backend/app.py файлына қосыңыз (басқа функциялардың арасына)

@app.post("/login", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1. Базаны аламыз
    db: Optional[Database] = getattr(request.app.state, 'db', None)
    if not db:
        raise HTTPException(status_code=503, detail="База данных недоступна")

    # 2. Қолданушыны email арқылы табамыз
    # (Бұрынғы db.authenticate_user орнына осыны қолданамыз)
    user = db.get_user_by_email(form_data.username)
    
    # 3. Егер қолданушы табылмаса НЕМЕСЕ пароль қате болса -> Қате береміз
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. Токен жасаймыз
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "id": user["id"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# === 4. Startup ===
@app.on_event("startup")
async def startup_event():
    global redis_pool
    logger.info("🚀 1. БАСТАЛДЫ: Запуск приложения...")
    
    try:
        # 1. Database
        logger.info("⏳ 2. Database қосылуда...")
        app.state.db = Database()
        app.state.db.initialize()
        logger.info("✅ 3. Database қосылды!")

        # 2. Searcher
        logger.info("⏳ 4. Searcher қосылуда...")
        app.state.searcher = WebSearcher()
        logger.info("✅ 5. Searcher дайын!")

        # 3. Gemini
        logger.info("⏳ 6. Gemini API тексерілуде...")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            raise ValueError("❌ GEMINI_API_KEY не найден!")
        genai.configure(api_key=GEMINI_API_KEY)
        
        TEXT_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        text_conf = {"temperature": 0.3, "response_mime_type": "application/json"}
        app.state.gemini_model = genai.GenerativeModel(TEXT_MODEL, generation_config=text_conf)
        
        # Vision Model setup...
        vision_conf = {"temperature": 0.4}
        app.state.gemini_vision_model = genai.GenerativeModel(TEXT_MODEL, generation_config=vision_conf)
        
        # Fallback Model setup...
        FALLBACK_MODEL = "gemini-pro-latest"
        fallback_conf = {"temperature": 0.45, "response_mime_type": "application/json"}
        app.state.gemini_fallback_model = genai.GenerativeModel(FALLBACK_MODEL, generation_config=fallback_conf)
        logger.info("✅ 7. Gemini дайын!")

        # 4. Secret Key
        SECRET_KEY = os.getenv("SECRET_KEY")
        if not SECRET_KEY:
            raise ValueError("❌ SECRET_KEY не найден!")
        app.state.secret_key = SECRET_KEY

        # 5. Redis
        logger.info("⏳ 8. Redis қосылуда...")
        redis_url = os.getenv("REDIS_URL")
        
        if redis_url:
            # Тырнақшаларды алып тастау үшін тазалау
            redis_url = redis_url.replace('"', '').strip()
            
            # Timeout қосамыз (Егер 5 секунд жауап бермесе, күтпейміз)
            redis_pool = redis.ConnectionPool.from_url(
                redis_url, 
                decode_responses=True,
                socket_timeout=5.0,  # <--- МАҢЫЗДЫ: 5 секундтан артық күтпеу
                socket_connect_timeout=5.0
            )
            
            try:
                # Тексеру (Ping)
                r = redis.Redis(connection_pool=redis_pool)
                r.ping()
                logger.info("✅ 9. Redis сәтті қосылды!")
            except Exception as re:
                logger.error(f"⚠️ Redis қатесі (бірақ сервер қосыла береді): {re}")
                redis_pool = None
        else:
            logger.warning("⚠️ REDIS_URL жоқ, Redis қосылмайды.")
            redis_pool = None

    except Exception as e:
        logger.error(f"❌ Startup ішінде КРИТИКАЛЫҚ ҚАТЕ: {e}", exc_info=True)
        # Қате болса да сервер құламауы үшін (debug үшін):
        # app.state.db = None
        # raise e  <-- Мұны алып тастасақ, сервер бәрібір қосылады (қатені көру үшін)
        raise e


# === 5. Helpers ===
def get_redis() -> Optional[redis.Redis]:
    if redis_pool:
        try:
            r = redis.Redis(connection_pool=redis_pool)
            r.ping()
            return r
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return None
    return None


async def get_optional_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    if token is None:
        return None
    secret = getattr(request.app.state, 'secret_key', None)
    db: Optional[Database] = getattr(request.app.state, 'db', None)
    if not secret or not db:
        raise HTTPException(status_code=503, detail="Auth сервис недоступен")
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Недопустимый токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Недопустимый токен")
    user = db.get_user_by_email(email=email)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


async def rate_limit_guest(
    request: Request,
    redis_client: Optional[redis.Redis] = Depends(get_redis),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    if current_user is not None:
        return
    if not redis_client:
        return
    
    # ✅ (v4.6.2) Правильное получение IP
    ip = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or request.client.host
    
    key = f"rate_limit_guest:{ip}"
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, GUEST_WINDOW_SECONDS, nx=True)
        count, _ = pipe.execute()
        if count > GUEST_REQUEST_LIMIT:
            raise HTTPException(status_code=429, detail="Лимит гостей исчерпан")
    except Exception as e:
        logger.error(f"Ошибка Redis rate limit: {e}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    secret = getattr(app.state, "secret_key", None)
    if not secret:
        raise RuntimeError("SECRET_KEY не найден")
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


async def get_current_user(current_user: Optional[dict] = Depends(get_optional_current_user)) -> dict:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Требуется вход")
    return current_user
# === ИСПРАВЛЕННАЯ ВЕРСИЯ ПРОМПТА ===
def get_vision_analysis_prompt(language_code: str, text_prompt: str) -> str:
    """Генерирует УСИЛЕННЫЙ промпт v4.6.5 для анализа изображений."""
    lang_map = {"kk": "Kazakh", "ru": "Russian", "en": "English"}
    output_language_name = lang_map.get(language_code, "Russian")
    schema_json = json.dumps(GeminiVisionAnalysisInternal.model_json_schema(), indent=2, ensure_ascii=False)

    prompt = f"""
Ты — **очень** строгий криминалист по цифровым изображениям. Твоя главная задача — найти **любые** признаки подделки. Не доверяй изображению по умолчанию.

УТВЕРЖДЕНИЕ: "{text_prompt}"
ИЗОБРАЖЕНИЕ: [прикреплено]
ЯЗЫК ОТВЕТА: {output_language_name}

ИНСТРУКЦИИ (Следуй **строго** по шагам):
Ты ДОЛЖЕН заполнить ВСЕ поля JSON-схемы. НЕ выноси вердикт, пока не заполнишь 'ai_artifact_check' и 'context_check'.

1.  **ai_artifact_check (КРИТИЧЕСКИЙ ШАГ - Ищи подделку!)**:
    * **Ищи ИИ-артефакты:** 6 пальцев, странные тени, нечитаемые надписи, асимметрия, нелогичные объекты, повторяющиеся узоры, "пластиковые" лица/кожа. **Любое** подозрение — фиксируй.
    * **Ищи МАНИПУЛЯЦИИ (Photoshop/Вставка):**
        * **Освещение:** Совпадает ли свет на *всех* объектах и фоне?
        * **Разрешение/Шум/Фокус:** Все ли части изображения одинаково четкие/размытые/шумные? Нет ли резких перепадов?
        * **Края объектов:** Есть ли неестественно резкие, "вырезанные" или наоборот, "грязные", размытые края? Особенно вокруг людей, предметов.
        * **Перспектива/Масштаб:** Соответствуют ли размеры и углы объектов друг другу и фону?
        * **Отражения/Тени:** Правильно ли расположены тени и отражения? Соответствуют ли они источникам света?
        * **Нелогичность:** Есть ли что-то странное в самой сцене? (Например, Байтерек за окном автобуса).
    * **ЗАПИШИ СЮДА свой подробный вывод** (на {output_language_name}). Если нашел **хотя бы один** подозрительный признак, опиши его четко. Если *абсолютно* ничего нет, напиши "Признаков ИИ-генерации или манипуляций не обнаружено." **Будь скептиком!**

2.  **context_check (Второстепенный шаг)**:
    * **Только после** Шага 1, если изображение кажется подлинным, выполни "обратный поиск по картинке" в своих знаниях.
    * Где и когда это фото появлялось *впервые*? Соответствует ли контекст утверждению? Это старое фото, выдаваемое за новое?
    * **ЗАПИШИ СЮДА свой вывод** (на {output_language_name}). Если ничего нет, напиши "Контекст изображения не найден."

3.  **verdict (ВЕРДИКТ - Артефакты важнее контекста!)**:
    * **ПРАВИЛО 1 (ВАЖНЕЙШЕЕ):** Если в 'ai_artifact_check' найден **хотя бы один** признак ИИ или манипуляции, вердикт **ОБЯЗАТЕЛЬНО** должен быть "Фейк (ИИ-генерация)" или "Фейк (Манипуляция)", **даже если контекст кажется правильным**.
    * **ПРАВИЛО 2:** НЕ ПЫТАЙСЯ оправдать ИИ-фейк или манипуляцию, придумывая им реальный контекст. Артефакты главнее.
    * **ПРАВИЛО 3:** Вердикт "Подлинное" ставь **только** если 'ai_artifact_check' **абсолютно чист** И 'context_check' подтверждает контекст утверждения.
    * Во всех остальных сомнительных случаях (например, артефактов нет, но контекст не найден или противоречив) — ставь "Спорное".
    * Вынеси вердикт (на {output_language_name}).

4.  **explanation (Объяснение)**:
    * Кратко (2-3 предложения на {output_language_name}) объясни свой вердикт, **обязательно ссылаясь** на конкретные находки из 'ai_artifact_check' и 'context_check'. Объясни, **почему** ты считаешь это фейком/подлинным/спорным.

5.  **confidence (Уверенность)**:
    * Оцени свою **общую уверенность** в вердикте от 0.0 до 1.0. Будь честен: если есть сомнения, уверенность не должна быть 1.0.

Твой ответ ДОЛЖЕН быть в строгом JSON-формате ({schema_json}) на {output_language_name} языке. Не добавляй никакого текста до или после JSON.
"""
    return prompt


# === 7. /analyze_image (v4.6 с fallback, confidence и retry) ===
# ИСПРАВЛЕННАЯ ВЕРСИЯ - Улучшена обработка ошибок парсинга JSON
@app.post("/analyze_image", response_model=ImageAnalysisResponse, tags=["Analysis"])
async def analyze_image(
    request: Request,
    text: str = Form(...),
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_optional_current_user),
    _guest_limit_check: None = Depends(rate_limit_guest)
):
    primary_vision_model = getattr(request.app.state, "gemini_vision_model", None)
    fallback_vision_model = getattr(request.app.state, "gemini_fallback_model", None)
    db: Optional[Database] = getattr(request.app.state, "db", None)
    if not db or not (primary_vision_model or fallback_vision_model):
        raise HTTPException(503, "Vision сервис недоступен")

    user_id_for_db = None # ✅ Добавлено для сохранения истории
    if current_user:
        user_id = current_user.get('id')
        if not user_id: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ошибка ID пользователя.")
        # Лимит для пользователя проверяется внутри check_and_update_rate_limit, вызываемого из /analyze
        # Здесь нам нужен только user_id для сохранения
        user_id_for_db = user_id
        logger.info(f"Анализ (Image Upload) для: {current_user.get('email')}")
    else:
        # Гостевой лимит проверяется через _guest_limit_check
         ip_guest = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or request.client.host
         logger.info(f"Анализ (Image Upload) для гостя: {ip_guest or 'unknown'}")


    try:
        img_bytes = await file.read()
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode == "RGBA": img = img.convert("RGB")
        img.thumbnail((2048, 2048)); buf = io.BytesIO()
        img.save(buf, format="JPEG"); image_part = {"mime_type": "image/jpeg", "data": buf.getvalue()}
        logger.info(f"Загруженное изображение обработано ({(len(image_part['data'])/1024):.1f} KB)")
    except Exception as e: 
        logger.error(f"Ошибка обработки загруженного изображения: {e}", exc_info=True)
        raise HTTPException(500, f"Ошибка обработки изображения: {e}")
        
    language_code = detect_language(text)
    prompt = get_vision_analysis_prompt(language_code, text)
        
    analysis_data: Optional[GeminiVisionAnalysisInternal] = None
    last_exception: Optional[Exception] = None
    model_used_name = primary_vision_model.model_name if primary_vision_model else 'N/A'

    try: # Блок Primary -> Fallback
        if not primary_vision_model: raise RuntimeError("Primary vision model not loaded")
        logger.info(f"Попытка 1 (Image Upload): Вызов {model_used_name}...");
        for attempt in range(MAX_RETRIES_GEMINI): # Цикл перезапроса
            try: 
                logger.info(f"...попытка {attempt + 1}"); 
                response = await primary_vision_model.generate_content_async([prompt, image_part], generation_config={"response_mime_type": "application/json"})
                
                # ✅ ИСПРАВЛЕНИЕ: Добавлена обработка ошибки парсинга
                try:
                    analysis_data = GeminiVisionAnalysisInternal.model_validate_json(response.text)
                    logger.info(f"...Успех парсинга JSON. V: {analysis_data.verdict}, C: {analysis_data.confidence:.2f}"); 
                    break # Выходим из цикла ретраев если парсинг успешен
                except (ValidationError, json.JSONDecodeError) as p_err:
                    last_exception = p_err
                    logger.error(f"...НЕ УДАЛОСЬ (Парсинг JSON): {p_err}\nRaw response: {response.text}", exc_info=False) # Логируем RAW ответ
                    if attempt == MAX_RETRIES_GEMINI - 1: raise p_err # Если последняя попытка - пробрасываем ошибку
                    await asyncio.sleep(1) # Ждем перед следующей попыткой
                    continue # Переходим к следующей попытке парсинга

            except Exception as api_err: 
                last_exception = api_err
                logger.error(f"...НЕ УДАЛОСЬ (API): {api_err}", exc_info=(attempt == MAX_RETRIES_GEMINI-1))
                if attempt == MAX_RETRIES_GEMINI - 1: raise api_err # Пробрасываем ошибку API если последняя попытка
                await asyncio.sleep(1) # Ждем перед следующей попыткой API
        
        if analysis_data is None: raise last_exception if last_exception else RuntimeError(f"Primary model {model_used_name} failed after {MAX_RETRIES_GEMINI} attempts")
    
    except Exception as primary_error: # Если Primary модель совсем провалилась
        logger.error(f"Основная модель (Image Upload) {model_used_name} ПРОВАЛИЛАСЬ: {primary_error}. Эскалация!");
        if not fallback_vision_model: logger.critical("Fallback (Image Upload) НЕдоступна!"); raise HTTPException(503, "Ошибка AI")
        
        model_used_name = fallback_vision_model.model_name
        try: 
            logger.info(f"Попытка 2 (Image Upload): Вызов Fallback {model_used_name}..."); 
            response = await fallback_vision_model.generate_content_async([prompt, image_part], generation_config={"response_mime_type": "application/json"})
            
            # ✅ ИСПРАВЛЕНИЕ: Добавлена обработка ошибки парсинга для Fallback
            try:
                analysis_data = GeminiVisionAnalysisInternal.model_validate_json(response.text)
                logger.info(f"...Fallback Успех парсинга JSON. V: {analysis_data.verdict}, C: {analysis_data.confidence:.2f}"); 
            except (ValidationError, json.JSONDecodeError) as p_err_fb:
                 logger.critical(f"Fallback (Image Upload) НЕ СМОГ распарсить JSON! Err: {p_err_fb}\nRaw response: {response.text}", exc_info=True)
                 raise HTTPException(500, "Ошибка AI (Fallback JSON)")

        except Exception as fallback_error: 
            logger.critical(f"Обе модели (Image Upload) провалились! Err1: {primary_error}, Err2: {fallback_error}", exc_info=True); 
            raise HTTPException(500, "Ошибка AI (Обе модели)")

    # Возвращаем результат анализа ИЗОБРАЖЕНИЯ (ImageAnalysisResponse)
    if analysis_data:
        logger.info(f"Финальный ответ (Image Upload) через: {model_used_name}")
        # ✅ Сохраняем историю для пользователя, если он есть
        response_to_save = {
            "verdict": analysis_data.verdict,
            "confidence": analysis_data.confidence,
            "explanation": analysis_data.explanation,
            "original_statement": text,
            "analysis_type": "image_upload" # Добавим тип анализа
        }
        if user_id_for_db:
             db.save_analysis(
                user_id=user_id_for_db, text=f"Image Upload | Claim: {text}", 
                verdict=analysis_data.verdict, confidence=analysis_data.confidence, 
                full_response=response_to_save
            )

        return ImageAnalysisResponse(**response_to_save)
    else: 
        logger.error("Неизвестная ошибка (Image Upload) - analysis_data is None.")
        raise HTTPException(500, "Неизвестная ошибка AI.")


# === ✅✅✅ ОБЪЕДИНЕННЫЙ ЭНДПОИНТ: /analyze_url (v4.8 - Картинки + Статьи) === ✅✅✅
# ИСПРАВЛЕННАЯ ВЕРСИЯ - Возвращает FullAnalysisResponse для HTML
@app.post("/analyze_url", 
          # Указываем Union для Swagger, но FastAPI может ругаться. 
          # Главное, что мы возвращаем ПРАВИЛЬНУЮ СТРУКТУРУ ДАННЫХ.
          # response_model=Union[FullAnalysisResponse, ImageAnalysisResponse], 
          tags=["Analysis"]) 
async def analyze_url(
    request: Request,
    body: UrlAnalysisRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user),
    _guest_limit_check: None = Depends(rate_limit_guest)
):
    """
    Анализирует контент по URL (v4.8):
    - Если URL ведет на ИЗОБРАЖЕНИЕ -> использует Vision модель (возвращает ImageAnalysisResponse).
    - Если URL ведет на HTML -> извлекает текст и использует Text модель (возвращает FullAnalysisResponse).
    """
    primary_vision_model = getattr(request.app.state, "gemini_vision_model", None)
    fallback_vision_model = getattr(request.app.state, "gemini_fallback_model", None)
    text_model = getattr(request.app.state, "gemini_model", None)
    detector = getattr(request.app.state, "detector", None)      
    searcher = getattr(request.app.state, "searcher", None)      
    db: Optional[Database] = getattr(request.app.state, "db", None)

    if not db or not detector or not searcher or not text_model or not (primary_vision_model or fallback_vision_model):
        raise HTTPException(503, "Сервис анализа временно недоступен")

    user_id_for_db = None # ✅ Добавлено для сохранения истории
    if current_user:
        user_id = current_user.get('id')
        if not user_id: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ошибка ID пользователя.")
        if not db.check_and_update_rate_limit(user_id=user_id, limit=USER_DAILY_REQUEST_LIMIT):
             raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Дневной лимит запросов исчерпан.")
        user_id_for_db = user_id # ✅ Сохраняем ID для истории
        logger.info(f"Анализ (URL) для: {current_user.get('email')}")
    else:
        ip_guest = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or request.client.host
        logger.info(f"Анализ (URL) для гостя: {ip_guest or 'unknown'}")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=URL_DOWNLOAD_TIMEOUT) as client:
            logger.info(f"Скачивание контента с URL: {body.url}")
            url_str = str(body.url)
            response = await client.get(url_str)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            content = await response.aread()
    except httpx.HTTPStatusError as e: logger.error(f"Ошибка скачивания URL (HTTP {e.response.status_code}): {body.url}", exc_info=False); raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Не удалось скачать: Ошибка {e.response.status_code}")
    except httpx.RequestError as e: logger.error(f"Ошибка скачивания URL (Network): {body.url}", exc_info=False); raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Не удалось подключиться к URL: {e}")
    except Exception as e: logger.error(f"Неизвестная ошибка скачивания URL: {body.url}", exc_info=True); raise HTTPException(500, f"Ошибка при скачивании URL: {e}")

    # === СЛУЧАЙ 1: ЭТО ИЗОБРАЖЕНИЕ ===
    if content_type.startswith("image/"):
        logger.info(f"Обнаружено ИЗОБРАЖЕНИЕ (Type: {content_type}). Запуск Vision анализа...")
        try:
            img = Image.open(io.BytesIO(content))
            if img.mode == "RGBA": img = img.convert("RGB")
            img.thumbnail((2048, 2048)); buf = io.BytesIO()
            img.save(buf, format="JPEG"); image_part = {"mime_type": "image/jpeg", "data": buf.getvalue()}
            logger.info(f"Изображение по URL обработано ({(len(image_part['data'])/1024):.1f} KB)")
        except Exception as e: logger.error(f"Ошибка обработки изображения с URL: {body.url}", exc_info=True); raise HTTPException(500, f"Ошибка обработки файла с URL: {e}")

        language_code = detect_language(body.text)
        prompt = get_vision_analysis_prompt(language_code, body.text)
        logger.info(f"Язык запроса/ответа (URL-Image): {language_code}")

        analysis_data: Optional[GeminiVisionAnalysisInternal] = None
        last_exception: Optional[Exception] = None
        model_used_name = primary_vision_model.model_name if primary_vision_model else 'N/A'
        
        try: # Блок Primary -> Fallback
            if not primary_vision_model: raise RuntimeError("Primary vision model not loaded")
            logger.info(f"Попытка 1 (URL-Image): Вызов {model_used_name}...");
            for attempt in range(MAX_RETRIES_GEMINI): # Цикл перезапроса
                try: 
                    logger.info(f"...попытка {attempt + 1}"); 
                    response = await primary_vision_model.generate_content_async([prompt, image_part], generation_config={"response_mime_type": "application/json"})
                    
                    # ✅ ИСПРАВЛЕНИЕ: Добавлена обработка ошибки парсинга
                    try:
                        analysis_data = GeminiVisionAnalysisInternal.model_validate_json(response.text)
                        logger.info(f"...Успех парсинга JSON. V: {analysis_data.verdict}, C: {analysis_data.confidence:.2f}"); 
                        break # Выходим из цикла ретраев если парсинг успешен
                    except (ValidationError, json.JSONDecodeError) as p_err:
                        last_exception = p_err
                        logger.error(f"...НЕ УДАЛОСЬ (Парсинг JSON): {p_err}\nRaw response: {response.text}", exc_info=False) # Логируем RAW ответ
                        if attempt == MAX_RETRIES_GEMINI - 1: raise p_err # Если последняя попытка - пробрасываем ошибку
                        await asyncio.sleep(1) # Ждем перед следующей попыткой
                        continue # Переходим к следующей попытке парсинга

                except Exception as api_err: 
                    last_exception = api_err
                    logger.error(f"...НЕ УДАЛОСЬ (API): {api_err}", exc_info=(attempt == MAX_RETRIES_GEMINI-1))
                    if attempt == MAX_RETRIES_GEMINI - 1: raise api_err # Пробрасываем ошибку API если последняя попытка
                    await asyncio.sleep(1) # Ждем перед следующей попыткой API
            
            if analysis_data is None: raise last_exception if last_exception else RuntimeError(f"Primary model {model_used_name} failed after {MAX_RETRIES_GEMINI} attempts")
        
        except Exception as primary_error: # Если Primary модель совсем провалилась
            logger.error(f"Основная модель (URL-Image) {model_used_name} ПРОВАЛИЛАСЬ: {primary_error}. Эскалация!");
            if not fallback_vision_model: logger.critical("Fallback (URL-Image) НЕдоступна!"); raise HTTPException(503, "Ошибка AI")
            
            model_used_name = fallback_vision_model.model_name
            try: 
                logger.info(f"Попытка 2 (URL-Image): Вызов Fallback {model_used_name}..."); 
                response = await fallback_vision_model.generate_content_async([prompt, image_part], generation_config={"response_mime_type": "application/json"})
                
                # ✅ ИСПРАВЛЕНИЕ: Добавлена обработка ошибки парсинга для Fallback
                try:
                    analysis_data = GeminiVisionAnalysisInternal.model_validate_json(response.text)
                    logger.info(f"...Fallback Успех парсинга JSON. V: {analysis_data.verdict}, C: {analysis_data.confidence:.2f}"); 
                except (ValidationError, json.JSONDecodeError) as p_err_fb:
                     logger.critical(f"Fallback (URL-Image) НЕ СМОГ распарсить JSON! Err: {p_err_fb}\nRaw response: {response.text}", exc_info=True)
                     raise HTTPException(500, "Ошибка AI (Fallback JSON)")

            except Exception as fallback_error: 
                logger.critical(f"Обе модели (URL-Image) провалились! Err1: {primary_error}, Err2: {fallback_error}", exc_info=True); 
                raise HTTPException(500, "Ошибка AI (Обе модели)")

        # Возвращаем результат анализа ИЗОБРАЖЕНИЯ (ImageAnalysisResponse)
        if analysis_data:
            logger.info(f"Финальный ответ (URL-Image) через: {model_used_name}")
            # ✅ Сохраняем историю для пользователя, если он есть
            response_to_save = {
                "verdict": analysis_data.verdict,
                "confidence": analysis_data.confidence,
                "explanation": analysis_data.explanation,
                "original_statement": body.text,
                "analysis_type": "image_url" # Добавим тип анализа
            }
            if user_id_for_db:
                 db.save_analysis(
                    user_id=user_id_for_db, text=f"Image URL: {body.url} | Claim: {body.text}", 
                    verdict=analysis_data.verdict, confidence=analysis_data.confidence, 
                    full_response=response_to_save
                )
            
            return ImageAnalysisResponse(**response_to_save)
        else: 
            # Эта ветка не должна достигаться из-за raise выше, но на всякий случай
            logger.error("Неизвестная ошибка (URL-Image) - analysis_data is None.")
            raise HTTPException(500, "Неизвестная ошибка AI.")

    # === СЛУЧАЙ 2: ЭТО HTML СТРАНИЦА ===
    elif content_type.startswith("text/html"):
        logger.info(f"Обнаружен HTML (Type: {content_type}). Запуск Text анализа...")
        try:
            html_text = content.decode(response.encoding or 'utf-8')
            soup = BeautifulSoup(html_text, "html.parser")
            main_content = soup.find("article") or soup.find("main") or \
                           soup.find("div", class_=lambda x: x and 'article' in x.lower()) or \
                           soup.find("div", id=lambda x: x and 'content' in x.lower()) or \
                           soup.body
            article_text = main_content.get_text(separator="\n", strip=True) if main_content else soup.get_text(separator="\n", strip=True)

            if not article_text or len(article_text) < 50: # Уменьшил порог
                logger.warning(f"Не удалось извлечь достаточно текста из HTML ({len(article_text)} chars). URL: {body.url}")
                # Можно или падать, или пытаться анализировать только user claim
                # Попробуем анализировать только claim + URL
                article_text = "Контент страницы не удалось извлечь."
                # raise ValueError("Не удалось извлечь достаточно текста из HTML.")
            
            logger.info(f"Извлечено {len(article_text)} символов текста из HTML.")
            text_to_analyze = body.text
            sources_for_prompt_url = f"- Title: Веб-страница\n  URL: {url_str}\n  Description: {article_text[:1500]}..."

        except Exception as e:
            logger.error(f"Ошибка парсинга HTML или извлечения текста: {e}", exc_info=True)
            raise HTTPException(400, f"Не удалось извлечь текст статьи: {e}")

        language = detect_language(text_to_analyze)
        local_recommendation = None
        # ... (логика для local_recommendation остается) ...
        if language == 'kk':
             try:
                 clean_article_text = preprocess_text(article_text if len(article_text) > 50 else text_to_analyze) # Берем текст статьи если есть, иначе claim
                 prediction = detector.predict(clean_article_text, language)
                 if prediction['classification'] in ['real', 'fake']: local_recommendation = prediction['classification']
                 logger.info(f"Локальная 'kk' модель (URL-Text) РЕКОМЕНДУЕТ: {local_recommendation}")
             except Exception as e: logger.error(f"Ошибка 'kk' модели (URL-Text): {e}")

        logger.info("Вызов Gemini Text (URL-Text)...")
        final_prompt = get_gemini_full_analysis_prompt(
            language=language,
            text=text_to_analyze,
            sources_text=sources_for_prompt_url,
            local_model_recommendation=local_recommendation
        )
        try:
            response_gemini = await text_model.generate_content_async(final_prompt)
            # ✅ ИСПРАВЛЕНИЕ: Добавлена обработка ошибки парсинга
            try:
                gemini_full_response = GeminiFullAnalysisResponse.model_validate_json(response_gemini.text)
            except (ValidationError, json.JSONDecodeError) as p_err_txt:
                 logger.error(f"НЕ УДАЛОСЬ (Парсинг JSON Text): {p_err_txt}\nRaw response: {response_gemini.text}", exc_info=False)
                 raise HTTPException(500, "Ошибка AI (Text JSON)")
                 
            analysis_data_dict = gemini_full_response.model_dump()
            final_verdict = analysis_data_dict.pop("verdict")
            final_confidence = analysis_data_dict.pop("confidence")
            logger.info(f"Gemini Text (URL-Text) Успех. Вердикт: {final_verdict}")

            # ✅✅✅ ИСПРАВЛЕНИЕ: Возвращаем СЛОВАРЬ в формате FullAnalysisResponse ✅✅✅
            response_data = {
                "verdict": final_verdict,
                "confidence": final_confidence,
                "original_statement": body.text,
                **analysis_data_dict # Добавляем bias_identification, detailed_explanation, sources, search_suggestions
            }

# ... (db.save_analysis басы) ...
            analysis_id = None
            if user_id_for_db:
                analysis_id = db.save_analysis(
                    user_id=user_id_for_db, 
                    text=f"URL: {body.url} | Claim: {body.text}", 
                    verdict=final_verdict.value, 
                    confidence=final_confidence, 
                    full_response=response_data # Бұл жол түсіп қалған болуы мүмкін
                ) # ✅ 1. Жақшаны жабамыз
                response_data["analysis_id"] = analysis_id
            
            return FullAnalysisResponse(**response_data) # немесе LinkAnalysisResponse (функцияға байланысты)

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal Error")


# ✅ 2. Prompt функциясы бөлек тұруы керек (Indentation дұрыс болуы шарт)
def get_gemini_full_analysis_prompt(language, text, sources_text, local_model_recommendation=None):
    # Карта тілдері
    lang_map = {"kk": "Kazakh", "ru": "Russian", "en": "English"}
    output_lang = lang_map.get(language, "Russian")

    rec_line = ""
    if local_model_recommendation:
        rec_line = f"\n(Предварительный AI-анализ: {local_model_recommendation})"

    # ✅ 3. Тырнақшалар (f""") міндетті түрде болуы керек
    prompt = f"""
Ты — главный фактчекер (Chief Fact-Checker). 
Твоя задача — определить достоверность утверждения на {output_lang} языке.

Утверждение: "{text}"{rec_line}

Источники:
{sources_text}

Проанализируй:
1. Соответствие утверждения источникам.
2. Предвзятость или манипулятивные формулировки.
3. Вероятность того, что утверждение является ложным.

Ответ дай строго в формате JSON:
{{
  "verdict": "real | fake | controversial",
  "confidence": 0.0-1.0,
  "bias_identification": "Текстовое описание предвзятости",
  "detailed_explanation": "Развернутое объяснение вывода",
  "sources": [{{ "title": "...", "url": "...", "description": "..." }}],
  "search_suggestions": ["ключевое слово 1", "ключевое слово 2"]
}}
"""
    return prompt.strip()

@app.post(
    "/analyze",
    # response_model=FullAnalysisResponse,  <-- Егер Pydantic модель жоғарыда болса, қосыңыз
    tags=["Analysis"],
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Лимит запросов исчерпан."},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Сервис недоступен."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Внутренняя ошибка."}
    }
)
async def analyze_text(
    req_body: AnalysisRequest,
    request: Request, 
    current_user: Optional[dict] = Depends(get_optional_current_user),
    # _guest_limit_check: None = Depends(rate_limit_guest) # Redis жоқ болса, алып тастаңыз
):
    # 1. Тек жеңіл компоненттерді аламыз
    searcher = getattr(request.app.state, 'searcher', None)
    gemini_model = getattr(request.app.state, 'gemini_model', None)
    db: Optional[Database] = getattr(request.app.state, 'db', None)

    # Detector керек емес!
    if not all([searcher, gemini_model, db]):
        raise HTTPException(status_code=503, detail="Сервис временно недоступен.")
    
    user_id_for_db = None
    if current_user:
        logger.info(f"Анализ (Текст) для пользователя: {current_user.get('email')}")
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Ошибка аутентификации пользователя.")

        # Redis өшірулі болса, лимит тексеру қате беруі мүмкін.
        # Егер Redis жоқ болса, бұл блокты try-except-ке алыңыз:
        try:
            is_limit_ok = db.check_and_update_rate_limit(user_id=user_id, limit=USER_DAILY_REQUEST_LIMIT)
            if not is_limit_ok:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Дневной лимит запросов исчерпан."
                )
        except Exception:
            pass # Redis жоқ болса, лимитті елемейміз
        
        user_id_for_db = user_id
    else:
        ip_guest = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or request.client.host
        logger.info(f"Анализ (Текст) для гостя с IP: {ip_guest or 'unknown'}")
        
    try:
        language = detect_language(req_body.text)
        clean_text = preprocess_text(req_body.text)

        # 2. Іздеу (SerpAPI)
        logger.info(f"Searching: '{clean_text[:50]}...' (lang: {language})")
        search_results = searcher.search(req_body.text, language, max_results=3) # 3 нәтиже жетеді
        
        sources_for_prompt = "\n".join([
            f"- Title: {s.get('title', 'N/A')}\n  URL: {s.get('url', 'N/A')}\n  Description: {s.get('description', 'N/A')}"
            for s in search_results
        ]) if search_results else "No relevant sources found."

        # 3. Жергілікті модельді (local_recommendation) ТОЛЫҚ ӨШІРДІК
        # Оның орнына Gemini-ге "None" жібереміз.

        logger.info("Вызов Gemini (Chief Fact-Checker)...")

        # 1. Қазіргі уақытты анықтаймыз (2026 жыл проблемасын шешу үшін)
        current_date_str = datetime.now().strftime("%Y-%m-%d (%A)")

        # 2. Негізгі промптты аламыз
        base_prompt = get_gemini_full_analysis_prompt(
            language=language,
            text=req_body.text,
            sources_text=sources_for_prompt,
            local_model_recommendation=None # Жергілікті модельді өшірдік
        )

        # 3. Промптқа "Бүгін 2026 жыл" деп жалғаймыз
        final_prompt = f"""
        [SYSTEM NOTE: IMPORTANT CONTEXT]
        Today's Date: {current_date_str}. 
        Current Year: 2026.
        Any news or events dated {current_date_str} or earlier are PAST or PRESENT facts, not future predictions.
        Treat "2026" as the current year.
        --------------------------------------------------
        {base_prompt}
        """
        
        # 4. Gemini-ді шақырамыз
        response_gemini = await gemini_model.generate_content_async(final_prompt)
        
        try:
            # 5. Жауапты өңдеу (Parsing)
            gemini_full_response = GeminiFullAnalysisResponse.model_validate_json(response_gemini.text)
            analysis_data_dict = gemini_full_response.model_dump()
            final_verdict = analysis_data_dict.pop("verdict")
            final_confidence = analysis_data_dict.pop("confidence")
        except Exception as json_e:
            logger.error(f"❌ JSON Error: {json_e}")
            raise HTTPException(status_code=500, detail="Ошибка AI (JSON Parse).")

        # 6. Нәтижені жинақтау
        response_data = {
            "verdict": final_verdict, 
            "confidence": final_confidence,
            "original_statement": req_body.text, 
            "local_label": None, 
            **analysis_data_dict
        }

        # Базаға сақтау
        analysis_id = None
        if user_id_for_db: 
            analysis_id = db.save_analysis(
                user_id=user_id_for_db, text=req_body.text, verdict=final_verdict.value,
                confidence=final_confidence, full_response=response_data
            )
            response_data["analysis_id"] = analysis_id
            
        return FullAnalysisResponse(**response_data)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка.")


# ⛔️ (v4.6.2) ДУБЛИКАТ /analyze_image (v4.3) УДАЛЕН ⛔️


@app.get("/users/me/status", response_model=UserStatusResponse, tags=["User"])
async def read_users_me_status(request: Request, current_user: dict = Depends(get_current_user)):
    db: Optional[Database] = getattr(request.app.state, 'db', None)
    if not db: raise HTTPException(status_code=503, detail="База данных недоступна")
    user_id = current_user.get('id')
    if not user_id: raise HTTPException(status_code=400, detail="ID пользователя не найден")
    user_status_data = db.get_user_status(user_id)
    if not user_status_data:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    user_status_data['daily_limit'] = USER_DAILY_REQUEST_LIMIT
    return UserStatusResponse(**user_status_data)


@app.post("/vote", status_code=status.HTTP_200_OK, tags=["User"])
async def submit_vote(vote_req: VoteRequest, request: Request, current_user: dict = Depends(get_current_user)):
    db: Optional[Database] = getattr(request.app.state, 'db', None)
    if not db:
        raise HTTPException(status_code=503, detail="База данных недоступна")
    user_id = current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=4400, detail="ID пользователя не найден")
    if vote_req.vote not in [1, -1]:
        raise HTTPException(status_code=422, detail="Неверное значение для голоса. Допустимо 1 или -1.")
    success = db.save_vote(user_id=user_id, analysis_id=vote_req.analysis_id, vote=vote_req.vote)
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось сохранить голос.")
    return {"message": "Спасибо за ваш отзыв!"}


# backend/app.py - get_history функциясын алмастырыңыз

# backend/app.py ішіне қосыңыз (Мысалы, /users/me/status функциясынан кейін)

# backend/app.py файлына қосыңыз

class NewsItem(BaseModel):
    title: str
    link: str
    source: str
    published: str
    summary: str

@app.get("/news_feed", response_model=List[NewsItem], tags=["News"])
async def get_news_feed():
    """
    RSS арқылы соңғы жаңалықтарды (қазақша/орысша) тартып алады.
    """
    rss_urls = [
        "https://tengrinews.kz/news.xml",       # Tengrinews (Ru)
        "https://kaz.tengrinews.kz/news.xml",   # Tengrinews (Kz)
        "https://www.inform.kz/rss/kaz.xml",    # Inform.kz (Kz)
        "https://forbes.kz/rss.xml"             # Forbes (Ru)
    ]
    
    all_news = []
    
    # Әр сайттан 3 жаңалықтан аламыз
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                # Сурет бар ма тексереміз (кейбір RSS-те болады)
                # Бірақ қарапайым болу үшін тек мәтінін аламыз
                all_news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": url.split('/')[2], # tengerinews.kz деген сияқты
                    "published": getattr(entry, 'published', 'Just now'),
                    "summary": getattr(entry, 'summary', '')[:200] + "..." # Қысқаша мазмұны
                })
        except Exception as e:
            logger.error(f"RSS Error ({url}): {e}")
            continue

    # Араластырып жібереміз (Shuffle) немесе уақытымен сұрыптауға болады
    return all_news

@app.get("/users/guest/status", response_model=GuestStatusResponse, tags=["User"])
async def read_guest_status(request: Request):
    # 1. Қонақтың IP адресін анықтаймыз
    ip = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or request.client.host
    
    # 2. Redis-тен осы IP бүгін қанша рет тексергенін қараймыз
    requests_count = 0
    if redis_pool:
        try:
            r = redis.Redis(connection_pool=redis_pool)
            val = r.get(f"rate_limit_guest:{ip}")
            if val:
                requests_count = int(val)
        except Exception:
            pass # Егер Redis істемесе, 0 деп көрсете береміз
            
    return {
        "requests_today": requests_count,
        "daily_limit": GUEST_REQUEST_LIMIT
    }

@app.get("/history", response_model=List[dict], tags=["User"])
async def get_history(request: Request, current_user: dict = Depends(get_current_user)):
    db: Optional[Database] = getattr(request.app.state, 'db', None)
    if not db: 
        raise HTTPException(status_code=503, detail="БД недоступна")
        
    user_id = current_user.get('id')
    if not user_id: 
        raise HTTPException(status_code=400, detail="ID пользователя не найден")
        
    # 'await' жоқ, себебі db синхронды
    history_items = db.get_user_history(user_id=user_id, limit=20) 
    
    formatted_history = []
    
    for item in history_items:
        # FrontEnd күтіп тұрған форматқа келтіру (тек 5 кілт):
        formatted_history.append({
            "id": item.get("id"),
            "text": item.get("text"),
            "verdict": item.get("verdict", item.get("label", "controversial")), # 'verdict' немесе 'label'-ді қолдану
            "confidence": item.get("confidence"),
            "created_at": item.get("created_at").isoformat() if item.get("created_at") else None,
        })
    
    # Егер дерек жоқ болса, бос массив қайтарамыз (FrontEnd Skeleton-нан шығу үшін)
    return formatted_history