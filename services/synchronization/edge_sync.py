from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time
import uuid


@dataclass(slots=True)
class SyncEnvelope:
    event_id: str
    device_id: str
    sequence: int
    payload: dict
    created_at: float
    checksum: str


class OfflineQueue:
    def __init__(self, path: str | Path, device_id: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.device_id = device_id
        if not self.path.exists():
            self.path.write_text("[]")

    def _load(self) -> list[dict]:
        return json.loads(self.path.read_text())

    def enqueue(self, payload: dict, checksum: str) -> SyncEnvelope:
        items = self._load()
        env = SyncEnvelope(str(uuid.uuid4()), self.device_id, len(items) + 1, payload, time.time(), checksum)
        items.append(asdict(env))
        self.path.write_text(json.dumps(items, indent=2))
        return env

    def pending(self) -> list[dict]:
        return self._load()

    def acknowledge(self, event_id: str) -> None:
        items = [x for x in self._load() if x["event_id"] != event_id]
        self.path.write_text(json.dumps(items, indent=2))
