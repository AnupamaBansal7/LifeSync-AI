# LifeSync AI – Intelligent Personal Life Management Operating System

> **One person. Multiple responsibilities. One intelligent operating system.**

LifeSync AI is a centralized, AI-powered personal life management platform designed to help people orchestrate every dimension of their existence. Rather than forcing users into a single identity or rigid productivity silo, LifeSync AI introduces a **multi-role architecture** anchored by personal wellness (`personal`), dynamically coordinating specialized AI agents across professional, academic, entrepreneurial, and creative responsibilities.

Featuring a futuristic glassmorphic UI with an interactive **3D WebGL AI Core**, real-time conflict-aware calendar scheduling, semantic RAG memory via `pgvector`, hierarchical OKR roadmaps, habit streak matrices, and automated event triggers, LifeSync AI operates as a proactive personal copilot.

---

## Architecture Overview

```
                                    +-----------------------------------------------+
                                    |               LifeSync AI OS                  |
                                    |           React 19 + TypeScript + Vite        |
                                    |  Three.js 3D Core | Framer Motion | Recharts  |
                                    +-----------------------+-----------------------+
                                                            |
                                               REST APIs / JWT Token Auth
                                                            |
                                    +-----------------------v-----------------------+
                                    |         FastAPI Async Backend Services        |
                                    |   54 Endpoints across 12 Modular Subsystems   |
                                    +-----------------------+-----------------------+
                                                            |
                     +--------------------------------------+--------------------------------------+
                     |                                      |                                      |
         +-----------v-----------+              +-----------v-----------+              +-----------v-----------+
         | Multi-Agent Ecosystem |              |   Data & Vector Store |              |  Task & Event Engine  |
         |  Orchestrator Engine  |              | PostgreSQL 16+pgvector|              | Redis 7 & Background  |
         |  Tool Calling Registry|              | SQLAlchemy 2.0 Async  |              | Asynchronous Tasks    |
         +-----------+-----------+              +-----------------------+              +-----------------------+
                     |
        +------------+------------+
        |                         |
+-------v-------+         +-------v-------+
|  Cloud LLMs   |         |  Local LLMs   |
| (OpenAI-Compat|         | (Ollama:8b /  |
|  Groq, vLLM)  |         |  Mistral/Qwen)|
+---------------+         +---------------+
```

---

## Core Capabilities & Feature Highlights

### 1. 3D Reactive AI Core (WebGL & CSS Fallback)
- **Interactive Three.js Core**: A multi-layered geodesic sphere with orbital particles, breathing glow effects, and continuous mouse-driven parallax.
- **Dynamic State Awareness**: Visual states reflect system state in real time: `idle` (cyan pulse), `thinking` (spinning blue-indigo ring), `processing` (accelerated violet vortex), `executing` (amber plasma), `awaiting_approval` (pulsing rose shield), `completed` (emerald burst), and `error`.
- **Hardware-Aware Fallback**: Automatically degrades to a pure CSS animated halo if WebGL hardware acceleration is unavailable.

### 2. Multi-Role Life Management Architecture
- **Guaranteed Personal Primary Anchor**: Every user account is anchored by the `personal` role to protect personal health, sleep, and core routines.
- **Dynamic Secondary Roles**: Support for **Student**, **Working Professional**, **Entrepreneur**, **Manager**, **Freelancer**, **Teacher**, **Homemaker**, and configurable **Custom Roles**.
- **Role-Aware Context Switching**: Switching active role lens in the top navigation immediately adjusts prompt suggestions, dashboard priorities, and available agent assistance.
- **6-Step Onboarding Wizard**: Deep profiling wizard collecting academic curricula, organizational goals, business objectives, focus areas, and routine hours.

