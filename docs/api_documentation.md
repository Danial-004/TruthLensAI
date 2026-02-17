# TruthLens AI - API Documentation

## Base URL
```
Development: http://localhost:8000
Production: https://truthlens-api.onrender.com
```

## Authentication
Currently no authentication required. Future versions will support API keys.

---

## Endpoints

### 1. Root Endpoint

**GET** `/`

Welcome endpoint with basic information.

**Response** `200 OK`:
```json
{
  "message": "Welcome to TruthLens AI API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

**Example**:
```bash
curl http://localhost:8000/
```

---

### 2. Health Check

**GET** `/health`

Check API health status.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "database_connected": true
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some components unavailable

**Example**:
```bash
curl http://localhost:8000/health
```

---

### 3. Analyze Text

**POST** `/analyze`

Main endpoint for fake news detection.

**Request Body**:
```json
{
  "text": "string (required, 10-10000 chars)",
  "mode": "quick" | "deep" (optional, default: "quick"),
  "user_id": "string (optional)"
}
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | string | Yes | News text to analyze (min 10 words) |
| mode | string | No | Analysis mode: "quick" or "deep" |
| user_id | string | No | User identifier for history tracking |

**Response** `200 OK`:
```json
{
  "classification": "fake" | "real",
  "confidence": 0.87,
  "language": "en" | "ru" | "kz",
  "explanation": "This content contains unverified claims...",
  "sources": [
    {
      "title": "Reuters Fact Check",
      "url": "https://reuters.com/fact-check/...",
      "snippet": "Official verification confirms...",
      "relevance": 0.92
    }
  ],
  "keywords": ["unverified", "contradicts", "sources"],
  "timestamp": "2025-10-10T12:34:56Z",
  "analysis_id": 123
}
```

**Error Responses**:

`422 Unprocessable Entity`:
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

`500 Internal Server Error`:
```json
{
  "error": "Analysis failed",
  "detail": "Model inference error"
}
```

**Examples**:

```bash
# Quick analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Scientists discovered a new species of dinosaur in Kazakhstan mountains.",
    "mode": "quick"
  }'

# Deep analysis with user ID
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Breaking: Miracle cure discovered! Share before deleted!",
    "mode": "deep",
    "user_id": "user123"
  }'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "text": "Your news text here...",
        "mode": "deep"
    }
)

result = response.json()
print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']}")
```

**JavaScript Example**:
```javascript
fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    text: 'Your news text here...',
    mode: 'quick'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

### 4. Get History

**GET** `/history`

Retrieve user's analysis history.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User identifier |
| limit | integer | No | Max results (default: 20, max: 100) |

**Response** `200 OK`:
```json
{
  "history": [
    {
      "id": 123,
      "text": "News article text (truncated)...",
      "classification": "fake",
      "confidence": 0.87,
      "language": "en",
      "timestamp": "2025-10-10T12:34:56Z"
    }
  ],
  "count": 15
}
```

**Example**:
```bash
curl "http://localhost:8000/history?user_id=user123&limit=10"
```

---

### 5. Submit Feedback

**POST** `/feedback`

Submit feedback on an analysis result.

**Request Body**:
```json
{
  "analysis_id": 123,
  "rating": "up" | "down",
  "comment": "Optional feedback text"
}
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| analysis_id | integer | Yes | ID of analysis to rate |
| rating | string | Yes | "up" (thumbs up) or "down" (thumbs down) |
| comment | string | No | Optional user comment |

**Response** `200 OK`:
```json
{
  "message": "Feedback submitted successfully"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 123,
    "rating": "up",
    "comment": "Accurate analysis!"
  }'
```

---

### 6. Get Statistics

**GET** `/stats`

Get system statistics and metrics.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| days | integer | No | Number of days (default: 7) |

**Response** `200 OK`:
```json
{
  "period_days": 7,
  "total_analyses": 1523,
  "fake_count": 687,
  "real_count": 836,
  "average_confidence": 0.84,
  "daily_breakdown": [
    {
      "date": "2025-10-10",
      "total": 245,
      "fake": 112,
      "real": 133
    }
  ]
}
```

**Example**:
```bash
curl "http://localhost:8000/stats?days=30"
```

---

## Analysis Modes

### Quick Mode
- **Speed**: ~1.2 seconds
- **Uses cache**: Yes
- **Web search**: Only if confidence < 0.75
- **Best for**: Casual users, mobile apps

### Deep Mode
- **Speed**: ~2.7 seconds
- **Uses cache**: No
- **Web search**: Always performed
- **Best for**: Important decisions, fact-checking

---

## Response Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | System temporarily down |

---

## Rate Limiting

**Current limits**:
- 100 requests per hour per IP
- 1000 requests per day per IP

