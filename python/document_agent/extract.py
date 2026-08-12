"""Deterministic PDF text extraction → equipment spec (regex heuristics for samples)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_spec(text: str, source: str) -> dict[str, Any]:
    def find(pattern: str, cast=str, default=None):
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            return default
        return cast(m.group(1).strip())

    dims = re.search(
        r"Dimensions[^:]*:\s*(\d+)\s*mm\s*x\s*(\d+)\s*mm\s*x\s*(\d+)\s*mm",
        text,
        re.IGNORECASE,
    )
    height = width = depth = None
    if dims:
        height, width, depth = map(int, dims.groups())

    terminals = find(r"Terminals:\s*(\d+)", int)
    return {
        "equipment": find(r"Equipment:\s*(.+)", default="Unknown"),
        "manufacturer": find(r"Manufacturer:\s*(.+)", default="Unknown"),
        "model": find(r"Model:\s*(.+)", default="Unknown"),
        "rated_voltage_kv": find(r"Rated Voltage:\s*(\d+(?:\.\d+)?)", float),
        "height_mm": height,
        "width_mm": width,
        "depth_mm": depth,
        "weight_kg": find(r"Weight:\s*(\d+(?:\.\d+)?)", float),
        "mounting": find(r"Mounting:\s*(.+)"),
        "terminal_count": terminals,
        "units": "metric",
        "source_files": [source],
        "confidence": 0.9 if dims else 0.5,
        "notes": [],
    }
