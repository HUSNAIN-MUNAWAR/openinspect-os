from __future__ import annotations

from pathlib import Path
import csv
import json
import math
import random

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "project-owned"


def ensure_dirs() -> None:
    for name in ["structural", "pipeline", "sonar", "navigation", "ground_truth"]:
        (DATA / name).mkdir(parents=True, exist_ok=True)


def concrete_background(width: int, height: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = rng.normal(155, 15, (height, width)).astype(np.float32)
    coarse = cv2.GaussianBlur(rng.normal(0, 18, (height, width)).astype(np.float32), (0, 0), 18)
    img = np.clip(base + coarse, 55, 230).astype(np.uint8)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for _ in range(70):
        x, y = rng.integers(0, width), rng.integers(0, height)
        r = int(rng.integers(1, 5))
        color = int(rng.integers(110, 185))
        cv2.circle(img, (int(x), int(y)), r, (color, color, color), -1)
    return img


def draw_crack(image: np.ndarray, mask: np.ndarray, points: list[tuple[int, int]], width: int) -> None:
    for a, b in zip(points, points[1:]):
        cv2.line(image, a, b, (28, 28, 28), width, cv2.LINE_AA)
        cv2.line(mask, a, b, 255, width, cv2.LINE_AA)
    for x, y in points[1:-1:2]:
        cv2.circle(image, (x, y), max(1, width // 2), (15, 15, 15), -1)


def generate_structural() -> list[dict]:
    records = []
    for i in range(8):
        width, height = 960, 540
        image = concrete_background(width, height, 100 + i)
        mask = np.zeros((height, width), dtype=np.uint8)
        rng = random.Random(1000 + i)
        x, y = 80 + i * 4, 90 + (i % 3) * 40
        points = [(x, y)]
        for _ in range(8):
            x += rng.randint(60, 110)
            y += rng.randint(-45, 65)
            points.append((min(width - 40, x), max(30, min(height - 30, y))))
        crack_width = 2 + (i % 4)
        draw_crack(image, mask, points, crack_width)
        if i in {2, 5, 7}:
            branch = [points[3], (points[3][0] + 45, points[3][1] - 80), (points[3][0] + 80, points[3][1] - 140)]
            draw_crack(image, mask, branch, max(2, crack_width - 1))
        if i == 6:
            cv2.rectangle(image, (700, 90), (820, 190), (90, 90, 90), -1)
            cv2.rectangle(mask, (700, 90), (820, 190), 255, -1)
        image = cv2.GaussianBlur(image, (3, 3), 0.4 if i != 4 else 1.6)
        image_path = DATA / "structural" / f"structural_{i:02d}.png"
        mask_path = DATA / "ground_truth" / f"structural_{i:02d}_mask.png"
        cv2.imwrite(str(image_path), image)
        cv2.imwrite(str(mask_path), mask)
        records.append({"image": str(image_path.relative_to(ROOT)), "mask": str(mask_path.relative_to(ROOT)), "simulated_defect": True, "mm_per_pixel": 0.12 if i in {0, 1, 2} else None})
    return records


def underwater_background(width: int, height: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, height)[:, None]
    base = np.zeros((height, width, 3), np.float32)
    base[..., 0] = 100 + 60 * (1 - y)
    base[..., 1] = 90 + 55 * (1 - y)
    base[..., 2] = 35 + 20 * (1 - y)
    noise = rng.normal(0, 10, base.shape).astype(np.float32)
    image = np.clip(base + noise, 0, 255).astype(np.uint8)
    for _ in range(120):
        x = int(rng.integers(0, width)); yy = int(rng.integers(0, height)); r = int(rng.integers(1, 4))
        cv2.circle(image, (x, yy), r, (145, 160, 115), -1)
    return cv2.GaussianBlur(image, (5, 5), 0)


def generate_pipeline() -> list[dict]:
    records = []
    width, height = 960, 540
    for i in range(12):
        image = underwater_background(width, height, 200 + i)
        mask = np.zeros((height, width), dtype=np.uint8)
        offset = int(18 * math.sin(i / 2))
        p1 = (-40, 340 + offset)
        p2 = (1000, 245 + offset)
        cv2.line(image, p1, p2, (145, 148, 150), 46, cv2.LINE_AA)
        cv2.line(image, p1, p2, (82, 90, 95), 8, cv2.LINE_AA)
        cv2.line(mask, p1, p2, 255, 54, cv2.LINE_AA)
        if i in {5, 6}:
            haze = np.full_like(image, (30, 70, 70))
            image = cv2.addWeighted(image, 0.55, haze, 0.45, 0)
            image = cv2.GaussianBlur(image, (11, 11), 3)
        if i == 8:
            cv2.rectangle(image, (520, 255), (590, 335), (45, 55, 60), -1)
        image_path = DATA / "pipeline" / f"pipeline_{i:02d}.png"
        mask_path = DATA / "ground_truth" / f"pipeline_{i:02d}_mask.png"
        cv2.imwrite(str(image_path), image)
        cv2.imwrite(str(mask_path), mask)
        records.append({"image": str(image_path.relative_to(ROOT)), "mask": str(mask_path.relative_to(ROOT)), "timestamp_s": i * 0.5, "simulated_scene": True})
    return records


def generate_sonar() -> str:
    path = DATA / "sonar" / "pipeline_sonar.csv"
    bins = 96
    with path.open("w", newline="") as handle:
        fieldnames = ["timestamp_s"] + [f"bin_{i:03d}" for i in range(bins)]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        rng = np.random.default_rng(44)
        for frame in range(24):
            center = 52 + int(5 * math.sin(frame / 4))
            values = rng.normal(12, 2.5, bins)
            for b in range(bins):
                values[b] += 85 * math.exp(-((b - center) ** 2) / (2 * 3.3 ** 2))
            row = {"timestamp_s": round(frame * 0.25, 3)}
            row.update({f"bin_{i:03d}": round(float(values[i]), 3) for i in range(bins)})
            writer.writerow(row)
    return str(path.relative_to(ROOT))


def generate_navigation() -> str:
    path = DATA / "navigation" / "pipeline_navigation.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp_s", "latitude", "longitude", "depth_m"])
        writer.writeheader()
        lat, lon = 25.9212, 51.5102
        for i in range(24):
            writer.writerow({"timestamp_s": i * 0.25, "latitude": lat + i * 0.000006, "longitude": lon + i * 0.000011, "depth_m": 7.5 + 0.15 * math.sin(i / 3)})
    return str(path.relative_to(ROOT))


def main() -> None:
    ensure_dirs()
    structural = generate_structural()
    pipeline = generate_pipeline()
    sonar = generate_sonar()
    navigation = generate_navigation()
    manifest = {
        "name": "OpenInspect OS Project-Owned Demo Dataset",
        "version": "0.1.0",
        "license": "CC BY 4.0",
        "structural": structural,
        "pipeline": pipeline,
        "sonar": sonar,
        "navigation": navigation,
        "limitations": [
            "All visible defects and pipeline scenes are synthetic and intended for software validation only.",
            "No claim of production-grade corrosion or crack-width accuracy is made.",
            "Physical measurements are only emitted for samples carrying explicit mm_per_pixel calibration.",
        ],
    }
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"structural_images": len(structural), "pipeline_images": len(pipeline), "sonar": sonar, "navigation": navigation}, indent=2))


if __name__ == "__main__":
    main()
