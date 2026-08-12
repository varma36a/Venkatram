"""CLI: generate .rfa for a job folder via APS Design Automation."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aps.da_client import ApsError, generate_rfa


def main() -> None:
    p = argparse.ArgumentParser(description="APS Design Automation → .rfa")
    p.add_argument("--job", type=Path, required=True, help="Job output folder with revit_ops.json")
    p.add_argument(
        "--template",
        type=Path,
        default=Path(os.environ.get("APS_TEMPLATE_RFT", "revit/templates/template.rft")),
    )
    args = p.parse_args()
    template = args.template
    if not template.is_absolute():
        template = (Path(__file__).resolve().parents[2] / template).resolve()
    try:
        path = generate_rfa(args.job, template)
        print(path)
    except ApsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
