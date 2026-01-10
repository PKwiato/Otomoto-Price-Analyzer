#!/bin/bash
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt
echo "Starting FastAPI server..."
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
