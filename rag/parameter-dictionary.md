# Parameter Dictionary — Substation Equipment

Canonical parameter names for agents and Revit shared parameters.

| Canonical name | Revit name | Spec field | Notes |
|----------------|------------|------------|-------|
| width_mm | Width | width_mm | Instance length driven by type |
| height_mm | Height | height_mm | |
| depth_mm | Depth | depth_mm | |
| rated_voltage_kv | Rated_Voltage | rated_voltage_kv | Number, kV |
| weight_kg | Weight | weight_kg | Number, kg |
| manufacturer | Manufacturer | manufacturer | Text |
| model | Model | model | Text |
| mounting | Mounting | mounting | Text |
| terminal_count | Terminal_Count | terminal_count | Integer |

## Conflict resolution
1. Prefer explicit dimension table in PDF over body text.
2. Prefer CAD envelope over PDF when delta ≤ 25 mm and CAD layer is `ENVELOPE`.
3. Prefer PDF over CAD when delta > 25 mm; flag `geometry_conflict` for human review.
4. Manufacturer / model always from PDF title block when present.
