# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning: [SemVer](https://semver.org/).

## [Unreleased]
### Added
- Project skeleton: FastAPI backend (Clean Architecture), React + TypeScript frontend, Docker Compose for dev/test/prod.
- `GET /api/health` endpoint and a backend status card in the UI.
- MIT license.
- OpenTelemetry traces, metrics and logs from the API, viewed in Grafana (`grafana/otel-lgtm`) or written to JSON Lines files (`SA_OTEL_EXPORTER=file`).
