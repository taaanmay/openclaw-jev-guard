#!/bin/bash

echo "🚀 Jev Semantic Router - Quick Start"
echo "===================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

echo "✅ Python found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check API key
echo ""
echo "🔑 Checking API key..."
if [ -z "$OPENROUTER_API_KEY" ]; then
    if [ -f ".env" ]; then
        echo "   ✅ .env file found"
        export $(cat .env | xargs)
    else
        echo "   ⚠️  No .env file found"
        echo "   Create one from .env.example:"
        echo "      cp .env.example .env"
        echo "      # Edit .env and add your OpenRouter API key"
        exit 1
    fi
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "   ❌ OPENROUTER_API_KEY not set"
    exit 1
fi

echo "   ✅ API key loaded"

# Run tests
echo ""
echo "🧪 Running tests..."
python test_harness.py

echo ""
echo "✨ Done!"