### 3. Modular Multi-Agent Ecosystem
- **Orchestrator Engine**: Inspects natural language user prompts, matches intent against registered agent personas, dispatches scoped tools, and streams unified responses.
- **9 Common Agents**:
  1. *Personal Assistant Agent*: Natural language coordinator and personal context guide.
  2. *Task Management Agent*: Task breakdown, auto-prioritization, and deadline detection.
  3. *Planning Agent*: Conflict-aware daily, weekly, and monthly time-block planner.
  4. *Goal Management Agent*: Hierarchical OKR breakdown and progress monitoring.
  5. *Habit Agent*: Consistency tracking, streak maintenance, and behavioral nudges.
  6. *Calendar & Scheduling Agent*: Event scheduling, meeting slot proposals, and conflict resolution.
  7. *Memory Agent*: Long-term preference storage and semantic knowledge retrieval.
  8. *Research Agent*: Information synthesis, structured summaries, and knowledge curation.
  9. *Reflection & Review Agent*: Weekly debriefs, productivity scores, and habit analytics.
- **8 Role-Specific Agents**:
  - *Student*: Study Planning & Exam Preparation Agent
  - *Working Professional*: Work Execution & Career Development Agent
  - *Entrepreneur*: Business Strategy & Operations Agent
  - *Manager*: Team Planning & Meeting Alignment Agent
  - *Freelancer*: Client Deliverables & Workload Balancer Agent
  - *Teacher*: Lesson Planning & Curriculum Scheduling Agent
  - *Homemaker*: Household Routines & Budget Logistics Agent
  - *Custom*: User-Configured Agent with custom prompt directives.
- **Human-in-the-Loop Approvals**: High-impact agent actions generate verifiable approval cards requiring user authorization before executing database mutations.

### 4. Advanced Task & Kanban Management
- Dual-view toggle: Responsive **List View** and interactive drag-and-drop **Kanban Board** (`todo`, `in_progress`, `completed`).
- Priority matrix (`low`, `medium`, `high`, `urgent`), time estimation in minutes, due dates, and role tagging.
- **AI Task Decomposition**: One-click action allowing agents to decompose complex projects into atomic subtasks.

### 5. Smart Calendar & Time-Blocking
- Conflict-aware schedule timeline supporting **Agenda**, **Day**, **Week**, and **Month** views.
- **Locked Event Protection**: Explicit `is_locked` flag prevents automatic rescheduling algorithms from displacing sacred commitments (exams, client meetings, doctor appointments).
- One-click **"AI Plan My Day"** distribution engine generating realistic daily focus blocks.

### 6. Strategic Goals & Roadmaps
- Multi-horizon tracking: **Short-Term** (weeks/months) and **Long-Term** (multi-year) objectives.
- Atomic execution milestones with automated real-time progress recalculation upon milestone completion.
- One-click AI milestone breakdown.

### 7. Habits & Consistency Tracking
- Daily habit check-in, tracking current streak, best streak, and frequency schedules.
- Visual **7-Day Consistency Matrix** highlighting completion momentum across the week.
- Confetti celebration upon completing daily streaks.

### 8. Semantic Memory & RAG Knowledge Base
- **PostgreSQL pgvector** integration for vector similarity search using text embeddings.
- **Document Chunking & Ingestion**: Ingests reference notes, lecture materials, and company documents into chunked vector segments.
- Privacy-first memory management: granular categorization (`preference`, `responsibility`, `decision`, `academic`), importance scoring (0.1–1.0), and opt-in dataset consent.

### 9. Automations Engine & Scheduled Triggers
- Rule-based triggers (`daily_morning_briefing`, `overdue_task_escalation`, `habit_streak_risk`, `weekly_reflection_trigger`).
- Action dispatcher executing agent notifications, daily plan generation, and status updates.
- Test execution runner (`/api/v1/automations/{id}/trigger`) with historical execution logging.

### 10. Intelligence Analytics & Role Distribution
- **Recharts** interactive visualizations:
  - Role workload distribution pie chart.
  - Overall task completion rates.
  - Strategic goal progression momentum.
  - Habit consistency and active streak counts.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Framer Motion, Lucide React, Three.js, Recharts, Canvas-Confetti |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Asyncpg, Uvicorn |
