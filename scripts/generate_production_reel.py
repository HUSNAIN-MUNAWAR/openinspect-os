"""Render a deterministic, model-backed inspection animation reel."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image

# Running a script by path puts `scripts/` first on sys.path. Add the project
# root explicitly so the same command works from Windows, CI, and a shell.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.vision.underwater import analyze_underwater_image


SOURCE_DIR = ROOT / "datasets" / "project-owned" / "pipeline"
OUTPUT_DIR = ROOT / "demo" / "outputs"
REEL_PATH = OUTPUT_DIR / "production_inspection_reel.gif"
MANIFEST_PATH = OUTPUT_DIR / "production_inspection_reel_manifest.json"
FRAME_WIDTH, FRAME_HEIGHT = 960, 540


def _repo_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _fit(image: np.ndarray) -> np.ndarray:
    return cv2.resize(image, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)


def _label(frame: np.ndarray, origin: tuple[int, int], value: str, color: tuple[int, int, int], scale: float = 0.55) -> None:
    cv2.putText(frame, value, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def build_reel_frame(image: np.ndarray, frame_index: int, total_frames: int) -> tuple[np.ndarray, dict]:
    """Run the real baseline and render one annotated reel frame."""

    source = _fit(image)
    result = analyze_underwater_image(source)
    overlay = _fit(result.overlay)
    mask = _fit(result.pipeline_mask)

    rendered = cv2.addWeighted(source, 0.62, overlay, 0.38, 0.0)
    mask_color = np.zeros_like(rendered)
    mask_color[:, :, 1] = mask
    blended = cv2.addWeighted(rendered, 0.68, mask_color, 0.32, 0.0)
    rendered = np.where(mask[:, :, None] > 0, blended, rendered)

    cv2.rectangle(rendered, (0, 0), (FRAME_WIDTH, 52), (7, 16, 19), -1)
    cv2.rectangle(rendered, (0, FRAME_HEIGHT - 66), (FRAME_WIDTH, FRAME_HEIGHT), (7, 16, 19), -1)
    _label(rendered, (22, 23), "OPENINSPECT OS  /  PRODUCTION REFERENCE REEL", (67, 216, 196), 0.58)
    _label(rendered, (22, 43), f"FRAME {frame_index + 1:02d}/{total_frames:02d}  |  PIPELINE PASS {frame_index * 0.5:04.1f}s", (233, 244, 241), 0.48)

    phases = ["CAPTURE", "ENHANCE", "SEGMENT", "REVIEW"]
    active = min(len(phases) - 1, frame_index // max(1, total_frames // len(phases)))
    for idx, phase in enumerate(phases):
        x = 24 + idx * 122
        color = (67, 216, 196) if idx == active else (137, 162, 165)
        cv2.circle(rendered, (x, FRAME_HEIGHT - 37), 5, color, -1)
        _label(rendered, (x + 12, FRAME_HEIGHT - 32), phase, color, 0.44)
        if idx < len(phases) - 1:
            cv2.line(rendered, (x + 72, FRAME_HEIGHT - 37), (x + 106, FRAME_HEIGHT - 37), (35, 64, 72), 2)

    _label(rendered, (565, FRAME_HEIGHT - 45), "MODEL  underwater-pipeline-cv / classical-cv-0.1", (233, 244, 241), 0.43)
    _label(rendered, (565, FRAME_HEIGHT - 25), f"CONF {result.confidence:.3f}  VISIBILITY {result.visibility:.3f}", (240, 191, 91), 0.48)
    _label(rendered, (565, FRAME_HEIGHT - 8), "PROJECT-OWNED SYNTHETIC DATA  |  NOT FIELD PERFORMANCE", (137, 162, 165), 0.38)

    record = {
        "frame": frame_index + 1,
        "source": _repo_relative(SOURCE_DIR / f"pipeline_{frame_index:02d}.png"),
        "timestamp_s": round(frame_index * 0.5, 3),
        "model": "underwater-pipeline-cv",
        "model_version": "classical-cv-0.1",
        "confidence": round(result.confidence, 6),
        "visibility": round(result.visibility, 6),
        "provenance": "project-owned synthetic pipeline scene; algorithmic segmentation",
    }
    return rendered, record


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(SOURCE_DIR.glob("pipeline_*.png"))
    if not paths:
        raise SystemExit("No project-owned pipeline frames found; run `python scripts/generate_demo_data.py` first.")

    frames: list[Image.Image] = []
    records: list[dict] = []
    for index, path in enumerate(paths):
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise SystemExit(f"Unable to read synthetic frame: {path}")
        rendered, record = build_reel_frame(image, index, len(paths))
        frames.append(Image.fromarray(cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB)))
        records.append(record)

    frames[0].save(REEL_PATH, save_all=True, append_images=frames[1:], duration=220, loop=0, optimize=True)
    manifest = {
        "name": "OpenInspect OS Production Inspection Reel",
        "version": "0.1.0",
        "reel": _repo_relative(REEL_PATH),
        "source": "datasets/project-owned/pipeline",
        "model": {
            "name": "underwater-pipeline-cv",
            "version": "classical-cv-0.1",
            "implementation": "services.vision.underwater.analyze_underwater_image",
        },
        "limitations": [
            "Frames are project-owned synthetic scenes generated for software validation.",
            "The classical CV baseline is not a learned model or a field-performance claim.",
            "Confidence and visibility values are demo evidence, not calibrated offshore metrics.",
        ],
        "frames": records,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reel": str(REEL_PATH), "manifest": str(MANIFEST_PATH), "frames": len(frames)}, indent=2))


if __name__ == "__main__":
    main()
