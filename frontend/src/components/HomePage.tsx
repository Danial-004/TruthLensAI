import { useState } from 'react';
import { Search, Shield, Zap, Globe, ArrowRight, CheckCircle, AlertTriangle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Textarea } from './ui/textarea';
import { useTranslation } from '../hooks/useTranslation';

type Page = 'home' | 'check' | 'feed' | 'dashboard' | 'admin' | 'login' | 'signup' | 'test';

interface HomePageProps {
  onNavigate: (page: Page, params?: Record<string, string>) => void;
  params?: Record<string, string>;
}

export function HomePage({ onNavigate }: HomePageProps) {
  const { t } = useTranslation();
  const [demoText, setDemoText] = useState('');

  const features = [
    {
      icon: <Shield className="h-8 w-8 text-blue-600" />,
      title: t('feature1Title'),
      description: t('feature1Desc'),
    },
    {
      icon: <Globe className="h-8 w-8 text-teal-600" />,
      title: t('feature2Title'),
      description: t('feature2Desc'),
    },
    {
      icon: <Zap className="h-8 w-8 text-purple-600" />,
      title: t('feature3Title'),
      description: t('feature3Desc'),
    },
  ];

  const handleDemoAnalysis = () => {
    if (demoText.trim()) {
      onNavigate('check');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-teal-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-grid-slate-100 dark:bg-grid-slate-700/25 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]" />

        <div className="relative max-w-7xl mx-auto">
          <div className="text-center">
            <div className="flex justify-center mb-8">
              <div className="bg-gradient-to-br from-blue-600 to-teal-600 p-4 rounded-2xl shadow-lg">
                <Shield className="h-16 w-16 text-white" />
              </div>
            </div>

            <h1 className="text-4xl sm:text-6xl lg:text-7xl tracking-tight mb-6">
              <span className="block text-slate-900 dark:text-white">{t('heroTitle')}</span>
              <span className="block bg-gradient-to-r from-blue-600 via-teal-600 to-purple-600 bg-clip-text text-transparent">
                {t('appName')}
              </span>
            </h1>

            <p className="max-w-3xl mx-auto text-xl text-slate-600 dark:text-slate-300 mb-12">
              {t('heroSubtitle')}
            </p>

            {/* Demo Text Input */}
            <div className="max-w-2xl mx-auto mb-8">
              <Card className="p-6 shadow-2xl bg-white/80 dark:bg-slate-800/80 backdrop-blur border-0">
                <CardContent className="p-0">
                  <Textarea
                    placeholder={t('pasteText')}
                    value={demoText}
                    onChange={(e) => setDemoText(e.target.value)}
                    className="min-h-[120px] border-0 bg-transparent text-lg resize-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                  />
                  <div className="space-y-3">
                    {/* Quick Demo Buttons */}
                    <div className="flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setDemoText("BREAKING: Scientists discover miracle cure that doctors don't want you to know about! This shocking secret will change everything!")}
                      >
                        Try Fake Example
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setDemoText("According to a recent study published in Nature, researchers at Stanford University have developed a new renewable energy technology. The peer-reviewed research shows promising results.")}
                      >
                        Try Real Example
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setDemoText("Срочно! Невероятная сенсация потрясла мир! Ученые скрывают правду об этом открытии!")}
                      >
                        Try Russian
                      </Button>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-500 dark:text-slate-400">
                        {demoText.length} characters
                      </span>
                      <Button
                        onClick={handleDemoAnalysis}
                        disabled={!demoText.trim()}
                        className="bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700"
                      >
                        <Search className="h-4 w-4 mr-2" />
                        {t('analyzeText')}
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => onNavigate('check')}
                className="bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white px-8 py-3"
              >
                {t('getStarted')}
                <ArrowRight className="h-5 w-5 ml-2" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => onNavigate('feed')}
                className="border-2 border-blue-200 dark:border-blue-800 hover:bg-blue-50 dark:hover:bg-blue-900/30 px-8 py-3"
              >
                {t('newsFeed')}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white/50 dark:bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl text-slate-900 dark:text-white mb-4">
              {t('featuresTitle')}
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
              {t('featuresDesc')}
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-8 hover:shadow-xl transition-all duration-300 border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur">
                <CardContent className="p-0">
                  <div className="mb-6">{feature.icon}</div>
                  <h3 className="text-xl text-slate-900 dark:text-white mb-4">{feature.title}</h3>
                  <p className="text-slate-600 dark:text-slate-300">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Results Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl text-slate-900 dark:text-white mb-4">
              {t('actionTitle')}
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300">
              {t('actionDesc')}
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Fake News Example - Бұлар демо болғандықтан, ағылшынша қала бергені дұрыс немесе бөлек аударма қажет */}
            <Card className="p-6 border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-900/20">
              <CardContent className="p-0">
                <div className="flex items-center mb-4">
                  <AlertTriangle className="h-6 w-6 text-red-600 mr-2" />
                  <span className="bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200 px-3 py-1 rounded-full text-sm">
                    FAKE - 89% Confidence
                  </span>
                </div>
                <p className="text-slate-700 dark:text-slate-300 mb-4 italic">
                  "Scientists discover cure for all diseases in secret laboratory..."
                </p>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  <p className="mb-2"><strong>Key issues detected:</strong></p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Extraordinary claims without scientific evidence</li>
                    <li>No credible source citations</li>
                    <li>Sensationalist language patterns</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Real News Example */}
            <Card className="p-6 border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/20">
              <CardContent className="p-0">
                <div className="flex items-center mb-4">
                  <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
                  <span className="bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-200 px-3 py-1 rounded-full text-sm">
                    REAL - 85% Confidence
                  </span>
                </div>
                <p className="text-slate-700 dark:text-slate-300 mb-4 italic">
                  "New renewable energy project announced by government, construction to begin next year..."
                </p>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  <p className="mb-2"><strong>AI found verification from:</strong></p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>tengrinews.kz - Official announcement</li>
                    <li>kazinform.kz - Government confirmation</li>
                    <li>Multiple credible news outlets</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-teal-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl text-white mb-6">
            {t('ctaTitle')}
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            {t('ctaDesc')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              variant="secondary"
              onClick={() => onNavigate('signup')}
              className="bg-white text-blue-600 hover:bg-blue-50 px-8 py-3"
            >
              {t('btnSignUp')}
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => onNavigate('check')}
              className="border-2 border-white text-white hover:bg-white/10 px-8 py-3"
            >
              {t('btnDemo')}
            </Button>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20 border-t-4 border-blue-400">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-blue-800 dark:text-blue-200">
            ⚡ <strong>{t('disclaimer')}</strong> {t('disclaimerText')}
          </p>
        </div>
      </section>
    </div>
  );
}