import { Languages } from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { useTranslation } from '../hooks/useTranslation';
import { Language } from '../utils/translations';

const languages = [
  { code: 'en' as Language, name: 'English', flag: '🇺🇸' },
  { code: 'ru' as Language, name: 'Русский', flag: '🇷🇺' },
  { code: 'kz' as Language, name: 'Қазақша', flag: '🇰🇿' },
];

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useTranslation();

  const currentLanguage = languages.find(lang => lang.code === language) || languages[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Languages className="h-4 w-4" />
          <span className="hidden sm:inline">{currentLanguage.flag}</span>
          <span className="hidden md:inline">{currentLanguage.name}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[150px]">
        {languages.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => setLanguage(lang.code)}
            className={`gap-2 ${language === lang.code ? 'bg-slate-100 dark:bg-slate-700' : ''}`}
          >
            <span>{lang.flag}</span>
            <span>{lang.name}</span>
            {language === lang.code && (
              <span className="ml-auto text-xs text-slate-500">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}