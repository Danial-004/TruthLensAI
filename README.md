# 🔍 TruthLens AI - Fake News Detector

## Multilingual AI-Powered Misinformation Detection System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**TruthLens AI** is a production-ready web application that uses advanced machine learning to detect fake news and misinformation in **Kazakh, Russian, and English** languages. The system provides:

✅ **Real-time Classification** - Instant fake/real news detection  
✅ **AI Explanations** - Transparent reasoning for every decision  
✅ **Web Evidence** - Real-time source verification  
✅ **Multilingual Support** - KZ, RU, EN language detection  
✅ **Modern UI** - Clean, responsive interface with dark mode  

---

## ⭐ Features

### Core Functionality
- **Multilingual NLP**: XLM-RoBERTa transformer model
- **Language Auto-Detection**: Automatic KZ/RU/EN detection
- **Confidence Scoring**: Probabilistic classification (0-100%)
- **Keyword Extraction**: Highlight suspicious indicators
- **Web Search Integration**: SerpAPI, Bing, or Google Custom Search
- **Semantic Ranking**: Sentence-transformer similarity scoring
- **Analysis History**: User-specific query tracking
- **Feedback System**: User ratings for continuous improvement

### Technical Features
- **RESTful API**: FastAPI backend with async support
- **Database**: SQLite/PostgreSQL for persistence
- **Caching**: Query caching for performance
- **Rate Limiting**: API protection
- **CORS Support**: Cross-origin requests
- **Docker Ready**: Containerized deployment
- **CI/CD**: GitHub Actions compatible

---

## 🏗️ Architecture

### System Design

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │◄────►│   Backend    │◄────►│  Database   │
│  (HTML/JS)  │      │   (FastAPI)  │      │  (SQLite)   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  ML Models   │
                     │ (PyTorch +   │
                     │ Transformers)│
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Search APIs  │
                     │(SerpAPI/Bing)│
                     └──────────────┘
```

### Technology Stack

**Backend:**
- Python 3.9+
- FastAPI (Web Framework)
- PyTorch (Deep Learning)
- Transformers (NLP Models)
- Sentence-Transformers (Embeddings)
- SQLAlchemy (ORM)
- Langdetect (Language Detection)

**Frontend:**
- HTML5
- TailwindCSS 3.x
- Vanilla JavaScript
- Font Awesome Icons

**ML Models:**
- XLM-RoBERTa-base (Classification)
- all-MiniLM-L6-v2 (Embeddings)
- Custom fine-tuned models (optional)

**External APIs:**
- SerpAPI / Bing Search / Google Custom Search
- Web scraping fallback

---

## 🚀 Installation

### Prerequisites

```bash
# System Requirements
- Python 3.9 or higher
- 4GB RAM minimum
- Internet connection
- pip or conda
```

### Quick Start

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/truthlens-ai.git
cd truthlens-ai
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Set Up Environment Variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

Example `.env`:
```env
SERP_API_KEY=your_serpapi_key
BING_API_KEY=your_bing_key
DATABASE_URL=sqlite:///./truthlens.db
SECRET_KEY=your-secret-key-here
DEBUG=True
```

5. **Initialize Database**
```bash
cd backend
python -c "from database import Database; db = Database(); db.initialize()"
```

6. **Download ML Models** (First Run)
```bash
# Models will be downloaded automatically on first inference
# Or pre-download:
python -c "from transformers import AutoTokenizer, AutoModel; AutoTokenizer.from_pretrained('xlm-roberta-base'); AutoModel.from_pretrained('xlm-roberta-base')"
```

7. **Run Backend Server**
```bash
cd backend
python app.py
# Server runs on http://localhost:8000
```

8. **Serve Frontend**
```bash
# In a new terminal
cd frontend
python -m http.server 8080
# Open http://localhost:8080 in browser
```

---

## 💻 Usage

### Web Interface

1. **Navigate to** `http://localhost:8080`
2. **Choose Analysis Mode:**
   - **Quick**: Fast analysis with cached results
   - **Deep**: Comprehensive analysis with web search
3. **Enter Text**: Paste news article or social media post
4. **Click Analyze**: Get instant results
5. **Review Results:**
   - Classification (Fake/Real)
   - Confidence score
   - AI explanation
   - Evidence sources
   - Keywords

### API Usage

```python
import requests

# Analyze text
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "text": "Your news text here...",
        "mode": "deep",
        "user_id": "user123"
    }
)

result = response.json()
print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']}")
print(f"Explanation: {result['explanation']}")
```

