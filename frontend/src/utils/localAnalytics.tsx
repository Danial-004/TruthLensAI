// Local analytics for TruthLens - works entirely offline
interface PredictionRecord {
  id: string;
  text: string;
  classification: 'REAL' | 'FAKE' | 'UNCERTAIN';
  confidence: number;
  timestamp: string;
  language: string;
}

interface Analytics {
  totalPredictions: number;
  totalArticles: number;
  classifications: {
    fake: number;
    real: number;
    uncertain: number;
  };
  avgConfidence: number;
  recentActivity: PredictionRecord[];
}

export class LocalAnalytics {
  private static readonly STORAGE_KEY = 'truthlens_predictions';
  
  static savePrediction(prediction: PredictionRecord): void {
    try {
      const existing = this.getAllPredictions();
      const updated = [prediction, ...existing].slice(0, 100); // Keep only last 100
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to save prediction:', error);
    }
  }
  
  static getAllPredictions(): PredictionRecord[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Failed to load predictions:', error);
      return [];
    }
  }
  
  static getAnalytics(): Analytics {
    const predictions = this.getAllPredictions();
    
    const totalPredictions = predictions.length;
    const fakePredictions = predictions.filter(p => p.classification === 'FAKE').length;
    const realPredictions = predictions.filter(p => p.classification === 'REAL').length;
    const uncertainPredictions = predictions.filter(p => p.classification === 'UNCERTAIN').length;
    
    const avgConfidence = predictions.length > 0 
      ? Math.round(predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length)
      : 0;
    
    return {
      totalPredictions,
      totalArticles: 0, // Not using articles in offline mode
      classifications: {
        fake: fakePredictions,
        real: realPredictions,
        uncertain: uncertainPredictions
      },
      avgConfidence,
      recentActivity: predictions.slice(0, 10)
    };
  }
  
  static clearAll(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear predictions:', error);
    }
  }
  
  // Generate demo data for testing
  static generateDemoData(): void {
    const demoData: PredictionRecord[] = [
      {
        id: 'demo_1',
        text: 'According to research published in a peer-reviewed journal, scientists have made progress in renewable energy technology.',
        classification: 'REAL',
        confidence: 85,
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
        language: 'en'
      },
      {
        id: 'demo_2',
        text: 'Breaking: Unbelievable miracle cure discovered! This one weird trick will shock you!',
        classification: 'FAKE',
        confidence: 78,
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(), // 5 hours ago
        language: 'en'
      },
      {
        id: 'demo_3',
        text: 'Government officials announced new infrastructure projects today.',
        classification: 'REAL',
        confidence: 72,
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString(), // 8 hours ago
        language: 'en'
      },
      {
        id: 'demo_4',
        text: 'The weather was nice today. Some people went outside.',
        classification: 'UNCERTAIN',
        confidence: 60,
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(), // 12 hours ago
        language: 'en'
      },
      {
        id: 'demo_5',
        text: 'They don\'t want you to know this amazing secret that doctors hate!',
        classification: 'FAKE',
        confidence: 88,
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
        language: 'en'
      }
    ];
    
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(demoData));
  }
}