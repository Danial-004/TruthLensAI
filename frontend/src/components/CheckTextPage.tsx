// src/components/CheckTextPage.tsx
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader, CheckCircle, XCircle, AlertTriangle, ThumbsUp, ThumbsDown, Zap } from 'lucide-react';
import { useTranslation } from '@/hooks/useTranslation'; // Импорт

// @ts-ignore
import VerificationTabs from './AnalysisContainer';

import { checkText, submitVote, DetailedAnalysisResult, getUserStatus, getGuestStatus } from '@/utils/factCheckingService';
import { useAuth } from '@/hooks/useAuth';

export function CheckTextPage() {
  const { t } = useTranslation(); // t() қосамыз
  const { user, logout } = useAuth();
  const [text, setText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<DetailedAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [voteStatus, setVoteStatus] = useState<'up' | 'down' | null>(null);
  const [isVoting, setIsVoting] = useState(false);
  const [limitInfo, setLimitInfo] = useState<{ used: number; limit: number } | null>(null);
  const [isLoadingLimit, setIsLoadingLimit] = useState(true);

  // Лимит жүктеу
  useEffect(() => {
    const fetchLimit = async () => {
      setIsLoadingLimit(true);
      setLimitInfo(null);
      setError(null);
      try {
        if (user) {
          const tk = localStorage.getItem('accessToken');
          if (!tk) { if (logout) logout(); throw new Error("Token not found"); }
          const data = await getUserStatus(tk);
          setLimitInfo({ used: data.requests_today, limit: data.daily_limit });
        } else {
          const data = await getGuestStatus();
          setLimitInfo({ used: data.requests_today, limit: data.daily_limit });
        }
      } catch (err) {
        console.error('Limit error:', err);
        setLimitInfo({ used: 0, limit: 0 });
      } finally {
        setIsLoadingLimit(false);
      }
    };
    fetchLimit();
  }, [user, logout]);

  // Анализ функциясы
  const handleAnalysis = async () => {
    // Ескерту: Бұл жерде логика AnalysisContainer ішінде жүреді,
    // бірақ егер осы компонент арқылы шақырылса:
    if (!user) { setError(t('signIn')); return; }
    if (isLoadingLimit) return;
    if (limitInfo && limitInfo.used >= limitInfo.limit) {
      setError(t('error')); // Немесе арнайы 'limitReached'
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);
    setVoteStatus(null);

    try {
      const res = await checkText(text);
      setResult(res);
      setLimitInfo(prev => prev ? { ...prev, used: prev.used + 1 } : null);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('errorOccurred'));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleVote = async (vote: 1 | -1) => {
    if (!result?.analysis_id || isVoting || voteStatus) return;
    setIsVoting(true);
    try {
      await submitVote(result.analysis_id, vote);
      setVoteStatus(vote === 1 ? 'up' : 'down');
    } catch (e) { console.error(e); } finally { setIsVoting(false); }
  };

  const getVerdictBadge = (verdict: 'real' | 'fake' | 'controversial') => {
    switch (verdict) {
      case 'real': return <Badge className="bg-green-600/90 text-white gap-2 px-3 py-1"><CheckCircle size={16} />{t('real')}</Badge>;
      case 'fake': return <Badge variant="destructive" className="gap-2 px-3 py-1"><XCircle size={16} />{t('fake')}</Badge>;
      case 'controversial': return <Badge className="bg-orange-500/90 text-white gap-2 px-3 py-1"><AlertTriangle size={16} />{t('uncertain')}</Badge>;
      default: return <Badge variant="secondary">{t('uncertain')}</Badge>;
    }
  };

  const limitUsedPercent = limitInfo && limitInfo.limit > 0 ? (limitInfo.used / limitInfo.limit) * 100 : 0;

  return (
    <div
      className="min-h-screen w-full p-4 sm:p-8 text-slate-100"
      style={{
        backgroundColor: '#0f172a',
        backgroundImage: 'radial-gradient(#334155 1px, transparent 1px)',
        backgroundSize: '24px 24px'
      }}
    >
      <div className="max-w-4xl mx-auto space-y-8 relative z-10">

        {/* --- ЛИМИТ --- */}
        {!isLoadingLimit && limitInfo && (
          <Card className="border border-white/10 bg-slate-900/40 backdrop-blur-md shadow-xl">
            <CardContent className="p-4">
              <div className="flex justify-between items-center mb-2">
                <p className="text-sm font-medium flex items-center gap-2 text-slate-300">
                  <Zap size={18} className="text-yellow-400" /> {t('limitLabel')} {user ? t('user') : t('guest')}
                </p>
                <p className="text-sm font-mono text-white">{limitInfo.limit > 0 ? `${limitInfo.used}/${limitInfo.limit}` : 'N/A'}</p>
              </div>
              {limitInfo.limit > 0 && <Progress value={limitUsedPercent} className="h-1.5 bg-slate-700" />}
            </CardContent>
          </Card>
        )}

        {/* --- НЕГІЗГІ ТЕКСЕРУ --- */}
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>

          <Card className="relative border border-white/10 bg-slate-900/60 backdrop-blur-xl shadow-2xl overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-50" />

            <CardContent className="p-6 sm:p-10">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300">
                  {t('checkText')} {/* "Проверка достоверности" аударылды */}
                </h2>
                <p className="text-slate-400 mt-2">{t('aiAnalysisDesc')}</p>
              </div>

              <div className="
                        [&_.bg-card]:!bg-transparent 
                        [&_.bg-background]:!bg-transparent 
                        [&_.bg-slate-950]:!bg-transparent 
                        [&_.shadow-sm]:!shadow-none 
                        [&_.border]:!border-none
                        [&_textarea]:!bg-slate-800/40 [&_textarea]:!border-white/10 [&_textarea]:!text-white [&_textarea]:!backdrop-blur-sm
                        [&_input]:!bg-slate-800/40 [&_input]:!border-white/10 [&_input]:!text-white [&_input]:!backdrop-blur-sm
                        [&_div[role=tablist]]:!bg-slate-800/40 [&_div[role=tablist]]:!border-white/5
                    ">
                <VerificationTabs />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* --- НӘТИЖЕ (RESULT) --- */}
        <AnimatePresence>
          {result && !isAnalyzing && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <Card className="border border-white/10 bg-slate-900/80 backdrop-blur-md shadow-2xl">
                <CardHeader className="flex flex-row justify-between items-center pb-2 border-b border-white/5">
                  <CardTitle className="text-lg text-white">{t('verdict')}</CardTitle>
                  {getVerdictBadge(result.verdict)}
                </CardHeader>
                <CardContent className="pt-6 space-y-6">
                  {/* Бағалау */}
                  <div>
                    <div className="flex justify-between text-sm mb-2 text-slate-300">
                      <span>{t('confidence')}</span>
                      <span className="font-mono">{Math.round(result.confidence * 100)}%</span>
                    </div>
                    <Progress value={result.confidence * 100} className={`h-2 ${result.verdict === 'real' ? 'bg-green-900' : 'bg-red-900'}`} />
                  </div>

                  {/* Түсіндірме */}
                  <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                    <h4 className="font-semibold text-blue-300 mb-2">{t('explanation')}</h4>
                    <p className="text-slate-300 leading-relaxed text-sm">{result.detailed_explanation}</p>
                  </div>

                  {/* Источники */}
                  {result.sources && result.sources.length > 0 && (
                    <div className="grid gap-3 sm:grid-cols-2">
                      {result.sources.map((s, i) => (
                        <a key={i} href={s.url} target="_blank" rel="noopener" className="block p-3 rounded bg-slate-800/30 border border-white/5 hover:bg-slate-800/80 transition text-xs">
                          <p className="font-medium text-cyan-400 truncate">{s.title}</p>
                          <p className="text-slate-500 truncate mt-1">{s.url}</p>
                        </a>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Дауыс беру */}
              {user && result.analysis_id && (
                <div className="flex justify-center gap-4 py-4">
                  <Button variant="ghost" size="sm" onClick={() => handleVote(1)} className={`text-slate-400 hover:text-green-400 hover:bg-green-500/10 ${voteStatus === 'up' ? 'text-green-400 bg-green-500/10' : ''}`}>
                    <ThumbsUp className="mr-2 h-4 w-4" /> {t('helpful')}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleVote(-1)} className={`text-slate-400 hover:text-red-400 hover:bg-red-500/10 ${voteStatus === 'down' ? 'text-red-400 bg-red-500/10' : ''}`}>
                    <ThumbsDown className="mr-2 h-4 w-4" /> {t('notHelpful')}
                  </Button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}