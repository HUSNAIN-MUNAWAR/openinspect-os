# ADR 0001: Project-owned data is the default demo dependency

- Status: accepted
- Date: 2026-07-14

External inspection datasets vary in licence clarity and redistribution terms. The default demo therefore generates and owns its media, masks, sonar and navigation records. External datasets are optional adapters. This keeps CI reproducible and prevents accidental redistribution while preserving a path to real research data.
