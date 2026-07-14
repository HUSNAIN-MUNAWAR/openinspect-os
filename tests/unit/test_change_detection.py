import cv2
import numpy as np
from services.change_detection.registration import compare_images

def test_registration_and_change_mask():
    before = np.full((200,300,3), 160, np.uint8)
    cv2.line(before,(20,100),(250,100),(20,20,20),3)
    after = before.copy()
    cv2.circle(after,(180,130),18,(30,30,30),-1)
    result = compare_images(before, after)
    assert result.alignment_score >= 0.35
    assert result.changed_mask.sum() > 0
    assert result.status in {'changed','worsened-or-new'}
