#!/bin/bash
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt
echo "Starting Flask app..."
export PYTHONPATH="${PYTHONPATH}:."
python3 app.py
