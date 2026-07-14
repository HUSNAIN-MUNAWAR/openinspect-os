from services.synchronization.timestamps import align_timestamps

def test_timestamp_alignment_with_tolerance():
    matches = align_timestamps([0.0, 1.0, 2.0], [0.04, 1.3, 1.96], tolerance_s=0.1)
    assert matches == [(0,0,0.04),(2,2,0.040000000000000036)]
