# Inspection Workflow

1. Register organization, facility, asset and optional component hierarchy.
2. Create an inspection plan with objective, expected route, coverage target and safety notes.
3. Create a mission and upload image, video, sonar or navigation data.
4. Validate file size, checksum, timestamps and declared media type.
5. Run mission processing. Every finding references executable output and a provenance class.
6. Review findings: accept, reject, edit, request reinspection or create a maintenance recommendation.
7. Generate work orders and checksum-protected PDF reports.
8. Use the audit log to reconstruct the decision chain.

Finding provenance values intentionally distinguish `synthetic_defect`, `anomaly_candidate`, `model_inference` and `human_confirmed_finding`.
