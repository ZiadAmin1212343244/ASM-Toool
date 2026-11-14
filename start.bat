@echo off
REM Double-click start for Windows (no admin rights required)
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create venv. Ensure Python 3.12 is installed for your user.
    pause
    exit /b 1
  )
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)

if not exist ".env" (
  copy .env.example .env >nul
  echo Created .env from .env.example — update SECRET_KEY before production use.
)

if not exist "data\tpm.db" (
  echo Seeding demo data...
  python scripts\seed.py
)

python run.py
pause
