"""Generate minimal sample PDF datasheets (no external deps)."""
from __future__ import annotations

from pathlib import Path


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(path: Path, lines: list[str]) -> None:
    """Write a one-page PDF with Helvetica text lines."""
    y = 750
    content_lines = ["BT", "/F1 11 Tf"]
    for line in lines:
        content_lines.append(f"50 {y} Td ({_escape(line)}) Tj")
        content_lines.append("0 -16 Td")
        y -= 16
        # After first Td absolute, subsequent are relative — simplify:
    # Rebuild with absolute positioning for reliability
    content_lines = ["BT", "/F1 11 Tf"]
    y = 750
    for line in lines:
        content_lines.append(f"1 0 0 1 50 {y} Tm ({_escape(line)}) Tj")
        y -= 16
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out)


DATASHEETS = {
    "ABB_CB_245KV.pdf": [
        "ABB HIGH VOLTAGE PRODUCTS — TECHNICAL DATASHEET",
        "Equipment: Circuit Breaker",
        "Manufacturer: ABB",
        "Model: CB-245",
        "Rated Voltage: 245 kV",
        "Rated Frequency: 50/60 Hz",
        "Dimensions (H x W x D): 3200 mm x 1800 mm x 1200 mm",
        "Weight: 850 kg",
        "Mounting: Steel structure",
        "Terminals: 3 (top exits)",
        "Insulation: SF6",
        "Standard: IEC 62271-100",
    ],
    "Siemens_XFMR_132KV.pdf": [
        "SIEMENS ENERGY — POWER TRANSFORMER DATASHEET",
        "Equipment: Transformer",
        "Manufacturer: Siemens",
        "Model: XFMR-132-50",
        "Rated Voltage: 132 kV",
        "Rated Power: 50 MVA",
        "Dimensions (H x W x D): 4500 mm x 3200 mm x 2800 mm",
        "Weight: 42000 kg",
        "Mounting: Concrete pad",
        "Terminals: 6 (HV/LV bushings)",
        "Cooling: ONAN/ONAF",
        "Standard: IEC 60076",
    ],
    "GE_SD_145KV.pdf": [
        "GE VERNOVA — SWITCH DISCONNECTOR DATASHEET",
        "Equipment: Switch Disconnector",
        "Manufacturer: GE",
        "Model: SD-145",
        "Rated Voltage: 145 kV",
        "Dimensions (H x W x D): 2900 mm x 1600 mm x 1100 mm",
        "Weight: 620 kg",
        "Mounting: Steel structure",
        "Terminals: 3",
        "Operation: Motor / Manual",
        "Standard: IEC 62271-102",
    ],
}


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "samples" / "datasheets"
    for name, lines in DATASHEETS.items():
        write_simple_pdf(root / name, lines)
        print(f"Wrote {root / name}")


if __name__ == "__main__":
    main()
