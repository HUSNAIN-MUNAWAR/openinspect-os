# MLOps

The default release contains classical CV baselines because they are fully reproducible on CPU. The plugin boundary allows PyTorch/ONNX/OpenVINO models to replace them without changing the mission API.

Evaluation writes `demo/outputs/model_performance.json`. Release gates are stored with each model version. Metrics are never hard-coded into the UI; they are loaded from the generated evaluation artifact and database.

```yaml
release_gate:
  minimum_critical_recall: 0.90
  maximum_false_positive_rate: 0.10
  maximum_cpu_latency_ms: 150
  maximum_regression_percent: 3
  require_model_card: true
  require_failure_analysis: true
```

A candidate that misses a gate remains a candidate; the demo does not automatically label it production-ready.
