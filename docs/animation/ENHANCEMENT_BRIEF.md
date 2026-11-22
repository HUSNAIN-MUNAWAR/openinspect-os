# Production Animation Enhancement Brief

## Objective

Turn the existing OpenInspect OS synthetic pipeline demo into a clear production-reference reel that shows the complete evidence path: synthetic capture, image enhancement, classical-CV segmentation, confidence/visibility signals, and human-review handoff.

## Existing baseline

- Project-owned synthetic pipeline frames already exist under `datasets/project-owned/pipeline/`.
- The real deterministic baseline is `services.vision.underwater.analyze_underwater_image`.
- Existing evidence output remains available as `demo/outputs/pipeline_evidence.gif`.

## New deliverable

`python scripts/generate_production_reel.py` creates:

- `demo/outputs/production_inspection_reel.gif`
- `demo/outputs/production_inspection_reel_manifest.json`

The generated reel runs the actual repository baseline on every synthetic frame and records the model version, confidence, visibility, timestamp, and provenance for every frame.

## Model and data contract

| Field | Contract |
|---|---|
| Model | `underwater-pipeline-cv` |
| Version | `classical-cv-0.1` |
| Input | 960×540 project-owned synthetic pipeline frame |
| Output | Enhanced frame, candidate mask, overlay, confidence, visibility |
| Provenance | `project-owned synthetic pipeline scene; algorithmic segmentation` |
| Claim boundary | Software-validation demo only; no field-performance claim |

## Release gate

The reel is suitable for documentation and portfolio demonstration after the generator and manifest pass tests. It must not be presented as offshore inspection accuracy, corrosion detection, or a certified NDT result.
