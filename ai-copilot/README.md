# AI Customer Support Copilot

An enterprise-grade, omni-channel AI customer support platform combining GenAI, RAG, voice AI, smart ticketing, and agent copilot capabilities.

## Features

### Core Capabilities
- **Omni-Channel Communication** — Chat, voice, video, email, WhatsApp/SMS (Twilio), Slack/Teams
- **AI Chatbot (GenAI + RAG)** — Knowledge-base powered chatbot with multi-document search and context-aware conversations
- **Voice AI Support** — Speech-to-text transcription, AI voice responses, call recording and summarization
- **Video Support** — Video calls, screen sharing, AI transcript generation
- **Smart Ticketing** — Auto-creation, categorization, priority detection, routing, SLA tracking, duplicate detection
- **Agent Copilot** — Suggested replies, KB retrieval, ticket summaries, troubleshooting steps
- **NLP Intelligence** — Intent detection, sentiment analysis, urgency classification, language detection
- **Analytics Dashboard** — CSAT scoring, resolution metrics, agent performance, AI vs human resolution rate

### Technical Highlights
- Multi-tenant architecture with Row Level Security (RLS)
- Real-time WebSocket communication with streaming AI responses
- RAG pipeline: ingestion → chunking → embedding → pgvector search → context assembly → LLM
- Async task processing with Redis queues
- RBAC with JWT + API key authentication
- PII detection, audit logging, GDPR-compliant design

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Database | PostgreSQL 16 + pgvector (via Supabase) |
| Cache/Queue | Redis 7 |
| AI | OpenAI API (GPT-4o, text-embedding-3-small, Whisper, TTS) |
| Channels | Twilio (WhatsApp/SMS), SendGrid (Email) |
| Deployment | Docker, AWS (ECS, S3, SQS, CloudWatch) |

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  Clients: Admin (web), User UI (web), Mobile (iOS/Android)     │
│           Slack/Teams, WhatsApp/SMS, Email                      │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│  API Gateway / Load Balancer (AWS ALB)                          │
└────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐
│  Next.js App │   │  FastAPI API │   │  Webhooks (Twilio,   │
│  Admin + User│   │  REST + WS   │   │  Email, Slack)       │
└──────────────┘   └──────────────┘   └──────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  Services: Conversations, Ticketing, RAG, Agents/Copilot,      │
│  NLP, Voice/Video, Channels, Automation, Analytics             │
└────────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌──────────────┐  ┌─────────────┐  ┌──────────────┐
│  PostgreSQL  │  │   Redis     │  │  External:   │
│  + pgvector  │  │   Cache +   │  │  OpenAI,     │
│  (Supabase)  │  │   Queue     │  │  Twilio, S3  │
└──────────────┘  └─────────────┘  └──────────────┘
```

## Project Structure

```
ai-copilot/
├── backend/                    # FastAPI backend
│   ├── api/                    # Routes + dependencies
│   │   ├── routes/             # All API endpoints
│   │   └── dependencies/       # Auth, DB, Redis deps
│   ├── core/                   # Config, security, logging
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic
│   │   ├── rag/                # RAG pipeline
│   │   ├── agents/             # Chatbot + Copilot
│   │   ├── nlp/                # Intent, sentiment, language
│   │   ├── channels/           # Twilio, email, Slack
│   │   ├── voice/              # STT/TTS
│   │   └── automation/         # Routing, SLA, auto-actions
│   ├── integrations/           # External service clients
│   ├── workers/                # Background job processors
│   └── tests/                  # Test suite
├── frontend/                   # Next.js frontend
│   ├── app/                    # App Router pages
│   │   ├── (auth)/             # Login, register
│   │   ├── (user)/             # Customer UI
│   │   ├── (agent)/            # Agent dashboard
│   │   └── admin/              # Admin panel
│   ├── components/             # Reusable components
│   ├── hooks/                  # React hooks
│   ├── lib/                    # Utilities, API client
│   ├── services/               # API service functions
│   └── types/                  # TypeScript types
├── infra/                      # Infrastructure
│   └── db/init.sql             # Database schema + migrations
├── .github/workflows/          # CI/CD pipelines
├── docker-compose.yml          # Production compose
└── docker-compose.dev.yml      # Development overrides
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- (Optional) Twilio account, SendGrid API key

### 1. Clone and configure

```bash
git clone <repo-url> ai-copilot
cd ai-copilot

# Copy environment files
cp .env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env with your API keys
```

### 2. Start with Docker Compose

```bash
# Production mode
docker compose up -d

# Development mode (with hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 3. Access the application

| Service | URL |
|---------|-----|
| Frontend (User + Admin) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

### 4. Create an admin user

```bash
# Using the API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "securepassword",
    "display_name": "Admin User"
  }'
```

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

## API Documentation

The full API is documented at `/docs` (Swagger UI) when the backend is running. Key endpoint groups:

| Group | Prefix | Description |
|-------|--------|-------------|
| Auth | `/api/v1/auth` | Register, login, token refresh |
| Tickets | `/api/v1/tickets` | CRUD, messages, summary, routing |
| Conversations | `/api/v1/conversations` | CRUD, messages |
| Chat | `/api/v1/chat`, `/api/v1/ws/chat` | AI chat (REST + WebSocket) |
| Copilot | `/api/v1/copilot` | Suggest reply, summarize, KB retrieve |
| Voice | `/api/v1/voice` | Transcribe, synthesize, call management |
| Knowledge | `/api/v1/knowledge` | Documents, collections, ingestion |
| Customers | `/api/v1/customers` | Profile, tickets, context |
| Admin | `/api/v1/admin` | Agents, AI config, API keys, usage |
| Analytics | `/api/v1/analytics` | Dashboard, agents, calls |
| Webhooks | `/api/v1/webhooks` | Twilio, email, Slack, Teams |

## Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_tickets.py -v
```

## Deployment

### AWS (ECS)

The project includes GitHub Actions workflows for CI/CD:

1. **CI Pipeline** (`.github/workflows/ci.yml`) — Lint, test, build on every push
2. **Deploy Pipeline** (`.github/workflows/deploy.yml`) — Build Docker images, push to ECR, deploy to ECS on merge to `main`

### Required GitHub Secrets

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

### Required AWS Resources

- ECS Cluster + Services (backend, frontend)
- ECR Repositories (copilot-backend, copilot-frontend)
- ALB with TLS termination
- ElastiCache Redis
- S3 Bucket
- Secrets Manager (for API keys)
- CloudWatch (logs, metrics, alarms)

## License

Private. All rights reserved.
