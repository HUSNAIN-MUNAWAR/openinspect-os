from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import cv2
import numpy as np
from .quality import assess_quality
from .io import write_image


@dataclass(slots=True)
class UnderwaterResult:
    enhanced: np.ndarray
    pipeline_mask: np.ndarray
    overlay: np.ndarray
    visibility: float
    confidence: float
    quality: dict


def enhance_underwater(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    balanced = cv2.cvtColor(cv2.merge([l2, a, b]), cv2.COLOR_LAB2BGR)
    channels = cv2.split(balanced.astype(np.float32))
    means = [float(c.mean()) for c in channels]
    target = sum(means) / 3.0
    corrected = [np.clip(c * (target / max(m, 1e-6)), 0, 255).astype(np.uint8) for c, m in zip(channels, means)]
    return cv2.merge(corrected)


def segment_pipeline(image: np.ndarray) -> tuple[np.ndarray, float]:
    """Segment a visually neutral, elongated pipeline region.

    The classical baseline combines low-saturation material cues with geometric
    filtering. It is deliberately deterministic and inspectable; it is not a
    claim of general offshore defect recognition.
    """
    enhanced = enhance_underwater(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Painted or metallic pipe surfaces are commonly less saturated than the
    # surrounding synthetic water column. Geometry prevents broad neutral areas
    # from becoming pipeline detections.
    material = cv2.inRange(hsv, (0, 0, 60), (179, 85, 205))
    material = cv2.morphologyEx(material, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    material = cv2.morphologyEx(material, cv2.MORPH_CLOSE, np.ones((15, 45), np.uint8))

    mask = np.zeros_like(material)
    component_score = 0.0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(material)
    image_area = float(image.shape[0] * image.shape[1])
    for idx in range(1, count):
        x, y, width, height, area = stats[idx]
        aspect = width / max(height, 1)
        if width >= image.shape[1] * 0.22 and aspect >= 2.0 and area >= image_area * 0.005:
            mask[labels == idx] = 255
            component_score = max(component_score, min(1.0, width / image.shape[1]))

    # Hough-based fallback keeps the service useful when material colour alone
    # is insufficient, while still requiring an elongated structure.
    if cv2.countNonZero(mask) == 0:
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 45, 130)
        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=35,
            minLineLength=max(30, image.shape[1] // 5),
            maxLineGap=30,
        )
        line_score = 0.0
        if lines is not None:
            candidates = []
            for line in lines[:, 0]:
                x1, y1, x2, y2 = map(int, line)
                length = float(np.hypot(x2 - x1, y2 - y1))
                angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                if angle < 35 or angle > 145:
                    candidates.append((length, (x1, y1, x2, y2)))
            candidates.sort(reverse=True)
            for length, coords in candidates[:4]:
                cv2.line(mask, coords[:2], coords[2:], 255, 22)
                line_score += length
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
        component_score = float(np.clip(line_score / max(image.shape[1] * 2.5, 1), 0.0, 0.85))

    coverage = cv2.countNonZero(mask) / max(image_area, 1.0)
    confidence = float(np.clip(0.35 + 0.45 * component_score + 0.20 * min(coverage / 0.12, 1.0), 0.0, 0.98))
    return mask, confidence


def analyze_underwater_image(image: np.ndarray) -> UnderwaterResult:
    enhanced = enhance_underwater(image)
    mask, confidence = segment_pipeline(image)
    quality = assess_quality(enhanced, min_sharpness=10.0)
    overlay = enhanced.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 255, 255), 2)
    visibility = float(np.clip(quality.visibility * (0.5 + confidence / 2.0), 0.0, 1.0))
    return UnderwaterResult(enhanced, mask, overlay, visibility, confidence, asdict(quality))


def analyze_file(path: str | Path, output_dir: str | Path) -> dict:
    path = Path(path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"unable to read image: {path}")
    result = analyze_underwater_image(image)
    enhanced_path = output_dir / f"{path.stem}_enhanced.png"
    mask_path = output_dir / f"{path.stem}_pipeline_mask.png"
    overlay_path = output_dir / f"{path.stem}_pipeline_overlay.png"
    write_image(enhanced_path, result.enhanced)
    write_image(mask_path, result.pipeline_mask)
    write_image(overlay_path, result.overlay)
    return {
        "source": str(path),
        "enhanced": str(enhanced_path),
        "mask": str(mask_path),
        "overlay": str(overlay_path),
        "visibility": result.visibility,
        "confidence": result.confidence,
        "quality": result.quality,
        "provenance": "project-owned synthetic pipeline scene; algorithmic segmentation",
    }
