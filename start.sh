#!/bin/bash
echo "=================================================="
echo "⚡ Starting E-Commerce Lead Gen & Outreach Agent"
echo "=================================================="

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Uvicorn server on port 8000
echo "Starting backend server on http://localhost:8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
