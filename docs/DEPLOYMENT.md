# Deployment

## Local CPU demo

```bash
python -m pip install -e .[dev]
make demo
make api
cd apps/web && npm install && npm run dev
```

## Container stack

```bash
docker compose -f infra/compose/docker-compose.yml up --build
```

The Compose stack provisions PostGIS, Redis, MinIO, API and web services. SQLite is used only by the self-contained demo and tests.
