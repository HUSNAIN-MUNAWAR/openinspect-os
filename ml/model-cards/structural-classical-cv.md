# Model Card: Structural Classical CV 0.1.0

## Purpose

CPU-only baseline for dark crack/surface localization on concrete-like images, followed by morphology, skeletonization and measurement.

## Training

No learned training. Thresholds and morphology are deterministic.

## Evaluation

Run `make demo`; metrics are written to `demo/outputs/model_performance.json`. They apply only to the generated synthetic dataset.

## Limitations

Texture, shadows, joints and stains may cause errors. A rectangular simulated surface-damage sample is a documented failure case. Millimetres are emitted only when `mm_per_pixel` is supplied. Not certified for safety decisions.
