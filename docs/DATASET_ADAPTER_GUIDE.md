# Dataset Adapter Guide

Adapters convert a user-supplied source directory into a versioned manifest; they do not silently download or redistribute ambiguous data. Validate expected files, preserve upstream licence and attribution, calculate checksums, record sensor/timestamp/annotation schemas and expose deterministic train/validation/test splits. Add adapter tests using tiny project-owned fixtures.
