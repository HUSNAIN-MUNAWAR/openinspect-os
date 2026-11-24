"""Validated persistence for inspection evidence images."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def write_image(path: str | Path, image: np.ndarray) -> Path:
    """Write an inspection artifact or raise instead of returning false silently."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if image is None or image.size == 0:
        raise ValueError(f"cannot write empty inspection image: {destination}")
    if not cv2.imwrite(str(destination), image):
        raise OSError(f"OpenCV could not write inspection image: {destination}")
    if not destination.exists() or destination.stat().st_size == 0:
        raise OSError(f"inspection image write produced no bytes: {destination}")
    return destination
