"""Run the real OpenInspect structural analyzer and preserve a video of its output.

This is deliberately an evidence runner, not a visual mockup.  Every frame is
made from an image in the external Crack-Seg test split and every red box is
derived from the mask written by ``services.vision.structural.analyze_file``.
The repeated frames make the result watchable; they do not interpolate or
invent detections.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import shutil
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.external_crackseg_smoke_test import (  # noqa: E402
    DATASET_URL,
    ZIP_PATH,
    dataset_root,
    predicted_boxes,
    yolo_seg_boxes,
)
from services.vision.structural import analyze_file  # noqa: E402


OUTPUT_ROOT = ROOT / "docs" / "external-evaluation" / "runtime-smoke"
PROCESSED_ROOT = ROOT / "docs" / "external-evaluation" / "processed"
VIDEO_PATH = OUTPUT_ROOT / "runtime_video.mp4"
POSTER_PATH = OUTPUT_ROOT / "runtime_poster.png"
CSV_PATH = OUTPUT_ROOT / "runtime_predictions.csv"
SUMMARY_PATH = OUTPUT_ROOT / "runtime_summary.json"
IOU_THRESHOLD = 0.5
FRAMES_PER_SAMPLE = 6
FPS = 6


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def box_iou(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> float:
    lx1, ly1, lx2, ly2 = left
    rx1, ry1, rx2, ry2 = right
    ix1, iy1 = max(lx1, rx1), max(ly1, ry1)
    ix2, iy2 = min(lx2, rx2), min(ly2, ry2)
    intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    left_area = max(0, lx2 - lx1) * max(0, ly2 - ly1)
    right_area = max(0, rx2 - rx1) * max(0, ry2 - ry1)
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def match_predictions(
    gt_boxes: list[tuple[int, int, int, int]],
    pred_boxes: list[tuple[int, int, int, int]],
) -> tuple[dict[int, tuple[int | None, float]], dict[str, int]]:
    """Greedily match each prediction to its best still-unmatched GT box."""

    matches: dict[int, tuple[int | None, float]] = {}
    used_gt: set[int] = set()
    true_positive = 0
    for pred_index, pred_box in enumerate(pred_boxes):
        candidates = [
            (box_iou(pred_box, gt_box), gt_index)
            for gt_index, gt_box in enumerate(gt_boxes)
            if gt_index not in used_gt
        ]
        iou, gt_index = max(candidates, default=(0.0, None))
        if gt_index is not None and iou >= IOU_THRESHOLD:
            used_gt.add(gt_index)
            true_positive += 1
            matches[pred_index] = (gt_index, iou)
        else:
            matches[pred_index] = (None, iou)
    counts = {
        "true_positive": true_positive,
        "false_positive": len(pred_boxes) - true_positive,
        "false_negative": len(gt_boxes) - true_positive,
    }
    return matches, counts


def fit_image(image: np.ndarray, max_width: int = 800, max_height: int = 560) -> tuple[np.ndarray, float, int, int]:
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height)
    resized = cv2.resize(image, (max(1, round(width * scale)), max(1, round(height * scale))))
    return resized, scale, (max_width - resized.shape[1]) // 2, (max_height - resized.shape[0]) // 2


def put_text(canvas: np.ndarray, text: str, origin: tuple[int, int], scale: float = 0.65, color: tuple[int, int, int] = (220, 232, 236), thickness: int = 1) -> None:
    cv2.putText(canvas, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def render_frame(
    image_path: Path,
    gt_boxes: list[tuple[int, int, int, int]],
    pred_boxes: list[tuple[int, int, int, int]],
    matches: dict[int, tuple[int | None, float]],
    result: dict,
    frame_number: int,
    frame_count: int,
) -> np.ndarray:
    source = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if source is None:
        raise ValueError(f"unable to read source image: {image_path}")
    display, scale, offset_x, offset_y = fit_image(source)
    canvas = np.full((720, 1280, 3), (7, 16, 19), dtype=np.uint8)
    x0, y0 = 40 + offset_x, 110 + offset_y
    canvas[y0 : y0 + display.shape[0], x0 : x0 + display.shape[1]] = display

    def display_box(box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = box
        return (round(x0 + x1 * scale), round(y0 + y1 * scale), round(x0 + x2 * scale), round(y0 + y2 * scale))

    for box in gt_boxes:
        cv2.rectangle(canvas, display_box(box)[:2], display_box(box)[2:], (104, 214, 154), 2)
    for pred_index, box in enumerate(pred_boxes):
        matched_gt, iou = matches[pred_index]
        cv2.rectangle(canvas, display_box(box)[:2], display_box(box)[2:], (93, 98, 255), 2)
        label = f"P{pred_index + 1} {'TP' if matched_gt is not None else 'FP'}"
        if matched_gt is not None:
            label += f" {iou:.2f}"
        bx1, by1, _, _ = display_box(box)
        put_text(canvas, label, (bx1, max(98, by1 - 7)), 0.48, (93, 98, 255), 1)

    measurement = result["measurement"]
    counts = {
        "gt": len(gt_boxes),
        "pred": len(pred_boxes),
        "tp": sum(1 for gt_index, _ in matches.values() if gt_index is not None),
    }
    counts["fp"] = counts["pred"] - counts["tp"]
    put_text(canvas, "OpenInspect OS - REAL LOCAL RUNTIME", (40, 45), 1.0, (234, 241, 244), 2)
    put_text(canvas, f"source: {image_path.name}  |  frame {frame_number}/{frame_count}", (40, 78), 0.62, (142, 160, 168))
    put_text(canvas, "green = Crack-Seg label   red = mask-derived OpenInspect candidate", (40, 690), 0.55, (142, 160, 168))
    panel_x = 885
    put_text(canvas, "Evidence from services.vision.structural", (panel_x, 140), 0.62, (234, 241, 244), 1)
    lines = [
        "algorithm: deterministic classical CV",
        "learned checkpoint: none",
        f"confidence: {float(result['confidence']):.2f}",
        f"severity: {result['severity']}",
        f"affected area: {float(measurement['affected_area_percent']):.2f}%",
        "",
        f"ground-truth boxes: {counts['gt']}",
        f"predicted boxes: {counts['pred']}",
        f"matched TP (IoU >= {IOU_THRESHOLD:.1f}): {counts['tp']}",
        f"false positives: {counts['fp']}",
    ]
    for index, line in enumerate(lines):
        put_text(canvas, line, (panel_x, 180 + index * 29), 0.58, (215, 227, 230))
    return canvas


def main() -> None:
    root = dataset_root()
    image_dir = root / "images" / "test"
    label_dir = root / "labels" / "test"
    if not image_dir.exists():
        image_dir = next(root.rglob("images/test"))
        label_dir = image_dir.parents[1] / "labels" / "test"
    image_paths = sorted([*image_dir.glob("*.jpg"), *image_dir.glob("*.png")])[:4]
    if not image_paths:
        raise RuntimeError(f"no test images found under {image_dir}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if PROCESSED_ROOT.exists():
        shutil.rmtree(PROCESSED_ROOT)
    PROCESSED_ROOT.mkdir(parents=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(VIDEO_PATH), fourcc, FPS, (1280, 720))
    if not writer.isOpened():
        raise RuntimeError(f"unable to open video writer for {VIDEO_PATH}")

    rows: list[dict[str, object]] = []
    per_sample: list[dict[str, object]] = []
    total = {"ground_truth": 0, "predicted": 0, "true_positive": 0, "false_positive": 0, "false_negative": 0}
    first_frame: np.ndarray | None = None
    frame_count = len(image_paths) * FRAMES_PER_SAMPLE
    frame_number = 0
    try:
        for sample_index, image_path in enumerate(image_paths, start=1):
            result = analyze_file(image_path, PROCESSED_ROOT)
            image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"unable to read source image: {image_path}")
            height, width = image.shape[:2]
            gt_boxes = yolo_seg_boxes(label_dir / f"{image_path.stem}.txt", width, height)
            pred_boxes = predicted_boxes(Path(result["mask"]))
            matches, counts = match_predictions(gt_boxes, pred_boxes)
            for key in total:
                total[key] += counts.get(key, 0) if key != "ground_truth" and key != "predicted" else (len(gt_boxes) if key == "ground_truth" else len(pred_boxes))
            per_sample.append(
                {
                    "sample_index": sample_index,
                    "image": str(image_path.relative_to(ROOT)),
                    "ground_truth_boxes": len(gt_boxes),
                    "predicted_boxes": len(pred_boxes),
                    **counts,
                    "confidence": round(float(result["confidence"]), 6),
                    "severity": result["severity"],
                    "affected_area_percent": round(float(result["measurement"]["affected_area_percent"]), 6),
                    "mask": str(Path(result["mask"]).relative_to(ROOT)),
                    "overlay": str(Path(result["overlay"]).relative_to(ROOT)),
                }
            )
            for pred_index, pred_box in enumerate(pred_boxes):
                matched_gt, iou = matches[pred_index]
                rows.append(
                    {
                        "sample_index": sample_index,
                        "image": image_path.name,
                        "prediction_index": pred_index,
                        "x1": pred_box[0],
                        "y1": pred_box[1],
                        "x2": pred_box[2],
                        "y2": pred_box[3],
                        "matched_ground_truth_index": "" if matched_gt is None else matched_gt,
                        "iou": f"{iou:.6f}",
                        "status": "TP" if matched_gt is not None else "FP",
                        "confidence": f"{float(result['confidence']):.6f}",
                        "severity": result["severity"],
                    }
                )
            for _ in range(FRAMES_PER_SAMPLE):
                frame_number += 1
                frame = render_frame(image_path, gt_boxes, pred_boxes, matches, result, frame_number, frame_count)
                if first_frame is None:
                    first_frame = frame.copy()
                writer.write(frame)
    finally:
        writer.release()

    if first_frame is None:
        raise RuntimeError("runtime produced no frames")
    cv2.imwrite(str(POSTER_PATH), first_frame)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(rows[0]) if rows else ["sample_index", "image"]
        csv_writer = csv.DictWriter(handle, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(rows)

    denominator_precision = total["true_positive"] + total["false_positive"]
    denominator_recall = total["true_positive"] + total["false_negative"]
    precision = total["true_positive"] / denominator_precision if denominator_precision else 0.0
    recall = total["true_positive"] / denominator_recall if denominator_recall else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    output_hashes = {
        str(path.relative_to(ROOT)): file_sha256(path)
        for path in (VIDEO_PATH, POSTER_PATH, CSV_PATH)
    }
    summary = {
        "run_type": "external_crackseg_real_runtime_video",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": "py -3.12 -u scripts/generate_external_crackseg_runtime_video.py",
        "source": {
            "dataset": "Ultralytics Crack-Seg test split",
            "dataset_url": DATASET_URL,
            "archive": str(ZIP_PATH.relative_to(ROOT)),
            "archive_sha256": file_sha256(ZIP_PATH),
            "images_used": len(image_paths),
            "frames_per_image": FRAMES_PER_SAMPLE,
            "note": "Raw external data is not committed; the archive hash identifies the local input.",
        },
        "algorithm": {
            "entrypoint": "services.vision.structural.analyze_file",
            "type": "deterministic classical computer vision",
            "learned_model": None,
            "checkpoint": None,
            "device": "cpu",
            "matching_iou_threshold": IOU_THRESHOLD,
        },
        "runtime": {
            "python": platform.python_version(),
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "aggregate": {
            **total,
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
        },
        "per_sample": per_sample,
        "outputs": {
            "video": str(VIDEO_PATH.relative_to(ROOT)),
            "poster": str(POSTER_PATH.relative_to(ROOT)),
            "predictions_csv": str(CSV_PATH.relative_to(ROOT)),
            "sha256": output_hashes,
        },
        "interpretation": [
            "This video is a genuine local execution trace over four external test images.",
            "Repeated frames hold each analyzed input so the execution trace is readable; no detections are animated into existence.",
            "The result is a smoke test, not a learned-model benchmark or factory-performance claim.",
            "The observed false positives are retained as a limitation of this baseline.",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"video": str(VIDEO_PATH), "poster": str(POSTER_PATH), "summary": str(SUMMARY_PATH), "aggregate": summary["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()
