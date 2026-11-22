from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_animation_scene_manifest_is_reproducible_and_bounded() -> None:
    manifest = json.loads((ROOT / "docs/animation/scene_manifest.json").read_text(encoding="utf-8"))
    assert manifest["model"] == "underwater-pipeline-cv@classical-cv-0.1"
    assert manifest["source"] == "datasets/project-owned/pipeline"
    assert [scene["id"] for scene in manifest["scenes"]] == ["capture", "enhance", "segment", "review"]
    assert len(manifest["limitations"]) >= 3