| **Database** | PostgreSQL 16 + `pgvector` extension for semantic embeddings |
| **Caching / Queue** | Redis 7 + ARQ / asyncio background workers |
| **AI Providers** | OpenAI-Compatible API adapter (OpenAI, Groq, DeepSeek, vLLM) & Local Ollama (`http://localhost:11434/v1`) |
| **Tool Calling** | Scoped tool schemas with human-in-the-loop approval workflows |

---

## Directory Structure

```
LifeSync-AI/
├── docker-compose.yml          # PostgreSQL (pgvector) + Redis container configuration
├── README.md                   # Complete system documentation and guides
├── backend/
│   ├── pyproject.toml          # Python project metadata, dependencies, and pytest config
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint, lifespan event hooks, CORS setup
│   │   ├── core/               # App configuration, async database engine, JWT security
│   │   ├── models/             # SQLAlchemy ORM models (User, Role, Task, Goal, Habit, Memory, etc.)
│   │   ├── schemas/            # Pydantic validation schemas (Task, Goal, Habit, Calendar, etc.)
│   │   ├── api/v1/             # 12 REST API route modules (54 endpoints)
│   │   │   ├── auth.py         # Registration, login, JWT refresh, user profile
│   │   │   ├── onboarding.py   # Multi-step onboarding and role initialization
│   │   │   ├── roles.py        # Role activation, deactivation, and metadata editing
│   │   │   ├── dashboard.py    # Role-aware dashboard aggregation and productivity score
│   │   │   ├── tasks.py        # Task CRUD, status updates, and AI subtask breakdown
│   │   │   ├── calendar.py     # Calendar events, locked slots, and daily plans
│   │   │   ├── goals.py        # Goals, milestones, and progress recalculation
│   │   │   ├── habits.py       # Habits, streak logging, and frequency schedules
│   │   │   ├── assistant.py    # Conversational threads, agent dispatch, and approvals
│   │   │   ├── agents.py       # Agent catalog and execution run discovery
│   │   │   ├── memory.py       # Semantic search, memory records, and RAG ingestion
│   │   │   └── automations.py  # Automation rules, preset templates, and manual trigger
│   │   ├── ai/                 # Multi-agent architecture
│   │   │   ├── providers/      # Base provider, OpenAI-compatible, Ollama local, registry
│   │   │   ├── agents/         # BaseAgent, 9 common agents, 8 role-specific agents
│   │   │   ├── tools/          # 8 atomic executable tools (Task, Goal, Habit, Calendar, Memory)
│   │   │   ├── memory/         # Document chunking and semantic RAG retrieval service
│   │   │   ├── training/       # Opt-in fine-tuning dataset recorder and JSONL exporter
│   │   │   └── orchestrator.py # Intent parsing, agent selection, tool calling, approvals
│   │   ├── services/           # Seed service (default roles) and business logic
│   │   └── workers/            # Background cron jobs (deadline checker, streak monitor)
│   └── tests/                  # Pytest test suite (auth, tools, agents, RAG, automations)
└── frontend/
    ├── package.json            # Frontend dependencies and build scripts
    ├── tsconfig.json           # TypeScript configuration with strict module verification
    ├── vite.config.ts          # Vite build configuration and dev server proxy
    └── src/
        ├── App.tsx             # Master OS shell, global navigation, and state sync
        ├── types/              # Comprehensive TypeScript domain interfaces
        └── components/
            ├── 3d/             # AICore3D (Three.js WebGL) and AICoreFallback
            ├── layout/         # Sidebar (13 items), Navbar (role switcher), CommandPalette (Ctrl+K)
            ├── onboarding/     # 6-step multi-role onboarding wizard
            ├── dashboard/      # Personalized role-aware dashboard
            ├── assistant/      # Conversational workspace with agent badges and approval cards
            ├── agents/         # Agents catalog (18+ agents, tool inspection, run audit)
            ├── tasks/          # Dual-view List & Kanban task manager
            ├── calendar/       # Smart calendar with time-blocking and locked protection
            ├── goals/          # Strategic OKRs and milestone checklists
            ├── habits/         # Habit tracker with 7-day consistency matrix
            ├── automations/    # Automation rule manager and preset triggers
            ├── memory/         # Semantic memory search and RAG document library
            ├── analytics/      # Recharts productivity and role workload charts
            ├── workspace/      # Multi-role identities hub and quick launchpad
            ├── settings/       # Profile, working hours, AI provider, and JSON export
            └── integrations/   # Connectors (Google Calendar, GitHub, Notion, Ollama)
```

