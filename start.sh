#!/bin/bash

PROJECT_DIR="$HOME/Documents/localebookagent/ebookagent"

echo "Starting Kindle Agent..."

# Backend
gnome-terminal --title="Kindle Agent Backend" -- bash -c "
cd \"$PROJECT_DIR/backend\"
source .venv/bin/activate
echo 'Starting FastAPI...'
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
exec bash
"

sleep 2

# Frontend
gnome-terminal --title="Kindle Agent Frontend" -- bash -c "
cd \"$PROJECT_DIR/frontend\"
echo 'Starting React...'
npm start
exec bash
"

echo "Backend and Frontend launched."