from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    env = os.environ.copy()
    paths = [str(ROOT), str(ROOT / "apps" / "api"), str(ROOT / "apps" / "edge-agent")]
    env["PYTHONPATH"] = os.pathsep.join(paths + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    steps = [
        ROOT / "scripts" / "generate_demo_data.py",
        ROOT / "ml" / "evaluation" / "evaluate_demo.py",
        ROOT / "scripts" / "seed_demo.py",
        ROOT / "scripts" / "generate_demo_visuals.py",
    ]
    for step in steps:
        subprocess.run([sys.executable, str(step)], cwd=ROOT, env=env, check=True)
