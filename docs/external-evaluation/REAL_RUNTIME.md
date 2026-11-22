# Real runtime evidence

This folder contains an execution trace of the repository's actual structural
inspection path. It is intentionally separate from the older project-owned
synthetic demo reel.

## Reproduce

The first run downloads the external Crack-Seg archive if it is not already
present. The raw archive is ignored by git; its SHA-256 is recorded in the JSON
report so the local input can be identified without committing the dataset.

```powershell
py -3.12 -u scripts/generate_external_crackseg_runtime_video.py
```

The runner then:

1. selects the first four images from the external test split;
2. executes `services.vision.structural.analyze_file` on each image;
3. reads the actual mask written by that execution and derives candidate boxes;
4. compares those boxes with the dataset's YOLO-segmentation boxes at IoU 0.5;
5. holds each real analyzed image for six frames so the trace is watchable;
6. writes the MP4, poster, per-prediction CSV, and JSON report.

No box, score, input image, or model output is generated solely for display.
The repeated frames are a presentation choice; the detections are not
interpolated or animated into existence.

## Current result

The captured run uses deterministic classical computer vision and no learned
checkpoint. On the four selected images it produced:

| Measure | Result |
| --- | ---: |
| Ground-truth boxes | 8 |
| Predicted boxes | 26 |
| True positives (IoU >= 0.5) | 1 |
| False positives | 25 |
| Missed ground-truth boxes | 7 |
| Precision | 3.8462% |
| Recall | 12.5% |
| F1 | 0.058824 |

This is a real, reproducible baseline trace and a failure signal—not evidence
that OpenInspect is production-ready. The existing synthetic reel must not be
used to claim learned-model or field performance.

## Artifacts

- `runtime-smoke/runtime_video.mp4` — local execution trace.
- `runtime-smoke/runtime_poster.png` — first frame for visual inspection.
- `runtime-smoke/runtime_predictions.csv` — one row per predicted candidate,
  including TP/FP status and IoU.
- `runtime-smoke/runtime_summary.json` — input hash, runtime versions, model
  identity, per-sample counts, aggregate metrics, and output hashes.
