from services.localization.coverage import calculate_linear_coverage

def test_coverage_marks_missing_and_low_visibility():
    result = calculate_linear_coverage(20, [(1,0.8),(6,0.1),(16,0.7)], segment_length_m=5, visibility_threshold=0.2)
    assert result['coverage_percent'] == 50.0
    assert result['missing_segments'] == 1
    assert result['low_confidence_segments'] == 1
