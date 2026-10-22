#!/bin/bash
# AgriPlot Vision startup script using virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment .venv..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

echo "Starting AgriPlot Vision web server on http://127.0.0.1:8000 ..."
exec .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --reload
