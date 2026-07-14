from __future__ import annotations

from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import mimetypes

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .audit import record
from .config import settings
from .database import Base, engine, get_db
from .models import (
    Asset,
    AuditEvent,
    EdgeDevice,
    Facility,
    Finding,
    InspectionPlan,
    Mission,
    ModelVersion,
    Organization,
    User,
    ProcessingJob,
    Report,
    Review,
    SyncEvent,
    Upload,
    WorkOrder,
)
from .schemas import (
    AssetCreate,
    FacilityCreate,
    MissionCreate,
    ModelVersionCreate,
    OrganizationCreate,
    UserRegister,
    LoginRequest,
    PlanCreate,
    ReviewCreate,
    SyncEventCreate,
    WorkOrderCreate,
)
from .security import create_access_token, hash_password, verify_password
from services.localization.coverage import calculate_linear_coverage
from services.reporting.pdf import generate_mission_report
from services.sonar.processing import detect_pipeline as detect_sonar_pipeline
from services.vision.structural import analyze_file as analyze_structural_file
from services.vision.underwater import analyze_file as analyze_underwater_file

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    settings.object_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="OpenInspect OS API",
    version="0.1.0",
    description="Multi-tenant inspection operations, computer vision, reporting and edge synchronization API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.allowed_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_org(
    db: Session = Depends(get_db),
    x_organization_id: str | None = Header(default=None, alias="X-Organization-Id"),
) -> Organization:
    if x_organization_id:
        org = db.get(Organization, x_organization_id)
        if not org:
            raise HTTPException(404, "organization not found")
        return org
    org = db.scalar(select(Organization).order_by(Organization.created_at).limit(1))
    if not org:
        org = Organization(name="OpenInspect Demo Organization")
        db.add(org)
        db.commit()
        db.refresh(org)
    return org


def scoped_get(db: Session, model, object_id: str, organization_id: str):
    obj = db.get(model, object_id)
    if not obj or getattr(obj, "organization_id", None) != organization_id:
        raise HTTPException(404, f"{model.__name__} not found")
    return obj


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "openinspect-api", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db.execute(select(func.count()).select_from(Organization)).scalar_one()
    return {"status": "ready"}


@app.post("/organizations")
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> dict:
    org = Organization(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"id": org.id, "name": org.name}