---

## Quickstart & Installation

### Prerequisites
- **Node.js**: v18+ (tested on Node v24)
- **Python**: 3.12+
- **Docker & Docker Compose**: For PostgreSQL (pgvector) and Redis
- **Optional**: [Ollama](https://ollama.ai/) for running local offline models (`ollama run llama3.1:8b`)

---

### Step 1: Start Infrastructure Containers

Start PostgreSQL with the `pgvector` extension and Redis:

```bash
docker compose up -d
```

Verify containers are running:
```bash
docker ps
```
- PostgreSQL: `localhost:5432` (`lifesync / lifesync_secret / lifesync_db`)
- Redis: `localhost:6379`

---

### Step 2: Configure and Run Backend

1. Navigate to the backend directory and activate the virtual environment:
   ```bash
   cd backend
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   # source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Configure environment variables (optional, defaults in `app/core/config.py` are pre-configured for local development):
   ```bash
   # Create .env from template if desired
   OPENAI_API_KEY="sk-..."       # Optional: For cloud OpenAI-compatible models
   LOCAL_LLM_BASE_URL="http://localhost:11434/v1"  # Optional: For local Ollama
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Verify backend health and interactive Swagger documentation:
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - API Prefix: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)

---

### Step 3: Configure and Run Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open the application:
   - URL: [http://localhost:5173](http://localhost:5173)

---

## Running Automated Tests

LifeSync AI comes with a dedicated unit and integration test suite verifying authentication security, tool execution, multi-agent dispatch, RAG chunking, and role automation:

```bash
# From the backend directory
pytest tests -v
```

**Test Suite Coverage:**
- `test_auth_security.py`: Password hashing, JWT token generation, refresh tokens, and payload validation.
- `test_tools_and_agents.py`: Atomic tool validation, execution mocking, common agents registry, and role-specific agent activation.
- `test_rag_and_training.py`: Deterministic document chunking, fallback embeddings, and opt-in JSONL fine-tuning dataset export.
- `test_roles_and_automations.py`: Default role catalog (guaranteed `personal` primary), role switcher, and automation preset triggers.

---

## Multi-Agent Ecosystem Reference

LifeSync AI dynamically activates autonomous agents based on the user's active roles:

### Common Agents (Always Available)
| Agent | Role Slug | Key Tools & Scope |
|---|---|---|
| **Personal Assistant** | `personal_assistant` | Coordinates cross-cutting requests and synthesizes multi-role priorities. |
| **Task Management** | `task_management` | `create_task`, `update_task_status`, subtask decomposition. |
| **Planning Agent** | `planning` | `save_daily_plan`, `create_calendar_block`, conflict resolution. |
| **Goal Management** | `goal_management` | `create_goal`, milestone sequencing, horizon tracking. |
| **Habit Agent** | `habit_management` | `create_habit`, `log_habit`, streak calculation. |
| **Calendar & Scheduling** | `calendar_scheduling` | `create_calendar_block`, locked event conflict avoidance. |
| **Memory Agent** | `memory_agent` | `store_long_term_memory`, `search_memory`, user preferences. |
| **Research Agent** | `research` | Information synthesis and document indexing. |
| **Reflection & Review** | `reflection_review` | Weekly reviews and productivity score analysis. |

### Role-Specific Agents (Dynamically Activated)
| Agent | Active When Role Selected | Focus Area |
|---|---|---|
| **Study & Exam Prep** | `student` | Revision timetables, syllabus coverage, exam preparation. |
| **Work & Career** | `professional` | Sprint goals, meeting notes, professional milestone delivery. |
| **Business Strategy** | `entrepreneur` | Revenue milestones, pitch planning, operational priorities. |
| **Team Planning** | `manager` | Standup agendas, 1:1 prep, sprint tracking. |
| **Client Deliverables** | `freelancer` | Billable hour allocations, proposal milestones, client deadlines. |
| **Lesson Planning** | `teacher` | Curricula scheduling, grading sprints, lecture blocks. |
| **Household Logistics** | `homemaker` | Meal schedules, recurring supply orders, home maintenance. |
| **Custom Role Agent** | `custom` | Tailored domain workflows based on user-defined prompt rules. |

---

## Verifiable Tool Calling & Human-in-the-Loop Approvals

LifeSync AI separates conversational generation from real-world state mutation. When an agent proposes creating or updating database records:

1. **Tool Invocation**: The orchestrator matches the intent to an atomic tool schema (e.g., `create_calendar_block`).
2. **Risk Assessment**:
   - If the user enabled `Auto-Approve Low-Risk Actions` in Settings and the action is low-risk (e.g. logging a completed habit), the action executes immediately.
   - For high-impact mutations or conflicting events, an **Approval Card** is generated with action parameters.
3. **User Confirmation**: The UI renders an interactive card with `Approve` and `Reject` buttons.
4. **Execution & Audit**: Upon approval, the tool executes against the database and logs the audit event.

---

## REST API Reference (54 Active Endpoints)

| Module | Base Path | Methods & Descriptions |
|---|---|---|
| **Auth** | `/api/v1/auth` | `POST /register`, `POST /login`, `POST /refresh`, `GET /me`, `PUT /profile`, `PUT /preferences` |
| **Onboarding** | `/api/v1/onboarding` | `GET /status`, `POST /complete` (6-step profile setup & module toggling) |
| **Roles** | `/api/v1/roles` | `GET /catalog`, `GET /`, `POST /activate`, `DELETE /{role_id}`, `PUT /{id}/metadata` |
| **Dashboard** | `/api/v1/dashboard` | `GET /summary` (role-aware productivity score, priorities, habits, events) |
| **Tasks** | `/api/v1/tasks` | `GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /{id}/breakdown` |
| **Calendar** | `/api/v1/calendar` | `GET /events`, `POST /events`, `DELETE /events/{id}`, `GET /daily-plans`, `POST /daily-plans` |
| **Goals** | `/api/v1/goals` | `GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /{id}/milestones/{mid}/toggle` |
| **Habits** | `/api/v1/habits` | `GET /`, `POST /`, `GET /{id}`, `DELETE /{id}`, `POST /{id}/log`, `GET /{id}/logs` |
| **Assistant** | `/api/v1/assistant` | `GET /threads`, `POST /threads`, `GET /threads/{id}`, `POST /threads/{id}/messages`, `POST /approvals/{id}` |
| **Agents** | `/api/v1/agents` | `GET /catalog`, `GET /runs` |
| **Memory** | `/api/v1/memory` | `GET /`, `POST /`, `DELETE /{id}`, `POST /search`, `POST /documents/ingest` |
| **Automations** | `/api/v1/automations`| `GET /`, `POST /`, `PUT /{id}/toggle`, `DELETE /{id}`, `POST /{id}/trigger`, `GET /templates` |

---

## Data Privacy & Portability

- **Local Model Independence**: Connect to Ollama without transmitting personal data to cloud providers.
- **Full Data Export**: Export all user data, role metadata, tasks, goals, habits, and preferences as JSON from the Settings tab.
- **Opt-In Fine-Tuning Dataset**: Consent-controlled recording of approved interaction pairs for offline model training and fine-tuning (`app.ai.training.dataset_exporter`).

---

## License

This project is licensed under the MIT License.
