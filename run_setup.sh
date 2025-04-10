#!/bin/bash
# Helper script to run the modular setup

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if morphcloud is installed
python3 -c "import morphcloud" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing morphcloud package..."
    pip install morphcloud
fi

# Check for API key
if [ -z "$MORPH_API_KEY" ]; then
    echo "Error: MORPH_API_KEY environment variable is not set."
    echo "Please set it with: export MORPH_API_KEY='your-api-key-here'"
    exit 1
fi

# Run the setup script
echo "Starting Morph.so modular environment setup..."
python3 setup.py "$@"
