from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "demo" / "outputs"

partial = json.loads((OUTPUT / "partial_summary.json").read_text())
reports = json.loads((OUTPUT / "reports_manifest.json").read_text())
partial["reports"] = reports
summary_path = OUTPUT / "demo_summary.json"
summary_path.write_text(json.dumps(partial, indent=2))
print(json.dumps({
    "summary": str(summary_path),
    "reports": [r["object_path"] for r in reports],
    "dashboard": partial["dashboard"],
    "sync_replay": partial["edge"]["duplicate_replay"]["status"],
}, indent=2), flush=True)
import os as _os
_os._exit(0)
