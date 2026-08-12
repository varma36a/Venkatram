# Substation Equipment → Revit Family Agent

End-to-end agentic workflow: **PDF datasheets + CAD drawings → validated Revit Family (`.rfa`)**, with RAG over company BIM standards.

---

## For your friend (has Revit on Windows) — start here

**Goal:** turn `revit_ops.json` into a real **`.rfa`** family on your PC.  
You do **not** need Autodesk cloud (APS). Full guide: [`revit/FRIEND_REVIT_STEPS.md`](revit/FRIEND_REVIT_STEPS.md).

### Quick path (about 10 minutes after build)

1. **Install** [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) and open **PowerShell**.

2. **Clone & build**

```bat
git clone <REPO_URL>
cd Venkatram\revit\FamilyOpsDA
dotnet build -c Release
```

3. **Install add-in** — copy these files into  
   `%AppData%\Autodesk\Revit\Addins\2025\`  
   (use `2024` / `2026` if that is your Revit year):

| Copy from | Notes |
|-----------|--------|
| `bin\Release\net8.0-windows\FamilyOpsDA.dll` | required |
| `bin\Release\net8.0-windows\Newtonsoft.Json.dll` | if present |
| `FamilyOpsDA.addin` | edit `<Assembly>` to the **full path** of the DLL if Revit does not find it |

4. **Prepare job folder**

```bat
mkdir C:\Temp\FamilyOpsJob
copy <repo>\examples\ABB_CB_245KV\revit_ops.json C:\Temp\FamilyOpsJob\
```

Copy a Revit template to the same folder as **`template.rft`**, e.g. from:

```text
C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\
```

Use `Electrical Equipment.rft` or `Generic Model.rft` → rename/copy to `C:\Temp\FamilyOpsJob\template.rft`.

5. **Run Revit** → ribbon tab **FamilyOps** → **Build .rfa from JSON** → Yes.

6. **Collect output**

```text
C:\Temp\FamilyOpsJob\result.rfa
C:\Temp\FamilyOpsJob\SUB_CB_245KV_ABB.rfa
```

Open the `.rfa` in Family Editor and confirm dimensions (1800 × 3200 × 1200 mm).

### Important: `.rft` vs `.rfa`

| File | Role |
|------|------|
| **`.rft`** | Template you **start from** (ships with Revit) |
| **`revit_ops.json`** | Instructions from the Mac/agent pipeline |
| **`.rfa`** | Family you **save / send back** |

### Sample job in this repo

```text
examples/ABB_CB_245KV/revit_ops.json
examples/ABB_CB_245KV/family_plan.json
examples/ABB_CB_245KV/validation_report.json
```

If the add-in fails, use the **manual Option B** in [`revit/FRIEND_REVIT_STEPS.md`](revit/FRIEND_REVIT_STEPS.md) (create family by hand from `family_plan.json`).

---

## Principle

**AI decides. Deterministic software executes.**

| AI (agents) | Deterministic execution |
|-------------|-------------------------|
| Identify equipment | Create extrusion / reference planes |
| Extract & reconcile parameters | Set parameters / connectors |
| Select family template & standards | Save `.rfa` via Revit API |
| Plan geometry & connectors | Validate dimensions numerically |
| Diagnose validation failures | Apply repair ops from plan |

## Pipeline

```text
PDF + CAD  →  Document Agent  →  Spec JSON
                CAD Agent      →  Geometry JSON
                RAG / Standards →  Standard hits
                     ↓
              Equipment Reasoning
                     ↓
              Family Planner (ops plan)
                     ↓
              Revit Generator (local Revit or APS)
                     ↓
              Validation → PASS publish | FAIL repair loop
```

## Mac / agent quick start (produce `revit_ops.json`)

```bash
cd python && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m pipeline.run_job \
  --pdf ../samples/datasheets/ABB_CB_245KV.pdf \
  --cad ../samples/cad/ABB_CB_245KV.dxf \
  --out ../output/ABB_CB_245KV
```

Then send your friend `output/<job>/revit_ops.json` (or the whole job folder).

## Sample inputs

| File | Equipment |
|------|-----------|
| `samples/datasheets/ABB_CB_245KV.pdf` | 245 kV circuit breaker |
| `samples/datasheets/Siemens_XFMR_132KV.pdf` | 132 kV transformer |
| `samples/datasheets/GE_SD_145KV.pdf` | 145 kV switch-disconnector |
| Matching `.dxf` under `samples/cad/` | Envelope + terminals |

## Outputs per job

```text
output/<job>/  (or examples/ABB_CB_245KV/)
  spec.json
  geometry.json
  standards.json
  family_plan.json
  revit_ops.json          ← give this to your Revit friend
  validation_report.json
  *.rfa                   ← friend generates on Windows Revit
```

## Optional: cloud `.rfa` (APS) from Mac

See [`revit/MAC_APS.md`](revit/MAC_APS.md) and [`revit/APS_SETUP.md`](revit/APS_SETUP.md). Not required if your friend has Revit.

## Docs map

| Doc | Audience |
|-----|----------|
| [`revit/FRIEND_REVIT_STEPS.md`](revit/FRIEND_REVIT_STEPS.md) | Windows + Revit friend |
| [`revit/MAC_APS.md`](revit/MAC_APS.md) | Mac + Autodesk cloud |
| [`workflows/ORCHESTRATOR_PROMPT.md`](workflows/ORCHESTRATOR_PROMPT.md) | Agent orchestrator |
| `agents/schemas/` | JSON contracts |

## Phases

1. PDF → structured spec  
2. CAD → structured geometry  
3. RAG for BIM / company standards  
4. Family planner  
5. Revit API generation (friend’s PC or APS)  
6. Validation  
7. Agentic repair loop  
8. Human approval + BIM library publish  
