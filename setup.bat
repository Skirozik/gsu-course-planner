@echo off
REM GSU Course Planner - Windows Setup Script

echo 🎓 Setting up GSU Course Planner...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

REM Install requirements
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your ANTHROPIC_API_KEY
)

REM Create data directories
echo 📁 Creating data directories...
if not exist "data\transcripts" mkdir "data\transcripts"
if not exist "data\course_catalogs" mkdir "data\course_catalogs"

echo.
echo ✅ Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env and add your ANTHROPIC_API_KEY
echo 2. Activate the virtual environment: venv\Scripts\activate
echo 3. Run the app: streamlit run app.py
echo.
echo 🎉 Happy coding!

pause
