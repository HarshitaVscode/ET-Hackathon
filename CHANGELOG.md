# Changelog

All notable changes to Vayu-Drishti will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-22

### Added

- Health Risk Advisory System notebook with multilingual citizen advisories
- Enforcement Intelligence & Prioritisation Agent with satellite-driven hotspot detection
- Hyperlocal AQI Forecasting Agent with 7-model comparison and walk-forward validation
- Interactive India GIS map with 20+ layers, 3 basemaps, and search tools
- SHAP-based explainable AI panel for enforcement decisions
- Environmental Intelligence Command Centre dashboard
- Comprehensive AQI Prediction Calculator with ipywidgets interface
- Multi-language health advisory support (English, Hindi, Kannada, Tamil)
- Multi-channel delivery framework (mobile, SMS, IVR, web, public displays)

### Changed

- AQI Prediction Calculator UI redesigned to match project dark theme
- Background opacity fixed across all widget containers for consistent theming
- Widget colors set via Python API for reliable rendering (handle_color, layout backgrounds)

### Removed

- 10 stub agent microservices (build-only stubs, unused)
- Build caches (.pytest_cache, .ruff_cache, catboost_info, egg-info)
- Development tools (scripts/, deploy/, backend/setup.py)
- generate_notebook.py files (superseded by static notebooks)
- GitHub CI/CD workflow (infra/monitoring, .github/workflows/ci.yml)

### Fixed

- Input card controls not rendering due to missing `sections.append(grid)` call
- `color` parameter in Layout (not valid in ipywidgets 7.x, caused TraitError)
- White container backgrounds showing through dark theme
- Inconsistent widget theming between inline styles and CSS

## [0.1.0] - 2025-07-19

### Added

- Initial project scaffold with multi-agent architecture
- FastAPI unified backend with REST, GraphQL, and WebSocket support
- Next.js frontend with interactive maps, charts, and 3D twin
- 13 specialized AI agents (AQI forecast, burn detection, source attribution, etc.)
- Knowledge graph and decision engine modules
- Ingestion pipeline with CPCB, IMD, Sentinel, Bhuvan, and citizen connectors
- Prometheus + Grafana monitoring stack
- Demo data seeding script
- Comprehensive Git and CI/CD configuration
