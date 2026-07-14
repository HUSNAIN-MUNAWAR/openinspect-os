from services.vision.temporal import Observation, merge_observations

def test_temporal_deduplication_and_best_frame():
    observations = [
        Observation(1,0.1,(10,10,40,40),0.7,40,0.6,'a.png'),
        Observation(2,0.2,(12,11,42,41),0.9,80,0.8,'b.png'),
        Observation(20,2.0,(200,200,230,230),0.8,60,0.7,'c.png'),
    ]
    tracks = merge_observations(observations, max_frame_gap=5)
    assert len(tracks) == 2
    assert tracks[0].best.evidence_path == 'b.png'
    assert tracks[0].start_timestamp == 0.1
    assert tracks[0].end_timestamp == 0.2
