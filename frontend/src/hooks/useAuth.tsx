// src/hooks/useAuth.tsx

import { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { registerUser, loginUser } from '../utils/authService'; // <-- Импортируем наши API функции

// Тип для данных пользователя
interface User {
  email: string;
}

// Тип для контекста
interface AuthContextType {
  user: User | null;
  signIn: (email: string, password: string) => Promise<{ error: string | null }>;
  signUp: (email: string, password: string) => Promise<{ error: string | null }>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Проверяем наличие токена и данных пользователя при загрузке
    const token = localStorage.getItem('accessToken');
    const userEmail = localStorage.getItem('userEmail');
    if (token && userEmail) {
      setUser({ email: userEmail });
    }
    setIsLoading(false);
  }, []);

  // Функция для входа
  const signIn = async (email: string, password: string) => {
    try {
      const data = await loginUser(email, password);
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('userEmail', email); // Сохраняем email для отображения
      setUser({ email });
      return { error: null };
    } catch (error) {
      // Возвращаем объект с ошибкой для отображения в форме
      return { error: error instanceof Error ? error.message : 'Неизвестная ошибка' };
    }
  };

  // Функция для регистрации
  const signUp = async (email: string, password: string) => {
    try {
      await registerUser(email, password);
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Неизвестная ошибка' };
    }
  };

  // Функция для выхода
  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userEmail');
    setUser(null);
  };

  const value = { user, signIn, signUp, logout, isLoading };

  return (
    <AuthContext.Provider value={value}>
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};