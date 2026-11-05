#!/usr/bin/env bash
# Starts the CRISPR-X FastAPI backend on http://localhost:8000
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt
echo ""
echo "Starting CRISPR-X backend at http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
