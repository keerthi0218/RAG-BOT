#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-build}"
PORT="${PORT:-8000}"

case "$MODE" in
  build)
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python create_db.py
    python ingest.py
    ;;
  start)
    uvicorn app:app --host 0.0.0.0 --port "$PORT"
    ;;
  *)
    echo "Usage: bash deploy.sh [build|start]"
    exit 1
    ;;
esac
