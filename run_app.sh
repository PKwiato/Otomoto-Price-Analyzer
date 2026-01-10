#!/bin/bash
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt
echo "Starting Streamlit app..."
export PYTHONPATH="${PYTHONPATH}:."
python3 -m streamlit run app.py --server.port 8501
