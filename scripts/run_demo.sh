#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=".:apps/api:apps/edge-agent:${PYTHONPATH:-}"
python scripts/generate_demo_data.py
python ml/evaluation/evaluate_demo.py
python scripts/seed_demo.py
python scripts/generate_demo_visuals.py
