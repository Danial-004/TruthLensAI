// src/components/Header.tsx

import { useState } from 'react';
import { Shield, Moon, Sun, User, LogOut, Menu, X } from 'lucide-react';
import { Button } from './ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/dropdown-menu';
import { useTranslation } from '../hooks/useTranslation';
import { useTheme } from '../hooks/useTheme';
import { useAuth } from '../hooks/useAuth';
import { LanguageSwitcher } from './LanguageSwitcher';

interface HeaderProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export function Header({ currentPage, onNavigate }: HeaderProps) {
  const { t } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  // ✅ ИСПРАВЛЕНО: Используем 'logout' вместо 'signOut'
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Логика навигации остается прежней
  const navigationItems = [
    { id: 'home', label: t('home') },
    { id: 'check', label: t('checkText') },
    { id: 'feed', label: t('newsFeed') },
  ];

  // Проверяем роль пользователя. Примечание: user может быть null
  if (user?.email && user.email.includes('@admin.com')) { // Пример проверки на админа
    navigationItems.push({ id: 'admin', label: t('admin') });
    navigationItems.push({ id: 'test', label: 'Test' });
  }

  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50 backdrop-blur-sm bg-opacity-95 dark:bg-opacity-95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div
            className="flex items-center space-x-2 cursor-pointer"
            onClick={() => onNavigate('home')}
          >
            <div className="bg-gradient-to-br from-blue-600 to-teal-600 p-2 rounded-lg">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent">
              TruthLens AI
            </span>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`px-3 py-2 rounded-md transition-colors ${currentPage === item.id
                  ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
                  : 'text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400'
                  }`}
              >
                {item.label}
              </button>
            ))}
          </nav>

          {/* Desktop Controls */}
          <div className="hidden md:flex items-center space-x-4">
            <LanguageSwitcher />

            {/* <Button variant="ghost" size="sm" onClick={toggleTheme}>
              {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </Button> */}

            {/* User Menu */}
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <User className="h-4 w-4 mr-2" />
                    {user.email}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => onNavigate('dashboard')}>
                    {t('dashboard')}
                  </DropdownMenuItem>
                  {/* ✅ ИСПРАВЛЕНО: Вызываем 'logout' */}
                  <DropdownMenuItem onClick={logout}>
                    <LogOut className="h-4 w-4 mr-2" />
                    {t('logout')}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex space-x-2">
                <Button variant="ghost" size="sm" onClick={() => onNavigate('login')}>
                  {t('login')}
                </Button>
                <Button size="sm" onClick={() => onNavigate('signup')}>
                  {t('signup')}
                </Button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </Button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex flex-col space-y-2">
              {navigationItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    onNavigate(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`px-3 py-2 rounded-md text-left transition-colors ${currentPage === item.id
                    ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
                    : 'text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400'
                    }`}
                >
                  {item.label}
                </button>
              ))}

              <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                {user ? (
                  <div className="space-y-2">
                    <div className="px-3 py-2 text-sm text-slate-600 dark:text-slate-300">
                      {user.email}
                    </div>
                    <button
                      onClick={() => {
                        // ✅ ИСПРАВЛЕНО: Вызываем 'logout'
                        logout();
                        setMobileMenuOpen(false);
                      }}
                      className="px-3 py-2 text-left w-full text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400"
                    >
                      {t('logout')}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <button
                      onClick={() => {
                        onNavigate('login');
                        setMobileMenuOpen(false);
                      }}
                      className="px-3 py-2 text-left w-full text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400"
                    >
                      {t('login')}
                    </button>
                    <button
                      onClick={() => {
                        onNavigate('signup');
                        setMobileMenuOpen(false);
                      }}
                      className="px-3 py-2 text-left w-full text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400"
                    >
                      {t('signup')}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}