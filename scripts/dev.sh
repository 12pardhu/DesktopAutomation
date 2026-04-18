#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

printf "Backend terminal:\n"
printf "  cd %s/backend\n" "$ROOT_DIR"
printf "  python3 -m venv .venv\n"
printf "  source .venv/bin/activate\n"
printf "  pip install -r requirements.txt\n"
printf "  python3 -m app.main\n\n"

printf "Dashboard terminal:\n"
printf "  cd %s/ui\n" "$ROOT_DIR"
printf "  npm install\n"
printf "  npm run electron:dev\n"
