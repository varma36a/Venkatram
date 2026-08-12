# Mac + APS Design Automation (no local Revit)

You stay on **Mac**. Revit runs in **Autodesk’s cloud**. You only need APS credentials and a `.rft` template file.

```text
Mac (you)                         Autodesk cloud
─────────                         ──────────────
PDF/CAD → plan → revit_ops.json
        → upload ops + template.rft ──► Design Automation (Revit engine)
        ← download SUB_*.rfa       ◄── result.rfa
```

## What Mac cannot do

- Install desktop Revit / open `.rfa` in Revit UI  
- Compile the AppBundle **locally** (`net8.0-windows`) — use **GitHub Actions** instead (one-time)

## Steps on your Mac

### 1) APS app
https://aps.autodesk.com/myapps → create app → enable **Design Automation** + **Data Management**.  
Copy Client ID + Client Secret.

### 2) Build AppBundle via GitHub (no Windows PC needed)
Push this repo to GitHub, then:

Actions → **Build FamilyOpsDA AppBundle** → Run workflow → download `FamilyOpsDA.zip` artifact.

### 3) Register activity (from Mac)

```bash
cd /Users/RohithGVMac/Venkatram
cp .env.example .env
# edit .env: APS_CLIENT_ID, APS_CLIENT_SECRET

cd python && source .venv/bin/activate
export $(grep -v '^#' ../.env | xargs)

python -m aps.register_activity --bundle ../FamilyOpsDA.zip --engine Autodesk.Revit+2025
# prints: export APS_ACTIVITY_ID=...
# paste that into .env
```

### 4) Family template `.rft`
You need **one** Revit family template file (binary from Autodesk). Get it from:
- a colleague’s Revit install, or  
- any machine with Revit: copy `Generic Model.rft` / `Electrical Equipment.rft`

Save as:

```text
revit/templates/template.rft
```

### 5) Generate `.rfa` on Mac

```bash
cd python && source .venv/bin/activate
export $(grep -v '^#' ../.env | xargs)

python -m pipeline.run_job \
  --pdf ../samples/datasheets/ABB_CB_245KV.pdf \
  --cad ../samples/cad/ABB_CB_245KV.dxf \
  --out ../output/ABB_CB_245KV \
  --aps
```

Result:

```text
output/ABB_CB_245KV/SUB_CB_245KV_ABB.rfa
```

## Checklist

| Item | On Mac? |
|------|---------|
| Run PDF/CAD pipeline | Yes |
| Call APS / download `.rfa` | Yes |
| Build AppBundle | Via GitHub Actions (Windows runner) |
| Supply `template.rft` | Yes (copy file into repo path) |
| Open `.rfa` in Revit UI | Need Windows+Revit or ACC viewer later |

Full detail: `revit/APS_SETUP.md`
