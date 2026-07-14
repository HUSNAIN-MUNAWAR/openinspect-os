# Contributing

OpenInspect OS accepts focused changes that preserve provenance, reproducibility and human review.

## Local checks

```bash
python -m pip install -e .[dev]
make demo
make test
make lint
cd apps/web && npm install && npm run typecheck && npm test && npm run build
```

## Rules

1. Never commit inspection media without explicit redistribution permission.
2. Label outputs as supervised ground truth, anomaly candidate, synthetic defect or human-confirmed finding.
3. Do not emit physical units without calibration and uncertainty metadata.
4. Add tests for measurements, tenant scope, sync idempotency and report changes.
5. Add a model card and evaluation artifact for every model version.
6. Do not present candidate models as production-ready.

Use conventional commits where practical. Significant architecture changes require an ADR under `docs/adr`.
