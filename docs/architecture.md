# TruthLens AI - System Architecture

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                     (Frontend - HTML/JS)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   API       │  │   Auth       │  │   Logging    │      │
│  │  Endpoints  │  │  Middleware  │  │   System     │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└──────────┬────────────────┬────────────────┬───────────────┘
           │                │                │
           ▼                ▼                ▼
  ┌────────────────┐ ┌─────────────┐ ┌──────────────┐
  │   ML Model     │ │  Database   │ │ Web Search   │
  │   (PyTorch)    │ │  (SQLite)   │ │  API Client  │
  └────────────────┘ └─────────────┘ └──────────────┘
           │                                  │
           ▼                                  ▼
  ┌────────────────┐                ┌──────────────┐
  │ Transformers   │                │  SerpAPI/    │
  │  XLM-RoBERTa   │                │  Bing API    │
  └────────────────┘                └──────────────┘
```

---

## 🏗️ Component Architecture

### 1. Frontend Layer

**Technology**: HTML5, TailwindCSS, Vanilla JavaScript

**Components**:
```
frontend/
├── index.html          # Main UI with all pages
├── script.js          # JavaScript logic (embedded)
└── style.css          # Custom styles (embedded)
```

**Responsibilities**:
- User interface rendering
- Input validation
- API communication
- Result visualization
- History management (localStorage)
- Dark/light mode
- Language switching

**Key Features**:
- Single Page Application (SPA) pattern
- Responsive design (mobile-first)
- Real-time feedback
- Loading states
- Error handling

---

### 2. Backend Layer

**Technology**: FastAPI, Python 3.9+, Uvicorn

**Structure**:
```
backend/
├── app.py             # Main FastAPI application
├── model.py           # ML inference engine
├── search_api.py      # Web search integration
├── database.py        # Data persistence
└── utils.py           # Helper functions
```

**API Endpoints**:
```python
POST   /analyze        # Main analysis endpoint
GET    /health         # Health check
GET    /history        # User history
POST   /feedback       # Submit feedback
GET    /stats          # System statistics
GET    /docs           # API documentation
```

**Responsibilities**:
- Request routing
- Input validation (Pydantic)
- Business logic coordination
- Error handling
- Response formatting
- Logging

---

### 3. ML Model Layer

**Technology**: PyTorch, Transformers, Sentence-Transformers

**Architecture**:
```
┌─────────────────────────────────────────┐
│          FakeNewsDetector               │
├─────────────────────────────────────────┤
│  1. Text Preprocessing                  │
│     - Cleaning                          │
│     - Normalization                     │
│     - Language detection                │
├─────────────────────────────────────────┤
│  2. Tokenization                        │
│     - XLM-RoBERTa Tokenizer            │
│     - Max length: 512 tokens           │
├─────────────────────────────────────────┤
│  3. Model Inference                     │
│     - Forward pass                      │
│     - Softmax activation               │
│     - Confidence calculation           │
├─────────────────────────────────────────┤
│  4. Feature Extraction                  │
│     - Keyword extraction               │
│     - Attention weights                │
│     - Embedding generation             │
├─────────────────────────────────────────┤
│  5. Post-processing                     │
│     - Label mapping                     │
│     - Explanation generation           │
│     - Result formatting                │
└─────────────────────────────────────────┘
```

**Models Used**:
- **Classification**: `xlm-roberta-base` (500MB)
  - Input: Text (any language)
  - Output: Fake/Real + Confidence
  
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (80MB)
  - Input: Text or query
  - Output: 384-dim vector
  - Use: Semantic similarity

**Inference Pipeline**:
```python
Input Text
    ↓
Language Detection (langdetect)
    ↓
Text Cleaning (regex, normalization)
    ↓
Tokenization (XLM-RoBERTa tokenizer)
    ↓
Model Forward Pass (PyTorch)
    ↓
Softmax & Confidence Calculation
    ↓
Keyword Extraction (TF-IDF)
    ↓
Result Assembly
    ↓
Output JSON
```

---

### 4. Search Integration Layer

**Technology**: REST API clients, BeautifulSoup

**Supported APIs**:
1. **SerpAPI** (Primary)
   - 100 free requests/month
   - Best quality results
   
2. **Bing Search API** (Secondary)
   - Microsoft Azure required
   - Good coverage
   
3. **Fallback** (Demo mode)
   - Mock results
   - No API key needed

**Search Pipeline**:
```
User Query
    ↓
Extract Keywords
    ↓
API Call (SerpAPI/Bing)
    ↓
Parse Results (title, URL, snippet)
    ↓
Semantic Similarity Scoring
    ↓
Rank by Relevance
    ↓
Filter by Trustworthiness
    ↓
Return Top 5 Sources
```

**Source Ranking Algorithm**:
```python
relevance_score = 
    0.6 * semantic_similarity +
    0.3 * source_trustworthiness +
    0.1 * freshness
