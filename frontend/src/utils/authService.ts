// src/utils/authService.ts

// Убедись, что VITE_API_URL прописан в твоем .env файле фронтенда
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Функция для регистрации нового пользователя.
 */
export const registerUser = async (email: string, password: string) => {
  const response = await fetch(`${API_BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    // Пробрасываем ошибку с текстом от сервера
    throw new Error(errorData.detail || `Ошибка регистрации: ${response.status}`);
  }

  return await response.json();
};

/**
 * Функция для входа пользователя в систему.
 * Возвращает токен доступа.
 */
export const loginUser = async (email: string, password: string) => {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    // FastAPI ожидает данные для логина в формате form-data
    body: new URLSearchParams({
      username: email,
      password: password,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `Ошибка входа: ${response.status}`);
  }

  return await response.json();
};