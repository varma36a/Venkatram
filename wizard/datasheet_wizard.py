"""
Datasheet Wizard — simple window for non-technical users.

Pick a PDF datasheet (+ optional CAD drawing) → creates JSON files in an Output folder.
"""
from __future__ import annotations

import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

def _find_repo() -> Path:
    """Locate project root (folder that contains python/ and rag/)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]

    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "python").is_dir() and (candidate / "rag").is_dir():
            return candidate
    # Fallback: wizard/ is directly under the project
    return here.parent


REPO = _find_repo()
PYTHON = REPO / "python"
for p in (PYTHON, REPO / "python"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


def run_pipeline(pdf: Path, cad: Path | None, out: Path, log) -> None:
    try:
        from cad_agent.parse_dxf import parse_dxf
        from document_agent.extract import extract_text, parse_spec
        from pipeline.planner import plan_family, validate
        from rag.index_corpus import load_corpus, retrieve
    except ImportError as e:
        raise RuntimeError(
            "Missing Python packages. Close this window, run Start-Datasheet-Wizard.bat "
            "again and wait for 'Installing packages' to finish.\n"
            f"Details: {e}"
        ) from e
    import json

    out.mkdir(parents=True, exist_ok=True)
    log(f"Project folder: {REPO}")
    log(f"Reading PDF: {pdf.name}")
    text = extract_text(pdf)
    if not (text or "").strip():
        raise RuntimeError(
            "Could not read text from this PDF. Try the sample file:\n"
            "samples\\datasheets\\ABB_CB_245KV.pdf"
        )
    spec = parse_spec(text, str(pdf))

    if cad and cad.exists():
        log(f"Reading CAD: {cad.name}")
        if cad.suffix.lower() == ".dwg":
            raise RuntimeError(
                "DWG is not supported yet. Save/export the drawing as DXF and try again.\n"
                f"Or use the sample: samples\\cad\\ABB_CB_245KV.dxf"
            )
        geometry = parse_dxf(cad)
    else:
        log("No CAD file — using PDF sizes only")
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

    corpus = REPO / "rag"
    if not corpus.is_dir():
        raise RuntimeError(
            f"Cannot find the 'rag' folder next to the project.\nExpected: {corpus}\n"
            "Re-download/unzip the full GitHub project and try again."
        )
    query = f"{spec.get('equipment')} {spec.get('rated_voltage_kv')} kV family naming"
    log("Looking up company standards…")
    standards = retrieve(load_corpus(corpus), query, k=5)
    plan = plan_family(spec, geometry, standards)
    report = validate(spec, plan)

    (out / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    (out / "geometry.json").write_text(json.dumps(geometry, indent=2), encoding="utf-8")
    (out / "standards.json").write_text(json.dumps(standards, indent=2), encoding="utf-8")
    (out / "family_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (out / "revit_ops.json").write_text(
        json.dumps({"version": "1.0", "ops": plan["ops"]}, indent=2), encoding="utf-8"
    )
    (out / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"Done. Validation: {report['status']}")
    log(f"Main file for Revit: {out / 'revit_ops.json'}")


class Wizard(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Substation Datasheet Wizard")
        self.geometry("640x480")
        self.minsize(560, 420)

        self.pdf = tk.StringVar()
        self.cad = tk.StringVar()
        self.out = tk.StringVar(value=str(Path.home() / "Desktop" / "FamilyOps_Output"))

        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Substation Datasheet → JSON", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(
            frm,
            text="Choose your equipment PDF. Optionally add a CAD drawing.\n"
            "Click Create — JSON files appear in the Output folder.",
            justify="left",
        ).pack(anchor="w", **pad)

        self._row(frm, "1. PDF datasheet *", self.pdf, self._browse_pdf)
        self._row(frm, "2. CAD drawing (optional)", self.cad, self._browse_cad)
        self._row(frm, "3. Output folder", self.out, self._browse_out)

        self.btn = ttk.Button(frm, text="Create JSON files", command=self._start)
        self.btn.pack(fill=tk.X, pady=12)

        ttk.Label(frm, text="Status").pack(anchor="w")
        self.log_box = tk.Text(frm, height=10, wrap="word")
        self.log_box.pack(fill=tk.BOTH, expand=True)

    def _row(self, parent, label, var, cmd) -> None:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(8, 0))
        row = ttk.Frame(parent)
        row.pack(fill=tk.X)
        ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="Browse…", command=cmd).pack(side=tk.LEFT, padx=(8, 0))

    def _browse_pdf(self) -> None:
        p = filedialog.askopenfilename(title="Select PDF datasheet", filetypes=[("PDF", "*.pdf")])
        if p:
            self.pdf.set(p)

    def _browse_cad(self) -> None:
        p = filedialog.askopenfilename(
            title="Select CAD drawing",
            filetypes=[("CAD", "*.dxf *.dwg"), ("DXF", "*.dxf"), ("All", "*.*")],
        )
        if p:
            self.cad.set(p)

    def _browse_out(self) -> None:
        p = filedialog.askdirectory(title="Choose output folder")
        if p:
            self.out.set(p)

    def _log(self, msg: str) -> None:
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.update_idletasks()

    def _start(self) -> None:
        pdf = Path(self.pdf.get().strip())
        if not pdf.exists():
            messagebox.showerror("Missing PDF", "Please choose a PDF datasheet first.")
            return
        cad_s = self.cad.get().strip()
        cad = Path(cad_s) if cad_s else None
        out = Path(self.out.get().strip())
        self.btn.configure(state=tk.DISABLED)
        self.log_box.delete("1.0", tk.END)

        def work():
            try:
                run_pipeline(pdf, cad, out, lambda m: self.after(0, self._log, m))
                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Finished",
                        f"JSON files created in:\n{out}\n\n"
                        "Give your Revit teammate the file named:\nrevit_ops.json",
                    ),
                )
            except Exception as e:
                err = traceback.format_exc()
                self.after(0, self._log, err)
                msg = str(e) if str(e) else "Something went wrong. See the status box."
                self.after(0, lambda m=msg: messagebox.showerror("Error", m))
            finally:
                self.after(0, lambda: self.btn.configure(state=tk.NORMAL))

        threading.Thread(target=work, daemon=True).start()


def main() -> None:
    Wizard().mainloop()


if __name__ == "__main__":
    main()
