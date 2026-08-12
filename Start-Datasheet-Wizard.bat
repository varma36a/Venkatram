@echo off
title Substation Datasheet Wizard
cd /d "%~dp0\.."

echo.
echo  Substation Datasheet Wizard
echo  ---------------------------
echo  This window creates JSON files from your PDF datasheet.
echo.

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set PY=py -3
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set PY=python
  ) else (
    echo Python was not found on this PC.
    echo.
    echo Please install Python 3 from https://www.python.org/downloads/
    echo IMPORTANT: during setup, check "Add python.exe to PATH"
    echo Then double-click this file again.
    echo.
    pause
    exit /b 1
  )
)

if not exist "python\.venv\Scripts\python.exe" (
  echo First-time setup: installing helper tools...
  %PY% -m venv python\.venv
  if errorlevel 1 (
    echo Could not create virtual environment.
    pause
    exit /b 1
  )
  call python\.venv\Scripts\activate.bat
  python -m pip install -r python\requirements.txt
) else (
  call python\.venv\Scripts\activate.bat
)

python wizard\datasheet_wizard.py
if errorlevel 1 pause
