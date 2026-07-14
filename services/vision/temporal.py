from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot


@dataclass(slots=True)
class Observation:
    frame_index: int
    timestamp_s: float
    bbox: tuple[int, int, int, int]
    confidence: float
    sharpness: float
    visibility: float
    evidence_path: str | None = None


@dataclass(slots=True)
class FindingTrack:
    observations: list[Observation] = field(default_factory=list)

    @property
    def start_timestamp(self) -> float:
        return min(o.timestamp_s for o in self.observations)

    @property
    def end_timestamp(self) -> float:
        return max(o.timestamp_s for o in self.observations)

    @property
    def best(self) -> Observation:
        return max(self.observations, key=lambda o: (o.sharpness * 0.45 + o.confidence * 100 * 0.4 + o.visibility * 100 * 0.15))

    @property
    def smoothed_confidence(self) -> float:
        alpha = 0.45
        value = self.observations[0].confidence
        for obs in self.observations[1:]:
            value = alpha * obs.confidence + (1 - alpha) * value
        return value


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1, ix2, iy2 = max(ax1, bx1), max(ay1, by1), min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    return inter / max(area_a + area_b - inter, 1)


def _center_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ac = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
    bc = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    return hypot(ac[0] - bc[0], ac[1] - bc[1])


def merge_observations(observations: list[Observation], max_frame_gap: int = 12, minimum_iou: float = 0.35, spatial_distance_threshold: float = 40.0) -> list[FindingTrack]:
    tracks: list[FindingTrack] = []
    for obs in sorted(observations, key=lambda o: o.frame_index):
        matched = None
        for track in reversed(tracks):
            last = track.observations[-1]
            if obs.frame_index - last.frame_index > max_frame_gap:
                continue
            if _iou(obs.bbox, last.bbox) >= minimum_iou or _center_distance(obs.bbox, last.bbox) <= spatial_distance_threshold:
                matched = track
                break
        if matched is None:
            tracks.append(FindingTrack([obs]))
        else:
            matched.observations.append(obs)
    return tracks
