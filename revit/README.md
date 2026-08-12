# Revit / APS execution bridge

Deterministic consumer of `revit_ops.json`.

| Path | Purpose |
|------|---------|
| `FamilyOpsDA/` | Design Automation DBApplication (build on Windows + Revit) |
| `APS_SETUP.md` | One-time AppBundle + Activity registration |
| `templates/` | Place `template.rft` (from your Revit install) |

```bash
# After APS setup + .env filled:
python -m aps.run_rfa --job ../output/ABB_CB_245KV
```
