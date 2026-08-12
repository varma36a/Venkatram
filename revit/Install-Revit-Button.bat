@echo off
title Install Revit Family Button
cd /d "%~dp0"

echo.
echo  Install "Create family from JSON" button in Revit
echo  -------------------------------------------------
echo.

set /p VER=Enter your Revit year (example 2025): 
if "%VER%"=="" set VER=2025

set ADDIN_DIR=%AppData%\Autodesk\Revit\Addins\%VER%
set DEST=%ADDIN_DIR%\FamilyOpsDA

if not exist "FamilyOpsDA\bin\Release\net8.0-windows\FamilyOpsDA.dll" (
  echo.
  echo The Revit button files are not built yet on this PC.
  echo.
  echo Easier option for non-technical users:
  echo   1. Ask your teammate to send you the "RevitButton" zip from GitHub Releases
  echo   2. Or use only the Datasheet Wizard ^(Start-Datasheet-Wizard.bat^)
  echo      to create JSON files — someone else can open them in Revit.
  echo.
  pause
  exit /b 1
)

mkdir "%DEST%" 2>nul
copy /Y "FamilyOpsDA\bin\Release\net8.0-windows\FamilyOpsDA.dll" "%DEST%\" >nul
if exist "FamilyOpsDA\bin\Release\net8.0-windows\Newtonsoft.Json.dll" (
  copy /Y "FamilyOpsDA\bin\Release\net8.0-windows\Newtonsoft.Json.dll" "%DEST%\" >nul
)

powershell -NoProfile -Command ^
  "(Get-Content 'FamilyOpsDA\FamilyOpsDA.addin') -replace '<Assembly>FamilyOpsDA.dll</Assembly>', '<Assembly>%DEST%\FamilyOpsDA.dll</Assembly>' | Set-Content '%ADDIN_DIR%\FamilyOpsDA.addin'"

echo.
echo Installed for Revit %VER%.
echo.
echo Next steps:
echo   1. Close Revit if it is open, then open Revit again
echo   2. Look for the ribbon tab named FamilyOps
echo   3. Click "Create family from JSON"
echo   4. Pick revit_ops.json, then a .rft template, then a save folder
echo.
pause
