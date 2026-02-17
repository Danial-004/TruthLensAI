// src/utils/factCheckingService.tsx

// ✅ ИСПРАВЛЕНО: Убедись, что VITE_API_URL прописан в твоем .env файле фронтенда
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Source {
    title: string;
    url: string;
    description: string;
}

export interface DetailedAnalysisResult {
    verdict: 'real' | 'fake' | 'controversial';
    confidence: number;
    original_statement: string;
    bias_identification: string;
    detailed_explanation: string;
    sources: Source[];
    search_suggestions: string[];
    analysis_id: number | null; // ID может быть null для гостей
}

// ✅ ИЗМЕНЕНО: checkText теперь работает и для гостей
export const checkText = async (text: string): Promise<DetailedAnalysisResult> => {
    const endpoint = `${API_BASE_URL}/analyze`;
    const token = localStorage.getItem('accessToken'); // Получаем токен

    const headers: HeadersInit = { // Используем HeadersInit для типа
        'Content-Type': 'application/json',
    };

    // Добавляем заголовок авторизации, ТОЛЬКО если токен есть
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: headers, // Передаем сформированные заголовки
            body: JSON.stringify({ text }),
        });

        // Обработка ошибок остается прежней
        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (jsonError) {
                // Если ответ не JSON (например, HTML ошибка сервера)
                throw new Error(`Ошибка сервера: ${response.status} - ${response.statusText}`);
            }
            throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error("Ошибка при вызове API анализа:", error);
        // Добавляем проверку типа ошибки перед пробросом
        if (error instanceof Error) {
            throw error;
        } else {
            throw new Error('Произошла неизвестная ошибка сети');
        }
    }
};

// Функция submitVote остается без изменений, так как голосовать могут только авторизованные
export const submitVote = async (analysis_id: number, vote: 1 | -1): Promise<{ message: string }> => {
    const endpoint = `${API_BASE_URL}/vote`;
    const token = localStorage.getItem('accessToken');

    if (!token) {
        throw new Error("Пользователь не авторизован для голосования.");
    }
    // ... остальная логика submitVote без изменений ...
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ analysis_id, vote }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Ошибка при отправке голоса:", error);
         if (error instanceof Error) {
            throw error;
        } else {
            throw new Error('Произошла неизвестная ошибка сети при голосовании');
        }
    }
};


export interface UserStatus {
    email: string;
    requests_today: number;
    daily_limit: number;
}

// ✅ ИЗМЕНЕНО: getUserStatus теперь лучше обрабатывает ошибки сети и JSON
export const getUserStatus = async (token: string | null): Promise<UserStatus> => {
    if (!token) {
        throw new Error("Пользователь не аутентифицирован.");
    }

    const endpoint = `${API_BASE_URL}/users/me/status`;

    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        // Явная проверка на 401 Unauthorized
        if (response.status === 401) {
            // Можно удалить невалидный токен
            localStorage.removeItem('accessToken');
            throw new Error("Сессия истекла или недействительна. Пожалуйста, войдите снова.");
        }

        if (!response.ok) {
             let errorData;
            try {
                errorData = await response.json();
            } catch (jsonError) {
                throw new Error(`Ошибка сервера: ${response.status} - ${response.statusText}`);
            }
           // Стало
            throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
        }

        // Попытка распарсить JSON, ловим ошибку если ответ не JSON
        try {
           return await response.json();
        } catch (jsonParseError) {
            console.error("Ошибка парсинга JSON от /users/me/status:", jsonParseError);
            throw new Error("Не удалось получить данные о статусе пользователя.");
        }
    } catch (error) {
         console.error("Ошибка при запросе статуса пользователя:", error);
         // Пробрасываем ошибку дальше
         if (error instanceof Error) {
            throw error;
        } else {
            throw new Error('Произошла неизвестная ошибка сети при запросе статуса');
        }
    }
};

// --- НОВАЯ ФУНКЦИЯ для статуса гостя ---
export interface GuestStatus {
    requests_today: number;
    daily_limit: number;
}

export const getGuestStatus = async (): Promise<GuestStatus> => {
    const endpoint = `${API_BASE_URL}/users/guest/status`;
    try {
        const response = await fetch(endpoint, { method: 'GET' });

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (jsonError) {
                throw new Error(`Ошибка сервера (статус гостя): ${response.status} - ${response.statusText}`);
            }
            throw new Error(errorData.detail || `Ошибка сервера (статус гостя): ${response.status}`);
        }

        try {
           return await response.json();
        } catch (jsonParseError) {
            console.error("Ошибка парсинга JSON от /users/guest/status:", jsonParseError);
            throw new Error("Не удалось получить данные о лимите гостя.");
        }

    } catch (error) {
        console.error("Ошибка при запросе статуса гостя:", error);
        if (error instanceof Error) {
            throw error;
        } else {
            throw new Error('Произошла неизвестная ошибка сети при запросе статуса гостя');
        }
    }
};