# Inspection Workflow Plugin Guide

Plugins may add asset types, capture devices, datasets, models, measurement functions, severity policies or report sections. A plugin must provide a stable identifier, JSON-serializable configuration, tenant-safe persistence, deterministic error handling and tests. Measurements must identify units, calibration source and uncertainty. Severity plugins are decision support and cannot bypass inspector approval.
