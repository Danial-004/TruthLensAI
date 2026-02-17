# --- Этап 1: Сборка зависимостей ---
# Используем официальный образ Python. Тег slim-buster - это легковесная версия Debian.
FROM python:3.9-slim-buster AS builder

# Устанавливаем рабочую директорию
WORKDIR /usr/src/app

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


# --- Этап 2: Финальный образ ---
# Используем тот же базовый образ для консистентности
FROM python:3.9-slim-buster

# Создаем непривилегированного пользователя для безопасности
RUN addgroup --system app && adduser --system --group app

# Создаем рабочую директорию
WORKDIR /home/app

# Копируем зависимости из этапа сборки
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .

# Устанавливаем зависимости из "колес" без компиляции
RUN pip install --no-cache /wheels/*

# Копируем код приложения (предполагается, что Dockerfile находится в папке backend)
COPY . .

# Меняем владельца файлов на нашего непривилегированного пользователя
RUN chown -R app:app /home/app

# Переключаемся на этого пользователя
USER app

# Открываем порт, который слушает наше приложение
EXPOSE 8000

# Запускаем приложение с помощью Gunicorn для продакшена
# -w 4: 4 worker-процесса
# -k uvicorn.workers.UvicornWorker: используем Uvicorn для асинхронности
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--host", "0.0.0.0", "--port", "8000"]