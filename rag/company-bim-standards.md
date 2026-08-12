# Company BIM Standards — Substation Electrical Equipment Families

## Scope
Applies to outdoor AIS / GIS substation equipment modeled as Revit families for electrical layouts.

## Category
Default category: **Electrical Equipment**.  
Use **Generic Model** only when no electrical connectors are required and the object is purely spatial.

## Family naming
```
SUB_<TYPE>_<VOLTAGE>KV_<OEM>
```
Examples:
- `SUB_CB_245KV_ABB`
- `SUB_XFMR_132KV_SIEMENS`
- `SUB_SD_145KV_GE`

Type codes: `CB` circuit breaker, `XFMR` transformer, `SD` switch-disconnector, `CT` current transformer, `VT` voltage transformer, `LA` surge arrester.

## Required type parameters
| Parameter | Type | Group | Unit |
|-----------|------|-------|------|
| Width | Length | Dimensions | mm |
| Height | Length | Dimensions | mm |
| Depth | Length | Dimensions | mm |
| Rated_Voltage | Number | Electrical | kV |
| Weight | Number | Identity Data | kg |
| Manufacturer | Text | Identity Data | — |
| Model | Text | Identity Data | — |
| Mounting | Text | Identity Data | — |

## Geometry rules
1. Origin at **bottom center** of equipment footprint.
2. Width along **X**, Depth along **Y**, Height along **Z**.
3. Envelope must match datasheet ±5 mm unless CAD overrides with documented reason.
4. Prefer single parametric extrusion for Phase 1; refine with nested families later.

## Connectors
- Electrical connectors for each terminal; place at CAD terminal coordinates when available.
- Connector system type: **Power Circuit** for HV terminals.
- Direction outward from equipment body.

## Materials
Default: `Substation - Equipment Steel` for enclosure; `Substation - Insulator Porcelain` for bushings when modeled.

## Visibility
- Coarse: envelope box only
- Medium: envelope + terminals
- Fine: envelope + terminals + mounting feet
