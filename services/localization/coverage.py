from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class CoverageSegment:
    start_m: float
    end_m: float
    visibility: float
    covered: bool
    reason: str


def calculate_linear_coverage(mission_distance_m: float, observations: list[tuple[float, float]], segment_length_m: float = 5.0, visibility_threshold: float = 0.22) -> dict:
    if mission_distance_m <= 0:
        return {"coverage_percent": 0.0, "segments": [], "missing_segments": 0, "low_confidence_segments": 0}
    segments: list[CoverageSegment] = []
    position = 0.0
    while position < mission_distance_m:
        end = min(mission_distance_m, position + segment_length_m)
        vals = [visibility for distance, visibility in observations if position <= distance < end]
        avg = sum(vals) / len(vals) if vals else 0.0
        covered = bool(vals) and avg >= visibility_threshold
        reason = "covered" if covered else ("low-visibility" if vals else "no-observation")
        segments.append(CoverageSegment(position, end, avg, covered, reason))
        position = end
    covered_length = sum(s.end_m - s.start_m for s in segments if s.covered)
    return {
        "coverage_percent": 100.0 * covered_length / mission_distance_m,
        "segments": [asdict(s) for s in segments],
        "missing_segments": sum(1 for s in segments if s.reason == "no-observation"),
        "low_confidence_segments": sum(1 for s in segments if s.reason == "low-visibility"),
    }
