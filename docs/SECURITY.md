# Security and Threat Model

## Principal threats

- Tampered or replayed inspection media
- Unauthorized report modification
- Model artifact replacement
- Malicious uploads and parser abuse
- Cross-tenant object access
- Edge-device compromise or credential theft
- Sync replay and sequence manipulation
- Audit-log deletion or alteration

## Implemented controls

- Tenant identifiers on all domain records and tenant-scoped queries
- SHA-256 checksums for uploads, reports and sync envelopes
- Replay-safe sync event IDs and per-device sequence uniqueness
- Password hashing and JWT primitives
- Upload size/type validation and isolated object paths
- Immutable-style audit events for state-changing actions
- Health/readiness endpoints and correlation-friendly structured records
- Environment-based secret configuration

## Production hardening still required

Use managed secrets, TLS/mTLS, malware scanning, object-store signed URLs, append-only audit storage, external identity, database row-level security, SBOMs and hardware-backed device identity before critical-infrastructure deployment.
