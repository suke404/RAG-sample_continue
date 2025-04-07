#!/bin/bash

# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Step 1: Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Step 2: Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Run the server
python server.py

# Deactivate virtual environment when done
deactivate 