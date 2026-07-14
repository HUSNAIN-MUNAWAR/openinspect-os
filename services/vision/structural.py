from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import cv2
import numpy as np
from skimage.morphology import skeletonize
from .quality import assess_quality


@dataclass(slots=True)
class CrackMeasurement:
    pixel_length: float
    mean_width_px: float
    max_width_px: float
    crack_density: float
    affected_area_percent: float
    calibrated_length_mm: float | None
    calibrated_mean_width_mm: float | None
    uncertainty_percent: float


@dataclass(slots=True)
class StructuralResult:
    mask: np.ndarray
    overlay: np.ndarray
    confidence: float
    severity: str
    measurement: CrackMeasurement
    quality: dict
    provenance: str = "project-owned synthetic ground truth compatible inference"


def _surface_mask(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    blackhat = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    _, mask = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    cleaned = np.zeros_like(mask)
    for idx in range(1, n):
        area = stats[idx, cv2.CC_STAT_AREA]
        w = stats[idx, cv2.CC_STAT_WIDTH]
        h = stats[idx, cv2.CC_STAT_HEIGHT]
        if 12 <= area <= gray.size * 0.15 and max(w, h) >= 8:
            cleaned[labels == idx] = 255
    return cleaned


def _measure(mask: np.ndarray, mm_per_pixel: float | None) -> CrackMeasurement:
    binary = mask > 0
    skeleton = skeletonize(binary)
    pixel_length = float(skeleton.sum())
    dist = cv2.distanceTransform(binary.astype(np.uint8), cv2.DIST_L2, 5)
    widths = 2.0 * dist[skeleton]
    mean_width = float(widths.mean()) if widths.size else 0.0
    max_width = float(widths.max()) if widths.size else 0.0
    area = float(binary.sum())
    affected = (area / binary.size) * 100.0
    density = pixel_length / max(binary.size, 1)
    calibrated_length = pixel_length * mm_per_pixel if mm_per_pixel else None
    calibrated_width = mean_width * mm_per_pixel if mm_per_pixel else None
    uncertainty = 8.0 if mm_per_pixel else 20.0
    return CrackMeasurement(pixel_length, mean_width, max_width, density, affected, calibrated_length, calibrated_width, uncertainty)


def _severity(m: CrackMeasurement) -> str:
    width = m.calibrated_mean_width_mm if m.calibrated_mean_width_mm is not None else m.mean_width_px
    if m.calibrated_mean_width_mm is not None:
        if width >= 1.0 or m.affected_area_percent >= 2.5:
            return "critical"
        if width >= 0.5 or m.affected_area_percent >= 1.0:
            return "high"
        if width >= 0.2:
            return "moderate"
        return "low"
    if width >= 8 or m.affected_area_percent >= 2.5:
        return "high-relative"
    if width >= 4 or m.affected_area_percent >= 1.0:
        return "moderate-relative"
    return "low-relative"


def analyze_structural_image(image: np.ndarray, mm_per_pixel: float | None = None) -> StructuralResult:
    quality = assess_quality(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = _surface_mask(gray)
    measurement = _measure(mask, mm_per_pixel)
    contrast_signal = float(np.mean(cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, np.ones((9, 9), np.uint8))[mask > 0])) if np.any(mask) else 0.0
    confidence = float(np.clip((contrast_signal / 55.0) * min(1.0, measurement.pixel_length / 120.0), 0.0, 0.99))
    overlay = image.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 0, 255), 2)
    return StructuralResult(mask, overlay, confidence, _severity(measurement), measurement, asdict(quality))


def analyze_file(path: str | Path, output_dir: str | Path, mm_per_pixel: float | None = None) -> dict:
    path = Path(path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"unable to read image: {path}")
    result = analyze_structural_image(image, mm_per_pixel)
    mask_path = output_dir / f"{path.stem}_mask.png"
    overlay_path = output_dir / f"{path.stem}_overlay.png"
    cv2.imwrite(str(mask_path), result.mask)
    cv2.imwrite(str(overlay_path), result.overlay)
    return {
        "source": str(path),
        "mask": str(mask_path),
        "overlay": str(overlay_path),
        "confidence": result.confidence,
        "severity": result.severity,
        "measurement": asdict(result.measurement),
        "quality": result.quality,
        "provenance": result.provenance,
    }
