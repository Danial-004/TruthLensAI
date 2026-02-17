// src/components/DashboardPage.tsx (ФИНАЛДЫҚ НҰСҚА)
import { useState, useEffect } from 'react';
import {
  XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line
} from 'recharts';
import {
  Activity, Target, FileText,
  Shield, Clock, CheckCircle, AlertTriangle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import { useTranslation } from '../hooks/useTranslation';
import { useAuth } from '../hooks/useAuth';
import { motion } from 'framer-motion';
// Format импортын қосамыз
import { formatDistanceToNow, format } from 'date-fns';
import { ru } from 'date-fns/locale';

type Page = 'home' | 'check' | 'feed' | 'dashboard' | 'admin' | 'login' | 'signup' | 'test';

interface DashboardPageProps {
  onNavigate: (page: Page, params?: Record<string, string>) => void;
}

interface HistoryItem {
  id: number;
  text: string;
  verdict: 'real' | 'fake' | 'controversial';
  confidence: number;
  created_at: string;
}

interface Stats {
  totalPredictions: number;
  classifications: {
    fake: number;
    real: number;
    uncertain: number;
  };
  avgConfidence: number;
}

// ✅ ТҮЗЕТУ 1: API URL-ды backend портына (8000) ауыстырамыз
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const { t } = useTranslation();
  // useAuth-тан user объектісін аламыз
  const { user, loading: authLoading } = useAuth();

  const [stats, setStats] = useState<Stats | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ✅ ТҮЗЕТУ 2: Логиканы қайта жазу (Token Timing)
  useEffect(() => {
    const token = localStorage.getItem('token');

    // Егер аутентификация жүктеліп болса AND қолданушы бар болса
    if (!authLoading && user && token) {
      // Fetch сұранысын жібереміз
      fetchDashboardData(token);
    }
    // Егер аутентификация жүктеліп болса AND қолданушы жоқ болса
    else if (!authLoading && !user) {
      setError("Не найден токен авторизации. Войдите заново.");
      setLoading(false);
    }
    // Егер әлі жүктеліп жатса, ештеңе істемейміз (Skeleton тұрады)
  }, [authLoading, user]);

  const fetchDashboardData = async (token: string) => {
    // loading: true-ден бастаймыз
    // setError: қателерді тазалаймыз
    setLoading(true);
    setError(null);

    try {
      console.log("Fetching /history...");
      const response = await fetch(`${API_URL}/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        // Токен жарамсыз болса, оны жоямыз
        localStorage.removeItem('token');
        throw new Error("Ошибка аутентификации. Войдите заново.");
      }

      if (!response.ok) {
        throw new Error(`Не удалось загрузить историю (${response.status}).`);
      }

      const historyList: HistoryItem[] = await response.json();
      console.log("Fetched history:", historyList);

      // --- СТАТИСТИКАНЫ ЕСЕПТЕУ ЛОГИКАСЫ (STATS CALCULATION) ---
      const totalPredictions = historyList.length;
      const real = historyList.filter(item => item.verdict === 'real').length;
      const fake = historyList.filter(item => item.verdict === 'fake').length;
      const uncertain = historyList.filter(item => item.verdict === 'controversial').length;

      const avgConfidence =
        totalPredictions > 0
          ? Math.round(
            (historyList.reduce((acc, item) => acc + item.confidence, 0) / totalPredictions) * 100
          )
          : 0;

      setStats({
        totalPredictions,
        classifications: { real, fake, uncertain },
        avgConfidence,
      });
      setHistory(historyList);
      // --------------------------------------------------------

    } catch (error: any) {
      console.error("Ошибка при загрузке данных дашборда:", error);
      setError(error.message);
    } finally {
      // ✅ ФИНАЛДЫҚ ТҮЗЕТУ: Әрқашан жүктеуді аяқтаймыз, Skeleton жоғалады!
      setLoading(false);
    }
  };

  const chartData =
    stats && stats.totalPredictions > 0
      ? [
        { name: 'Real', value: stats.classifications.real, color: '#10b981' },
        { name: 'Fake', value: stats.classifications.fake, color: '#ef4444' },
        { name: 'Uncertain', value: stats.classifications.uncertain, color: '#f59e0b' },
      ]
      : [];

  const activityData = history.reduce((acc, item) => {
    // Fix: Use ISO string split to get YYYY-MM-DD
    const dateKey = new Date(item.created_at).toISOString().split('T')[0];
    acc[dateKey] = (acc[dateKey] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sortedDateKeys = Object.keys(activityData).sort((a, b) => {
    return new Date(a).getTime() - new Date(b).getTime();
  });

  const lineChartData = sortedDateKeys.map(dateKey => {
    const dateObj = new Date(dateKey);
    return {
      // Fix: Format using date-fns with ru locale
      day: format(dateObj, 'd MMM', { locale: ru }),
      predictions: activityData[dateKey],
    };
  });

  const formatDate = (dateString: string) =>
    formatDistanceToNow(new Date(dateString), { addSuffix: true, locale: ru });

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'real': return 'bg-green-100 text-green-800 border-green-400/50';
      case 'fake': return 'bg-red-100 text-red-800 border-red-400/50';
      case 'controversial': return 'bg-yellow-100 text-yellow-800 border-yellow-400/50';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getClassificationText = (classification: string) => {
    switch (classification) {
      case 'real': return 'Real';
      case 'fake': return 'Fake';
      case 'controversial': return 'Controversial';
      default: return 'Unknown';
    }
  };

  // ===== UI =====
  // Show skeleton if data is loading OR auth is still checking
  if (loading || authLoading) {
    // [ ... Skeleton UI remains the same ... ]
    return (
      <div className="p-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-16" />
            </CardHeader>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    // [ ... Error UI remains the same ... ]
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-10 text-center">
          <CardContent>
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl text-red-600 mb-2">
              Failed to load data
            </h2>
            <p className="text-slate-500">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-3xl text-slate-900 mb-6">{t('dashboard')}</h1>
        <p className="text-slate-600 mb-8">
          Welcome back, {user?.email || 'User'}
        </p>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <StatCard title="Total Checks" value={stats?.totalPredictions || 0} icon={<FileText className="h-4 w-4 text-blue-600" />} />
          <StatCard
            title="Avg. Confidence"
            value={`${stats?.avgConfidence || 0}%`}
            icon={<Target className="h-4 w-4 text-green-600" />} />

          <StatCard title="Real News" value={stats?.classifications.real || 0} icon={<CheckCircle className="h-4 w-4 text-green-600" />} />
          <StatCard title="Fake Detected" value={stats?.classifications.fake || 0} icon={<Shield className="h-4 w-4 text-red-600" />} />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
          <ChartCard title="Classification Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%" cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  dataKey="value"
                >
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Weekly Activity">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={lineChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="predictions" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Activity */}
        <ActivityCard
          history={history}
          getClassificationColor={getClassificationColor}
          getClassificationText={getClassificationText}
          formatDate={formatDate}
        />
      </div>
    </div>
  );
}

// [ ... Helper Components remain the same ... ]
function StatCard({ title, value, icon }: { title: string; value: number | string; icon: JSX.Element }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ActivityCard({ history, getClassificationColor, getClassificationText, formatDate }: any) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Activity className="h-5 w-5 mr-2" /> Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        {history.length > 0 ? (
          <motion.div className="space-y-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {history.slice(0, 5).map((item: any) => (
              <motion.div
                key={item.id}
                className="flex items-start justify-between p-4 bg-slate-50 rounded-lg"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="flex-1 overflow-hidden">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline" className={getClassificationColor(item.verdict)}>
                      {getClassificationText(item.verdict)}
                    </Badge>
                    <span className="text-sm text-slate-500">
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-sm text-slate-700 line-clamp-2">
                    {item.text.substring(0, 100)}...
                  </p>
                </div>
                <div className="flex items-center text-xs text-slate-500 ml-4">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatDate(item.created_at)}
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <div className="text-center text-slate-500 py-8">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No recent activity</p>
            <p className="text-sm">Start checking news to see your analysis history.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}