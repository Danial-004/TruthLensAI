import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

// Тек 'dark' типін қалдырамыз
type Theme = 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // State әрқашан 'dark' болады
  const [theme] = useState<Theme>('dark');

  useEffect(() => {
    // Сайт ашылғанда HTML-ге "dark" класын күштеп қосамыз
    const root = window.document.documentElement;
    root.classList.remove('light');
    root.classList.add('dark');

    // Ескі "light" деген жазба қалмас үшін тазалап тастаймыз
    localStorage.setItem('truthlens-theme', 'dark');
  }, []);

  // Бұл функция енді бос болады (ауыстыру мүмкін емес)
  // Бірақ басқа файлдарда қате шықпас үшін қалдырдық
  const toggleTheme = () => {
    console.log("Theme is locked to Dark Mode");
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}