from pathlib import Path
import cv2
from services.vision.structural import analyze_structural_image

ROOT = Path(__file__).resolve().parents[2]

def test_structural_mask_and_measurement():
    image = cv2.imread(str(ROOT / 'datasets/project-owned/structural/structural_00.png'))
    result = analyze_structural_image(image, mm_per_pixel=0.12)
    assert result.mask.shape == image.shape[:2]
    assert result.measurement.pixel_length > 50
    assert result.measurement.calibrated_length_mm is not None
    assert 0 <= result.confidence <= 1
