from __future__ import annotations

from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "demo" / "outputs"
DB = OUTPUT / "openinspect_demo.db"
OBJECT_ROOT = OUTPUT / "object-store"
sys.path[:0] = [str(ROOT), str(ROOT / "apps/api")]

from openinspect_api.models import Mission, Facility, Asset, Finding, AuditEvent, Report
from services.reporting.pdf import generate_mission_report


def main() -> None:
    engine = create_engine(f"sqlite:///{DB}")
    reports = []
    with Session(engine) as db:
        missions = db.scalars(select(Mission).order_by(Mission.name)).all()
        for mission in missions:
            facility = db.get(Facility, mission.facility_id)
            asset = db.get(Asset, mission.asset_id)
            findings = db.scalars(select(Finding).where(Finding.mission_id == mission.id)).all()
            audit = db.scalars(select(AuditEvent).where(AuditEvent.entity_id == mission.id).order_by(AuditEvent.created_at)).all()
            report_type = "coverage" if mission.mission_type == "pipeline" else "mission"
            data = {
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
                "sign_off": "Generated report — inspector digital sign-off pending",
            }
            path = OBJECT_ROOT / mission.organization_id / mission.id / "reports" / f"{report_type}-{mission.id}.pdf"
            generate_mission_report(data, path)
            digest = sha256(path.read_bytes()).hexdigest()
            obj = Report(
                organization_id=mission.organization_id,
                mission_id=mission.id,
                report_type=report_type,
                object_path=str(path),
                checksum=digest,
            )
            db.add(obj)
            db.flush()
            reports.append({"id": obj.id, "mission_id": mission.id, "report_type": report_type, "object_path": str(path), "checksum": digest})
        db.commit()
    manifest = OUTPUT / "reports_manifest.json"
    manifest.write_text(json.dumps(reports, indent=2))
    print(json.dumps(reports, indent=2), flush=True)
    import os as _os
    _os._exit(0)


if __name__ == "__main__":
    main()
