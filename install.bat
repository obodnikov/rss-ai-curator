@echo off
REM RSS AI Curator - Windows Installation Script

echo ==================================================
echo   RSS AI Curator - Installation Script
echo ==================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
echo [OK] Dependencies installed

REM Create directories
echo.
echo Creating directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist config mkdir config
type nul > data\.gitkeep
type nul > logs\.gitkeep
echo [OK] Directories created

REM Setup configuration
echo.
echo Setting up configuration files...

if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [OK] .env file created from template
        echo [!] Please edit .env and add your API keys
    ) else (
        (
            echo # OpenAI API Key ^(Required^)
            echo OPENAI_API_KEY=your-openai-key-here
            echo.
            echo # Anthropic API Key ^(Optional^)
            echo ANTHROPIC_API_KEY=your-anthropic-key-here
            echo.
            echo # Telegram Configuration ^(Required^)
            echo TELEGRAM_BOT_TOKEN=your-bot-token-here
            echo TELEGRAM_ADMIN_USER_ID=your-telegram-user-id
        ) > .env
        echo [OK] .env file created
    )
) else (
    echo .env file already exists, skipping...
)

REM Initialize database with shown_to_user fields
echo.
echo Initializing database with shown tracking...
python main.py init
echo [OK] Database initialized with shown_to_user fields

REM Print next steps
echo.
echo ==================================================
echo   Installation Complete! 🎉
echo ==================================================
echo.
echo Next steps:
echo.
echo 1. Edit .env file with your API keys:
echo    notepad .env
echo.
echo 2. Customize your RSS feeds in config\config.yaml
echo.
echo 3. Start the bot:
echo    python main.py start
echo.
echo 4. Or run individual commands:
echo    python main.py fetch   # Fetch RSS feeds
echo    python main.py digest  # Generate digest
echo    python main.py stats   # Show statistics
echo.
echo For detailed documentation, see:
echo   - README.md
echo   - docs\SETUP_GUIDE.md
echo.
echo Note: Articles are tracked with 'shown_to_user' field
echo No migration needed - database created with v0.1.0 schema!
echo.
echo ==================================================
echo.
pause
