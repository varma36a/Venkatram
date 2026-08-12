# For your friend (Windows + Revit) — generate `.rfa` from `revit_ops.json`

You do **not** need Autodesk APS / cloud. Use your local Revit.

## What you receive

| File | Meaning |
|------|---------|
| `revit_ops.json` | Step-by-step Revit API instructions (create family, params, extrusion, save) |
| `family_plan.json` | Human-readable plan (family name, dimensions, connectors) |
| `spec.json` | Values extracted from the OEM datasheet |

**Output you create:** a Revit **Family** file ending in **`.rfa`**  
(example: `SUB_CB_245KV_ABB.rfa`)

| Extension | What it is |
|-----------|------------|
| `.rft` | Family **template** — already installed with Revit (you start from this) |
| `.rfa` | Family **result** — what you save at the end |

## Sample already in this repo

```text
examples/ABB_CB_245KV/revit_ops.json
```

Target family name: **`SUB_CB_245KV_ABB`**  
Envelope: **1800 × 3200 × 1200 mm**, 245 kV circuit breaker.

---

## Option A — Recommended: Local FamilyOpsDA add-in (Revit 2025)

### A1. Prerequisites
- Windows PC with **Revit 2025** (2024/2026 also OK if you retarget)
- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- Visual Studio 2022 **or** just `dotnet` CLI

### A2. Clone and build

```bat
git clone <THIS_REPO_URL>
cd Venkatram\revit\FamilyOpsDA
dotnet build -c Release
```

### A3. Install the add-in for local Revit

1. Create folder (example):

```text
%AppData%\Autodesk\Revit\Addins\2025\FamilyOpsDA\
```

2. Copy into that folder:
   - `bin\Release\net8.0-windows\FamilyOpsDA.dll`
   - `bin\Release\net8.0-windows\Newtonsoft.Json.dll`
   - `FamilyOpsDA.addin` (edit `Assembly` path if needed to the full DLL path)

3. Restart Revit.

> Design Automation uses `IExternalDBApplication` (no ribbon button). For a first local test, prefer **Option B** (macro / journal-free runner) below, or ask the Mac-side teammate to enable a simple ExternalCommand wrapper.

### A4. Prepare working folder

Copy these into one folder, e.g. `C:\Temp\ABB_CB_245KV\`:

```text
revit_ops.json          (from examples/ABB_CB_245KV/)
template.rft            (from your Revit templates — see A5)
```

### A5. Get `template.rft`

From your Revit install templates, copy one of:

- `Electrical Equipment.rft` (preferred for HV gear), or  
- `Generic Model.rft` / `Metric Generic Model.rft`

Rename/copy to:

```text
C:\Temp\ABB_CB_245KV\template.rft
```

Typical locations (version may differ):

```text
C:\ProgramData\Autodesk\RVT 2025\Family Templates\English\
```

### A6. Run generation

With the add-in loaded, run FamilyOpsDA against that folder (working directory must contain `revit_ops.json` + `template.rft`).  
On success you get:

```text
C:\Temp\ABB_CB_245KV\result.rfa
C:\Temp\ABB_CB_245KV\SUB_CB_245KV_ABB.rfa
```

Open the `.rfa` in Revit Family Editor and check Width / Height / Depth / parameters.

---

## Option B — Manual check (no coding)

If the add-in is not ready yet, use the JSON as a **spec sheet**:

1. Open Revit → **New** → **Family** → pick **Electrical Equipment** (or Generic Model).
2. Read `examples/ABB_CB_245KV/family_plan.json`.
3. Create reference planes and a box extrusion:
   - Width = **1800 mm**
   - Depth = **1200 mm**
   - Height = **3200 mm**
4. Add type/instance parameters listed in the plan (`Rated_Voltage`, `Weight`, `Manufacturer`, `Model`, …).
5. **Save As** → `SUB_CB_245KV_ABB.rfa`.

Use `validation_report.json` as the acceptance checklist (all rows should match).

---

## Option C — Cloud (APS) — only if no local Revit for batch jobs

See [`APS_SETUP.md`](APS_SETUP.md) / [`MAC_APS.md`](MAC_APS.md). Not required when you have Revit installed.

---

## Checklist before you send `.rfa` back

- [ ] File name matches `family_plan.json` → `family_name`
- [ ] Dimensions match datasheet (±5 mm)
- [ ] `Rated_Voltage`, `Manufacturer`, `Model` filled
- [ ] Family opens without errors in Family Editor
- [ ] (Optional) 3 electrical connectors if `terminal_count` = 3

## If something fails

Send back:
1. Screenshot of the error  
2. Your Revit version  
3. Which template `.rft` you used  
4. The `revit_ops.json` you ran