**Headers returned**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1696939200
```

**Error Response** `429 Too Many Requests`:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

---

## Language Detection

System automatically detects:
- **English (en)**: Latin characters, English patterns
- **Russian (ru)**: Cyrillic characters
- **Kazakh (kz)**: Specific Kazakh characters (ә, і, ң, ғ, ү, ұ, қ, ө, һ)

Language is automatically detected and used for:
- Model inference
- Explanation generation
- Source search query

---

## Error Handling

### Common Errors

**Text too short**:
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "ensure this value has at least 10 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Invalid mode**:
```json
{
  "detail": [
    {
      "loc": ["body", "mode"],
      "msg": "value is not a valid enumeration member; permitted: 'quick', 'deep'",
      "type": "type_error.enum"
    }
  ]
}
```

**Model not loaded**:
```json
{
  "error": "Service temporarily unavailable",
  "detail": "ML model initialization in progress"
}
```

---

## Interactive API Documentation

### Swagger UI
```
http://localhost:8000/docs
```
- Interactive interface
- Try out endpoints
- See request/response examples
- Authentication testing

### ReDoc
```
http://localhost:8000/redoc
```
- Clean documentation view
- Searchable
- Code examples
- Schema definitions

---

## SDKs and Client Libraries

### Python SDK Example

```python
class TruthLensClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def analyze(self, text, mode="quick", user_id=None):
        """Analyze text for fake news"""
        response = requests.post(
            f"{self.base_url}/analyze",
            json={
                "text": text,
                "mode": mode,
                "user_id": user_id
            }
        )
        return response.json()
    
    def get_history(self, user_id, limit=20):
        """Get user history"""
        response = requests.get(
            f"{self.base_url}/history",
            params={"user_id": user_id, "limit": limit}
        )
        return response.json()

# Usage
client = TruthLensClient()
result = client.analyze("News text here...", mode="deep")
print(result['classification'])
```

### JavaScript SDK Example

```javascript
class TruthLensClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }
  
  async analyze(text, mode = 'quick', userId = null) {
    const response = await fetch(`${this.baseURL}/analyze`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text, mode, user_id: userId})
    });
    return await response.json();
  }
  
  async getHistory(userId, limit = 20) {
    const response = await fetch(
      `${this.baseURL}/history?user_id=${userId}&limit=${limit}`
    );
    return await response.json();
  }
}

// Usage
const client = new TruthLensClient();
const result = await client.analyze('News text here...', 'deep');
console.log(result.classification);
```

---

## Webhooks (Future Feature)

**POST** `/webhooks/register` (Coming soon)

Register a webhook for real-time notifications.

```json
{
  "url": "https://your-app.com/webhook",
  "events": ["analysis.completed", "feedback.received"],
  "secret": "your_webhook_secret"
}
```

---

## Batch Analysis (Future Feature)

**POST** `/analyze/batch` (Coming soon)

Analyze multiple texts in one request.

```json
{
  "texts": [
    "First news article...",
    "Second news article...",
    "Third news article..."
  ],
  "mode": "quick"
}
```

---

## CORS Configuration

Allowed origins:
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- Production domains (configured in .env)

Allowed methods:
- GET, POST, PUT, DELETE, OPTIONS

Allowed headers:
- Content-Type, Authorization

---

## Best Practices

### 1. Text Input
- **Minimum**: 10 words for reliable analysis
- **Optimal**: 50-500 words
- **Maximum**: 10,000 characters
- **Format**: Plain text (HTML will be stripped)

### 2. Performance
- Use **quick mode** for real-time applications
- Use **deep mode** for critical decisions
- Implement caching on client side
- Handle errors gracefully

### 3. User Experience
- Show loading indicators during analysis
- Display confidence scores clearly
- Provide source links for verification
- Allow user feedback

### 4. Error Handling
```python
try:
    result = requests.post(url, json=data, timeout=10)
    result.raise_for_status()
    return result.json()
except requests.Timeout:
    # Handle timeout
    return {"error": "Request timeout"}
except requests.RequestException as e:
    # Handle other errors
    return {"error": str(e)}
```

---

## Code Examples

### Complete Analysis Flow (Python)

```python
import requests
from typing import Dict, Optional

