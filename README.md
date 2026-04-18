# Intelligent Offline Desktop Automation Assistant using Local LLMs

Final year project for a fully offline desktop automation assistant built with local LLMs, voice input, task execution, and a monitoring dashboard.

## What This Project Does

- Accepts text commands
- Accepts voice commands
- Converts natural language into structured task steps
- Executes desktop actions one by one
- Stores command history, run logs, and execution status
- Shows everything in a React dashboard
- Works without internet for runtime automation and local AI inference

## Tech Stack

- Frontend: React, TypeScript, TailwindCSS, Electron
- Backend: FastAPI, Python
- Local AI: Ollama with `llama3`
- Voice:
  - macOS: native speech fallback + browser speech recognition + local backend support
  - Windows/Linux: local backend support through Vosk or Whisper.cpp, with browser speech recognition available in the UI when supported
- Automation: `subprocess`, `os`, `pyautogui`, `osascript` on macOS fallback
- Database: SQLite
- Secure memory: encrypted local file storage with Fernet

## Platform Support

### Current status

The project is designed to be cross-platform, but support is not identical on every OS yet.

| Feature | macOS | Windows | Linux |
|---|---|---|---|
| React dashboard | Yes | Yes | Yes |
| FastAPI backend | Yes | Yes | Yes |
| Ollama local LLM | Yes | Yes | Yes |
| Command planning | Yes | Yes | Yes |
| SQLite history/logging | Yes | Yes | Yes |
| Open applications/files/folders | Yes | Yes | Yes |
| Browser speech recognition in UI | Yes | Yes | Yes |
| Backend offline speech recognition | Yes | Yes, with Vosk/Whisper.cpp | Yes, with Vosk/Whisper.cpp |
| Keyboard typing fallback without `pyautogui` | Yes | No | No |

### Important note

- On macOS, voice and typing automation are currently the strongest because the project includes macOS-native fallback handling.
- On Windows and Linux, the project still runs, and offline voice commands are supported through Vosk or Whisper.cpp.
- For reliable Windows/Linux voice transcription and typing/click automation you should install and configure:
  - `pyautogui`
  - `vosk` with a local model, or `whisper.cpp`

So the honest answer is:

- Yes, the project architecture is cross-platform.
- Yes, the UI, backend, planning, logging, and app opening work across platforms.
- But the current repository is still most complete on macOS because of native fallbacks.
- Windows/Linux need extra runtime setup for full voice + keyboard automation reliability, but offline voice support is included through Vosk or Whisper.cpp.

## Folder Structure

```text
backend/
  app/
    api/                REST routes
    automation_module/  OS-aware automation helpers
    core/               config and language detection
    llm_module/         Ollama integration
    memory_module/      encrypted local memory
    schemas/            request/response/task models
    security_module/    encryption helpers
    services/           planner, executor, queue, auth
    storage/            SQLite layer
    voice_module/       speech and noise modules
  data/                 SQLite DB and encrypted memory
  requirements.txt
ui/
  electron/            Electron shell
  src/                 React dashboard
docs/
  architecture.md
scripts/
  dev.sh
```

## Minimum Requirements

### Hardware

- 8 GB RAM minimum
- 16 GB RAM recommended for smoother local LLM usage
- 10 GB free disk space minimum
- Microphone for voice commands

### Software

- Python 3.11 or later
- Node.js 20 or later
- npm 9 or later
- Ollama installed locally
- One local Ollama model such as `llama3`

## Required Installations

### 1. Install Python

Check:

```bash
python3 --version
```

### 2. Install Node.js

Check:

```bash
node -v
npm -v
```

### 3. Install Ollama

After installing Ollama, run:

```bash
ollama pull llama3
ollama serve
```

### 4. Backend Python packages

Installed from:

```bash
backend/requirements.txt
```

