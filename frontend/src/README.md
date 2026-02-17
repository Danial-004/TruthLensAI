# TruthLens - AI-Powered Fake News Detection

A sophisticated multilingual fake news detection platform powered by OpenAI GPT-4 and real-time source verification.

## Features

🔍 **Real AI Fact-Checking**: Uses AI combined with searches across trusted news sources
🌍 **Multilingual Support**: Supports Kazakh, Russian, and English with native language responses  
📊 **Trusted Source Verification**: Verifies claims against Tengrinews, Kazinform, Wikipedia, Reuters, and other authoritative sources
⚡ **Real-time Analysis**: Instant fact-checking with confidence scores and detailed explanations
🔐 **User Authentication**: Secure sign-up/sign-in with role-based access
📱 **Responsive Design**: Modern, responsive UI with dark/light mode support

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS
- **Backend**: Supabase Edge Functions, Hono
- **AI**: OpenAI GPT-4 API
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth

## Environment Setup

Create a `.env` file with the following variables:

```env
# Supabase Configuration (already provided)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# OpenAI API (you need to add this)
OPENAI_API_KEY=your_openai_api_key
```

## Getting Started

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **The application will be available at `http://localhost:3000`**

## How It Works

1. **Content Analysis**: User submits text or article URL
2. **Claim Extraction**: AI extracts key factual claims from the content
3. **Source Search**: System searches trusted news sources for relevant information
4. **AI Verification**: OpenAI GPT-4 analyzes claims against found sources
5. **Results**: Returns classification (FAKE/TRUE/UNCERTAIN) with confidence score, explanation, and source links

## Trusted Sources

- tengrinews.kz
- egemen.kz
- zakon.kz
- kazinform.kz
- wikipedia.org
- reuters.com
- bbc.com
- apnews.com

## API Endpoints

- `POST /make-server-b3bf384e/check-news` - Fact-check content
- `GET /make-server-b3bf384e/predictions` - Get user's history
- `GET /make-server-b3bf384e/predictions/:id` - Get specific prediction details
- `GET /make-server-b3bf384e/health` - Service health check

## Usage Examples

### Text Analysis
```typescript
const result = await factCheckingService.checkNews(
  "Scientists discover cure for all diseases in secret laboratory..."
);
// Returns: { label: "FAKE", confidence: 0.89, explanation: "...", sources: [...] }
```

### URL Analysis
```typescript
const result = await factCheckingService.checkNews(
  undefined,
  "https://example.com/news-article"
);
```

## Contributing

This is an educational project demonstrating real AI-powered fact-checking capabilities. The system provides accurate verification by combining advanced language models with trusted source searches.

## License

Educational use only. Not for commercial purposes.