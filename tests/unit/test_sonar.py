from pathlib import Path
from services.sonar.processing import detect_pipeline

ROOT = Path(__file__).resolve().parents[2]

def test_sonar_pipeline_detection():
    detections = detect_pipeline(ROOT / 'datasets/project-owned/sonar/pipeline_sonar.csv')
    assert len(detections) >= 20
    assert all(0 <= x.confidence <= 1 for x in detections)
