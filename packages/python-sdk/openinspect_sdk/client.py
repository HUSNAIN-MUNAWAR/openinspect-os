from __future__ import annotations
from pathlib import Path
import httpx


class OpenInspectClient:
    def __init__(self, base_url: str, organization_id: str | None = None, timeout: float = 30.0):
        headers = {"X-Organization-Id": organization_id} if organization_id else {}
        self.client = httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=timeout)

    def facilities(self) -> list[dict]:
        return self.client.get("/facilities").raise_for_status().json()

    def assets(self, facility_id: str | None = None) -> list[dict]:
        params = {"facility_id": facility_id} if facility_id else None
        return self.client.get("/assets", params=params).raise_for_status().json()

    def missions(self) -> list[dict]:
        return self.client.get("/missions").raise_for_status().json()

    def findings(self, mission_id: str | None = None) -> list[dict]:
        params = {"mission_id": mission_id} if mission_id else None
        return self.client.get("/findings", params=params).raise_for_status().json()

    def upload(self, mission_id: str, path: str | Path, media_type: str) -> dict:
        path = Path(path)
        with path.open("rb") as handle:
            response = self.client.post(f"/missions/{mission_id}/uploads", params={"media_type": media_type}, files={"file": (path.name, handle)})
        return response.raise_for_status().json()

    def process(self, mission_id: str) -> dict:
        return self.client.post(f"/missions/{mission_id}/process").raise_for_status().json()