```

---

### 5. Database Layer

**Technology**: SQLite (development), PostgreSQL-ready

**Schema**:
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analyses table
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    text TEXT NOT NULL,
    text_hash TEXT NOT NULL,  -- For caching
    classification TEXT NOT NULL,
    confidence REAL NOT NULL,
    language TEXT NOT NULL,
    explanation TEXT,
    sources TEXT,  -- JSON
    keywords TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback table
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    analysis_id INTEGER NOT NULL,
    user_id TEXT,
    rating TEXT NOT NULL,  -- 'up' or 'down'
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Statistics table
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_analyses INTEGER DEFAULT 0,
    fake_count INTEGER DEFAULT 0,
    real_count INTEGER DEFAULT 0,
    avg_confidence REAL DEFAULT 0,
    unique_users INTEGER DEFAULT 0
);
```

**Caching Strategy**:
- Cache key: MD5 hash of cleaned text
- TTL: 24 hours
- Hit rate target: >30%

---

## 🔄 Data Flow

### Analysis Request Flow

```
1. User inputs text in Frontend
        ↓
2. Frontend validates (min 10 words)
        ↓
3. POST /analyze to Backend
        ↓
4. Backend preprocesses text
        ↓
5. Check cache (text_hash)
        ├─ Hit: Return cached result
        └─ Miss: Continue ↓
6. Detect language (EN/RU/KZ)
        ↓
7. ML model prediction
        ↓
8. If confidence < 0.75 OR deep mode:
   ├─ Perform web search
   ├─ Rank sources by similarity
   └─ Generate evidence
        ↓
9. Generate explanation
        ↓
10. Save to database
        ↓
11. Return JSON response
        ↓
12. Frontend displays results
```

### Request/Response Format

**Request**:
```json
POST /analyze
{
  "text": "News article text here...",
  "mode": "quick",
  "user_id": "user123"
}
```

**Response**:
```json
{
  "classification": "fake",
  "confidence": 0.87,
  "language": "en",
  "explanation": "This content contains unverified claims...",
  "sources": [
    {
      "title": "Reuters Fact Check",
      "url": "https://...",
      "snippet": "...",
      "relevance": 0.92
    }
  ],
  "keywords": ["unverified", "contradicts"],
  "timestamp": "2025-10-10T12:34:56Z"
}
```

---

## ⚡ Performance Optimizations

### 1. Model Loading
- **Lazy loading**: Models load on first request
- **Singleton pattern**: One model instance shared
- **Memory management**: Automatic garbage collection

### 2. Caching
- **Query cache**: MD5-based text hashing
- **Model cache**: Hugging Face local cache
- **API cache**: 24-hour TTL for search results

### 3. Concurrent Processing
- **Async/await**: FastAPI async endpoints
- **Background tasks**: Non-blocking DB writes
- **Connection pooling**: Database connections

### 4. Resource Management
- **GPU utilization**: Automatic CUDA detection
- **CPU fallback**: Works without GPU
- **Memory limits**: Max 4GB recommended

---

## 🔒 Security Architecture

### Input Validation
- **Length limits**: 10-10,000 words
- **SQL injection**: Parametrized queries
- **XSS protection**: HTML escaping
- **CORS**: Configured origins only

### Authentication (Optional)
- **Password hashing**: bcrypt
- **Session management**: JWT tokens
- **Rate limiting**: 100 requests/hour/user

### Data Privacy
- **No PII collection**: Anonymous by default
- **Opt-in history**: User choice
- **Secure storage**: Encrypted at rest

---

## 📊 Monitoring & Logging

### Logging Strategy
```python
logs/
├── app.log          # Application logs
├── error.log        # Errors only
└── access.log       # API access logs
```

### Log Levels
- **DEBUG**: Development details
- **INFO**: Normal operations
- **WARNING**: Unusual but handled
- **ERROR**: Errors that need attention
- **CRITICAL**: System failures

### Metrics Tracked
- Request count
- Response time (P50, P95, P99)
- Error rate
- Cache hit rate
- Model accuracy
- User engagement

---

## 🚀 Deployment Architecture

### Development
```
localhost:8000 (Backend)
localhost:8080 (Frontend)
SQLite database
Mock search results
```

### Production
```
render.com/huggingface.co (Backend)
CDN (Frontend static files)
PostgreSQL (Database)
Real API keys (Search)
```

### Scaling Strategy
- **Horizontal**: Multiple backend instances
- **Load balancer**: Nginx/AWS ALB
- **Cache layer**: Redis
- **CDN**: Static assets
- **Database**: Read replicas

---

## 🔧 Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | HTML/CSS/JS | ES6+ |
| UI Framework | TailwindCSS | 3.x |
| Backend | FastAPI | 0.104+ |
| Server | Uvicorn | 0.24+ |
| ML Framework | PyTorch | 2.1+ |
| NLP | Transformers | 4.35+ |
| Embeddings | Sentence-Transformers | 2.2+ |
| Database | SQLite/PostgreSQL | - |
| Language Detection | langdetect | 1.0+ |
| Web Client | requests | 2.31+ |

---

## 📈 Future Architecture Enhancements

### Phase 2
- Microservices architecture
- Message queue (RabbitMQ)
- Caching layer (Redis)
- Monitoring (Prometheus/Grafana)

### Phase 3
- Kubernetes deployment
- Multi-region deployment
- Real-time processing
- GraphQL API

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-10  
**Maintained By**: Development Team