---

## 📚 API Documentation

### Endpoints

#### POST `/analyze`
Analyze text for fake news detection.

**Request:**
```json
{
  "text": "string (10-10000 chars)",
  "mode": "quick" | "deep",
  "user_id": "optional string"
}
```

**Response:**
```json
{
  "classification": "fake" | "real",
  "confidence": 0.87,
  "language": "en" | "ru" | "kz",
  "explanation": "string",
  "sources": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string",
      "relevance": 0.92
    }
  ],
  "keywords": ["string"],
  "timestamp": "2025-10-07T12:34:56Z"
}
```

#### GET `/health`
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "database_connected": true
}
```

#### GET `/history?user_id=xxx&limit=20`
Get user analysis history.

#### POST `/feedback`
Submit feedback for analysis.

**Interactive API Docs:** `http://localhost:8000/docs`

---

## 🌐 Deployment

### Deploy to Render

1. **Create `render.yaml`:**
```yaml
services:
  - type: web
    name: truthlens-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SERP_API_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
```

2. **Deploy:**
```bash
# Connect GitHub repo to Render
# Add environment variables in Render dashboard
# Deploy automatically on git push
```

### Deploy to Hugging Face Spaces

1. **Create `app.py`:**
```python
import gradio as gr
from backend.app import analyze_text

def analyze(text, mode):
    result = analyze_text({"text": text, "mode": mode})
    return result

demo = gr.Interface(
    fn=analyze,
    inputs=[
        gr.Textbox(lines=10, label="News Text"),
        gr.Radio(["quick", "deep"], label="Mode")
    ],
    outputs=gr.JSON(label="Results")
)

demo.launch()
```

2. **Push to HF Spaces**

### Deploy with Docker

```bash
# Build image
docker build -t truthlens-ai .

# Run container
docker run -p 8000:8000 --env-file .env truthlens-ai
```

---

## 🛠️ Development

### Project Structure

```
TruthLensAI/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── model.py            # ML inference
│   ├── search_api.py       # Web search
│   ├── database.py         # Database operations
│   ├── utils.py            # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html          # Main page
│   ├── script.js           # JavaScript
│   └── style.css           # Styles
├── models/                 # Trained models
├── data/                   # Training data
├── tests/                  # Unit tests
├── docs/                   # Documentation
├── logs/                   # Application logs
├── README.md
├── .env.example
├── .gitignore
└── requirements.txt
```

### Adding New Features

1. **New ML Model:**
```python
# backend/model.py
def load_custom_model(model_path):
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    return model
```

2. **New API Endpoint:**
```python
# backend/app.py
@app.post("/custom-endpoint")
async def custom_function(request: CustomRequest):
    # Your logic here
    return {"result": "data"}
```

### Code Style

```bash
# Format code
black backend/
isort backend/

# Lint
flake8 backend/
pylint backend/

# Type checking
mypy backend/
```

---

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest tests/

# With coverage
pytest --cov=backend tests/

# Specific test file
pytest tests/test_model.py -v
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test analyze endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Breaking news: scientists discover...", "mode": "quick"}'
```

---

## 📊 Performance Benchmarks

Target Metrics:
- **Accuracy**: >85%
- **Precision**: >80%
- **Recall**: >80%
- **F1 Score**: >0.82
- **Response Time**: <3 seconds
- **API Uptime**: >99%

---

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Project Lead**: Your Name
- **AI Engineer**: Your Name
- **Frontend Developer**: Your Name

---

## 📞 Support

- **Documentation**: [docs.truthlens.ai](https://docs.truthlens.ai)
- **Issues**: [GitHub Issues](https://github.com/yourusername/truthlens-ai/issues)
- **Email**: support@truthlens.ai

---

## 🙏 Acknowledgments

- Hugging Face Transformers
- FastAPI Framework
- TailwindCSS
- SerpAPI / Bing Search API
- XLM-RoBERTa Model Authors

---

## 🔮 Roadmap

- [ ] Mobile app (React Native)
- [ ] Chrome extension
- [ ] Telegram bot integration
- [ ] Real-time news monitoring
- [ ] Multimodal analysis (images)
- [ ] Advanced visualization dashboard
- [ ] API webhooks
- [ ] Multi-user authentication
- [ ] Admin panel

---

**Built with ❤️ for truth and transparency**