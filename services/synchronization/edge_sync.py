from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import tempfile
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
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"offline queue is unreadable: {self.path}") from exc
        if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
            raise RuntimeError(f"offline queue must contain a JSON object list: {self.path}")
        return payload

    def _save(self, items: list[dict]) -> None:
        encoded = json.dumps(items, indent=2, sort_keys=True) + "\n"
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def enqueue(self, payload: dict, checksum: str) -> SyncEnvelope:
        items = self._load()
        env = SyncEnvelope(str(uuid.uuid4()), self.device_id, len(items) + 1, payload, time.time(), checksum)
        items.append(asdict(env))
        self._save(items)
        return env

    def pending(self) -> list[dict]:
        return self._load()

    def acknowledge(self, event_id: str) -> None:
        items = [x for x in self._load() if x["event_id"] != event_id]
        self._save(items)
