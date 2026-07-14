from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass(slots=True)
class QualityMetrics:
    sharpness: float
    brightness: float
    contrast: float
    visibility: float
    usable: bool


def assess_quality(image: np.ndarray, min_sharpness: float = 18.0) -> QualityMetrics:
    if image is None or image.size == 0:
        raise ValueError("image is empty")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())
    visibility = float(np.clip((contrast / 64.0) * (1.0 - abs(brightness - 128.0) / 160.0), 0.0, 1.0))
    usable = sharpness >= min_sharpness and 20.0 <= brightness <= 235.0 and visibility >= 0.08
    return QualityMetrics(sharpness, brightness, contrast, visibility, usable)
