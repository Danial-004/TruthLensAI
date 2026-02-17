// Local news feed for TruthLens - curated content for demonstration
interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  source: string;
  author: string;
  published_at: string;
  language: string;
  category: string;
  image_url?: string;
}

export class LocalNewsFeed {
  private static readonly demoArticles: NewsArticle[] = [
    {
      id: 'article_1',
      title: 'New Renewable Energy Research Shows Promising Results',
      summary: 'Scientists at leading universities have published findings on improved solar panel efficiency.',
      content: 'According to research published in a peer-reviewed journal, scientists have made significant progress in renewable energy technology. The study, conducted over two years, shows promising results that could contribute to sustainable development goals.',
      source: 'Tech Research Today',
      author: 'Dr. Sarah Chen',
      published_at: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(), // 6 hours ago
      language: 'en',
      category: 'Technology',
      image_url: 'https://images.unsplash.com/photo-1466611653911-95081537e5b7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    },
    {
      id: 'article_2',
      title: 'Government Announces Infrastructure Investment Plan',
      summary: 'Officials outline comprehensive strategy for modernizing national transportation networks.',
      content: 'Government officials announced new infrastructure projects today. The ministry reported that construction will begin next quarter, according to the spokesperson who stated the budget has been approved by the committee. The plan includes roads, bridges, and public transit improvements.',
      source: 'National News Wire',
      author: 'Michael Rodriguez',
      published_at: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(), // 12 hours ago
      language: 'en',
      category: 'Politics',
      image_url: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    },
    {
      id: 'article_3',
      title: 'Climate Change Conference Reaches Historic Agreement',
      summary: 'International delegates agree on binding emissions targets for the next decade.',
      content: 'After weeks of negotiations, climate experts and government representatives have reached a consensus on new environmental policies. Data from multiple studies indicates the urgency of immediate action. Research shows that coordinated global efforts could significantly impact future outcomes.',
      source: 'Global Environment Report',
      author: 'Dr. Emma Thompson',
      published_at: new Date(Date.now() - 1000 * 60 * 60 * 18).toISOString(), // 18 hours ago
      language: 'en',
      category: 'Environment',
      image_url: 'https://images.unsplash.com/photo-1611273426858-450d8e3c9fce?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    },
    {
      id: 'article_4',
      title: 'Healthcare Innovation Breakthrough Announced',
      summary: 'Medical researchers develop new treatment approach with clinical trial success.',
      content: 'Healthcare professionals report significant advances in treatment methodologies. According to peer-reviewed studies, the new approach shows measurable improvements in patient outcomes. Multiple hospitals have confirmed the effectiveness through controlled trials.',
      source: 'Medical Science Journal',
      author: 'Dr. James Wilson',
      published_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
      language: 'en',
      category: 'Health',
      image_url: 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    },
    {
      id: 'article_5',
      title: 'Education Technology Transforms Learning Outcomes',
      summary: 'Schools report improved student engagement through innovative digital platforms.',
      content: 'Educational institutions are implementing new learning technologies with measurable success. Statistics show improved student performance across multiple metrics. Experts say the integration of digital tools has enhanced traditional teaching methods.',
      source: 'Education Weekly',
      author: 'Prof. Lisa Anderson',
      published_at: new Date(Date.now() - 1000 * 60 * 60 * 36).toISOString(), // 1.5 days ago
      language: 'en',
      category: 'Education',
      image_url: 'https://images.unsplash.com/photo-1509062522246-3755977927d7?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    },
    {
      id: 'article_6',
      title: 'Инновационные технологии в сфере транспорта',
      summary: 'Российские инженеры представили новые решения для городского транспорта.',
      content: 'Согласно исследованию, проведенному ведущими специалистами, новые транспортные технологии показывают значительные улучшения в эффективности. Данные показывают, что инновационные подходы могут существенно изменить городскую мобильность.',
      source: 'Техно Вести',
      author: 'Иван Петров',
      published_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // 2 days ago
      language: 'ru',
      category: 'Technology',
      image_url: 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    },
    {
      id: 'article_7',
      title: 'Қазақстанда жаңа ғылыми жобалар іске қосылды',
      summary: 'Ғалымдар отандық ғылым саласындағы жетістіктерді баяндады.',
      content: 'Зерттеу бойынша, мамандар айтуы бойынша, жаңа ғылыми әзірlemeler елдің технологиялық дамуына үлкен үлес қосуда. Деректер көрсетеді, ғылыми инновациялар болашақ дамуға ықпал етеді.',
      source: 'Ғылым Жаңалықтары',
      author: 'Айгүл Смағұлова',
      published_at: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(), // 3 days ago
      language: 'kz',
      category: 'Science',
      image_url: 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
    }
  ];

  static getArticles(language: string = 'all'): NewsArticle[] {
    if (language === 'all') {
      return [...this.demoArticles].sort((a, b) => 
        new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      );
    }
    
    return this.demoArticles
      .filter(article => article.language === language)
      .sort((a, b) => 
        new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      );
  }

  static getArticleById(id: string): NewsArticle | null {
    return this.demoArticles.find(article => article.id === id) || null;
  }

  static getCategories(): string[] {
    const categories = new Set(this.demoArticles.map(article => article.category));
    return Array.from(categories).sort();
  }

  static getLanguages(): Array<{ code: string; name: string }> {
    return [
      { code: 'all', name: 'All Languages' },
      { code: 'en', name: 'English' },
      { code: 'ru', name: 'Русский' },
      { code: 'kz', name: 'Қазақша' }
    ];
  }
}