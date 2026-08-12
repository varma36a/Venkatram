"""Plan family + emit deterministic Revit ops from spec + geometry + RAG hits."""
from __future__ import annotations

import re
from typing import Any


TYPE_MAP = {
    "circuit breaker": "CB",
    "transformer": "XFMR",
    "switch disconnector": "SD",
}


def _slug_oem(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper())[:12] or "OEM"


def plan_family(spec: dict[str, Any], geometry: dict[str, Any], standards: list[dict]) -> dict[str, Any]:
    eq = (spec.get("equipment") or "").lower()
    type_code = next((v for k, v in TYPE_MAP.items() if k in eq), "EQ")
    kv = int(spec.get("rated_voltage_kv") or 0)
    oem = _slug_oem(spec.get("manufacturer") or "OEM")
    family_name = f"SUB_{type_code}_{kv}KV_{oem}"

    # Prefer CAD envelope when present
    box = (geometry.get("geometry") or [{}])[0] if geometry.get("geometry") else {}
    width = box.get("width") or spec.get("width_mm")
    height = box.get("height") or spec.get("height_mm")
    depth = box.get("depth") or spec.get("depth_mm")

    connectors = []
    for c in geometry.get("connections") or []:
        connectors.append(
            {
                "system": "Power Circuit",
                "x": c["x"],
                "y": c["y"],
                "z": c["z"],
                "direction": c.get("direction", "+Z"),
            }
        )

    params = [
        {"name": "Width", "type": "Length", "value": width, "group": "Dimensions"},
        {"name": "Height", "type": "Length", "value": height, "group": "Dimensions"},
        {"name": "Depth", "type": "Length", "value": depth, "group": "Dimensions"},
        {"name": "Rated_Voltage", "type": "Number", "value": spec.get("rated_voltage_kv"), "group": "Electrical"},
        {"name": "Weight", "type": "Number", "value": spec.get("weight_kg"), "group": "Identity Data"},
        {"name": "Manufacturer", "type": "Text", "value": spec.get("manufacturer"), "group": "Identity Data"},
        {"name": "Model", "type": "Text", "value": spec.get("model"), "group": "Identity Data"},
        {"name": "Mounting", "type": "Text", "value": spec.get("mounting"), "group": "Identity Data"},
    ]

    ops = [
        {"op": "CreateFamilyDocument", "args": {"template": "Electrical Equipment.rft"}},
        {"op": "CreateReferencePlane", "args": {"name": "Left"}},
        {"op": "CreateReferencePlane", "args": {"name": "Right"}},
        {"op": "CreateReferencePlane", "args": {"name": "Front"}},
        {"op": "CreateReferencePlane", "args": {"name": "Back"}},
        {"op": "CreateReferencePlane", "args": {"name": "Bottom"}},
        {"op": "CreateReferencePlane", "args": {"name": "Top"}},
    ]
    for p in params:
        ops.append({"op": "CreateParameter", "args": p})
    ops.append(
        {
            "op": "CreateExtrusion",
            "args": {"width": width, "depth": depth, "height": height, "material": "Substation - Equipment Steel"},
        }
    )
    for i, c in enumerate(connectors, start=1):
        ops.append({"op": "CreateConnector", "args": {**c, "name": f"Terminal_{i}"}})
    ops.append({"op": "CreateType", "args": {"type_name": f"{kv}kV"}})
    ops.append({"op": "SaveFamily", "args": {"path": f"{family_name}.rfa"}})

    return {
        "family_name": family_name,
        "category": "Electrical Equipment",
        "template": "Electrical Equipment.rft",
        "parameters": params,
        "geometry_strategy": {
            "reference_planes": ["Left", "Right", "Front", "Back", "Bottom", "Top"],
            "solids": [{"type": "extrusion", "driven_by": ["Width", "Depth", "Height"]}],
            "materials": ["Substation - Equipment Steel"],
            "visibility": {"coarse": "envelope", "medium": "envelope+connectors", "fine": "envelope+connectors+base"},
        },
        "connectors": connectors,
        "ops": ops,
        "standards_applied": [s.get("path", s.get("title")) for s in standards],
    }


def validate(spec: dict[str, Any], plan: dict[str, Any], tol_mm: float = 5.0) -> dict[str, Any]:
    param_map = {p["name"]: p["value"] for p in plan.get("parameters", [])}
    checks = []

    def check(prop, expected, actual, tolerance=None):
        ok = expected == actual
        if tolerance is not None and expected is not None and actual is not None:
            try:
                ok = abs(float(expected) - float(actual)) <= tolerance
            except (TypeError, ValueError):
                ok = False
        checks.append(
            {
                "property": prop,
                "expected": expected,
                "actual": actual,
                "tolerance": tolerance,
                "status": "PASS" if ok else "FAIL",
            }
        )

    check("Height", spec.get("height_mm"), param_map.get("Height"), tol_mm)
    check("Width", spec.get("width_mm"), param_map.get("Width"), tol_mm)
    check("Depth", spec.get("depth_mm"), param_map.get("Depth"), tol_mm)
    check("Weight", spec.get("weight_kg"), param_map.get("Weight"), 5)
    check("Voltage", spec.get("rated_voltage_kv"), param_map.get("Rated_Voltage"), 0)
    check("Connectors", spec.get("terminal_count"), len(plan.get("connectors") or []))
    naming_ok = bool(re.match(r"^SUB_[A-Z0-9_]+$", plan.get("family_name") or ""))
    checks.append(
        {
            "property": "Naming",
            "expected": "SUB_<TYPE>_<KV>KV_<OEM>",
            "actual": plan.get("family_name"),
            "status": "PASS" if naming_ok else "FAIL",
        }
    )
    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    repair = [c["property"] for c in checks if c["status"] == "FAIL"]
    return {"status": status, "checks": checks, "repair_hints": repair}
