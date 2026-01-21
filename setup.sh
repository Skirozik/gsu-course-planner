#!/bin/bash

# GSU Course Planner - Setup Script
# This script sets up the development environment

echo "🎓 Setting up GSU Course Planner..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Mac/Linux
    source venv/bin/activate
fi

# Install requirements
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your ANTHROPIC_API_KEY"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/transcripts
mkdir -p data/course_catalogs

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY"
echo "2. Activate the virtual environment:"
echo "   - Windows: venv\\Scripts\\activate"
echo "   - Mac/Linux: source venv/bin/activate"
echo "3. Run the app: streamlit run app.py"
echo ""
echo "🎉 Happy coding!"
