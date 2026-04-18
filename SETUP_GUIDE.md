# Setup Guide

This file explains how a new user can clone this repository and run the project on their own laptop.

## 1. What This Project Needs

Install these first:

- Git
- Python 3.11 or newer
- Node.js 20 or newer
- npm
- Ollama

Optional but recommended for voice and automation:

- `pyautogui`
- `pyttsx3`
- `vosk` with an offline model, or `whisper.cpp`

Most Python packages are already listed in `backend/requirements.txt`.

## 1A. Install Commands

Use the commands below based on your laptop.

### macOS

If you use Homebrew:

```bash
brew install git python node
brew install --cask ollama
```

Check installations:

```bash
git --version
python3 --version
node -v
npm -v
ollama --version
```

### Windows

Install these manually if they are not already installed:

- Git for Windows
- Python 3.11+
- Node.js 20+
- Ollama for Windows

Then check:

```powershell
git --version
python --version
node -v
npm -v
ollama --version
```

### Linux

Example for Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nodejs npm
```

Then install Ollama from the official package instructions for your distribution.

Check:

```bash
git --version
python3 --version
node -v
npm -v
ollama --version
```

## 2. Clone The Repository

Open a terminal and run:

```bash
git clone <YOUR_REPOSITORY_URL>
cd "<YOUR_PROJECT_FOLDER>"
```

Replace:

- `<YOUR_REPOSITORY_URL>` with the GitHub repository URL
- `<YOUR_PROJECT_FOLDER>` with the folder created after cloning

## 3. Install Ollama And Local Model

Install Ollama on your laptop.

Then run:

```bash
ollama pull llama3
ollama serve
```

Keep `ollama serve` running in its own terminal.

## 4. Backend Setup

Open a new terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `pyautogui`, `pyttsx3`, or `vosk` fail during the requirements install, run them again manually:

macOS/Linux:

```bash
pip install pyautogui pyttsx3 vosk
```

Windows:

```powershell
pip install pyautogui pyttsx3 vosk
```

## 5. Configure Backend Environment

Create or edit:

```text
backend/.env
```

Use this basic config:

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
TTS_ENGINE=pyttsx3
```

## 6. Voice Setup

### macOS

Usually this works with:

```env
STT_ENGINE=auto
```

macOS can use the local speech fallback when available.

Allow these permissions if prompted:

- Microphone
- Speech Recognition
- Accessibility

### Windows

For strong offline voice support, use Vosk or Whisper.cpp.

Example with Vosk:

```env
STT_ENGINE=auto
VOSK_MODEL_PATH=C:\path\to\your\vosk-model
TTS_ENGINE=pyttsx3
```

Install Vosk in the backend environment if needed:

```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install vosk pyttsx3 pyautogui
```

Download an offline Vosk model and place it somewhere like:

```text
C:\vosk-models\vosk-model-small-en-us-0.15
```

Then set:

```env
VOSK_MODEL_PATH=C:\vosk-models\vosk-model-small-en-us-0.15
```

### Linux

Use Vosk or Whisper.cpp similarly:

```env
STT_ENGINE=auto
VOSK_MODEL_PATH=/absolute/path/to/vosk-model
TTS_ENGINE=pyttsx3
```

Install the packages:

```bash
cd backend
source .venv/bin/activate
pip install vosk pyttsx3 pyautogui
```

## 7. Start The Backend

From the `backend` folder:

macOS/Linux:

```bash
source .venv/bin/activate
python3 -m app.main
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m app.main
```

Backend will run at:

```text
http://127.0.0.1:8765
```

## 8. Frontend Setup

Open another terminal:

```bash
cd ui
npm install
```

If Electron install has issues, retry:

```bash
cd ui
npm install electron
npm install
```

## 9. Start The Frontend

For Electron desktop app:

```bash
cd ui
npm run electron:dev
```

For browser mode:

```bash
cd ui
npm run dev
```

Frontend runs at:

```text
http://127.0.0.1:5173
```

## 10. Full Run Order

Use 3 terminals:

### Terminal 1

```bash
ollama serve
```

### Terminal 2

```bash
cd backend
source .venv/bin/activate
python3 -m app.main
```

### Terminal 3

```bash
cd ui
npm run electron:dev
```

## 10A. Exact Copy-Paste Commands For A New User

### macOS

```bash
git clone <YOUR_REPOSITORY_URL>
cd "<YOUR_PROJECT_FOLDER>"
brew install git python node
brew install --cask ollama
ollama pull llama3
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyautogui pyttsx3 vosk
python3 -m app.main
```

Open a second terminal:

```bash
ollama serve
```

Open a third terminal:

```bash
cd "<YOUR_PROJECT_FOLDER>/ui"
npm install
npm run electron:dev
```

### Windows PowerShell

```powershell
git clone <YOUR_REPOSITORY_URL>
cd "<YOUR_PROJECT_FOLDER>"
ollama pull llama3
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyautogui pyttsx3 vosk
python -m app.main
```

Open a second PowerShell:

```powershell
ollama serve
```

Open a third PowerShell:

```powershell
cd "<YOUR_PROJECT_FOLDER>\ui"
npm install
npm run electron:dev
```

### Linux

```bash
git clone <YOUR_REPOSITORY_URL>
cd "<YOUR_PROJECT_FOLDER>"
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nodejs npm
ollama pull llama3
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyautogui pyttsx3 vosk
python3 -m app.main
```

Open a second terminal:

```bash
ollama serve
```

Open a third terminal:

```bash
cd "<YOUR_PROJECT_FOLDER>/ui"
npm install
npm run electron:dev
```

## 11. First Test Commands

Try these:

- `Open Chrome`
- `Open Terminal`
- `Open Finder`
- `Open Chrome then open YouTube`
- `Open Chrome and type in the URL bar github.com`

Voice test examples:

- `Open Chrome`
- `Open Terminal`
- `Open Slack`

## 12. Where Data Is Stored

Encrypted memory:

```text
backend/data/memory.enc
```

Command history, run logs, analytics:

```text
backend/data/assistant.db
```

## 13. Common Problems

### Backend does not start

Make sure:

- Python is installed
- virtual environment is activated
- `pip install -r requirements.txt` finished successfully

### Frontend does not start

Make sure:

- Node.js is installed
- `npm install` completed

### Ollama errors

Make sure:

- Ollama is installed
- `ollama serve` is running
- `llama3` is pulled locally

### Voice commands do not work

Check:

- microphone permission
- speech recognition permission
- backend is running
- frontend is restarted
- Vosk or Whisper.cpp path is configured on Windows/Linux

### App opens but typing does not happen

Check:

- Accessibility permission on macOS
- `pyautogui` installed for cross-platform keyboard automation

## 14. Quick Summary

If someone freshly clones the repo, the shortest path is:

1. Clone the repo
2. Install Python, Node.js, and Ollama
3. Run `ollama pull llama3`
4. Set up `backend/.venv`
5. Install backend packages
6. Start backend
7. Install UI packages
8. Start Electron UI

## 15. Recommended Next Step For New Users

After the first successful run:

- confirm Ollama response works
- test one text command
- test one voice command
- check the dashboard history
