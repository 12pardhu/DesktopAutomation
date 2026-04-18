# Intelligent Offline Desktop Automation Assistant using Local LLMs

Production-level final year project for building a fully offline desktop automation assistant with voice control, natural language planning, task execution, and a live monitoring dashboard.

## Tech Stack

- Frontend: React, TypeScript, TailwindCSS, Electron
- Backend: FastAPI, Python
- AI Engine: Ollama with `llama3`
- Voice: Vosk or Whisper.cpp for STT, `pyttsx3` for TTS
- Automation: `subprocess`, `os`, `pyautogui`
- Database: SQLite
- Secure memory: encrypted local store with Fernet

## Key Features

- Fully offline execution flow
- Text and voice command input
- Natural language to JSON task conversion
- Sequential task execution with queue safety
- Command history and step logs
- Real-time run tracker
- Analytics summary panel
- English, Hindi, and Telugu support
- Optional local login
- Local encrypted memory storage

## Folder Structure

```text
backend/
  app/
    api/                REST routes and dependency wiring
    automation_module/  OS-aware path and app helpers
    core/               runtime settings and language detection
    llm_module/         Ollama provider
    memory_module/      encrypted local memory
    schemas/            request/response and task models
    security_module/    local crypto helpers
    services/           planner, queue, executor, auth, orchestrator
    storage/            SQLite persistence layer
    voice_module/       STT, TTS, noise filtering
  requirements.txt
ui/
  electron/            desktop shell
  src/
    components/        dashboard panels
    lib/               frontend API client
    types/             shared UI types
docs/
  architecture.md
scripts/
  dev.sh
```

## Architecture Summary

1. User enters a text or voice command from the dashboard.
2. FastAPI receives the request.
3. Ollama with `llama3` converts the command into structured task JSON.
4. The command and task plan are stored in SQLite.
5. The queue worker executes the steps one by one.
6. Every step result is logged to SQLite.
7. React dashboard polls the backend to show live status, history, and analytics.

## Supported Task Format

The planner returns structured JSON like this:

```json
{
  "tasks": [
    { "action": "open_app", "app": "chrome" },
    { "action": "wait", "seconds": 2 },
    { "action": "open_url", "url": "https://www.youtube.com" }
  ]
}
```

Required actions implemented:

- `open_app`
- `navigate_directory`
- `search_file`
- `open_file`
- `type_text`
- `click`
- `wait`

Additional helper action:

- `open_url`

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.main
```

Backend runs at `http://127.0.0.1:8765`.

## Frontend Setup

```bash
cd ui
npm install
npm run dev
```

For desktop mode:

```bash
cd ui
npm run electron:dev
```

## Offline Dependency Setup

Install Ollama locally and pull the local model:

```bash
ollama pull llama3
ollama serve
```

For offline speech recognition, configure either:

- `STT_ENGINE=vosk` and `VOSK_MODEL_PATH=/absolute/path/to/vosk-model`
- `STT_ENGINE=whisper.cpp` with `WHISPER_CPP_BIN` and `WHISPER_MODEL_PATH`

## Environment Variables

Optional `.env` inside `backend/`:

```env
ASSISTANT_HOST=127.0.0.1
ASSISTANT_PORT=8765
ASSISTANT_SECRET=change-this-secret
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3
STT_ENGINE=vosk
VOSK_MODEL_PATH=/absolute/path/to/vosk-model
TTS_ENGINE=pyttsx3
ASSISTANT_AUTH_ENABLED=false
ASSISTANT_AUTH_PASSWORD=1234
```

## API Endpoints

- `GET /health`
- `POST /api/chat`
- `GET /api/models`
- `GET /api/history`
- `GET /api/runs/active`
- `GET /api/runs/{run_id}`
- `GET /api/analytics`
- `GET /api/memory`
- `DELETE /api/memory`
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/voice/transcribe`
- `POST /api/voice/speak`
- `POST /api/auth/login`

## Example Commands

- `Open Chrome then open YouTube`
- `Open downloads folder and open resume.pdf`
- `Search file image.jpeg and open it`
- `Type Hello from offline assistant`
- `Wait 3 seconds then open calculator`
- `డౌన్లోడ్స్ ఫోల్డర్ ఓపెన్ చేయి`
- `यूट्यूब खोलो`

## Database Contents

SQLite stores:

- original command
- detected language
- reply summary
- task plan JSON
- run status
- step status
- timestamps
- analytics counters

## Verification

Completed locally:

- `python3 -m compileall backend/app`
- `npm run build`

Not completed in this workspace:

- backend dependency installation in `backend/.venv`
- live FastAPI boot with installed packages
- live Ollama / Vosk / pyttsx3 runtime execution

The current workspace already builds the frontend successfully, but the backend virtual environment still needs `pip install -r requirements.txt` before running.

## Launch Helper

```bash
./scripts/dev.sh
```

## Final Year Project Highlights

- Modular layered architecture
- Offline-first AI design
- Local automation with queue safety
- Activity logging and analytics
- Multilingual voice and command support
- Security-conscious local storage
