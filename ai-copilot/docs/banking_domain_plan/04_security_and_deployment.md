# Security Plan & Deployment Demo Guide

This document outlines the security architecture for the AI Banking Copilot, emphasizing strict access controls and data protection suitable for a financial institution, followed by a step-by-step guide on how to demonstrate the system's capabilities.

## G. Authentication & Security Plan

A banking copilot handles highly sensitive Personally Identifiable Information (PII) and financial data. Security is paramount.

### 1. Role-Based Access Control (RBAC)

We implement a strict least-privilege model using custom User Roles.

| Role | Access Level | Description |
| :--- | :--- | :--- |
| `Customer` | Self | Can only view their own tickets, conversations, and profile. |
| `Agent_Tier1` | Queue Specific | Can view unassigned tickets in General queues. Cannot access full transaction histories without an active ticket. |
| `Fraud_Specialist` | Elevated | Can view URGENT tickets, block cards, and view complete transaction histories for assigned cases. |
| `Loan_Officer` | Specialized | Can view loan-related inquiries and documents. Cannot view general credit card transaction history. |
| `Admin` | Global (Config) | Can manage RAG documents, AI system prompts, and configure SLA routing rules. Cannot view PII in tickets unless assigned. |
| `Auditor` | Read-Only | Read-only access to all tickets and AI transcripts for compliance reporting. |

### 2. Token & Session Management

*   **Access Tokens (JWT):** Short-lived (15 minutes). Contains user ID and Role. Signed with RS256 using a securely stored private key.
*   **Refresh Tokens:** Long-lived (7 days), stored securely in an HTTP-Only, Secure, SameSite=Strict cookie.
*   **Revocation:** Redis maintains a blocklist for revoked tokens (e.g., upon logout or password reset) to ensure immediate invalidation.
*   **API Keys:** Server-to-server communication (e.g., webhooks from the Core Banking System) uses long-lived API keys with specific scopes.

### 3. Password & Security Policies

*   **Complexity:** Minimum 12 characters, requiring uppercase, lowercase, numbers, and symbols.
*   **Hashing:** Argon2id or bcrypt (cost factor 12+) via `passlib`.
*   **MFA (Multi-Factor Auth):** Mandatory for all Agent and Admin roles (TOTP via Google Authenticator/Authy).
*   **Rate Limiting:** Strict limits on login attempts (e.g., 5 failures per 15 minutes triggers an IP block and account lockout).
*   **Data Masking:** The backend automatically redacts credit card numbers (showing only the last 4 digits) and Social Security Numbers in all database records, logs, and API responses unless explicitly requested by an authorized `Fraud_Specialist`.

---

## H. Demo Script & Deployment Guide

This section provides a step-by-step script to showcase the core value proposition of the AI Banking Copilot to stakeholders.

### 1. Step-by-Step Demo Script (The "Fraud Alert" Scenario)

**Setup:**
*   Ensure the backend and frontend are running (`docker compose up -d`).
*   Ensure a document titled "Fraud Handling Procedure 2024" is ingested into the RAG system.
*   Log in as `Customer` in one browser window, and as `Fraud_Specialist` in another.

**Step 1: The Customer Inquiry (AI Chatbot & RAG)**
*   **Action:** As the `Customer`, open the chat widget and type: *"I just saw a $500 charge from Best Buy that I didn't make!"*
*   **Expected Output:** The AI immediately responds: *"I'm sorry to hear about this unauthorized charge. Based on our Fraud Handling Procedure, I need to temporarily freeze your card ending in 1234. Should I proceed and open a fraud dispute ticket for you?"*
*   **Narrative:** Highlight how the NLP pipeline detected the 'Fraud' intent and extracted the unstated context (the user's card), while the RAG system provided the correct procedure.

**Step 2: Automated Escalation (Ticketing System)**
*   **Action:** As the `Customer`, reply: *"Yes, please freeze it and open a ticket."*
*   **Expected Output:** The AI confirms the action: *"Your card is frozen. I have created URGENT Ticket TKT-9876. A Fraud Specialist is reviewing this now."*
*   **Narrative:** Show the audience that the system didn't just answer a question; it performed an action (mock API call to Core Banking) and routed the ticket perfectly based on SLA rules.

**Step 3: The Agent Copilot (Agent Dashboard)**
*   **Action:** Switch to the `Fraud_Specialist` window. Open `TKT-9876`.
*   **Expected Output:** The dashboard shows the full chat transcript. On the right side, the **AI Copilot Panel** displays a 2-sentence summary: *"Customer disputes $500 Best Buy charge. Card 1234 has been automatically frozen."* Below the summary, the Copilot suggests three pre-written replies for the agent.
*   **Narrative:** Emphasize how much time this saves the agent. They don't have to read the whole chat; the AI summarizes it and drafts the response.

**Step 4: Resolution & Analytics (Admin Dashboard)**
*   **Action:** As the Agent, click a suggested reply ("Hello, I see the charge. I am processing the dispute form now."), resolve the ticket, and switch to the Admin Dashboard.
*   **Expected Output:** The Analytics dashboard updates in real-time, showing "AI Resolution Rate: +1", "Avg Agent Response Time: < 1 min", and "Active Fraud Alerts: 0".

### 2. Deployment Guide (Production AWS ECS)

The application is containerized and designed for AWS Elastic Container Service (ECS) with Fargate.

**Prerequisites:**
1.  AWS Account with ECR, ECS, RDS (PostgreSQL), and ElastiCache (Redis) configured.
2.  OpenAI API Key and (Optional) Twilio API Key in AWS Secrets Manager.
3.  GitHub Actions configured with AWS deployment credentials.

**Environment Configurations (`.env.production`):**
```env
APP_ENV=production
DEBUG=False
CORS_ORIGINS=https://app.yourbank.com,https://admin.yourbank.com

# Database (Supabase or RDS)
DATABASE_URL=postgresql+asyncpg://user:pass@db.yourbank.com:5432/copilot

# Redis
REDIS_URL=rediss://cache.yourbank.com:6379

# AI
OPENAI_API_KEY=sk-...

# Security
SECRET_KEY=generate_a_very_long_random_string_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

**Deployment Steps:**
1.  **Database Migration:** Run Alembic migrations against the production RDS instance (`alembic upgrade head`).
2.  **Push to ECR:** The GitHub Action `.github/workflows/deploy.yml` automatically builds the `backend` and `frontend` Docker images and pushes them to Amazon ECR upon merge to the `main` branch.
3.  **ECS Update:** The GitHub Action updates the ECS Task Definitions with the new image tags and forces a new deployment on the ECS Services.
4.  **Health Check:** The Application Load Balancer (ALB) routes traffic to the new containers once they pass the `/api/v1/health` check, draining the old containers seamlessly.
