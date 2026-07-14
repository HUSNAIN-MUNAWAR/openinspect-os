# Model Contribution Guide

A model plugin must declare input contract, preprocessing, output schema, supported hardware, licence, dataset provenance, thresholds and calibration requirements. It must return evidence masks or candidate regions rather than canned findings, include a model card and evaluation JSON, pass release gates without fabricated metrics, and preserve human-review status. Exported artifacts belong outside Git unless their licence and size are suitable for redistribution.
