# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Asia/Kolkata
WORKDIR /app
RUN useradd --create-home --uid 1000 app

FROM base AS dev
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev]"
# Owned by the app user so tools can write caches (.ruff_cache, .mypy_cache, .pytest_cache) as non-root.
COPY --chown=app:app . .
RUN chown app:app /app
USER app
CMD ["uvicorn", "stock_analyzer.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--app-dir", "src"]

FROM base AS prod
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["uvicorn", "stock_analyzer.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
