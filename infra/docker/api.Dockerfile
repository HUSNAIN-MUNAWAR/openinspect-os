FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md LICENSE ./
COPY services services
COPY apps/api apps/api
COPY apps/edge-agent apps/edge-agent
COPY packages/python-sdk packages/python-sdk
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app:/app/apps/api
CMD ["uvicorn", "openinspect_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
