# For your friend — simple steps (no coding)

You only need to create **JSON files** from a PDF datasheet.  
Someone with Revit can turn those JSON files into a family (`.rfa`) later.

---

## What you will do

1. Open a small window (the **Datasheet Wizard**)
2. Choose your **PDF** datasheet
3. (Optional) Choose a **CAD** drawing
4. Click **Create JSON files**
5. Send the output folder back to your teammate

---

## First time on your Windows PC

### Step 1 — Get the project
- Download the project ZIP from GitHub **or** clone it if you already know how  
  https://github.com/varma36a/Venkatram
- Unzip it anywhere (for example your Desktop)

### Step 2 — Install Python (only once)
1. Open https://www.python.org/downloads/
2. Download Python 3 and run the installer
3. **Turn ON** the checkbox: **Add python.exe to PATH**
4. Click Install

### Step 3 — Start the wizard
1. Open the unzipped folder
2. Double-click **`Start-Datasheet-Wizard.bat`**
3. The first run may take a few minutes (it installs helpers automatically)
4. A window titled **Substation Datasheet Wizard** opens

---

## Every time after that

1. Double-click **`Start-Datasheet-Wizard.bat`**
2. Click **Browse…** next to **PDF datasheet** and pick your PDF  
   (sample file: `samples\datasheets\ABB_CB_245KV.pdf`)
3. Optional: Browse for a CAD file (`.dxf`)  
   (sample: `samples\cad\ABB_CB_245KV.dxf`)
4. Choose an **Output folder** (Desktop\FamilyOps_Output is fine)
5. Click **Create JSON files**
6. When it says Finished, open that folder

### Files you should see

| File | What it is |
|------|------------|
| `revit_ops.json` | **Main file** — send this for Revit family creation |
| `family_plan.json` | Easy-to-read summary (sizes, name, etc.) |
| `spec.json` | Values read from the PDF |
| `validation_report.json` | Pass/fail checklist |

---

## Try with the sample (recommended first run)

1. PDF = `samples\datasheets\ABB_CB_245KV.pdf`
2. CAD = `samples\cad\ABB_CB_245KV.dxf`
3. Click **Create JSON files**
4. Confirm `revit_ops.json` appears in the output folder

---

## If you also have Revit and want the family file (`.rfa`)

Only if your teammate already built / sent the Revit button package:

1. Double-click `revit\Install-Revit-Button.bat` and type your Revit year (e.g. `2025`)
2. Restart Revit
3. Open the **FamilyOps** tab → **Create family from JSON**
4. Pick `revit_ops.json` → pick a `.rft` template from Revit → pick a save folder
5. Open the new `.rfa` file

> `.rft` = starter template that comes with Revit  
> `.rfa` = finished family file

---

## Need help?

Send your teammate:
- a screenshot of any error
- the PDF you used
- your Windows version
