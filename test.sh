#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated virtual environment"
else
    echo "Virtual environment not found. Please run run.sh first."
    exit 1
fi

# Run the test script
echo "Running tests..."
python test_system.py

# Deactivate virtual environment
deactivate 