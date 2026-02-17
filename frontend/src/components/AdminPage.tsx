import { useState, useEffect } from 'react';
import { Users, Database, Settings, Activity, RefreshCw, Shield, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Skeleton } from './ui/skeleton';
import { useTranslation } from '../hooks/useTranslation';
import { useAuth } from '../hooks/useAuth';
import { LocalAnalytics } from '../utils/localAnalytics';

interface AdminStats {
  totalPredictions: number;
  totalArticles: number;
  classifications: {
    fake: number;
    real: number;
    uncertain: number;
  };
  avgConfidence: number;
  recentActivity: any[];
}

export function AdminPage() {
  const { t } = useTranslation();
  const { user, session } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    if (session && user?.user_metadata?.role === 'admin') {
      fetchAdminStats();
    }
  }, [session, user]);

  const fetchAdminStats = async () => {
    setLoading(true);
    try {
      const analytics = LocalAnalytics.getAnalytics();
      setStats(analytics);
    } catch (error) {
      console.error('Failed to fetch admin stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeDemoData = async () => {
    setActionLoading('demo');
    try {
      LocalAnalytics.generateDemoData();
      await fetchAdminStats();
    } catch (error) {
      console.error('Failed to initialize demo data:', error);
    } finally {
      setActionLoading(null);
    }
  };

  if (!user || user.user_metadata?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Card className="p-8">
            <CardContent>
              <Shield className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <h2 className="text-xl text-slate-600 dark:text-slate-400 mb-2">
                Access Denied
              </h2>
              <p className="text-slate-500 dark:text-slate-500">
                You need administrator privileges to access this page.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl text-slate-900 dark:text-white mb-4">
            {t('admin')} Dashboard
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300">
            System management and analytics
          </p>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="sources">Sources</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[...Array(4)].map((_, index) => (
                  <Card key={index}>
                    <CardHeader className="pb-3">
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-8 w-16" />
                    </CardHeader>
                  </Card>
                ))}
              </div>
            ) : (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm">Total Predictions</CardTitle>
                      <Activity className="h-4 w-4 text-blue-600" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl">{stats?.totalPredictions || 0}</div>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        +12% from last week
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm">Articles Analyzed</CardTitle>
                      <Database className="h-4 w-4 text-green-600" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl">{stats?.totalArticles || 0}</div>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        From trusted sources
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm">Fake News Detected</CardTitle>
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl text-red-600">
                        {stats?.classifications.fake || 0}
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        Flagged as false
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm">System Accuracy</CardTitle>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl text-green-600">
                        {stats?.avgConfidence || 0}%
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        Average confidence
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Classification Breakdown */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <Card className="border-green-200 dark:border-green-800">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg flex items-center">
                        <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                        Real News
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl text-green-600 mb-2">
                        {stats?.classifications.real || 0}
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Verified as authentic
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="border-red-200 dark:border-red-800">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg flex items-center">
                        <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                        Fake News
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl text-red-600 mb-2">
                        {stats?.classifications.fake || 0}
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Flagged as false
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="border-yellow-200 dark:border-yellow-800">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg flex items-center">
                        <Clock className="h-5 w-5 text-yellow-600 mr-2" />
                        Uncertain
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl text-yellow-600 mb-2">
                        {stats?.classifications.uncertain || 0}
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Requires review
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Recent Activity */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="flex items-center">
                        <Activity className="h-5 w-5 mr-2" />
                        Recent System Activity
                      </span>
                      <Button variant="outline" size="sm" onClick={fetchAdminStats}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refresh
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {stats?.recentActivity?.length ? (
                      <div className="space-y-3">
                        {stats.recentActivity.slice(0, 5).map((activity, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                            <div className="flex items-center space-x-3">
                              <div className="w-2 h-2 bg-blue-500 rounded-full" />
                              <span className="text-sm">
                                Text analyzed: {activity.classification}
                              </span>
                            </div>
                            <Badge variant="outline">
                              {activity.confidence}% confidence
                            </Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center text-slate-500 dark:text-slate-400 py-8">
                        <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No recent activity</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Users className="h-5 w-5 mr-2" />
                  User Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Alert>
                  <Users className="h-4 w-4" />
                  <AlertDescription>
                    User management features are coming soon. Currently using Supabase Auth for user handling.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sources Tab */}
          <TabsContent value="sources" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Database className="h-5 w-5 mr-2" />
                  News Sources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { name: 'Tengri News', domain: 'tengrinews.kz', status: 'active', language: 'KZ' },
                    { name: 'Egemen Kazakhstan', domain: 'egemen.kz', status: 'active', language: 'KZ' },
                    { name: 'BBC News', domain: 'bbc.com', status: 'active', language: 'EN' },
                    { name: 'RT Russia', domain: 'rt.com', status: 'monitoring', language: 'RU' }
                  ].map((source, index) => (
                    <div key={index} className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{source.name}</h4>
                        <Badge variant={source.status === 'active' ? 'default' : 'secondary'}>
                          {source.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                        {source.domain}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {source.language}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  System Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <Button 
                    onClick={initializeDemoData}
                    disabled={actionLoading === 'demo'}
                    className="w-full sm:w-auto"
                  >
                    {actionLoading === 'demo' ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Initializing...
                      </>
                    ) : (
                      <>
                        <Database className="h-4 w-4 mr-2" />
                        Initialize Demo Data
                      </>
                    )}
                  </Button>
                  
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      This will populate the system with sample articles and predictions for demonstration purposes.
                    </AlertDescription>
                  </Alert>
                </div>

                <div className="pt-6 border-t border-slate-200 dark:border-slate-700">
                  <h4 className="text-sm font-medium mb-4">ML Model Configuration</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Primary Model:</span>
                      <Badge>facebook/bart-large-mnli</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Confidence Threshold:</span>
                      <Badge variant="outline">70%</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Languages Supported:</span>
                      <div className="flex space-x-1">
                        <Badge variant="outline" className="text-xs">EN</Badge>
                        <Badge variant="outline" className="text-xs">RU</Badge>
                        <Badge variant="outline" className="text-xs">KZ</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}