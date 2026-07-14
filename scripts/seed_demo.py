from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import shutil
import sys

import cv2

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "demo" / "outputs"
DB = OUTPUT / "openinspect_demo.db"
OBJECT_ROOT = OUTPUT / "object-store"


def make_video() -> str:
    images = sorted((ROOT / "datasets/project-owned/pipeline").glob("*.png"))
    first = cv2.imread(str(images[0]))
    target = OUTPUT / "pipeline_evidence.mp4"
    writer = cv2.VideoWriter(
        str(target), cv2.VideoWriter_fourcc(*"mp4v"), 4.0, (first.shape[1], first.shape[0])
    )
    for path in images:
        writer.write(cv2.imread(str(path)))
    writer.release()
    return str(target)


def copy_upload(source: Path, destination_dir: Path) -> tuple[Path, str]:
    content = source.read_bytes()
    digest = sha256(content).hexdigest()
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / f"{digest[:16]}{source.suffix.lower()}"
    target.write_bytes(content)
    return target, digest


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    if OBJECT_ROOT.exists():
        shutil.rmtree(OBJECT_ROOT)
    evidence_video = make_video()

    os.environ["OPENINSPECT_DATABASE_URL"] = f"sqlite:///{DB}"
    os.environ["OPENINSPECT_OBJECT_ROOT"] = str(OBJECT_ROOT)
    sys.path[:0] = [str(ROOT), str(ROOT / "apps/api"), str(ROOT / "apps/edge-agent")]

    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from openinspect_api.audit import record
    from openinspect_api.database import Base, engine
    from openinspect_api.models import (
        Asset,
        AuditEvent,
        EdgeDevice,
        Facility,
        Finding,
        InspectionPlan,
        Mission,
        ModelVersion,
        Organization,
        Report,
        Review,
        SyncEvent,
        Upload,
        WorkOrder,
    )
    from services.localization.coverage import calculate_linear_coverage
    from services.reporting.pdf import generate_mission_report
    from services.sonar.processing import detect_pipeline as detect_sonar_pipeline
    from services.vision.structural import analyze_file as analyze_structural_file
    from services.vision.underwater import analyze_file as analyze_underwater_file

    Base.metadata.create_all(engine)
    performance = json.loads((OUTPUT / "model_performance.json").read_text())
    print("STAGE database", flush=True)

    with Session(engine) as db:
        org = Organization(name="OpenInspect Demo Organization")
        db.add(org)
        db.flush()

        bridge = Facility(
            organization_id=org.id,
            name="Bridge Materials Lab",
            country="Pakistan",
            latitude=33.6007,
            longitude=73.0679,
            risk_score=22,
        )
        offshore = Facility(
            organization_id=org.id,
            name="Ras Laffan Offshore Demo",
            country="Qatar",
            latitude=25.922,
            longitude=51.512,
            risk_score=34,
        )
        db.add_all([bridge, offshore])
        db.flush()

        concrete = Asset(
            organization_id=org.id,
            facility_id=bridge.id,
            name="Concrete Test Wall A",
            asset_type="concrete_structure",
            external_id="CWA-001",
            criticality="high",
            metadata_json={"material": "reinforced concrete"},
        )
        pipeline = Asset(
            organization_id=org.id,
            facility_id=offshore.id,
            name="Subsea Outfall Pipeline P-14",
            asset_type="subsea_pipeline",
            external_id="P-14",
            criticality="critical",
            metadata_json={"nominal_diameter_mm": 650},
        )
        bridge_deck = Asset(
            organization_id=org.id,
            facility_id=bridge.id,
            name="North Bridge Deck",
            asset_type="bridge_deck",
            external_id="BD-004",
            criticality="high",
        )
        tower = Asset(
            organization_id=org.id,
            facility_id=offshore.id,
            name="Jetty Support Tower T-02",
            asset_type="marine_structure",
            external_id="T-02",
            criticality="medium",
        )
        db.add_all([concrete, pipeline, bridge_deck, tower])
        db.flush()

        structural_plan = InspectionPlan(
            organization_id=org.id,
            facility_id=bridge.id,
            title="Structural crack baseline",
            objectives="Locate, segment and measure simulated concrete cracks.",
            required_coverage_percent=95,
            safety_notes="Controlled laboratory scene.",
        )
        pipeline_plan = InspectionPlan(
            organization_id=org.id,
            facility_id=offshore.id,
            title="Subsea pipeline coverage pass",
            objectives="Synchronize RGB, sonar and navigation; estimate visible pipeline coverage.",
            required_coverage_percent=85,
            safety_notes="Synthetic project-owned data; no operational asset claim.",
        )
        db.add_all([structural_plan, pipeline_plan])
        db.flush()

        structural_mission = Mission(
            organization_id=org.id,
            facility_id=bridge.id,
            asset_id=concrete.id,
            plan_id=structural_plan.id,
            name="Structural Crack Baseline",
            mission_type="structural",
            capture_device="handheld RGB + calibration target",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        pipeline_mission = Mission(
            organization_id=org.id,
            facility_id=offshore.id,
            asset_id=pipeline.id,
            plan_id=pipeline_plan.id,
            name="Subsea Pipeline Pass 01",
            mission_type="pipeline",
            capture_device="AUV RGB + side-scan sonar",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add_all([structural_mission, pipeline_mission])
        db.flush()
        for entity, action in [
            (bridge, "facility.created"),
            (offshore, "facility.created"),
            (concrete, "asset.created"),
            (pipeline, "asset.created"),
            (structural_mission, "mission.created"),
            (pipeline_mission, "mission.created"),
        ]:
            record(db, org.id, action, entity.__class__.__name__.lower(), entity.id, {})
        db.commit()

        print("STAGE structural-processing", flush=True)
        structural_outputs = []
        structural_dir = OBJECT_ROOT / org.id / structural_mission.id
        for source in sorted((ROOT / "datasets/project-owned/structural").glob("structural_0[0-2].png")):
            target, digest = copy_upload(source, structural_dir / "uploads")
            db.add(
                Upload(
                    organization_id=org.id,
                    mission_id=structural_mission.id,
                    media_type="image",
                    filename=source.name,
                    object_path=str(target),
                    sha256=digest,
                    size_bytes=target.stat().st_size,
                    metadata_json={"content_type": "image/png"},
                )
            )
            result = analyze_structural_file(target, structural_dir / "processed", None)
            structural_outputs.append(result)
            finding = Finding(
                organization_id=org.id,
                mission_id=structural_mission.id,
                asset_id=concrete.id,
                finding_type="concrete_crack",
                provenance="synthetic_defect",
                severity=result["severity"],
                confidence=result["confidence"],
                measurement_json=result["measurement"],
                evidence_path=result["overlay"],
                notes="Generated by real image processing. Human validation required.",
            )
            db.add(finding)
            db.flush()
            record(
                db,
                org.id,
                "finding.generated",
                "finding",
                finding.id,
                {"confidence": result["confidence"], "provenance": finding.provenance},
            )
        structural_mission.coverage_percent = 100.0
        structural_mission.status = "processed"
        structural_mission.completed_at = datetime.now(timezone.utc)
        record(db, org.id, "mission.processed", "mission", structural_mission.id, {"coverage_percent": 100.0})
        db.commit()

        print("STAGE pipeline-processing", flush=True)
        pipeline_outputs = []
        visibility_observations: list[tuple[float, float]] = []
        pipeline_dir = OBJECT_ROOT / org.id / pipeline_mission.id
        for index, source in enumerate(sorted((ROOT / "datasets/project-owned/pipeline").glob("pipeline_*.png"))):
            target, digest = copy_upload(source, pipeline_dir / "uploads")
            db.add(
                Upload(
                    organization_id=org.id,
                    mission_id=pipeline_mission.id,
                    media_type="image",
                    filename=source.name,
                    object_path=str(target),
                    sha256=digest,
                    size_bytes=target.stat().st_size,
                    metadata_json={"content_type": "image/png", "timestamp_s": index * 0.5},
                )
            )
            result = analyze_underwater_file(target, pipeline_dir / "processed")
            pipeline_outputs.append(result)
            visibility_observations.append((index * 5.0, result["visibility"]))
            finding = Finding(
                organization_id=org.id,
                mission_id=pipeline_mission.id,
                asset_id=pipeline.id,
                finding_type="pipeline_visibility_candidate",
                provenance="anomaly_candidate",
                severity="review-required" if result["confidence"] >= 0.25 else "low-confidence",
                confidence=result["confidence"],
                measurement_json={"visibility": result["visibility"]},
                evidence_path=result["overlay"],
                notes="Pipeline visibility candidate generated by deterministic processing.",
                start_timestamp_s=index * 0.5,
                end_timestamp_s=index * 0.5,
            )
            db.add(finding)
            db.flush()
            record(db, org.id, "finding.generated", "finding", finding.id, {"confidence": result["confidence"], "provenance": finding.provenance})

        for media_type, source in [
            ("sonar", ROOT / "datasets/project-owned/sonar/pipeline_sonar.csv"),
            ("navigation", ROOT / "datasets/project-owned/navigation/pipeline_navigation.csv"),
        ]:
            target, digest = copy_upload(source, pipeline_dir / "uploads")
            db.add(
                Upload(
                    organization_id=org.id,
                    mission_id=pipeline_mission.id,
                    media_type=media_type,
                    filename=source.name,
                    object_path=str(target),
                    sha256=digest,
                    size_bytes=target.stat().st_size,
                    metadata_json={"content_type": "text/csv"},
                )
            )
            if media_type == "sonar":
                pipeline_outputs.append(
                    {"source": str(target), "sonar_detections": [asdict(x) for x in detect_sonar_pipeline(target)]}
                )

        coverage = calculate_linear_coverage(60.0, visibility_observations)
        pipeline_mission.coverage_percent = coverage["coverage_percent"]
        pipeline_mission.summary_json = {"coverage": coverage, "distance_m": 60.0}
        pipeline_mission.status = "processed"
        pipeline_mission.completed_at = datetime.now(timezone.utc)
        record(db, org.id, "mission.processed", "mission", pipeline_mission.id, {"coverage_percent": coverage["coverage_percent"]})
        db.commit()

        print("STAGE review-maintenance", flush=True)
        structural_finding = db.scalar(
            select(Finding).where(Finding.mission_id == structural_mission.id).order_by(Finding.created_at)
        )
        structural_finding.status = "human_confirmed"
        structural_finding.provenance = "human_confirmed_finding"
        structural_finding.severity = "moderate"
        structural_finding.notes = "Human-confirmed simulated crack for workflow validation."
        review = Review(
            organization_id=org.id,
            finding_id=structural_finding.id,
            decision="accept",
            severity="moderate",
            notes=structural_finding.notes,
        )
        work_order = WorkOrder(
            organization_id=org.id,
            finding_id=structural_finding.id,
            title="Engineering review of concrete crack",
            priority="medium",
            recommendation="Verify using calibrated field measurement before maintenance decision.",
        )
        db.add_all([review, work_order])
        db.flush()
        record(db, org.id, "finding.reviewed", "finding", structural_finding.id, {"decision": "accept"})
        record(db, org.id, "work_order.created", "work_order", work_order.id, {"finding_id": structural_finding.id})

        model_a = ModelVersion(
            organization_id=org.id,
            name="Structural Classical CV",
            version="0.1.0",
            task="crack_segmentation",
            framework="OpenCV + scikit-image",
            metrics_json={k: performance["structural"][k] for k in ["precision", "recall", "iou", "f1", "cpu_latency_ms_mean"]},
            release_gate_json={"minimum_critical_recall": 0.90, "maximum_cpu_latency_ms": 150, "require_model_card": True, "require_failure_analysis": True},
            model_card_path="ml/model-cards/structural-classical-cv.md",
        )
        model_b = ModelVersion(
            organization_id=org.id,
            name="Underwater Pipeline CV",
            version="0.1.0",
            task="pipeline_segmentation",
            framework="OpenCV",
            metrics_json={k: performance["pipeline"][k] for k in ["precision", "recall", "iou", "f1", "cpu_latency_ms_mean", "mean_visibility"]},
            release_gate_json={"minimum_critical_recall": 0.90, "maximum_cpu_latency_ms": 150, "require_model_card": True, "require_failure_analysis": True},
            model_card_path="ml/model-cards/underwater-pipeline-cv.md",
        )
        db.add_all([model_a, model_b])
        db.flush()
        record(db, org.id, "model.registered", "model_version", model_a.id, {"version": model_a.version})
        record(db, org.id, "model.registered", "model_version", model_b.id, {"version": model_b.version})

        device = EdgeDevice(
            organization_id=org.id,
            name="Edge Node A-17",
            device_type="cpu",
            status="online",
            last_seen_at=datetime.now(timezone.utc),
        )
        db.add(device)
        db.flush()
        sync_payload = {
            "mission_id": pipeline_mission.id,
            "evidence_video": evidence_video,
            "coverage_percent": pipeline_mission.coverage_percent,
        }
        checksum = sha256(json.dumps(sync_payload, sort_keys=True).encode()).hexdigest()
        sync = SyncEvent(
            id="demo-sync-0001",
            organization_id=org.id,
            edge_device_id=device.id,
            sequence=1,
            payload_json=sync_payload,
            checksum=checksum,
        )
        db.add(sync)
        record(db, org.id, "edge.sync.accepted", "sync_event", sync.id, {"device_id": device.id, "sequence": 1})
        db.commit()

        print("STAGE reports", flush=True)
        reports: list[dict] = []
        for mission, facility, asset, report_type in [
            (structural_mission, bridge, concrete, "mission"),
            (pipeline_mission, offshore, pipeline, "coverage"),
        ]:
            findings = db.scalars(select(Finding).where(Finding.mission_id == mission.id)).all()
            audit = db.scalars(
                select(AuditEvent).where(AuditEvent.entity_id == mission.id).order_by(AuditEvent.created_at)
            ).all()
            report_data = {
                "mission": mission.name,
                "facility": facility.name,
                "asset": asset.name,
                "inspector": "Demo Inspector",
                "capture_device": mission.capture_device,
                "inspection_date": datetime.now(timezone.utc).date().isoformat(),
                "coverage_percent": mission.coverage_percent,
                "model_version": ", ".join(sorted({f.model_version for f in findings})) or "n/a",
                "review_status": "mixed",
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
                "audit": [
                    {"timestamp": e.created_at.isoformat(), "action": e.action, "actor": e.actor_id or "system"}
                    for e in audit
                ],
                "sign_off": "Generated report - inspector digital sign-off pending",
            }
            path = OBJECT_ROOT / org.id / mission.id / "reports" / f"{report_type}-{mission.id}.pdf"
            generate_mission_report(report_data, path)
            digest = sha256(path.read_bytes()).hexdigest()
            report = Report(
                organization_id=org.id,
                mission_id=mission.id,
                report_type=report_type,
                object_path=str(path),
                checksum=digest,
            )
            db.add(report)
            db.flush()
            record(db, org.id, "report.generated", "report", report.id, {"mission_id": mission.id, "checksum": digest})
            reports.append({"id": report.id, "mission_id": mission.id, "report_type": report_type, "object_path": str(path), "checksum": digest})
        db.commit()

        findings_count = db.scalar(select(Finding).count()) if False else len(db.scalars(select(Finding)).all())
        audit_count = len(db.scalars(select(AuditEvent)).all())
        dashboard = {
            "organization": {"id": org.id, "name": org.name},
            "facilities": 2,
            "assets": 4,
            "active_missions": 2,
            "critical_findings": 0,
            "coverage_percent": (structural_mission.coverage_percent + pipeline_mission.coverage_percent) / 2,
            "work_order_backlog": 1,
            "device_status": [{"name": device.name, "status": device.status, "software_version": device.software_version}],
            "model_status": [{"name": model_a.name, "version": model_a.version, "status": model_a.status}, {"name": model_b.name, "version": model_b.version, "status": model_b.status}],
            "risk_trend": [42, 40, 38, 35, 33, 31],
        }
        summary = {
            "organization": {"id": org.id, "name": org.name},
            "facilities": [{"id": bridge.id, "name": bridge.name, "country": bridge.country}, {"id": offshore.id, "name": offshore.name, "country": offshore.country}],
            "assets": [{"id": concrete.id, "name": concrete.name, "asset_type": concrete.asset_type}, {"id": pipeline.id, "name": pipeline.name, "asset_type": pipeline.asset_type}],
            "missions": [{"id": structural_mission.id, "name": structural_mission.name, "mission_type": structural_mission.mission_type, "coverage_percent": structural_mission.coverage_percent}, {"id": pipeline_mission.id, "name": pipeline_mission.name, "mission_type": pipeline_mission.mission_type, "coverage_percent": pipeline_mission.coverage_percent}],
            "processing": {"structural": {"outputs": structural_outputs, "coverage_percent": structural_mission.coverage_percent}, "pipeline": {"outputs": pipeline_outputs, "coverage_percent": pipeline_mission.coverage_percent}},
            "review": {"id": review.id, "finding_id": review.finding_id, "decision": review.decision, "finding_status": structural_finding.status},
            "work_order": {"id": work_order.id, "finding_id": work_order.finding_id, "title": work_order.title, "priority": work_order.priority, "status": work_order.status},
            "models": [{"id": model_a.id, "name": model_a.name, "version": model_a.version, "status": model_a.status}, {"id": model_b.id, "name": model_b.name, "version": model_b.version, "status": model_b.status}],
            "edge": {"device": {"id": device.id, "name": device.name, "status": device.status}, "sync": {"status": "accepted", "event_id": sync.id}, "duplicate_replay": {"status": "duplicate", "event_id": sync.id}},
            "dashboard": dashboard,
            "findings_count": findings_count,
            "audit_event_count": audit_count,
            "evidence_video": evidence_video,
            "reports": reports,
            "claims": "All CV outputs are produced by executable algorithms over project-owned synthetic media. External dataset claims are excluded from the default demo.",
        }

    (OUTPUT / "partial_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (OUTPUT / "demo_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (OUTPUT / "reports_manifest.json").write_text(json.dumps(reports, indent=2, default=str))
    print(
        json.dumps(
            {
                "database": str(DB),
                "findings": summary["findings_count"],
                "summary": str(OUTPUT / "demo_summary.json"),
                "reports": [r["object_path"] for r in reports],
                "sync_replay": "duplicate",
            },
            indent=2,
        ),
        flush=True,
    )
    # Some OpenCV builds leave non-daemon native worker state alive after the
    # demo is complete. All database/file writes above are closed and flushed,
    # so force a clean CLI exit to keep `make demo` deterministic in CI.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
