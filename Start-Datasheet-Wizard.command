#!/bin/bash
# Double-click this file on Mac (or run: ./Start-Datasheet-Wizard.command)
set -e
cd "$(dirname "$0")"
echo ""
echo " Substation Datasheet Wizard (Mac)"
echo " ---------------------------------"
echo " Folder: $PWD"
echo ""

if [[ ! -f "wizard/datasheet_wizard.py" ]]; then
  echo "ERROR: wizard/datasheet_wizard.py not found."
  echo "Open this from the project root (same folder as python/, rag/, samples/)."
  read -r -p "Press Enter to close…"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found."
  echo "Install from https://www.python.org/downloads/mac-osx/ or: brew install python"
  read -r -p "Press Enter to close…"
  exit 1
fi

if [[ ! -x "python/.venv/bin/python" ]]; then
  echo "First-time setup…"
  python3 -m venv python/.venv
  # shellcheck disable=SC1091
  source python/.venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r python/requirements.txt
else
  # shellcheck disable=SC1091
  source python/.venv/bin/activate
fi

echo "Starting…"
# Prefer GUI wizard; if Tk is missing, fall back to sample CLI job
if python -c "import tkinter" 2>/dev/null; then
  python wizard/datasheet_wizard.py
else
  echo ""
  echo "Tk window not available on this Python. Running sample job in Terminal instead…"
  echo "PDF: samples/datasheets/ABB_CB_245KV.pdf"
  mkdir -p "$HOME/Desktop/FamilyOps_Output"
  python -m pipeline.run_job \
    --pdf samples/datasheets/ABB_CB_245KV.pdf \
    --cad samples/cad/ABB_CB_245KV.dxf \
    --out "$HOME/Desktop/FamilyOps_Output"
  echo ""
  echo "Done. JSON files are on your Desktop in FamilyOps_Output"
  echo "Main file: $HOME/Desktop/FamilyOps_Output/revit_ops.json"
  open "$HOME/Desktop/FamilyOps_Output" 2>/dev/null || true
fi

echo ""
read -r -p "Press Enter to close…"
