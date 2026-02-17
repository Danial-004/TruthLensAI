import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { HomePage } from './components/HomePage';
import { CheckTextPage } from './components/CheckTextPage';
import { NewsFeedPage } from './components/NewsFeedPage';
//import { DashboardPage } from './components/DashboardPage';
import { AdminPage } from './components/AdminPage';
import { AuthPage } from './components/AuthPage';
import { TestPage } from './components/TestPage';
import { TranslationProvider } from './hooks/useTranslation';
import { ThemeProvider } from './hooks/useTheme';
import { AuthProvider } from './hooks/useAuth';
import { Toaster } from './components/ui/sonner';

type Page = 'home' | 'check' | 'feed' | 'dashboard' | 'admin' | 'login' | 'signup' | 'test';


export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [pageParams, setPageParams] = useState<Record<string, string>>({});

  const setCurrentPageWithParams = (page: Page, params?: Record<string, string>) => {
    setCurrentPage(page);
    setPageParams(params || {});
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage onNavigate={setCurrentPageWithParams} params={pageParams} />;
      case 'check':
        return <CheckTextPage />;
      case 'feed':
        return <NewsFeedPage onNavigate={setCurrentPageWithParams} />;
      //case 'dashboard':
      //  return <DashboardPage onNavigate={setCurrentPageWithParams} />;
      case 'admin':
        return <AdminPage />;
      case 'test':
        return <TestPage />;
      case 'login':
        return <AuthPage mode="login" onNavigate={setCurrentPageWithParams} />;
      case 'signup':
        return <AuthPage mode="signup" onNavigate={setCurrentPageWithParams} />;
      default:
        return <HomePage onNavigate={setCurrentPageWithParams} params={pageParams} />;
    }
  };

  return (
    <ThemeProvider>
      <TranslationProvider>
        <AuthProvider>
          <div className="min-h-screen bg-white dark:bg-slate-900 transition-colors">
            <Header currentPage={currentPage} onNavigate={setCurrentPage} />
            <main>{renderPage()}</main>
            <Toaster />
          </div>
        </AuthProvider>
      </TranslationProvider>
    </ThemeProvider>
  );
}