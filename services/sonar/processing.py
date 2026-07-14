from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import cv2
import numpy as np


@dataclass(slots=True)
class SonarDetection:
    timestamp_s: float
    range_bin: int
    intensity: float
    confidence: float


def load_sonar_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    timestamps, rows = [], []
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        bins = [c for c in reader.fieldnames or [] if c.startswith("bin_")]
        for row in reader:
            timestamps.append(float(row["timestamp_s"]))
            rows.append([float(row[b]) for b in bins])
    return np.asarray(timestamps, dtype=np.float32), np.asarray(rows, dtype=np.float32)


def detect_pipeline(path: str | Path) -> list[SonarDetection]:
    timestamps, matrix = load_sonar_csv(path)
    if matrix.size == 0:
        return []
    smooth = cv2.GaussianBlur(matrix, (5, 5), 0)
    detections: list[SonarDetection] = []
    for idx, row in enumerate(smooth):
        b = int(np.argmax(row))
        peak = float(row[b])
        baseline = float(np.median(row))
        confidence = float(np.clip((peak - baseline) / max(peak, 1e-6), 0.0, 1.0))
        if confidence >= 0.25:
            detections.append(SonarDetection(float(timestamps[idx]), b, peak, confidence))
    return detections
