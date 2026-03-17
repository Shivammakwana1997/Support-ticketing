# AI Banking Copilot: Progress Audit & Roadmap

This document outlines the current state of the AI Copilot project, what is missing to transition it to a production-grade banking domain system, and a prioritized roadmap for completion.

## A. Progress Audit

### What is Built (Current State)
The current codebase provides a solid foundation but lacks banking-specific domain logic, robust AI integration, and a finished frontend.

**Backend (FastAPI)**
- ✅ **Core Structure:** Modular FastAPI setup (`api/`, `core/`, `models/`, `services/`).
- ✅ **Database & ORM:** PostgreSQL + SQLAlchemy models defined (`User`, `Ticket`, `Message`, `Conversation`, `Knowledge`).
- ✅ **Authentication:** Basic JWT authentication and RBAC foundations (Admin, Agent, Viewer).
- ✅ **API Endpoints:** Skeleton REST API routes for tickets, conversations, chat, voice, and webhooks.
- ✅ **Service Layer:** Basic service classes for ticketing, auth, and conversations are stubbed out.

**Frontend (Next.js)**
- ✅ **Framework:** Next.js 14 (App Router) with TypeScript and Tailwind CSS.
- ✅ **Routing Structure:** Basic folders established for `(auth)`, `(user)`, `(agent)`, and `admin`.

### What is Missing (Gap Analysis)
To transform this into a production-grade Banking AI Copilot, the following critical components must be built:

**1. Banking Domain Shift (Critical)**
- ❌ **Banking Data Models:** Need models for `Transaction`, `Card`, `Account`, and `Dispute`.
- ❌ **Banking Intents:** The NLP pipeline must be trained to recognize banking specific intents: "Dispute Charge", "Report Fraud", "Lost/Stolen Card", "Check Balance", "Loan Inquiry".

**2. AI & RAG Integration (Major)**
- ❌ **RAG Pipeline Implementation:** The `services/rag/` module is incomplete. Needs document ingestion (chunking, embedding via `pgvector`) for banking policies (e.g., "Card Replacement Policy").
- ❌ **AI Chatbot Logic:** The `services/agents/` module needs to connect the LLM (OpenAI) with the RAG pipeline to answer user queries accurately.
- ❌ **Intent & Entity Extraction:** Extracting credit card last 4 digits, transaction amounts, and dates from user messages.

**3. Ticketing & Automation (Major)**
- ❌ **SLA & Routing Rules:** Ticket routing logic must handle critical banking events (e.g., routing "Fraud" directly to Tier 2 Fraud Specialists with a 15-minute SLA).
- ❌ **State Transitions:** Robust ticket lifecycle management (Open -> Investigating -> Resolved).

**4. UI/UX & Frontend (Major)**
- ❌ **Banking Theme:** The UI needs a clean, trustworthy, consistent banking theme (e.g., Shadcn UI with a professional color palette).
- ❌ **Interactive Dashboards:** Agent dashboard showing ticket queues, customer context (recent transactions), and Copilot suggestions.
- ❌ **Customer Chat Interface:** A polished, real-time chat widget for the customer to interact with the AI.

## C. Detailed Development Roadmap

This roadmap organizes the remaining work into prioritized sprints.

### Sprint 1: Foundation & Domain Shift (Estimated: 1 Week)
**Goal:** Adapt the database and models to the banking domain and finalize the core API.
*   **Task 1.1:** Update SQLAlchemy models to include Banking entities (`CreditCard`, `Transaction`, `Dispute`). (1 Day)
*   **Task 1.2:** Update Pydantic schemas to reflect new models and strict validation. (1 Day)
*   **Task 1.3:** Implement robust error handling and consistency across all FastAPI endpoints. (1 Day)
*   **Task 1.4:** Define new User Roles (e.g., `FraudSpecialist`, `CustomerServiceAgent`). (0.5 Days)

### Sprint 2: AI Core & RAG Pipeline (Estimated: 2 Weeks)
**Goal:** Build the AI brain that can ingest banking documents and answer queries.
*   **Task 2.1:** Implement the RAG ingestion pipeline (PDF/Text parsing, chunking, OpenAI embeddings, `pgvector` storage). (3 Days)
*   **Task 2.2:** Build the retrieval system (Semantic search + metadata filtering). (2 Days)
*   **Task 2.3:** Implement the AI Chatbot service (`services/agents/`) integrating RAG context + system prompts. (3 Days)
*   **Task 2.4:** Build the NLP pipeline (Intent classification and Entity Extraction for cards/amounts). (2 Days)

### Sprint 3: Smart Ticketing & Automation (Estimated: 1.5 Weeks)
**Goal:** Automate ticket creation, routing, and agent assistance.
*   **Task 3.1:** Implement Automated Ticket Creation from AI Chatbot interactions (handoff to human). (2 Days)
*   **Task 3.2:** Build the Routing Engine (Rule-based routing based on intent, e.g., "Fraud" -> High Priority queue). (2 Days)
*   **Task 3.3:** Implement SLA tracking and escalation logic (Background workers/Redis). (2 Days)
*   **Task 3.4:** Build the Agent Copilot API (Generate suggested replies, summarize ticket history). (1.5 Days)

### Sprint 4: Frontend UI/UX & Integration (Estimated: 2 Weeks)
**Goal:** Build a production-ready, trustworthy banking interface.
*   **Task 4.1:** Establish the global banking UI theme (Tailwind config, UI component library). (2 Days)
*   **Task 4.2:** Build the Customer Chat Interface (Real-time WebSockets, message history, typing indicators). (3 Days)
*   **Task 4.3:** Build the Agent Dashboard (Queue management, customer context panel, Copilot integration). (3 Days)
*   **Task 4.4:** Build the Admin Dashboard (Analytics, AI configuration, knowledge base management). (2 Days)

### Sprint 5: Hardening & Demo (Estimated: 1 Week)
**Goal:** Prepare for production and create demo materials.
*   **Task 5.1:** Comprehensive testing (Unit tests, integration tests for critical paths). (2 Days)
*   **Task 5.2:** Security review (RLS policies, API rate limiting, PII redaction in logs). (1 Day)
*   **Task 5.3:** Finalize deployment configurations (Docker Compose, AWS ECS templates). (1 Day)
*   **Task 5.4:** Create end-to-end Demo Script and record walkthrough. (1 Day)

### Prioritized TODO List (Immediate Next Steps)
1.  Review and approve this documentation architecture.
2.  Begin **Sprint 1, Task 1.1**: Update `models/` to include banking domain entities.
3.  Update the UI/UX theme in the `frontend/` to reflect a banking aesthetic.
