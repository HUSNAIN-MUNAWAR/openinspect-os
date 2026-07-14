from __future__ import annotations

from sqlalchemy.orm import Session
from .models import AuditEvent


def record(db: Session, organization_id: str, action: str, entity_type: str, entity_id: str, metadata: dict | None = None, actor_id: str | None = None) -> AuditEvent:
    event = AuditEvent(organization_id=organization_id, action=action, entity_type=entity_type, entity_id=entity_id, metadata_json=metadata or {}, actor_id=actor_id)
    db.add(event)
    db.flush()
    return event
