from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import csv
from math import radians, sin, cos, asin, sqrt


@dataclass(slots=True)
class GPSPoint:
    timestamp_s: float
    latitude: float
    longitude: float
    depth_m: float = 0.0


def read_navigation_csv(path: str | Path) -> list[GPSPoint]:
    points: list[GPSPoint] = []
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            points.append(GPSPoint(float(row["timestamp_s"]), float(row["latitude"]), float(row["longitude"]), float(row.get("depth_m", 0.0))))
    return points


def haversine_m(a: GPSPoint, b: GPSPoint) -> float:
    r = 6371000.0
    dlat, dlon = radians(b.latitude - a.latitude), radians(b.longitude - a.longitude)
    lat1, lat2 = radians(a.latitude), radians(b.latitude)
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(h))


def summarize_trajectory(points: list[GPSPoint]) -> dict:
    distance = sum(haversine_m(a, b) for a, b in zip(points, points[1:]))
    return {"points": [asdict(p) for p in points], "distance_m": distance, "duration_s": (points[-1].timestamp_s - points[0].timestamp_s) if len(points) > 1 else 0.0}
