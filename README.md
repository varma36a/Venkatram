# Substation Equipment → Revit Family Agent

PDF / CAD datasheets → JSON instructions → Revit family (`.rfa`).

---

## Send this to your friend (non-technical)

**Read this only:** [`FOR_YOUR_FRIEND.md`](FOR_YOUR_FRIEND.md)

### Short version

1. Install Python once (check **Add to PATH**)
2. Double-click **`Start-Datasheet-Wizard.bat`**
3. Choose a **PDF** → click **Create JSON files**
4. Send back the Output folder (especially `revit_ops.json`)

Sample PDF: `samples/datasheets/ABB_CB_245KV.pdf`

Optional Windows exe pack: run GitHub Action **Build Datasheet Wizard** and send them the zip artifact (`DatasheetWizard.exe`).

---

## For developers / Mac pipeline

```bash
cd python && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m pipeline.run_job \
  --pdf ../samples/datasheets/ABB_CB_245KV.pdf \
  --cad ../samples/cad/ABB_CB_245KV.dxf \
  --out ../output/ABB_CB_245KV
```

## Docs

| Doc | Who |
|-----|-----|
| [`FOR_YOUR_FRIEND.md`](FOR_YOUR_FRIEND.md) | Non-technical teammate |
| [`revit/FRIEND_REVIT_STEPS.md`](revit/FRIEND_REVIT_STEPS.md) | If they also build `.rfa` in Revit |
| [`revit/MAC_APS.md`](revit/MAC_APS.md) | Mac + Autodesk cloud |
| [`workflows/ORCHESTRATOR_PROMPT.md`](workflows/ORCHESTRATOR_PROMPT.md) | Agent orchestrator |

## Principle

**AI decides. Deterministic software executes.** JSON ops drive Revit — the LLM does not “draw” the family file.
