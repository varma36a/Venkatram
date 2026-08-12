"""Deterministic DXF parse → geometry JSON."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import ezdxf


def parse_dxf(path: Path) -> dict[str, Any]:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    layers: set[str] = set()
    width = height = depth = None
    connections: list[dict[str, Any]] = []

    for e in msp:
        layers.add(e.dxf.layer)
        if e.dxftype() == "TEXT" and e.dxf.layer.upper() == "DIMS":
            # e.g. W=1800 H=3200 D=1200
            import re

            t = e.dxf.text
            wm = re.search(r"W\s*=\s*(\d+)", t, re.I)
            hm = re.search(r"H\s*=\s*(\d+)", t, re.I)
            dm = re.search(r"D\s*=\s*(\d+)", t, re.I)
            if wm:
                width = float(wm.group(1))
            if hm:
                height = float(hm.group(1))
            if dm:
                depth = float(dm.group(1))
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer.upper() == "ENVELOPE":
            pts = list(e.get_points("xy"))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if xs and ys and width is None:
                width = max(xs) - min(xs)
            if xs and ys and depth is None:
                depth = max(ys) - min(ys)
        if e.dxftype() == "POINT" and e.dxf.layer.upper() == "TERMINALS":
            connections.append(
                {
                    "type": "electrical",
                    "name": f"T{len(connections)+1}",
                    "x": float(e.dxf.location.x),
                    "y": float(e.dxf.location.y),
                    "z": float(e.dxf.location.z),
                    "direction": "+Z",
                }
            )

    geometry = []
    if width and height and depth:
        geometry.append(
            {
                "type": "box",
                "width": width,
                "height": height,
                "depth": depth,
                "origin": {"x": 0, "y": 0, "z": 0},
            }
        )

    return {
        "units": "mm",
        "geometry": geometry,
        "connections": connections,
        "layers_used": sorted(layers),
    }