Current required Python packages:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings`
- `httpx`
- `cryptography`
- `platformdirs`
- `python-multipart`
- `soundfile`
- `numpy`
- `pyautogui`
- `pyttsx3`
- `vosk`

### 5. Frontend Node packages

Installed from:

```bash
ui/package.json
```

Main frontend dependencies:

- `react`
- `react-dom`
- `vite`
- `tailwindcss`
- `electron`
- `lucide-react`

## Fresh Setup Guide

These steps are for a completely fresh user.

### Step 1. Open the project

```bash
cd "/Users/pardhasaradhiganta/Documents/New project"
```

### Step 2. Set up the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3. Check backend `.env`

File:

[`backend/.env`](/Users/pardhasaradhiganta/Documents/New%20project/backend/.env)

Recommended local config:

```env
ASSISTANT_HOST=127.0.0.1
ASSISTANT_PORT=8765
ASSISTANT_SECRET=change-this-long-local-passphrase
ASSISTANT_DATA_DIR=./data
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3
STT_ENGINE=auto
WHISPER_CPP_BIN=
WHISPER_MODEL_PATH=
VOSK_MODEL_PATH=
TTS_ENGINE=mock
```

### Voice engine selection

`STT_ENGINE=auto` behaves like this:

- If a valid `VOSK_MODEL_PATH` is present, backend voice uses `Vosk`
- Else if `WHISPER_CPP_BIN` and `WHISPER_MODEL_PATH` are present, backend voice uses `Whisper.cpp`
- Else on macOS it falls back to the native macOS speech path
- Else backend voice remains unconfigured and should be set up with Vosk or Whisper.cpp

### Recommended Windows offline voice config

```env
STT_ENGINE=auto
VOSK_MODEL_PATH=C:\path\to\vosk-model-small-en-us-0.15
TTS_ENGINE=pyttsx3
```

### Recommended macOS offline voice config

```env
STT_ENGINE=auto
TTS_ENGINE=pyttsx3
```

### Step 4. Start Ollama

Open a new terminal:

```bash
ollama serve
```

If `llama3` is not installed yet:

```bash
ollama pull llama3
ollama serve
```

### Step 5. Start the backend

```bash
cd "/Users/pardhasaradhiganta/Documents/New project/backend"
source .venv/bin/activate
python3 -m app.main
```

Backend runs at:

- `http://127.0.0.1:8765`

### Step 6. Start the frontend

Open another terminal:

```bash
cd "/Users/pardhasaradhiganta/Documents/New project/ui"
npm install
npm run electron:dev
```

If you only want the web version:

```bash
cd "/Users/pardhasaradhiganta/Documents/New project/ui"
npm install
npm run dev
```

Web dashboard runs at:

- `http://127.0.0.1:5173`

## First Run Permissions

### macOS

Allow these when prompted:

- Microphone
- Speech Recognition
- Accessibility

You may need to manually check:

- `System Settings -> Privacy & Security -> Microphone`
- `System Settings -> Privacy & Security -> Speech Recognition`
- `System Settings -> Privacy & Security -> Accessibility`

Accessibility permission is especially important for typing and click automation.

### Windows

You may need:

- microphone permission enabled
- app control permissions
- local Vosk/Whisper setup for backend voice transcription
- Accessibility-style permissions depending on the terminal/app used for automation

### Linux

You may need:

- microphone permission
- X11/Wayland compatibility for keyboard/mouse automation
- local Vosk/Whisper setup for backend voice transcription

## How the System Works

1. User speaks or types a command.
2. The frontend sends it to FastAPI.
3. Ollama converts the command into a task list.
4. The task list is stored in SQLite.
5. A queue worker runs each step in order.
6. The dashboard shows status and results.

## Supported Task Actions

- `open_app`
- `navigate_directory`
- `search_file`
- `open_file`
- `type_text`
- `click`
- `wait`
- `open_url`

## Example Commands

### Text commands

- `Open Chrome then open YouTube`
- `Open Terminal`
- `Open Finder`
- `Open downloads folder and open report.pdf`
- `Search file image.jpeg and open it`
- `Open Chrome and type in the URL bar github.com`

### Voice commands

- `Open Chrome`
- `Open Terminal`
- `Open Finder`
- `Open Chrome and type in the search bar YouTube`

## Files Where Data Is Stored

### Encrypted memory

Stored at:

- [`backend/data/memory.enc`](/Users/pardhasaradhiganta/Documents/New%20project/backend/data/memory.enc)

### Command history, run logs, and analytics

Stored at:

- [`backend/data/assistant.db`](/Users/pardhasaradhiganta/Documents/New%20project/backend/data/assistant.db)

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

## Common Problems

### Voice command is not transcribing

Check:

- microphone permission
- speech recognition permission
- backend is running
- frontend is restarted after code changes
- `STT_ENGINE=auto` or another valid offline engine
- `VOSK_MODEL_PATH` is set on Windows/Linux if using Vosk
- `WHISPER_CPP_BIN` and `WHISPER_MODEL_PATH` are set if using Whisper.cpp

### App opens but typing does not happen

Check:

- macOS Accessibility permission
- backend is restarted
- `pyautogui` installed if you want generic cross-platform typing automation

### Ollama is not responding

Run:

```bash
ollama serve
```

And make sure `llama3` is installed:

```bash
ollama pull llama3
```

## Verification Already Done

Verified in this workspace:

- backend Python compile
- frontend production build

## Quick Start Summary

### Terminal 1

```bash
cd "/Users/pardhasaradhiganta/Documents/New project/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.main
```

### Terminal 2

```bash
ollama serve
```

### Terminal 3

```bash
cd "/Users/pardhasaradhiganta/Documents/New project/ui"
npm install
npm run electron:dev
```
