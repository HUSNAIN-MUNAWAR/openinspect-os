# Model Card: Underwater Pipeline Classical CV 0.1.0

## Purpose

CPU-only enhancement and pipeline visibility segmentation using low-saturation material cues, connected-component geometry and a Hough-line fallback.

## Training

No learned training. The baseline is deterministic and inspectable.

## Evaluation

Run `make demo`; metrics are written to `demo/outputs/model_performance.json` and apply only to generated underwater pipeline scenes.

## Limitations

Neutral elongated objects can be confused with pipelines. Visibility is a quality heuristic. The output is not corrosion, coating-loss or weld-defect detection. Real underwater data requires dataset-specific validation and inspector review.
