from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile
import json
import shutil

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from services.vision.structural import analyze_file

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "external_data" / "crack-seg"
ZIP_PATH = DATA_ROOT / "crack-seg.zip"
EXTRACT_ROOT = DATA_ROOT / "archive"
OUTPUT_ROOT = ROOT / "docs" / "external-evaluation"
SCREENSHOT_PATH = ROOT / "docs" / "screenshots" / "external-crackseg-bboxes.png"
SUMMARY_PATH = OUTPUT_ROOT / "crackseg-summary.json"
DATASET_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/crack-seg.zip"


@dataclass(slots=True)
class SampleResult:
    image: str
    gt_boxes: int
    predicted_boxes: int
    confidence: float
    severity: str
    affected_area_percent: float


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def ensure_dataset() -> Path:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if not ZIP_PATH.exists():
        print(f"Downloading Crack-Seg dataset sample from {DATASET_URL}")
        urlretrieve(DATASET_URL, ZIP_PATH)
    if not EXTRACT_ROOT.exists():
        with ZipFile(ZIP_PATH) as archive:
            archive.extractall(EXTRACT_ROOT)
    return EXTRACT_ROOT


def dataset_root() -> Path:
    ensure_dataset()
    candidates = [p for p in EXTRACT_ROOT.rglob("data.yaml")]
    if candidates:
        return candidates[0].parent
    return EXTRACT_ROOT


def yolo_seg_boxes(label_path: Path, width: int, height: int) -> list[tuple[int, int, int, int]]:
    if not label_path.exists():
        return []
    boxes: list[tuple[int, int, int, int]] = []
    for raw in label_path.read_text().splitlines():
        parts = raw.split()
        if len(parts) < 7:
            continue
        coords = [float(x) for x in parts[1:]]
        xs = coords[0::2]
        ys = coords[1::2]
        x1 = max(0, int(min(xs) * width))
        y1 = max(0, int(min(ys) * height))
        x2 = min(width - 1, int(max(xs) * width))
        y2 = min(height - 1, int(max(ys) * height))
        if x2 > x1 and y2 > y1:
            boxes.append((x1, y1, x2, y2))
    return boxes


def predicted_boxes(mask_path: Path) -> list[tuple[int, int, int, int]]:
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return []
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[int, int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        aspect = max(w / max(h, 1), h / max(w, 1))
        if area >= 180 and max(w, h) >= 18 and (aspect >= 1.4 or area >= 700):
            candidates.append((x, y, x + w, y + h, int(area)))
    candidates.sort(key=lambda item: item[4], reverse=True)
    return [(x1, y1, x2, y2) for x1, y1, x2, y2, _ in candidates[:8]]


def draw_panel(image_path: Path, gt: list[tuple[int, int, int, int]], pred: list[tuple[int, int, int, int]], result: dict) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((520, 360))
    original_w, original_h = Image.open(image_path).size
    sx = image.width / original_w
    sy = image.height / original_h
    canvas = Image.new("RGB", (560, 470), "#0d1418")
    canvas.paste(image, (20, 66))
    draw = ImageDraw.Draw(canvas)
    title_font = _font(20, True)
    body_font = _font(13)
    small_font = _font(11)
    draw.text((20, 18), image_path.name, fill="#eaf1f4", font=title_font)
    draw.text((20, 42), "External Crack-Seg sample - green: dataset label, red: OpenInspect candidate", fill="#8ea0a8", font=small_font)
    for box in gt:
        x1, y1, x2, y2 = box
        draw.rectangle((20 + x1 * sx, 66 + y1 * sy, 20 + x2 * sx, 66 + y2 * sy), outline="#70d69a", width=3)
    for box in pred:
        x1, y1, x2, y2 = box
        draw.rectangle((20 + x1 * sx, 66 + y1 * sy, 20 + x2 * sx, 66 + y2 * sy), outline="#ff625d", width=3)
    y = 66 + image.height + 18
    measurement = result["measurement"]
    lines = [
        f"confidence: {result['confidence']:.2f}",
        f"severity: {result['severity']}",
        f"affected area: {measurement['affected_area_percent']:.2f}%",
        f"gt boxes: {len(gt)} / predicted boxes: {len(pred)}",
    ]
    for line in lines:
        draw.text((20, y), line, fill="#d7e3e6", font=body_font)
        y += 20
    return canvas


def main() -> None:
    root = dataset_root()
    image_dir = root / "images" / "test"
    label_dir = root / "labels" / "test"
    if not image_dir.exists():
        image_dir = next(root.rglob("images/test"))
        label_dir = image_dir.parents[1] / "labels" / "test"
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    processed = OUTPUT_ROOT / "processed"
    if processed.exists():
        shutil.rmtree(processed)
    processed.mkdir(parents=True)

    image_paths = sorted([*image_dir.glob("*.jpg"), *image_dir.glob("*.png")])[:4]
    panels: list[Image.Image] = []
    results: list[SampleResult] = []
    for image_path in image_paths:
        result = analyze_file(image_path, processed)
        image = Image.open(image_path)
        gt = yolo_seg_boxes(label_dir / f"{image_path.stem}.txt", image.width, image.height)
        pred = predicted_boxes(Path(result["mask"]))
        panels.append(draw_panel(image_path, gt, pred, result))
        results.append(
            SampleResult(
                image=image_path.name,
                gt_boxes=len(gt),
                predicted_boxes=len(pred),
                confidence=float(result["confidence"]),
                severity=str(result["severity"]),
                affected_area_percent=float(result["measurement"]["affected_area_percent"]),
            )
        )

    board = Image.new("RGB", (1120, 980), "#071013")
    draw = ImageDraw.Draw(board)
    draw.text((30, 24), "OpenInspect OS External Crack-Seg Smoke Test", fill="#eaf1f4", font=_font(28, True))
    draw.text((30, 58), "Green boxes are dataset labels. Red boxes are OpenInspect mask-derived candidate regions. This is a qualitative smoke test, not a benchmark claim.", fill="#8ea0a8", font=_font(14))
    for idx, panel in enumerate(panels):
        x = 0 if idx % 2 == 0 else 560
        y = 96 if idx < 2 else 540
        board.paste(panel, (x, y))
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    board.save(SCREENSHOT_PATH, quality=94)
    SUMMARY_PATH.write_text(json.dumps([asdict(r) for r in results], indent=2))
    print(json.dumps({"screenshot": str(SCREENSHOT_PATH), "summary": str(SUMMARY_PATH), "samples": len(results)}, indent=2))


if __name__ == "__main__":
    main()
