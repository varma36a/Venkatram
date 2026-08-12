# APS Design Automation — produce real `.rfa`

**On a Mac?** Start with [`MAC_APS.md`](MAC_APS.md) — you do **not** need Revit installed locally. Revit runs in Autodesk’s cloud.

This repo emits a real Revit family via **Autodesk Platform Services → Design Automation for Revit**.

## Prerequisites

1. APS app: https://aps.autodesk.com/myapps  
   Enable **Data Management API** + **Design Automation API**.
2. AppBundle ZIP — build with GitHub Action **Build FamilyOpsDA AppBundle** (recommended on Mac) or on any Windows machine with .NET 8 (NuGet provides Revit API; desktop Revit not required to *compile*).
3. A family template `.rft` copied to `revit/templates/template.rft` (from any Revit install / colleague).

## One-time setup

### A. Get `FamilyOpsDA.zip`

- **Mac:** push repo → GitHub Actions → download artifact `FamilyOpsDA.zip`
- **Windows (optional local):**

```bat
cd revit\FamilyOpsDA
dotnet build -c Release
```

Then zip `FamilyOpsDA.bundle` per Autodesk layout (see Action in `.github/workflows/build-familyops-bundle.yml`).

### B. Register nickname, AppBundle, Activity (works on Mac)

```bash
export APS_CLIENT_ID=...
export APS_CLIENT_SECRET=...
python python/aps/register_activity.py --bundle FamilyOpsDA.zip --engine Autodesk.Revit+2025
```

Note the printed `APS_ACTIVITY_ID`.

### C. Local secrets

```bash
cp .env.example .env
# fill APS_CLIENT_ID, APS_CLIENT_SECRET, APS_ACTIVITY_ID
# place template at revit/templates/template.rft
```

## Generate `.rfa` for an existing job

```bash
cd python && source .venv/bin/activate
export $(grep -v '^#' ../.env | xargs)

python -m aps.run_rfa --job ../output/ABB_CB_245KV \
  --template ../revit/templates/template.rft
```

On success:

```text
output/ABB_CB_245KV/SUB_CB_245KV_ABB.rfa
output/ABB_CB_245KV/result.rfa
```

## End-to-end with APS

```bash
python -m pipeline.run_job \
  --pdf ../samples/datasheets/ABB_CB_245KV.pdf \
  --cad ../samples/cad/ABB_CB_245KV.dxf \
  --out ../output/ABB_CB_245KV \
  --aps
```

## Activity contract

| Argument | localName | verb |
|----------|-----------|------|
| `revit_ops` | `revit_ops.json` | get |
| `template` | `template.rft` | get |
| `result` | `result.rfa` | put |

Engine default: `Autodesk.Revit+2025` (override with `--engine`).
