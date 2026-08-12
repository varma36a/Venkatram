@echo off
setlocal EnableExtensions
title Substation Datasheet Wizard

REM This .bat lives in the project root. Stay here (do NOT go up a folder).
cd /d "%~dp0"
if errorlevel 1 (
  echo Could not open the project folder:
  echo %~dp0
  pause
  exit /b 1
)

echo.
echo  Substation Datasheet Wizard
echo  ---------------------------
echo  Folder: %CD%
echo  This window creates JSON files from your PDF datasheet.
echo.

if not exist "wizard\datasheet_wizard.py" (
  echo ERROR: Cannot find wizard\datasheet_wizard.py
  echo.
  echo Make sure you unzipped the full project and that this file sits next to
  echo the "wizard", "python", and "samples" folders.
  echo.
  echo Current folder:
  echo   %CD%
  echo.
  dir /b
  echo.
  pause
  exit /b 1
)

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py -3"
  goto :have_python
)
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=python"
  goto :have_python
)

echo ERROR: Python was not found on this PC.
echo.
echo Please install Python 3 from:
echo   https://www.python.org/downloads/
echo.
echo IMPORTANT: during setup, CHECK the box
echo   "Add python.exe to PATH"
echo Then close this window and double-click this file again.
echo.
pause
exit /b 1

:have_python
echo Using: %PY%
echo.

if not exist "python\.venv\Scripts\python.exe" (
  echo First-time setup: creating helper environment...
  %PY% -m venv "python\.venv"
  if errorlevel 1 (
    echo ERROR: Could not create python\.venv
    echo Try reinstalling Python and checking "Add to PATH".
    pause
    exit /b 1
  )
  call "python\.venv\Scripts\activate.bat"
  echo Installing packages (one-time, may take a few minutes)...
  python -m pip install --upgrade pip
  python -m pip install -r "python\requirements.txt"
  if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection and try again.
    pause
    exit /b 1
  )
) else (
  call "python\.venv\Scripts\activate.bat"
)

echo Starting the wizard window...
python "wizard\datasheet_wizard.py"
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo.
  echo The wizard exited with an error code: %ERR%
  echo If a window did not open, Python may be missing Tk support.
  echo Reinstall Python from python.org and try again.
  pause
  exit /b %ERR%
)

endlocal
