# Approved Family Patterns

## Pattern: Box envelope + top terminals
Used for many CB / SD families.

```json
{
  "geometry_strategy": {
    "reference_planes": ["Left", "Right", "Front", "Back", "Bottom", "Top"],
    "solids": [{ "type": "extrusion", "driven_by": ["Width", "Depth", "Height"] }],
    "materials": ["Substation - Equipment Steel"],
    "visibility": { "coarse": "envelope", "medium": "envelope+connectors", "fine": "envelope+connectors+base" }
  }
}
```

## Previous approved example
- Family: `SUB_CB_245KV_ABB`
- Spec height 3200 / width 1800 / depth 1200
- Three Power Circuit connectors at Z≈2800 mm
