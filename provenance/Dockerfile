# One image runs the whole application: API, worker thread and dashboard.
# That is what makes it deployable on a single free-tier web service.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/ ./packages/
COPY apps/ ./apps/
COPY scripts/ ./scripts/

# SQLite and uploads live here. On a free tier this is ephemeral: the container
# is rebuilt on every deploy and the corpus goes with it. Mount a disk, or move
# PROVENANCE_DB to Postgres, before anyone relies on the data.
RUN mkdir -p /app/data
VOLUME ["/app/data"]

ENV PROVENANCE_DB=/app/data/provenance.db \
    PROVENANCE_CORPUS=/app/data/corpus.db \
    PROVENANCE_UPLOADS=/app/data/uploads \
    PROVENANCE_SECURE_COOKIES=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health')"

CMD ["python", "-m", "apps.api.main"]
