from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class UserRegister(BaseModel):
    organization_id: str
    email: str
    password: str = Field(min_length=10, max_length=128)
    full_name: str
    role: str = "inspector"


class LoginRequest(BaseModel):
    email: str
    password: str


class FacilityCreate(BaseModel):
    name: str
    country: str = ""
    latitude: float | None = None
    longitude: float | None = None


class AssetCreate(BaseModel):
    facility_id: str
    name: str
    asset_type: str
    external_id: str = ""
    criticality: str = "medium"
    metadata_json: dict = Field(default_factory=dict)


class PlanCreate(BaseModel):
    facility_id: str
    title: str
    objectives: str = ""
    required_coverage_percent: float = 90.0
    expected_route: dict = Field(default_factory=dict)
    safety_notes: str = ""


class MissionCreate(BaseModel):
    facility_id: str
    asset_id: str
    plan_id: str | None = None
    name: str
    mission_type: str
    capture_device: str = "handheld"
    scheduled_at: datetime | None = None


class ReviewCreate(BaseModel):
    decision: str
    severity: str | None = None
    finding_type: str | None = None
    notes: str = ""


class WorkOrderCreate(BaseModel):
    finding_id: str
    title: str
    priority: str = "medium"
    recommendation: str = ""
    due_at: datetime | None = None


class ModelVersionCreate(BaseModel):
    name: str
    version: str
    task: str
    framework: str
    metrics_json: dict = Field(default_factory=dict)
    release_gate_json: dict = Field(default_factory=dict)
    model_card_path: str = ""


class SyncEventCreate(BaseModel):
    event_id: str
    edge_device_id: str
    sequence: int
    payload: dict
    checksum: str
