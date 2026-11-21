# LifeSync AI: API & Agent Architecture Reference

## 1. System Architecture Overview

```mermaid
graph TD
    Client[Web UI / Desktop Companion] --> API[FastAPI Gateway /api/v1]
    
    API --> Routers[15 API Routers]
    Routers --> Orchestrator[AI Orchestrator Engine]
    
    subgraph Multi-Agent Layer (24 Agents)
        Orchestrator --> CommonAgents[15 Common Agents]
        Orchestrator --> RoleAgents[9 Role-Specific Agents]
    end
    
    subgraph Tool Layer (31 Tools)
        CommonAgents --> ProductivityTools[Tasks, Habits, Goals, Calendar]
        CommonAgents --> WorkspaceTools[Gmail, Calendar, Drive, Docs, Sheets]
        CommonAgents --> ComputerUseTools[App Launch, Window Inspect, Mouse, Keyboard]
    end
    
    subgraph Execution & Persistence
        ProductivityTools --> DB[(PostgreSQL + pgvector)]
        WorkspaceTools --> DB
        ComputerUseTools --> Win32[Windows Win32 API]
        Orchestrator --> WFEngine[Workflow DAG Engine]
        WFEngine --> DB
    end
```

---

## 2. API Routers Summary (15 Routers)

| Router Prefix | Tag | Description |
| :--- | :--- | :--- |
| `/auth` | Authentication | Registration, login, JWT token issuance, refresh |
| `/users` | User & Roles | User profile, role catalog, onboarding, preferences |
| `/dashboard` | Dashboard | Summary metrics, role highlights, daily briefs |
| `/tasks` | Tasks & Kanban | Task CRUD, status updates, history audits, subtasks |
| `/goals` | Goals & Habits | Milestones, habits, streaks, completions |
| `/calendar` | Calendar & Plans | Events, focus blocks, daily planning schedules |
| `/agents` | Agents & Runs | Agent catalog, manual execution, execution steps |
| `/assistant` | Assistant Chat | Conversational agent interaction, history, approvals |
| `/automations` | Automations | Automation rules, natural language generation, trigger logs |
| `/analytics` | Analytics | Productivity analytics, focus stats, role distribution |
| `/integrations` | Integrations | Google Workspace OAuth, status, synchronization |
| `/workflows` | Workflows | DAG task graphs, step execution, resume, cancel |
| `/projects` | Projects | Project workspaces, continuous notes, architectural decisions |
| `/proactive` | Proactive Intelligence | Morning briefings, deadline risk detection, cycle triggers |
| `/system` | System Diagnostics | Real-time telemetry, DB latency, agent/tool availability |

---

## 3. Specialized Agent Catalog (24 Agents)

### 15 Common Agents
1. `PersonalAssistantAgent` - General assistant and primary coordinator
2. `TaskManagementAgent` - Task scheduling, Kanban, priority breakdown
3. `EmailAgent` - Inbound email filtering, draft preparation, triage
4. `PlanningAgent` - Strategic roadmap and milestone decomposition
5. `GoalManagementAgent` - OKRs, long-term horizon tracking
6. `HabitAgent` - Habit tracking, streak preservation, nudges
7. `CalendarAgent` - Calendar scheduling, conflict resolution, focus blocks
8. `AutomationAgent` - Routine workflows, triggers, background rules
9. `MemoryAgent` - Vector retrieval, semantic indexing, preference storage
10. `AnalyticsAgent` - Productivity scoring, velocity analysis
11. `OnboardingAgent` - User persona setup and role configuration
12. `ScreenAssistanceAgent` - Visual understanding and screen advice
13. `IntegrationsAgent` - External service connector and synchronization
14. `ResearchReviewAgent` - Document summarization and literature analysis
15. `ComputerUseAgent` - Win32 window inspection, sanctioned application launch

### 9 Role-Specific Agents
1. `StudentAgent` - Exam preparation, coursework deadlines, study blocks
2. `ProfessionalAgent` - Stakeholder updates, sprint deliverables, meetings
3. `EntrepreneurAgent` - Runway tracking, investor updates, product launches
4. `ManagerAgent` - Delegation, 1-on-1 prep, team blocker identification
5. `FreelancerAgent` - Client invoicing, proposal preparation, billable hours
6. `TeacherAgent` - Lesson planning, student feedback, grading schedules
7. `HomemakerAgent` - Meal planning, grocery logistics, family calendar
8. `ResearcherAgent` - Citation analysis, experimental notes, paper drafts
9. `AthleteAgent` - Training sessions, recovery tracking, nutritional goals

---

## 4. Tool Registry (31 Tools)

1. `create_task` - Create a task
2. `batch_create_tasks` - Batch create multiple tasks
3. `update_task_status` - Update task status and due date
4. `delete_task` - Delete a task
5. `create_goal` - Create a strategic goal
6. `create_habit` - Create a habit tracker
7. `log_habit` - Log habit completion
8. `schedule_event` - Schedule calendar event
9. `create_calendar_block` - Create focus time block
10. `search_memory` - Semantic vector search via pgvector
11. `store_memory` - Store semantic context memory
12. `generate_plan` - Synthesize daily focus schedule
13. `send_email` - Send email (Approval Gated)
14. `search_emails` - Search Gmail threads
15. `read_email_thread` - Read email thread details
16. `archive_email` - Archive email message
17. `list_calendar_events` - Query calendar availability
18. `find_free_slots` - Scan for non-conflicting time slots
19. `search_drive_files` - Search Google Drive files
20. `read_docs_document` - Read Google Docs content
21. `append_docs_text` - Append notes to Google Doc
22. `read_sheets_data` - Read Google Sheets spreadsheet
23. `append_sheets_row` - Append row to Google Sheets
24. `analyze_screen` - Analyze desktop UI screenshot
25. `open_application` - Launch sanctioned application (Whitelist gated)
26. `inspect_window_state` - Inspect foreground window title
27. `send_keyboard_input` - Type keyboard input (Approval Gated)
28. `simulate_mouse_action` - Simulate mouse clicks (Approval Gated)
29. `emergency_stop` - Cancel all active automation threads
30. `summarize_notes` - Summarize project notes
31. `record_decision` - Record architectural decision
