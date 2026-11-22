PYTHON ?= python

.PHONY: install demo animation external-runtime api test lint clean frontend

install:
	$(PYTHON) -m pip install -e .[dev]

demo:
	$(PYTHON) scripts/run_demo.py

animation:
	$(PYTHON) scripts/generate_production_reel.py

external-runtime:
	$(PYTHON) scripts/generate_external_crackseg_runtime_video.py

api:
	PYTHONPATH=.:apps/api uvicorn openinspect_api.main:app --host 0.0.0.0 --port 8000 --reload

test:
	PYTHONPATH=.:apps/api:apps/edge-agent pytest

lint:
	ruff check .

frontend:
	cd apps/web && npm install && npm run dev

clean:
	rm -rf demo/outputs/* docs/screenshots/* datasets/project-owned/structural/* datasets/project-owned/pipeline/* datasets/project-owned/sonar/* datasets/project-owned/navigation/* datasets/project-owned/ground_truth/* openinspect.db
