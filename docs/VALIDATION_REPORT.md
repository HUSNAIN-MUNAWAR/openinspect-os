# OpenInspect OS Validation Report

Validation date: **2026-07-14**  
Validated artifact: local OpenInspect OS engineering reference implementation  
Default execution mode: CPU-only, SQLite/local object store, project-owned synthetic inspection media

## Executive result

The repository provides a runnable end-to-end inspection demonstration rather than a frontend-only mockup. The validated path creates assets and missions, performs executable structural and pipeline processing, persists findings and evidence, calculates measurements and coverage, records human review and maintenance work, generates PDF reports, registers models, and exercises replay-safe edge synchronization.

The result is **not** a certified NDT product and the included CV baselines are **not** field-performance models. All benchmark values below apply only to the generated project-owned validation set.

## Reproducible demo

Command:

```bash
make demo
```

Result: **PASS** (`MAKE_DEMO_RC=0`)

Generated:

- 8 structural RGB images and binary masks
- 12 sequential underwater-style pipeline frames and binary masks
- 24 timestamped sonar records
- 24 timestamped navigation records
- 1 organization, 2 facilities, 4 assets and 2 processed missions
- 15 persisted findings and 30 audit events
- accepted inspector review and a persisted work order
- 2 model-version records and 1 edge device
- accepted sync event plus duplicate-replay result
- 2 query-driven PDF reports
- 4 UI preview images, 1 MP4 evidence clip and 1 animated GIF

Mission results:

| Mission | Coverage |
|---|---:|
| Structural Crack Baseline | 100.0% |
| Subsea Pipeline Pass 01 | 83.33% |

## Measured CV results

Source: `demo/outputs/model_performance.json`

| Baseline | Images | Precision | Recall | IoU | F1 | Mean CPU latency | p95 CPU latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| Structural classical CV | 8 | 0.9151 | 0.7287 | 0.6791 | 0.7907 | 78.09 ms | 206.57 ms |
| Underwater pipeline classical CV | 12 | 0.9956 | 0.8513 | 0.8481 | 0.9174 | 143.52 ms | 195.30 ms |

The pipeline evaluation also recorded mean visibility `0.2818`. Latency depends on the executing CPU and must be regenerated on deployment hardware.

## Backend and ML checks

| Check | Result |
|---|---|
| `pytest -q` | **PASS - 10 tests** |
| `ruff check .` | **PASS** |
| mypy over services and API | **PASS - 26 source files** |
| editable package imports | **PASS** (`openinspect_api`, `openinspect_edge`, `openinspect_sdk`) |
| Alembic upgrade | **PASS - revision 0001** |
| Fresh migration schema | **PASS - 19 tables including Alembic metadata** |
| Compose YAML parse | **PASS** - `api`, `db`, `minio`, `redis`, `web` |

The test suite covers executable CV output, measurement behavior, temporal merging, coverage calculation, change detection, API/database behavior, tenant isolation, synchronization and reporting paths.

## API smoke test

The demo database was loaded through FastAPI's test client.

| Endpoint | Result |
|---|---|
| `/health` | 200 |
| `/ready` | 200 |
| `/dashboard` | 200 |
| `/facilities` | 200, 2 records |
| `/assets` | 200, 4 records |
| `/missions` | 200, 2 records |
| `/findings` | 200, 15 records |
| `/reports` | 200, 2 records |
| `/models` | 200, 2 records |

## Frontend checks

| Check | Result |
|---|---|
| `npm run lint` | **PASS** |
| `npm run typecheck` | **PASS** |
| `npm test` | **PASS - 1 navigation-contract test** |
| `npm run build` | **PASS** |
| `npm audit --audit-level=high` | **PASS - 0 vulnerabilities reported** |

Production build: Next.js 16.2.10 with Webpack, clean `.next` prebuild, single-CPU/worker-safe configuration. Generated routes:

```text
/
/_not-found
/assets
/coverage
/facilities
/missions
/mlops
/platform
/reports
/review
```

## PDF validation

Reports are generated from persisted database records with ReportLab and include mission/facility/asset metadata, coverage, findings, measurements, evidence, audit events and sign-off state.

| Report | Pages | Render validation |
|---|---:|---|
| Structural mission report | 3 | **PASS** |
| Pipeline coverage report | 5 | **PASS** |

Both reports were rendered to PNG at 120 DPI using the repository PDF-validation workflow. The inspected render had no clipped text, black glyph boxes or broken evidence images. SHA-256 checksums are stored with report records.

## Data and licensing validation

- Default demo input is project-owned generated data under CC BY 4.0.
- External data is opt-in; no third-party archive is committed.
- SDNET2018 official record and CC BY 4.0 status were verified on 2026-07-14.
- SubPipe v3 official Zenodo record, archive sizes/checksums, CC BY 4.0 dataset licence and required OceanScan-MST/REMARO attribution were verified on 2026-07-14.
- The SubPipe GitHub repository's GPL-3.0 code licence is documented separately from the dataset licence.
- Dataset adapters require user-provided local paths and produce manifests rather than silently copying archives.

See [`DATASETS.md`](DATASETS.md) and [`RESEARCH_SOURCES.md`](RESEARCH_SOURCES.md).

## Security validation performed

- tenant-scoped domain queries
- password/JWT primitives
- upload allow-list, size validation and SHA-256 checksums
- tenant-prefixed object paths
- correlation/audit records
- idempotent sync event IDs and duplicate replay handling
- health/readiness endpoints
- secret-pattern scan over committed source: no detected private keys, common cloud access keys or embedded API tokens
- documented OT-focused threat model for tampered media, report modification, model replacement, malicious uploads, cross-tenant access, edge compromise and replay

Production hardening still requires external identity/TLS, malware scanning or CDR, database row-level security, signed object URLs, managed secrets, append-only audit storage and hardware-backed edge identity.

## Environment limitation

A Docker executable was not available in the validation sandbox. Therefore, Dockerfiles, Compose topology and YAML structure were inspected, but container image builds were **not executed here**. Native Python/API/frontend builds and the complete demo path were executed successfully.

## Scope limitations and remaining production work

This artifact intentionally avoids false completeness claims:

- The bundled data is synthetic and small.
- Structural output is a deterministic classical-CV baseline; it is not a trained field-qualified crack model.
- Pipeline segmentation detects pipeline visibility, not corrosion.
- Sonar processing emits candidate range bins, not supervised defect diagnoses.
- Full SLAM is not implemented or simulated; the system uses timestamped navigation trajectory and coverage.
- SQLite/local files support the demo; production requires PostgreSQL/PostGIS, Redis workers and controlled object storage.
- Model-registry records and release gates are implemented, but a deployed MLflow server and real retraining orchestration remain deployment integrations.
- The review workspace supports persisted accept, reject, reinspection and work-order actions; pixel-level interactive mask editing and advanced visual split/merge tooling remain roadmap work.
- Formal API/ASME/DNV/ISO/AMPP severity compliance and qualified-inspector validation are outside the project's current claims.

## Final status

**Validated as a runnable, open-source engineering reference implementation and portfolio-grade CPU demo.**  
**Not validated as a production-certified critical-infrastructure inspection system.**
