from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass(slots=True)
class ChangeResult:
    aligned: np.ndarray
    changed_mask: np.ndarray
    alignment_score: float
    status: str
    transform: list[list[float]]


def compare_images(before: np.ndarray, after: np.ndarray, minimum_alignment: float = 0.35) -> ChangeResult:
    if before.shape[:2] != after.shape[:2]:
        after = cv2.resize(after, (before.shape[1], before.shape[0]))
    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
    warp: np.ndarray = np.eye(2, 3, dtype=np.float32)
    try:
        score, warp = cv2.findTransformECC(before_gray, after_gray, warp, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6))
        aligned = cv2.warpAffine(after, warp, (before.shape[1], before.shape[0]), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    except cv2.error:
        score = 0.0
        aligned = after.copy()
    diff = cv2.absdiff(before, aligned)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(diff_gray, 25, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    change_percent = float((mask > 0).mean() * 100.0)
    if score < minimum_alignment:
        status = "uncertain-comparison"
    elif change_percent > 4.0:
        status = "worsened-or-new"
    elif change_percent > 1.0:
        status = "changed"
    else:
        status = "stable"
    return ChangeResult(aligned, mask, float(score), status, warp.tolist())