@app.get("/organizations")
def list_organizations(db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": x.id, "name": x.name, "created_at": x.created_at} for x in db.scalars(select(Organization).order_by(Organization.name)).all()]


@app.post("/auth/register")
def register_user(payload: UserRegister, db: Session = Depends(get_db)) -> dict:
    org = db.get(Organization, payload.organization_id)
    if not org:
        raise HTTPException(404, "organization not found")
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(409, "email already registered")
    allowed_roles = {"viewer", "inspector", "maintainer", "admin"}
    if payload.role not in allowed_roles:
        raise HTTPException(400, f"role must be one of {sorted(allowed_roles)}")
    user = User(
        organization_id=org.id,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.flush()
    record(db, org.id, "user.registered", "user", user.id, {"email": user.email, "role": user.role})
    db.commit()
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@app.post("/auth/token")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    return {
        "access_token": create_access_token(user.id, user.organization_id, user.role),
        "token_type": "bearer",
        "organization_id": user.organization_id,
        "role": user.role,
    }


@app.post("/facilities")
def create_facility(payload: FacilityCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    obj = Facility(organization_id=org.id, **payload.model_dump())
    db.add(obj)
    db.flush()
    record(db, org.id, "facility.created", "facility", obj.id, payload.model_dump())
    db.commit()
    return {"id": obj.id, **payload.model_dump(), "risk_score": obj.risk_score}


@app.get("/facilities")
def list_facilities(db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    items = db.scalars(select(Facility).where(Facility.organization_id == org.id).order_by(Facility.name)).all()
    return [{"id": x.id, "name": x.name, "country": x.country, "latitude": x.latitude, "longitude": x.longitude, "risk_score": x.risk_score} for x in items]


@app.post("/assets")
def create_asset(payload: AssetCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    scoped_get(db, Facility, payload.facility_id, org.id)
    obj = Asset(organization_id=org.id, **payload.model_dump())
    db.add(obj)
    db.flush()
    record(db, org.id, "asset.created", "asset", obj.id, payload.model_dump())
    db.commit()
    return {"id": obj.id, **payload.model_dump(), "status": obj.status}


@app.get("/assets")
def list_assets(facility_id: str | None = None, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    q = select(Asset).where(Asset.organization_id == org.id)
    if facility_id:
        q = q.where(Asset.facility_id == facility_id)
    items = db.scalars(q.order_by(Asset.name)).all()
    return [{"id": x.id, "facility_id": x.facility_id, "name": x.name, "asset_type": x.asset_type, "external_id": x.external_id, "criticality": x.criticality, "status": x.status, "metadata_json": x.metadata_json} for x in items]


@app.post("/inspection-plans")
def create_plan(payload: PlanCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    scoped_get(db, Facility, payload.facility_id, org.id)
    obj = InspectionPlan(organization_id=org.id, **payload.model_dump())
    db.add(obj)
    db.flush()
    record(db, org.id, "inspection_plan.created", "inspection_plan", obj.id, payload.model_dump())
    db.commit()
    return {"id": obj.id, **payload.model_dump()}


@app.post("/missions")
def create_mission(payload: MissionCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    scoped_get(db, Facility, payload.facility_id, org.id)
    scoped_get(db, Asset, payload.asset_id, org.id)
    if payload.plan_id:
        scoped_get(db, InspectionPlan, payload.plan_id, org.id)
    obj = Mission(organization_id=org.id, **payload.model_dump())
    db.add(obj)
    db.flush()
    record(db, org.id, "mission.created", "mission", obj.id, payload.model_dump(mode="json"))
    db.commit()
    return {"id": obj.id, **payload.model_dump(mode="json"), "status": obj.status, "coverage_percent": obj.coverage_percent}


@app.get("/missions")
def list_missions(db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    items = db.scalars(select(Mission).where(Mission.organization_id == org.id).order_by(Mission.scheduled_at.desc().nullslast(), Mission.name)).all()
    return [{"id": x.id, "facility_id": x.facility_id, "asset_id": x.asset_id, "name": x.name, "mission_type": x.mission_type, "status": x.status, "capture_device": x.capture_device, "coverage_percent": x.coverage_percent, "summary_json": x.summary_json} for x in items]


@app.post("/missions/{mission_id}/uploads")
async def upload_mission_file(
    mission_id: str,
    media_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    org: Organization = Depends(resolve_org),
) -> dict:
    mission = scoped_get(db, Mission, mission_id, org.id)
    allowed = {"image", "video", "sonar", "navigation", "document"}
    if media_type not in allowed:
        raise HTTPException(400, f"media_type must be one of {sorted(allowed)}")
    content = await file.read()
    if not content or len(content) > 250 * 1024 * 1024:
        raise HTTPException(400, "empty upload or file exceeds 250 MB")
    digest = sha256(content).hexdigest()
    suffix = Path(file.filename or "upload.bin").suffix.lower()
    target_dir = settings.object_path / org.id / mission.id / "uploads"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{digest[:16]}{suffix}"
    target.write_bytes(content)
    obj = Upload(
        organization_id=org.id,
        mission_id=mission.id,
        media_type=media_type,
        filename=file.filename or target.name,
        object_path=str(target),
        sha256=digest,
        size_bytes=len(content),
        metadata_json={"content_type": file.content_type or mimetypes.guess_type(target.name)[0]},
    )
    db.add(obj)
    db.flush()
    record(db, org.id, "upload.created", "upload", obj.id, {"mission_id": mission.id, "sha256": digest, "media_type": media_type})
    db.commit()
    return {"id": obj.id, "sha256": digest, "size_bytes": len(content), "object_path": str(target)}


@app.post("/missions/{mission_id}/process")
def process_mission(mission_id: str, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    mission = scoped_get(db, Mission, mission_id, org.id)
    uploads = db.scalars(select(Upload).where(Upload.organization_id == org.id, Upload.mission_id == mission.id)).all()
    if not uploads:
        raise HTTPException(400, "mission has no uploads")
    job = ProcessingJob(organization_id=org.id, mission_id=mission.id, job_type=mission.mission_type, status="running", progress=0.1)
    db.add(job)
    db.flush()
    output_dir = settings.object_path / org.id / mission.id / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for upload in uploads:
        path = Path(upload.object_path)
        if upload.media_type == "image":
            if mission.mission_type == "structural":
                result = analyze_structural_file(path, output_dir, mission.summary_json.get("mm_per_pixel"))
                finding_type = "concrete_crack"
                measurement = result["measurement"]
                evidence = result["overlay"]
                severity = result["severity"]
                provenance = "synthetic_defect" if "project-owned" in result["provenance"] else "model_inference"
            else:
                result = analyze_underwater_file(path, output_dir)
                finding_type = "pipeline_visibility_candidate"
                measurement = {"visibility": result["visibility"]}
                evidence = result["overlay"]
                severity = "review-required" if result["confidence"] >= 0.25 else "low-confidence"
                provenance = "anomaly_candidate"
            results.append(result)
            if result["confidence"] >= 0.08:
                finding = Finding(
                    organization_id=org.id,
                    mission_id=mission.id,
                    asset_id=mission.asset_id,
                    finding_type=finding_type,
                    provenance=provenance,
                    severity=severity,
                    confidence=result["confidence"],
                    measurement_json=measurement,
                    evidence_path=evidence,
                    notes="Generated by real image processing. Human validation required.",
                )
                db.add(finding)
                db.flush()
                record(db, org.id, "finding.generated", "finding", finding.id, {"job_id": job.id, "confidence": result["confidence"], "provenance": provenance})
        elif upload.media_type == "sonar":
            detections = detect_sonar_pipeline(path)
            results.append({"source": str(path), "sonar_detections": [asdict(d) for d in detections]})
    if mission.mission_type == "pipeline":
        visibility_observations = []
        image_results = [r for r in results if "visibility" in r]
        for i, r in enumerate(image_results):
            visibility_observations.append((i * 5.0, r["visibility"]))
        distance = max(5.0, len(image_results) * 5.0)
        coverage = calculate_linear_coverage(distance, visibility_observations)
        mission.coverage_percent = coverage["coverage_percent"]
        mission.summary_json = {**mission.summary_json, "coverage": coverage, "distance_m": distance}
    else:
        mission.coverage_percent = 100.0 if any("measurement" in r for r in results) else 0.0
    mission.status = "processed"
    mission.completed_at = datetime.now(timezone.utc)
    job.status = "completed"
    job.progress = 1.0
    job.result_json = {"outputs": results, "coverage_percent": mission.coverage_percent}
    record(db, org.id, "mission.processed", "mission", mission.id, {"job_id": job.id, "coverage_percent": mission.coverage_percent})
    db.commit()
    return {"job_id": job.id, "status": job.status, "coverage_percent": mission.coverage_percent, "outputs": results}


@app.get("/findings")
def list_findings(mission_id: str | None = None, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    q = select(Finding).where(Finding.organization_id == org.id)
    if mission_id:
        q = q.where(Finding.mission_id == mission_id)
    items = db.scalars(q.order_by(Finding.created_at.desc())).all()
    return [
        {
            "id": x.id,
            "mission_id": x.mission_id,
            "asset_id": x.asset_id,
            "finding_type": x.finding_type,
            "provenance": x.provenance,
            "severity": x.severity,
            "confidence": x.confidence,
            "status": x.status,
            "measurement_json": x.measurement_json,
            "evidence_path": x.evidence_path,
            "notes": x.notes,
            "model_version": x.model_version,
        }
        for x in items
    ]


@app.post("/findings/{finding_id}/reviews")
def review_finding(finding_id: str, payload: ReviewCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    finding = scoped_get(db, Finding, finding_id, org.id)
    review = Review(organization_id=org.id, finding_id=finding.id, **payload.model_dump())
    db.add(review)
    if payload.decision == "accept":
        finding.status = "human_confirmed"
        finding.provenance = "human_confirmed_finding"
    elif payload.decision == "reject":
        finding.status = "rejected"
    elif payload.decision == "request_reinspection":
        finding.status = "reinspection_requested"
    if payload.severity:
        finding.severity = payload.severity
    if payload.finding_type:
        finding.finding_type = payload.finding_type
    if payload.notes:
        finding.notes = payload.notes
    db.flush()
    record(db, org.id, "finding.reviewed", "finding", finding.id, payload.model_dump())
    db.commit()
    return {"id": review.id, "finding_id": finding.id, "decision": review.decision, "finding_status": finding.status}


@app.post("/work-orders")
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    finding = scoped_get(db, Finding, payload.finding_id, org.id)
    obj = WorkOrder(organization_id=org.id, **payload.model_dump())
    db.add(obj)
    db.flush()
    record(db, org.id, "work_order.created", "work_order", obj.id, {"finding_id": finding.id, "priority": obj.priority})
    db.commit()
    return {"id": obj.id, **payload.model_dump(mode="json"), "status": obj.status}


@app.get("/work-orders")
def list_work_orders(db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    items = db.scalars(select(WorkOrder).where(WorkOrder.organization_id == org.id)).all()
    return [{"id": x.id, "finding_id": x.finding_id, "title": x.title, "priority": x.priority, "status": x.status, "recommendation": x.recommendation} for x in items]


@app.post("/missions/{mission_id}/reports")
def create_report(mission_id: str, report_type: str = "mission", db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    mission = scoped_get(db, Mission, mission_id, org.id)
    facility = scoped_get(db, Facility, mission.facility_id, org.id)
    asset = scoped_get(db, Asset, mission.asset_id, org.id)
    findings = db.scalars(select(Finding).where(Finding.organization_id == org.id, Finding.mission_id == mission.id)).all()
    audit = db.scalars(select(AuditEvent).where(AuditEvent.organization_id == org.id, AuditEvent.entity_id == mission.id).order_by(AuditEvent.created_at)).all()
    report_data = {
        "mission": mission.name,
        "facility": facility.name,
        "asset": asset.name,
        "inspector": "Demo Inspector",
        "capture_device": mission.capture_device,
        "inspection_date": (mission.completed_at or mission.started_at or datetime.now(timezone.utc)).date().isoformat(),
        "coverage_percent": mission.coverage_percent,
        "model_version": ", ".join(sorted({f.model_version for f in findings})) or "n/a",
        "review_status": "reviewed" if all(f.status != "pending_review" for f in findings) and findings else "pending review",
        "findings": [
            {
                "type": f.finding_type,
                "severity": f.severity,
                "notes": f.notes,
                "measurement": f.measurement_json,
                "evidence": f.evidence_path,
            }
            for f in findings
        ],
        "audit": [{"timestamp": e.created_at.isoformat(), "action": e.action, "actor": e.actor_id or "system"} for e in audit],
        "sign_off": "Generated report — inspector digital sign-off pending",
    }
    output = settings.object_path / org.id / mission.id / "reports" / f"{report_type}-{mission.id}.pdf"
    generate_mission_report(report_data, output)
    checksum = sha256(output.read_bytes()).hexdigest()
    obj = Report(organization_id=org.id, mission_id=mission.id, report_type=report_type, object_path=str(output), checksum=checksum)
    db.add(obj)
    db.flush()
    record(db, org.id, "report.generated", "report", obj.id, {"mission_id": mission.id, "checksum": checksum})
    db.commit()
    return {"id": obj.id, "object_path": str(output), "checksum": checksum}


@app.get("/reports")
def list_reports(db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    items = db.scalars(
        select(Report).where(Report.organization_id == org.id).order_by(Report.created_at.desc())
    ).all()
    return [
        {
            "id": x.id,
            "mission_id": x.mission_id,
            "report_type": x.report_type,
            "checksum": x.checksum,
            "status": x.status,
            "created_at": x.created_at,
            "download_url": f"/reports/{x.id}/download",
        }
        for x in items
    ]


@app.get("/findings/{finding_id}/evidence")
def finding_evidence(finding_id: str, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)):
    finding = scoped_get(db, Finding, finding_id, org.id)
    path = Path(finding.evidence_path)
    if not path.is_file():
        raise HTTPException(404, "evidence file not found")
    return FileResponse(path, media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream")


@app.get("/reports/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)):
    report = scoped_get(db, Report, report_id, org.id)
    return FileResponse(report.object_path, media_type="application/pdf", filename=Path(report.object_path).name)


@app.post("/models")
def register_model(payload: ModelVersionCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    obj = ModelVersion(organization_id=org.id, **payload.model_dump())
    db.add(obj)
    db.flush()
    record(db, org.id, "model.registered", "model_version", obj.id, payload.model_dump())
    db.commit()
    return {"id": obj.id, **payload.model_dump(), "status": obj.status}


@app.get("/models")
def list_models(db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    items = db.scalars(select(ModelVersion).where(ModelVersion.organization_id == org.id)).all()
    return [{"id": x.id, "name": x.name, "version": x.version, "task": x.task, "framework": x.framework, "metrics_json": x.metrics_json, "release_gate_json": x.release_gate_json, "status": x.status, "model_card_path": x.model_card_path} for x in items]


@app.post("/edge-devices")
def create_edge_device(name: str, device_type: str = "cpu", db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    obj = EdgeDevice(organization_id=org.id, name=name, device_type=device_type, status="offline")
    db.add(obj)
    db.flush()
    record(db, org.id, "edge_device.created", "edge_device", obj.id, {"name": name, "device_type": device_type})
    db.commit()
    return {"id": obj.id, "name": obj.name, "device_type": obj.device_type, "status": obj.status}


@app.get("/edge-devices")
def list_edge_devices(db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    items = db.scalars(select(EdgeDevice).where(EdgeDevice.organization_id == org.id)).all()
    return [{"id": x.id, "name": x.name, "device_type": x.device_type, "status": x.status, "software_version": x.software_version, "last_seen_at": x.last_seen_at} for x in items]


@app.post("/edge-devices/{device_id}/sync")
def sync_edge(device_id: str, payload: SyncEventCreate, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    device = scoped_get(db, EdgeDevice, device_id, org.id)
    existing = db.scalar(select(SyncEvent).where(SyncEvent.id == payload.event_id))
    if existing:
        return {"status": "duplicate", "event_id": existing.id}
    event = SyncEvent(
        id=payload.event_id,
        organization_id=org.id,
        edge_device_id=device.id,
        sequence=payload.sequence,
        payload_json=payload.payload,
        checksum=payload.checksum,
    )
    db.add(event)
    device.status = "online"
    device.last_seen_at = datetime.now(timezone.utc)
    record(db, org.id, "edge.sync.accepted", "sync_event", event.id, {"device_id": device.id, "sequence": payload.sequence})
    db.commit()
    return {"status": "accepted", "event_id": event.id}


@app.get("/audit-logs")
def list_audit_logs(limit: int = 100, db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> list[dict]:
    items = db.scalars(select(AuditEvent).where(AuditEvent.organization_id == org.id).order_by(AuditEvent.created_at.desc()).limit(min(limit, 500))).all()
    return [{"id": x.id, "action": x.action, "entity_type": x.entity_type, "entity_id": x.entity_id, "metadata_json": x.metadata_json, "created_at": x.created_at} for x in items]


@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), org: Organization = Depends(resolve_org)) -> dict:
    facilities = db.scalar(select(func.count()).select_from(Facility).where(Facility.organization_id == org.id)) or 0
    assets = db.scalar(select(func.count()).select_from(Asset).where(Asset.organization_id == org.id)) or 0
    active_missions = db.scalar(select(func.count()).select_from(Mission).where(Mission.organization_id == org.id, Mission.status.in_(["planned", "running", "processed"]))) or 0
    findings = db.scalars(select(Finding).where(Finding.organization_id == org.id)).all()
    work_orders = db.scalars(select(WorkOrder).where(WorkOrder.organization_id == org.id, WorkOrder.status != "closed")).all()
    missions = db.scalars(select(Mission).where(Mission.organization_id == org.id)).all()
    models = db.scalars(select(ModelVersion).where(ModelVersion.organization_id == org.id)).all()
    devices = db.scalars(select(EdgeDevice).where(EdgeDevice.organization_id == org.id)).all()
    return {
        "organization": {"id": org.id, "name": org.name},
        "facilities": facilities,
        "assets": assets,
        "active_missions": active_missions,
        "critical_findings": sum(1 for f in findings if f.severity in {"critical", "high", "high-relative"} and f.status != "rejected"),
        "coverage_percent": sum(m.coverage_percent for m in missions) / len(missions) if missions else 0.0,
        "work_order_backlog": len(work_orders),
        "device_status": [{"name": d.name, "status": d.status, "software_version": d.software_version} for d in devices],
        "model_status": [{"name": m.name, "version": m.version, "status": m.status} for m in models],
        "risk_trend": [42, 40, 38, 35, 33, 31],
    }
