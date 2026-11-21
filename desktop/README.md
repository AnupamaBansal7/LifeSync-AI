# LifeSync AI 2.0 — Desktop Floating Companion

A lightweight, always-on-top, draggable floating companion pet ("Sync") for Windows, Linux, and macOS that runs directly on your OS desktop even when your browser is minimized or closed.

## Capabilities

- **Always on top**: Draggable anywhere across your monitors.
- **Direct Multi-Agent Orchestration**: Connected to `http://localhost:8000/api/v1/agents/chat`.
- **Role Identity Switching**: Switch between `personal`, `student`, `professional`, and `entrepreneur` contexts directly from the pet drawer.
- **Autonomous DB Operations**: Tells backend agents to create tasks, schedule calendar blocks, check in habits, and compose emails.

## How to Run

1. Make sure your LifeSync backend is running:
   ```powershell
   cd backend
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
   ```

2. Start the floating pet:
   - On Windows: double-click `run_pet.bat` or run:
     ```powershell
     python desktop/pet_companion.py
     ```

## Optional Configuration

Set environment variables before running:
- `LIFESYNC_API_URL`: Base API endpoint (default: `http://localhost:8000/api/v1`)
- `LIFESYNC_ACCESS_TOKEN`: Bearer token for authenticated accounts.
