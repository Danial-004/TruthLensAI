// src/components/AuthPage.tsx

import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Loader } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

type Page = 'home' | 'check' | 'feed' | 'dashboard' | 'admin' | 'login' | 'signup' | 'test';

interface AuthPageProps {
  mode: 'login' | 'signup';
  onNavigate: (page: Page, params?: Record<string, string>) => void;
}

export function AuthPage({ mode, onNavigate }: AuthPageProps) {
  const { signIn, signUp } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let result;
      if (mode === 'signup') {
        result = await signUp(formData.email, formData.password);
        if (!result.error) {
          alert('Регистрация прошла успешно! Теперь вы можете войти.');
          onNavigate('login');
        } else {
          setError(result.error);
        }
      } else { // mode === 'login'
        result = await signIn(formData.email, formData.password);
        if (!result.error) {
          onNavigate('check');
        } else {
          setError(result.error);
        }
      }
    } catch (err) {
      // Этот блок теперь для самых непредвиденных случаев
      const message = err instanceof Error ? err.message : 'Произошла непредвиденная ошибка';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center text-2xl">
            {mode === 'signup' ? 'Создать аккаунт' : 'Вход в систему'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={formData.email} onChange={handleInputChange} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <Input id="password" type="password" value={formData.password} onChange={handleInputChange} required minLength={6} />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? <Loader className="animate-spin" /> : (mode === 'signup' ? 'Зарегистрироваться' : 'Войти')}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm">
            {mode === 'login' ? (
              <> Нет аккаунта? <button onClick={() => onNavigate('signup')} className="underline">Зарегистрироваться</button> </>
            ) : (
              <> Уже есть аккаунт? <button onClick={() => onNavigate('login')} className="underline">Войти</button> </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}