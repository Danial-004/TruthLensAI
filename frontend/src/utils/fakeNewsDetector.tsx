// Client-side fake news detection utility
// This provides a robust fallback when server functions are unavailable

export interface DetectionResult {
  id: string;
  classification: "REAL" | "FAKE" | "UNCERTAIN";
  confidence: number;
  explanation: {
    reasoning: string;
    keywords: string[];
    sources: string[];
  };
  language: string;
  model: string;
}

export class FakeNewsDetector {
  private static instance: FakeNewsDetector;

  static getInstance(): FakeNewsDetector {
    if (!FakeNewsDetector.instance) {
      FakeNewsDetector.instance = new FakeNewsDetector();
    }
    return FakeNewsDetector.instance;
  }

  async predict(
    text: string,
    language?: string,
  ): Promise<DetectionResult> {
    const detectedLanguage =
      language || this.detectLanguage(text);
    const result = this.analyzeContent(text, detectedLanguage);

    return {
      id: `pred_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      classification: result.classification,
      confidence: result.confidence,
      explanation: {
        reasoning: result.reasoning,
        keywords: this.extractKeywords(text),
        sources: result.sources,
      },
      language: detectedLanguage,
      model: "enhanced-client-heuristic",
    };
  }

  private analyzeContent(text: string, language: string) {
    const lowerText = text.toLowerCase();
    const analysis = this.getLanguageSpecificAnalysis(
      lowerText,
      language,
    );

    // Enhanced scoring system
    let credibilityScore = 0;
    let suspicionScore = 0;
    let neutralScore = 0;

    // Check for high-confidence fake indicators
    analysis.strongFakeIndicators.forEach((indicator) => {
      if (lowerText.includes(indicator)) {
        suspicionScore += 3;
      }
    });

    // Check for sensational language
    analysis.sensationalIndicators.forEach((indicator) => {
      if (lowerText.includes(indicator)) {
        suspicionScore += 1.5;
      }
    });

    // Check for credible journalism patterns
    analysis.credibilityIndicators.forEach((indicator) => {
      if (lowerText.includes(indicator)) {
        credibilityScore += 2.5;
      }
    });

    // Check for professional language
    analysis.professionalIndicators.forEach((indicator) => {
      if (lowerText.includes(indicator)) {
        credibilityScore += 1.5;
      }
    });

    // Structural analysis
    const structure = this.analyzeStructure(text);
    credibilityScore += structure.credibilityBonus;
    suspicionScore += structure.suspicionPenalty;
    neutralScore += structure.neutralScore;

    // Content quality analysis
    const quality = this.analyzeContentQuality(text);
    credibilityScore += quality.qualityScore;

    // Language-specific adjustments
    const langAdjustment = this.getLanguageAdjustment(
      text,
      language,
    );
    credibilityScore += langAdjustment.credibilityBonus;
    suspicionScore += langAdjustment.suspicionBonus;

    // Final classification logic
    return this.determineClassification(
      credibilityScore,
      suspicionScore,
      neutralScore,
      text,
    );
  }

  private getLanguageSpecificAnalysis(
    text: string,
    language: string,
  ) {
    const commonAnalysis = {
      strongFakeIndicators: [
        "miracle cure",
        "doctors hate this",
        "one weird trick",
        "shocking discovery",
        "they don't want you to know",
        "secret the government",
        "banned by authorities",
        "click here now",
        "limited time offer",
        "too good to be true",
        "you won't believe",
        "mind-blowing secret",
        "revolutionary breakthrough",
      ],
      sensationalIndicators: [
        "unbelievable",
        "shocking",
        "incredible",
        "amazing",
        "stunning",
        "mind-blowing",
        "life-changing",
        "revolutionary",
        "explosive",
        "bombshell",
        "earth-shattering",
        "game-changing",
      ],
      credibilityIndicators: [
        "according to research",
        "study published in",
        "peer-reviewed",
        "data from",
        "statistics show",
        "experts say",
        "research indicates",
        "analysis reveals",
        "survey found",
        "report shows",
        "verified by",
      ],
      professionalIndicators: [
        "officials said",
        "spokesperson stated",
        "government announced",
        "ministry reported",
        "committee decided",
        "board approved",
        "researchers found",
        "scientists discovered",
        "experts confirmed",
      ],
    };

    // Add language-specific indicators
    if (language === "ru") {
      return {
        ...commonAnalysis,
        strongFakeIndicators: [
          ...commonAnalysis.strongFakeIndicators,
          "чудодейственное средство",
          "врачи ненавидят",
          "скрывают от вас",
          "секретный метод",
          "запрещено властями",
          "сенсационное открытие",
        ],
        credibilityIndicators: [
          ...commonAnalysis.credibilityIndicators,
          "согласно исследованию",
          "опубликовано в журнале",
          "данные показывают",
          "эксперты подтверждают",
          "проверено источниками",
          "официальные данные",
        ],
        professionalIndicators: [
          ...commonAnalysis.professionalIndicators,
          "чиновники сообщили",
          "представитель заявил",
          "министерство объявило",
          "комитет принял решение",
          "совет утвердил",
        ],
      };
    }

    if (language === "kz") {
      return {
        ...commonAnalysis,
        strongFakeIndicators: [
          ...commonAnalysis.strongFakeIndicators,
          "қасиетті дәрі",
          "дәрігерлер жасырады",
          "жасырын ақпарат",
          "сенсациялық ашылу",
          "билік тыйым салған",
        ],
        credibilityIndicators: [
          ...commonAnalysis.credibilityIndicators,
          "зерттеу бойынша",
          "мамандар растады",
          "көпжылдық зерттеу",
          "ресми деректер",
          "тексерілген ақпарат",
        ],
        professionalIndicators: [
          ...commonAnalysis.professionalIndicators,
          "ресми мәлімдеме",
          "үкімет хабарлады",
          "комитет шешті",
          "кеңес мақұлдады",
          "министрлік жариялады",
        ],
      };
    }

    return commonAnalysis;
  }

  private analyzeStructure(text: string) {
    const sentences = text
      .split(/[.!?]+/)
      .filter((s) => s.trim().length > 0);
    const words = text.split(/\s+/).filter((w) => w.length > 0);
    const exclamationCount = (text.match(/!/g) || []).length;
    const capsWords = words.filter(
      (word) => word === word.toUpperCase() && word.length > 2,
    );
    const questionCount = (text.match(/\?/g) || []).length;

    let credibilityBonus = 0;
    let suspicionPenalty = 0;
    let neutralScore = 0;

    // Well-structured content indicators
    if (sentences.length >= 3 && words.length >= 50) {
      credibilityBonus += 1;
    }

    if (sentences.length >= 5 && words.length >= 100) {
      credibilityBonus += 0.5;
    }

    // Suspicious structure indicators
    if (
      exclamationCount > Math.max(3, sentences.length * 0.3)
    ) {
      suspicionPenalty += 1.5;
    }

    if (capsWords.length > words.length * 0.1) {
      suspicionPenalty += 1;
    }

    if (questionCount > sentences.length * 0.4) {
      suspicionPenalty += 0.5;
    }

    // Neutral content (neither good nor bad indicators)
    if (
      sentences.length >= 2 &&
      exclamationCount <= 1 &&
      capsWords.length === 0
    ) {
      neutralScore += 1;
    }

    return { credibilityBonus, suspicionPenalty, neutralScore };
  }

  private analyzeContentQuality(text: string) {
    let qualityScore = 0;

    // Check for URLs (suggests references)
    if (/https?:\/\//.test(text) || /www\./.test(text)) {
      qualityScore += 0.5;
    }

    // Check for date references (suggests current reporting)
    if (
      /\d{4}|\d{1,2}\/\d{1,2}|january|february|march|april|may|june|july|august|september|october|november|december/i.test(
        text,
      )
    ) {
      qualityScore += 0.3;
    }

    // Check for numbers and statistics
    if (/\d+%|\d+\.\d+|\d+,\d+/.test(text)) {
      qualityScore += 0.3;
    }

    // Check for proper nouns (names, places)
    const properNounCount = (
      text.match(/\b[A-Z][a-z]+\b/g) || []
    ).length;
    if (properNounCount >= 3) {
      qualityScore += 0.4;
    }

    return { qualityScore };
  }

  private getLanguageAdjustment(
    text: string,
    language: string,
  ) {
    let credibilityBonus = 0;
    let suspicionBonus = 0;

    // Language-specific patterns
    if (language === "en") {
      // English tends to have more formal structure
      if (
        /\b(according to|research|study|analysis)\b/i.test(text)
      ) {
        credibilityBonus += 0.3;
      }
    }

    return { credibilityBonus, suspicionBonus };
  }

  private determineClassification(
    credibilityScore: number,
    suspicionScore: number,
    neutralScore: number,
    text: string,
  ) {
    const totalScore = credibilityScore - suspicionScore;
    let classification: "REAL" | "FAKE" | "UNCERTAIN" =
      "UNCERTAIN";
    let confidence = 50;
    let reasoning = "";

    if (suspicionScore >= 3 && totalScore < -1) {
      classification = "FAKE";
      confidence = Math.min(90, 55 + suspicionScore * 8);
      reasoning =
        confidence > 80
          ? "Content contains strong indicators of misinformation including sensational language, unverifiable claims, and typical fake news patterns. Multiple red flags detected."
          : "Content shows several characteristics commonly found in unreliable sources. Consider verifying with trusted news outlets.";
    } else if (credibilityScore >= 3 && totalScore > 1) {
      classification = "REAL";
      confidence = Math.min(90, 55 + credibilityScore * 8);
      reasoning =
        confidence > 80
          ? "Content demonstrates strong characteristics of credible journalism including professional language, verifiable information, proper sourcing, and structured reporting."
          : "Content appears to follow journalistic standards and shows signs of credible reporting, but additional verification is recommended.";
    } else if (
      suspicionScore > credibilityScore &&
      suspicionScore >= 1.5
    ) {
      classification = "FAKE";
      confidence = Math.min(75, 50 + suspicionScore * 6);
      reasoning =
        "Content contains some indicators commonly associated with unreliable sources. Exercise caution and verify with trusted sources.";
    } else if (
      credibilityScore > suspicionScore &&
      credibilityScore >= 1.5
    ) {
      classification = "REAL";
      confidence = Math.min(75, 50 + credibilityScore * 6);
      reasoning =
        "Content shows some positive indicators of reliable reporting but would benefit from additional source verification.";
    } else {
      classification = "UNCERTAIN";
      confidence =
        50 + Math.max(0, Math.min(15, neutralScore * 5));
      reasoning =
        "Content analysis is inconclusive. The text contains mixed signals or insufficient distinctive markers for confident classification. Manual verification recommended.";
    }

    // Add context about the analysis method
    reasoning +=
      " (Analysis based on linguistic patterns, content structure, and credibility indicators)";

    return {
      classification,
      confidence: Math.round(confidence),
      reasoning,
      sources: this.generateSources(classification),
    };
  }

  private generateSources(classification: string): string[] {
    const sources = [];

    if (classification === "FAKE") {
      sources.push(
        "Fact-checking recommended: Snopes.com",
        "Cross-reference with: PolitiFact.org",
        "Verify with trusted news sources",
      );
    } else if (classification === "REAL") {
      sources.push(
        "Consider cross-referencing with multiple sources",
        "Check original source publication",
        "Verify publication date and context",
      );
    } else {
      sources.push(
        "Manual fact-checking recommended",
        "Cross-reference with trusted news sources",
        "Look for original source citations",
      );
    }

    return sources;
  }

  private extractKeywords(text: string): string[] {
    const words = text
      .toLowerCase()
      .replace(/[^\w\s\u0400-\u04FF\u0590-\u05FF]/g, "") // Keep alphanumeric, Cyrillic, and Hebrew
      .split(/\s+/)
      .filter((word) => word.length > 3)
      .filter((word) => !this.isStopWord(word));

    // Simple frequency analysis
    const wordCount: { [key: string]: number } = {};
    words.forEach((word) => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });

    return Object.entries(wordCount)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 6)
      .map(([word]) => word);
  }

  private isStopWord(word: string): boolean {
    const stopWords = new Set([
      "this",
      "that",
      "with",
      "have",
      "will",
      "from",
      "they",
      "been",
      "said",
      "each",
      "which",
      "their",
      "time",
      "would",
      "there",
      "what",
      "about",
      "если",
      "этот",
      "были",
      "есть",
      "или",
      "также",
      "может",
      "когда",
      "егер",
      "осы",
      "болды",
      "бар",
      "немесе",
      "сондай",
      "мүмкін",
      "қашан",
    ]);
    return stopWords.has(word);
  }

  detectLanguage(text: string): string {
    const cyrillicPattern = /[а-яё]/i;
    const kazakhPattern = /[әғіңөүұқһ]/i;

    if (kazakhPattern.test(text)) return "kz";
    if (cyrillicPattern.test(text)) return "ru";
    return "en";
  }
}