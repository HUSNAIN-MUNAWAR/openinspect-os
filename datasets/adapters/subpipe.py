from __future__ import annotations
from pathlib import Path
import json

def prepare(source_dir: str | Path, output_manifest: str | Path) -> dict:
    source = Path(source_dir)
    if not source.exists():
        raise FileNotFoundError('Provide a user-downloaded SubPipe or SubPipeMini directory.')
    rgb = sorted(source.rglob('*.jpg')) + sorted(source.rglob('*.png'))
    csvs = sorted(source.rglob('*.csv'))
    manifest = {
        'dataset': 'SubPipe',
        'source': str(source),
        'rgb_or_sonar_images': len(rgb),
        'csv_files': len(csvs),
        'redistribution': 'CC BY 4.0 dataset; preserve the official OceanScan-MST/REMARO attribution. The adapter keeps archives user-supplied.',
    }
    Path(output_manifest).write_text(json.dumps(manifest, indent=2))
    return manifest
