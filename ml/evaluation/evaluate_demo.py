from __future__ import annotations

from pathlib import Path
import json
import time

import cv2
import numpy as np

from services.vision.structural import analyze_structural_image
from services.vision.underwater import analyze_underwater_image

ROOT = Path(__file__).resolve().parents[2]


def metrics(pred: np.ndarray, gt: np.ndarray) -> dict:
    p = pred > 0
    g = gt > 0
    tp = int(np.logical_and(p, g).sum())
    fp = int(np.logical_and(p, ~g).sum())
    fn = int(np.logical_and(~p, g).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    iou = tp / max(tp + fp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    return {"precision": precision, "recall": recall, "iou": iou, "f1": f1}


def evaluate_structural() -> dict:
    rows = []
    latencies = []
    for image_path in sorted((ROOT / "datasets/project-owned/structural").glob("*.png")):
        gt_path = ROOT / "datasets/project-owned/ground_truth" / f"{image_path.stem}_mask.png"
        image = cv2.imread(str(image_path)); gt = cv2.imread(str(gt_path), cv2.IMREAD_GRAYSCALE)
        start = time.perf_counter(); result = analyze_structural_image(image); latencies.append((time.perf_counter()-start)*1000)
        row = metrics(result.mask, gt); row["image"] = image_path.name; rows.append(row)
    return {
        "images": len(rows),
        "precision": float(np.mean([r["precision"] for r in rows])),
        "recall": float(np.mean([r["recall"] for r in rows])),
        "iou": float(np.mean([r["iou"] for r in rows])),
        "f1": float(np.mean([r["f1"] for r in rows])),
        "cpu_latency_ms_mean": float(np.mean(latencies)),
        "cpu_latency_ms_p95": float(np.percentile(latencies,95)),
        "per_image": rows,
    }


def evaluate_pipeline() -> dict:
    rows = []
    latencies = []
    for image_path in sorted((ROOT / "datasets/project-owned/pipeline").glob("*.png")):
        gt_path = ROOT / "datasets/project-owned/ground_truth" / f"{image_path.stem}_mask.png"
        image = cv2.imread(str(image_path)); gt = cv2.imread(str(gt_path), cv2.IMREAD_GRAYSCALE)
        start = time.perf_counter(); result = analyze_underwater_image(image); latencies.append((time.perf_counter()-start)*1000)
        row = metrics(result.pipeline_mask, gt); row["image"] = image_path.name; row["visibility"] = result.visibility; rows.append(row)
    return {
        "images": len(rows),
        "precision": float(np.mean([r["precision"] for r in rows])),
        "recall": float(np.mean([r["recall"] for r in rows])),
        "iou": float(np.mean([r["iou"] for r in rows])),
        "f1": float(np.mean([r["f1"] for r in rows])),
        "cpu_latency_ms_mean": float(np.mean(latencies)),
        "cpu_latency_ms_p95": float(np.percentile(latencies,95)),
        "mean_visibility": float(np.mean([r["visibility"] for r in rows])),
        "per_image": rows,
    }


def main() -> None:
    output = ROOT / "demo/outputs"
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "dataset": "OpenInspect OS Project-Owned Demo Dataset v0.1.0",
        "hardware": "runtime-dependent CPU benchmark",
        "structural": evaluate_structural(),
        "pipeline": evaluate_pipeline(),
        "claims": "Metrics apply only to the project-owned synthetic validation set and are not field-performance claims.",
    }
    path = output / "model_performance.json"
    path.write_text(json.dumps(report, indent=2))
    concise = {
        "output": str(path),
        "structural": {k: v for k, v in report["structural"].items() if k != "per_image"},
        "pipeline": {k: v for k, v in report["pipeline"].items() if k != "per_image"},
        "claims": report["claims"],
    }
    print(json.dumps(concise, indent=2), flush=True)


if __name__ == "__main__":
    main()
