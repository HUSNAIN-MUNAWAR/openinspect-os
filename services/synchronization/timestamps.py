from __future__ import annotations

from bisect import bisect_left


def align_timestamps(primary: list[float], secondary: list[float], tolerance_s: float = 0.25) -> list[tuple[int, int, float]]:
    matches: list[tuple[int, int, float]] = []
    if not secondary:
        return matches
    for i, value in enumerate(primary):
        pos = bisect_left(secondary, value)
        candidates = [j for j in (pos - 1, pos) if 0 <= j < len(secondary)]
        if not candidates:
            continue
        j = min(candidates, key=lambda idx: abs(secondary[idx] - value))
        delta = abs(secondary[j] - value)
        if delta <= tolerance_s:
            matches.append((i, j, delta))
    return matches
