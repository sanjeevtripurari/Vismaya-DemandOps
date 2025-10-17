#!/bin/bash

# Unix/Linux/Mac script to run Vismaya DemandOps locally

echo "================================================"
echo "🎯 Vismaya DemandOps - Local Runner (Unix/Linux/Mac)"
echo "Team MaximAI - AI-Powered FinOps Platform"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating..."
    python3 setup-venv.py
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if activation worked
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Install/update dependencies
echo "📦 Checking dependencies..."
python -m pip install --upgrade pip setuptools
python -m pip install -r requirements.txt

# Run the application
echo "🚀 Starting Vismaya DemandOps..."
echo "📊 Dashboard will open at: http://localhost:8503"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

python start-vismaya.py

echo ""
echo "👋 Application stopped"