FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY services services
COPY apps/edge-agent apps/edge-agent
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app:/app/apps/edge-agent
ENTRYPOINT ["python", "-m", "openinspect_edge.cli"]
