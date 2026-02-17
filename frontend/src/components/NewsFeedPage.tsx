import { useState, useEffect } from 'react';
import { ExternalLink, Clock, Globe } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import { formatDistanceToNow } from 'date-fns';
import { ru, enUS, kz } from 'date-fns/locale'; // kz локалін қосу керек болуы мүмкін, әзірге ru/en
import { useTranslation } from '../hooks/useTranslation'; // Импорт

interface Article {
  title: string;
  link: string;
  published: string;
  source: string;
}

type Page = 'home' | 'check' | 'feed' | 'dashboard' | 'admin' | 'login' | 'signup' | 'test';

type NewsFeedPageProps = {
  onNavigate?: (page: Page, params?: Record<string, string>) => void;
};

export function NewsFeedPage({ onNavigate }: NewsFeedPageProps) {
  const { t, language } = useTranslation(); // Тілді аламыз
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticles = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('http://localhost:8000/news_feed');
        if (!response.ok) {
          throw new Error('Error loading news');
        }
        const data = await response.json();
        // Егер бэкенд тікелей тізім қайтарса (сіздің жағдайыңызда):
        setArticles(Array.isArray(data) ? data : (Array.isArray(data.articles) ? data.articles : []));
      } catch (err) {
        setError(t('errorOccurred'));
        setArticles([]);
      } finally {
        setLoading(false);
      }
    };
    fetchArticles();
  }, [t]);

  // Сортировка
  const sortedArticles = [...articles].sort((a, b) => {
    const dateA = new Date(a.published).getTime();
    const dateB = new Date(b.published).getTime();
    if (dateA !== dateB) return dateB - dateA;
    return a.source.localeCompare(b.source);
  });

  const handleCheckNews = (url: string, title: string) => {
    if (onNavigate) {
      onNavigate('home', { tab: 'url', url, text: title });
    }
  };

  // Уақыт форматы үшін локаль таңдау
  const getDateLocale = () => {
    if (language === 'ru') return ru;
    // if (language === 'kz') return kz; // date-fns-те қазақша 'kk' болуы мүмкін
    return enUS;
  };

  return (
    <div className="min-h-screen bg-[#0b1121] text-white py-8"
      style={{ backgroundImage: 'radial-gradient(#334155 1.5px, transparent 1.5px)', backgroundSize: '30px 30px' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400 mb-4">
            {t('newsFeed')}
          </h1>
          <p className="text-xl text-slate-400">
            {t('newsSubtitle')}
          </p>
        </div>

        {error && (
          <Card className="mb-6 bg-red-900/20 border-red-800">
            <CardContent className="text-red-400 text-center py-4">
              {error}
            </CardContent>
          </Card>
        )}

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, index) => (
              <Card key={index} className="bg-slate-900/60 border-white/10">
                <CardHeader>
                  <Skeleton className="h-6 w-3/4 bg-slate-700" />
                  <Skeleton className="h-4 w-1/2 bg-slate-700" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-20 w-full bg-slate-700" />
                  <div className="flex justify-between items-center mt-4">
                    <Skeleton className="h-4 w-20 bg-slate-700" />
                    <Skeleton className="h-6 w-16 bg-slate-700" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : sortedArticles.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortedArticles.map((article, idx) => (
              <Card key={idx} className="bg-slate-900/60 backdrop-blur-sm border border-white/10 hover:border-blue-500/50 hover:shadow-lg transition-all duration-300">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between mb-2">
                    <Badge variant="outline" className="text-xs border-blue-500/30 text-blue-300">
                      {article.source}
                    </Badge>
                    <div className="flex items-center text-xs text-slate-400">
                      <Clock className="h-3 w-3 mr-1" />
                      {/* Уақытты көрсету (қате болса try-catch ішінде) */}
                      {(() => {
                        try {
                          return formatDistanceToNow(new Date(article.published), { addSuffix: true, locale: getDateLocale() });
                        } catch (e) {
                          return article.published;
                        }
                      })()}
                    </div>
                  </div>
                  <CardTitle className="text-lg leading-tight text-slate-100 hover:text-blue-400 transition-colors">
                    <a href={article.link} target="_blank" rel="noopener noreferrer" className="hover:underline">
                      {article.title}
                    </a>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between mt-4 border-t border-white/5 pt-4">
                    <Button variant="outline" size="sm" onClick={() => handleCheckNews(article.link, article.title)} className="border-white/10 hover:bg-white/10 text-slate-300">
                      {t('analyzeText')}
                    </Button>
                    <Button variant="ghost" size="sm" asChild className="text-blue-400 hover:text-blue-300 hover:bg-blue-900/20">
                      <a href={article.link} target="_blank" rel="noopener noreferrer" className="flex items-center">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        {t('read')}
                      </a>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="text-center py-12 bg-slate-900/40 border-white/10">
            <CardContent>
              <Globe className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg text-slate-300 mb-2">
                {t('noNews')}
              </h3>
              <p className="text-sm text-slate-500">
                {t('checkLater')}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}