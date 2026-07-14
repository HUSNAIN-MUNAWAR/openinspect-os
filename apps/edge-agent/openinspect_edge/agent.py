from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import json

from services.synchronization.edge_sync import OfflineQueue
from services.vision.structural import analyze_file as analyze_structural
from services.vision.underwater import analyze_file as analyze_pipeline


@dataclass(slots=True)
class DeviceHealth:
    device_id: str
    status: str
    queue_depth: int
    free_bytes: int
    software_version: str = "0.1.0"


class EdgeAgent:
    def __init__(self, root: str | Path, device_id: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.device_id = device_id
        self.queue = OfflineQueue(self.root / "queue.json", device_id)

    def ingest(self, image_path: str | Path, mission_type: str) -> dict:
        output_dir = self.root / "evidence"
        if mission_type == "structural":
            result = analyze_structural(image_path, output_dir)
        elif mission_type == "pipeline":
            result = analyze_pipeline(image_path, output_dir)
        else:
            raise ValueError("mission_type must be structural or pipeline")
        digest = sha256(json.dumps(result, sort_keys=True, default=str).encode()).hexdigest()
        envelope = self.queue.enqueue({"mission_type": mission_type, "result": result}, digest)
        return {"envelope": asdict(envelope), "result": result}

    def health(self) -> DeviceHealth:
        import shutil
        free = shutil.disk_usage(self.root).free
        return DeviceHealth(self.device_id, "ready", len(self.queue.pending()), free)
