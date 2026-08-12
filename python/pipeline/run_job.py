"""End-to-end: PDF + DXF → plan → validation → optional APS .rfa."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cad_agent.parse_dxf import parse_dxf
from document_agent.extract import extract_text, parse_spec
from pipeline.planner import plan_family, validate
from rag.index_corpus import load_corpus, retrieve


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF/CAD → Revit family plan (+ optional APS .rfa)")
    parser.add_argument("--pdf", type=Path, required=True, help="Equipment datasheet PDF")
    parser.add_argument("--cad", type=Path, default=None, help="Optional DXF drawing (omit if you only have PDF)")
    parser.add_argument("--corpus", type=Path, default=REPO / "rag")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--aps", action="store_true", help="Generate real .rfa via APS Design Automation")
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Family .rft template (or set APS_TEMPLATE_RFT)",
    )
    args = parser.parse_args()

    _load_dotenv(REPO / ".env")
    args.out.mkdir(parents=True, exist_ok=True)

    text = extract_text(args.pdf)
    spec = parse_spec(text, str(args.pdf))
    if args.cad and args.cad.exists():
        geometry = parse_dxf(args.cad)
    else:
        # PDF-only: build envelope from datasheet dimensions
        geometry = {
            "units": "mm",
            "geometry": [
                {
                    "type": "box",
                    "width": spec.get("width_mm") or 1000,
                    "height": spec.get("height_mm") or 1000,
                    "depth": spec.get("depth_mm") or 1000,
                    "origin": {"x": 0, "y": 0, "z": 0},
                }
            ],
            "connections": [],
            "layers_used": [],
        }
        if not args.cad:
            print("No CAD file — using PDF dimensions only")

    query = (
        f"{spec.get('equipment')} {spec.get('rated_voltage_kv')} kV "
        f"family naming parameters connectors BIM standard"
    )
    chunks = load_corpus(args.corpus)
    standards = retrieve(chunks, query, k=5)

    plan = plan_family(spec, geometry, standards)
    report = validate(spec, plan)

    (args.out / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    (args.out / "geometry.json").write_text(json.dumps(geometry, indent=2), encoding="utf-8")
    (args.out / "standards.json").write_text(json.dumps(standards, indent=2), encoding="utf-8")
    (args.out / "family_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (args.out / "revit_ops.json").write_text(
        json.dumps({"version": "1.0", "ops": plan["ops"]}, indent=2), encoding="utf-8"
    )
    (args.out / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    stub = args.out / f"{plan['family_name']}.rfa.stub.md"
    stub.write_text(
        "\n".join(
            [
                f"# Generate-ready package: {plan['family_name']}.rfa",
                "",
                "Run with `--aps` after APS setup (see revit/APS_SETUP.md).",
                "",
                f"Validation: **{report['status']}**",
                "",
                "Ops count: " + str(len(plan["ops"])),
            ]
        ),
        encoding="utf-8",
    )
    print(f"Job written to {args.out} — validation={report['status']}")

    if args.aps:
        from aps.da_client import generate_rfa

        template = args.template or Path(os.environ.get("APS_TEMPLATE_RFT", "revit/templates/template.rft"))
        if not template.is_absolute():
            template = (REPO / template).resolve()
        rfa = generate_rfa(args.out, template, family_name=plan["family_name"])
        print(f"RFA: {rfa}")


if __name__ == "__main__":
    main()