class FakeNewsAnalyzer:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
    
    def check_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            data = response.json()
            return data.get("status") == "healthy"
        except:
            return False
    
    def analyze_news(
        self, 
        text: str, 
        mode: str = "quick",
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Analyze news text for authenticity
        
        Args:
            text: News article text
            mode: 'quick' or 'deep'
            user_id: Optional user identifier
            
        Returns:
            Analysis results dictionary
        """
        # Validate input
        words = text.split()
        if len(words) < 10:
            raise ValueError("Text must contain at least 10 words")
        
        # Make request
        response = requests.post(
            f"{self.api_url}/analyze",
            json={
                "text": text,
                "mode": mode,
                "user_id": user_id
            },
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_verdict(self, result: Dict) -> str:
        """Get human-readable verdict"""
        classification = result['classification']
        confidence = result['confidence'] * 100
        
        if classification == 'fake':
            if confidence >= 85:
                return f"⛔ Likely FAKE ({confidence:.0f}% confidence)"
            elif confidence >= 70:
                return f"⚠️ Possibly FAKE ({confidence:.0f}% confidence)"
            else:
                return f"❓ Uncertain - needs verification ({confidence:.0f}% confidence)"
        else:
            if confidence >= 85:
                return f"✅ Likely REAL ({confidence:.0f}% confidence)"
            elif confidence >= 70:
                return f"✓ Possibly REAL ({confidence:.0f}% confidence)"
            else:
                return f"❓ Uncertain - needs verification ({confidence:.0f}% confidence)"

# Usage example
analyzer = FakeNewsAnalyzer()

# Check health
if not analyzer.check_health():
    print("⚠️ API is not available")
    exit(1)

# Analyze text
text = """
Scientists at Kazakhstan's leading research institute have 
discovered a new species of dinosaur in the Alatau mountains. 
The fossil, dating back to the Jurassic period, represents 
a significant paleontological find.
"""

try:
    result = analyzer.analyze_news(text, mode="deep")
    
    print(analyzer.get_verdict(result))
    print(f"\nLanguage: {result['language']}")
    print(f"Explanation: {result['explanation']}")
    
    if result['sources']:
        print(f"\nSources ({len(result['sources'])}):")
        for source in result['sources']:
            print(f"  - {source['title']} ({source['relevance']:.0%})")
            print(f"    {source['url']}")
    
except ValueError as e:
    print(f"❌ Validation error: {e}")
except requests.RequestException as e:
    print(f"❌ API error: {e}")
```

### Complete Analysis Flow (JavaScript)

```javascript
class NewsVerifier {
  constructor(apiUrl = 'http://localhost:8000') {
    this.apiUrl = apiUrl;
  }
  
  async checkHealth() {
    try {
      const response = await fetch(`${this.apiUrl}/health`);
      const data = await response.json();
      return data.status === 'healthy';
    } catch {
      return false;
    }
  }
  
  async analyzeNews(text, mode = 'quick', userId = null) {
    // Validate
    const wordCount = text.trim().split(/\s+/).length;
    if (wordCount < 10) {
      throw new Error('Text must contain at least 10 words');
    }
    
    // Request
    const response = await fetch(`${this.apiUrl}/analyze`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        text: text,
        mode: mode,
        user_id: userId
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  }
  
  getVerdict(result) {
    const { classification, confidence } = result;
    const percent = (confidence * 100).toFixed(0);
    
    if (classification === 'fake') {
      if (confidence >= 0.85) return `⛔ Likely FAKE (${percent}%)`;
      if (confidence >= 0.70) return `⚠️ Possibly FAKE (${percent}%)`;
      return `❓ Uncertain (${percent}%)`;
    } else {
      if (confidence >= 0.85) return `✅ Likely REAL (${percent}%)`;
      if (confidence >= 0.70) return `✓ Possibly REAL (${percent}%)`;
      return `❓ Uncertain (${percent}%)`;
    }
  }
}

// Usage
const verifier = new NewsVerifier();

async function checkNews() {
  // Check health
  const isHealthy = await verifier.checkHealth();
  if (!isHealthy) {
    console.error('⚠️ API is not available');
    return;
  }
  
  // Analyze
  const text = `Scientists discovered a new species...`;
  
  try {
    const result = await verifier.analyzeNews(text, 'deep');
    
    console.log(verifier.getVerdict(result));
    console.log(`Language: ${result.language}`);
    console.log(`Explanation: ${result.explanation}`);
    
    if (result.sources.length > 0) {
      console.log(`\nSources (${result.sources.length}):`);
      result.sources.forEach(source => {
        console.log(`  - ${source.title} (${(source.relevance * 100).toFixed(0)}%)`);
        console.log(`    ${source.url}`);
      });
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

checkNews();
```

---

## Testing

### Test Endpoint Availability
```bash
# Health check
curl -f http://localhost:8000/health || echo "API is down"

# Test analyze
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Test news article with enough words to pass validation check", "mode":"quick"}' \
  | jq .
```

### Test Different Languages
```bash
# English
curl -X POST http://localhost:8000/analyze \
  -d '{"text":"Scientists discovered new species in mountains"}' | jq .

# Russian  
curl -X POST http://localhost:8000/analyze \
  -d '{"text":"Учёные обнаружили новый вид в горах"}' | jq .

# Kazakh
curl -X POST http://localhost:8000/analyze \
  -d '{"text":"Ғалымдар тауларда жаңа түр тапты"}' | jq .
```

---

## Changelog

### v1.0.0 (2025-10-10)
- ✅ Initial release
- ✅ `/analyze` endpoint
- ✅ `/health` endpoint
- ✅ `/history` endpoint
- ✅ `/feedback` endpoint
- ✅ Multi-language support (EN/RU/KZ)
- ✅ Quick and Deep modes

### v1.1.0 (Planned)
- 🔄 Batch analysis
- 🔄 Webhooks
- 🔄 API key authentication
- 🔄 Advanced statistics

---

## Support

**Documentation**: http://localhost:8000/docs  
**Issues**: GitHub Issues  
**Email**: api-support@truthlens.ai

---

**Last Updated**: 2025-10-10  
**API Version**: 1.0.0