# Release Process

1. Freeze dataset manifests and regenerate `make demo`.
2. Run Python tests, type checks, frontend tests/build and container build.
3. Review model cards, failure analysis and release gates.
4. Confirm no external media, secrets or customer identifiers are present.
5. Render and inspect generated PDFs and screenshots.
6. Update changelog and tag a signed semantic version.
7. Publish checksums, SBOM/container provenance and migration notes.
