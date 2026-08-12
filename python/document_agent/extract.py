"""PDF text extraction → equipment spec (regex + OCR fallback for drawing PDFs)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def extract_text(pdf_path: Path) -> str:
    """Extract text; OCR scanned/drawing PDFs when native text is thin."""
    chunks: list[str] = []

    def _usable(t: str) -> bool:
        # Drawing PDFs often only contain a signature stamp — force OCR then.
        if len(t) < 200:
            return False
        keys = ("kV", "mm", "Equipment", "Disconnector", "Breaker", "Transformer", "Dimension", "DRAWING")
        return sum(1 for k in keys if k.lower() in t.lower()) >= 1

    # 1) pypdf
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
    except Exception:
        pass

    text = "\n".join(chunks).strip()
    if _usable(text):
        return text

    # 2) PyMuPDF native text
    try:
        import pymupdf

        doc = pymupdf.open(str(pdf_path))
        chunks = [page.get_text("text") or "" for page in doc]
        text = "\n".join(chunks).strip()
        if _usable(text):
            return text
    except Exception:
        pass

    # 3) OCR (drawing / scanned sheets)
    try:
        import io

        import pymupdf
        import pytesseract
        from PIL import Image

        doc = pymupdf.open(str(pdf_path))
        ocr_parts: list[str] = []
        for page in doc:
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_parts.append(pytesseract.image_to_string(img) or "")
        text = "\n".join(ocr_parts).strip()
        if text:
            return text
    except Exception as e:
        return text or f"[OCR unavailable: {e}]"

    return text


def _from_filename(path: str) -> dict[str, Any]:
    """Best-effort hints from names like DIN-50923_S3CD-3_2T-300_3150_revC.pdf"""
    name = Path(path).stem
    out: dict[str, Any] = {}
    # ...-300_3150 or ...-300/3150 → kV / A
    m = re.search(r"(?i)(?:^|[_\-/])(\d{2,3})[_\-/](\d{3,5})(?:_|$|rev)", name)
    if m:
        out["rated_voltage_kv"] = float(m.group(1))
        out["rated_current_a"] = float(m.group(2))
    m = re.search(r"(?i)(S3CD[\w\-/]*\d)", name)
    if m:
        out["model"] = m.group(1).replace("_", "/")
    if re.search(r"(?i)disconnect|S3CD|RCP", name):
        out["equipment"] = "Switch Disconnector"
    if re.search(r"(?i)\bGE\b|Grid.?Solutions", name):
        out["manufacturer"] = "GE"
    return out


def parse_spec(text: str, source: str) -> dict[str, Any]:
    def find(pattern: str, cast=str, default=None):
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if not m:
            return default
        return cast(m.group(1).strip())

    hints = _from_filename(source)

    # HxWxD style
    dims = re.search(
        r"Dimensions[^:]*:\s*(\d+)\s*mm\s*x\s*(\d+)\s*mm\s*x\s*(\d+)\s*mm",
        text,
        re.IGNORECASE,
    )
    height = width = depth = None
    if dims:
        height, width, depth = map(int, dims.groups())

    # Drawing callouts common on HV gear sheets (OCR)
    if height is None:
        # e.g. 3290±20 or 3110±20 — take the larger as overall height hint
        hs = [int(x) for x in re.findall(r"\b(3\d{3})\s*±\s*\d+", text)]
        if hs:
            height = max(hs)
        else:
            m = re.search(r"\b(39\d{2}|3[12]\d{2})\b", text)
            if m:
                height = int(m.group(1))

    if width is None:
        # phase spacing / overall often ~3200 on this family of drawings
        m = re.search(r"\b(3200|3500|4000|4500)\b", text)
        if m:
            width = int(m.group(1))
        elif hints.get("rated_voltage_kv"):
            width = 3500  # Xb min often used as footprint length

    if depth is None:
        m = re.search(r"~\s*(1[5-9]\d{2}|2\d{3})\b", text)
        if m:
            depth = int(m.group(1))
        else:
            m = re.search(r"\b(1700|1800|2000|2200)\b", text)
            if m:
                depth = int(m.group(1))

    equipment = find(r"Equipment(?:\s*Type)?\s*:\s*(.+)", default=None)
    if not equipment:
        if re.search(r"(?i)disconnector", text):
            equipment = "Switch Disconnector"
        elif re.search(r"(?i)circuit\s*breaker", text):
            equipment = "Circuit Breaker"
        elif re.search(r"(?i)transformer", text):
            equipment = "Transformer"
        else:
            equipment = hints.get("equipment", "Unknown")

    manufacturer = find(r"Manufacturer\s*:\s*(.+)", default=None)
    if not manufacturer:
        if re.search(r"(?i)Grid Solutions|GE Grid|\bGE\b", text):
            manufacturer = "GE"
        elif re.search(r"(?i)\bABB\b", text):
            manufacturer = "ABB"
        elif re.search(r"(?i)Siemens", text):
            manufacturer = "Siemens"
        else:
            manufacturer = hints.get("manufacturer", "Unknown")

    model = find(r"Model\s*:\s*(.+)", default=None)
    if not model:
        m = re.search(r"(S3CD[\w\-/]+?\d{3,4}/\d{3,5})", text, re.IGNORECASE)
        if m:
            model = m.group(1)
        else:
            model = hints.get("model", "Unknown")

    voltage = find(r"(?:Rated\s*)?Voltage\s*:?\s*(\d+(?:\.\d+)?)\s*kV", float)
    if voltage is None:
        m = re.search(r"\b(\d{2,3})\s*kV\b", text, re.IGNORECASE)
        if m:
            voltage = float(m.group(1))
        else:
            voltage = hints.get("rated_voltage_kv")

    weight = find(r"Weight\s*:?\s*(\d+(?:\.\d+)?)", float)
    mounting = find(r"Mounting\s*:\s*(.+)")
    terminals = find(r"Terminals?\s*:?\s*(\d+)", int)
    if terminals is None and re.search(r"(?i)three[\s-]*pole|3[\s-]*pole", text):
        terminals = 3

    notes = []
    if "OCR" in text[:40] or len(text) > 200 and not dims:
        notes.append("Parsed from drawing PDF (OCR / title block heuristics)")

    return {
        "equipment": (equipment or "Unknown").split("\n")[0].strip(),
        "manufacturer": (manufacturer or "Unknown").split("\n")[0].strip(),
        "model": (model or "Unknown").split("\n")[0].strip(),
        "rated_voltage_kv": voltage,
        "height_mm": height,
        "width_mm": width,
        "depth_mm": depth,
        "weight_kg": weight,
        "mounting": mounting,
        "terminal_count": terminals,
        "units": "metric",
        "source_files": [source],
        "confidence": 0.85 if (voltage and height and width) else 0.55,
        "notes": notes,
    }
