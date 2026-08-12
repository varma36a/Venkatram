# Family Templates

## Electrical Equipment.rft
Use for HV equipment with electrical connectors.

Planner must emit:
1. `CreateFamilyDocument` with template `Electrical Equipment.rft`
2. Reference planes: Left/Right (Width), Front/Back (Depth), Bottom/Top (Height)
3. Locked dimensions to Width/Height/Depth parameters
4. Extrusion solid for envelope
5. Connectors per terminal
6. Type with Rated_Voltage

## Generic Model.rft
Fallback when no electrical domain connectors are required.

## Nested bushings (Phase 2+)
Optional nested family `SUB_BUSHING_HV.rfa` for Fine detail level only.
