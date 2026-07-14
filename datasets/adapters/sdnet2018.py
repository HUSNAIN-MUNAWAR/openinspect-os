from __future__ import annotations
from pathlib import Path

PUBLISHED_CHECKSUM = "677411e784f194422c90f52d9ed0d7c6"  # Host publishes a 32-character checksum; verify its stated algorithm before use.

def prepare(source_dir: str | Path, output_manifest: str | Path) -> dict:
    source = Path(source_dir)
    images = sorted(source.rglob('*.jpg')) + sorted(source.rglob('*.jpeg'))
    if not images:
        raise FileNotFoundError('No SDNET2018 JPEG files found. Download from the official USU page first.')
    records = [{'path': str(p), 'label': 'cracked' if '/C' in str(p).replace('\\','/') else 'uncracked'} for p in images]
    import json
    Path(output_manifest).write_text(json.dumps({'dataset':'SDNET2018','images':len(records),'records':records},indent=2))
    return {'images': len(records), 'manifest': str(output_manifest)}
