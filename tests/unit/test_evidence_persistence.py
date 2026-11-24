import cv2
import numpy as np
import pytest

from services.vision.io import write_image


def test_write_image_rejects_failed_encoder(monkeypatch, tmp_path):
    monkeypatch.setattr(cv2, "imwrite", lambda *_args: False)
    with pytest.raises(OSError, match="could not write"):
        write_image(tmp_path / "overlay.png", np.zeros((8, 8, 3), dtype=np.uint8))


def test_write_image_persists_nonempty_artifact(tmp_path):
    destination = write_image(tmp_path / "overlay.png", np.zeros((8, 8, 3), dtype=np.uint8))
    assert destination.exists()
    assert destination.stat().st_size > 0
