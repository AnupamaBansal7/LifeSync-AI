# LifeSync AI: Setup & Deployment Guide

## 1. Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: 20+ and npm
- **Database**: PostgreSQL 16 with `pgvector` extension
- **Cache / Queue**: Redis 7+
- **Docker**: Optional, for containerized deployment

---

## 2. Quickstart with Docker Compose

To spin up the entire production stack (PostgreSQL + pgvector, Redis, FastAPI Backend, and Nginx Frontend):

```bash
# 1. Clone repository
git clone https://github.com/AnupamaBansal7/LifeSync-AI.git
cd LifeSync-AI

# 2. Configure environment
cp .env.example .env
# Edit .env with your SECRET_KEY and AI API keys

# 3. Launch full stack
docker compose -f docker-compose.prod.yml up -d --build

# 4. Access applications
# Web Dashboard: http://localhost:80
# API Documentation: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

---

## 3. Local Development Setup

### Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies in editable mode with development tools
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
# Accessible at http://localhost:5173
```

---

## 4. Running Automated Tests

```bash
# Run complete backend test suite (25 tests)
backend\.venv\Scripts\pytest.exe backend/tests -v

# Run frontend production build check
npm --prefix frontend run build
```

---

## 5. Google Workspace Integration Setup

To connect Gmail, Google Calendar, and Google Drive:
1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **Gmail API**, **Google Calendar API**, and **Google Drive API**.
3. Create OAuth 2.0 Credentials (Web Application).
4. Set Authorized Redirect URI to:
   `http://localhost:8000/api/v1/integrations/google/callback`
5. Add the client credentials to your `.env`:
   ```env
   GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET="your-client-secret"
   GOOGLE_REDIRECT_URI="http://localhost:8000/api/v1/integrations/google/callback"
   ```
6. Navigate to **Integrations** in the LifeSync dashboard and click **Connect Google Workspace**.

---

## 6. Windows Desktop Companion Setup

The desktop companion provides a draggable floating companion with Windows autostart:

```bash
# Run desktop companion
python desktop/pet_companion.py
```
- Click and drag the floating orb to reposition it anywhere on your desktop.
- Right-click for options: **Open Dashboard**, **Emergency Stop**, or **Close**.
