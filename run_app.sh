#!/bin/bash
# Script to run the Flask app

echo "Starting Multilingual Speech Translation Assistant..."
echo "=========================================="

# Activate virtual environment
source venv/bin/activate

# Run the app
echo "Starting Flask server..."
python app.py
