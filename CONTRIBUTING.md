# Contributing to Vayu-Drishti

Thank you for your interest in contributing! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and constructive. Harassment or discriminatory behavior
will not be tolerated.

## How to Contribute

### 1. Reporting Bugs

- Check the issue tracker to avoid duplicates
- Include steps to reproduce, expected vs. actual behavior
- Mention your OS, Python version, and browser (for frontend issues)

### 2. Suggesting Features

- Open a GitHub Issue with the `enhancement` label
- Describe the problem you're solving, not just the feature you want
- Include mockups or examples if applicable

### 3. Submitting Code

1. **Fork** the repository
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make your changes** following the project conventions
4. **Run the tests**:
   ```bash
   make test
   ```
5. **Lint your code**:
   ```bash
   # Python
   ruff check .
   # TypeScript
   cd frontend && npm run lint
   ```
6. **Commit** using conventional commits:
   ```
   feat: add AQI threshold alerting
   fix: correct CPCB API pagination offset
   refactor: extract event bus into shared module
   ```
7. **Push** and open a Pull Request against `main`

### 4. Pull Request Guidelines

- Keep PRs focused — one feature/fix per PR
- Write a clear title and description
- Reference related issues
- Ensure all CI checks pass
- Request review from at least one maintainer

## Development Setup

See [README.md](README.md) for installation and running instructions.

## Project Structure

```
agents/             AI agent microservices (13 agents)
api-gateway/        API gateway (REST, GraphQL, WebSocket)
backend/            Unified FastAPI backend
data/               Runtime data (gitignored)
decision-engine/    RL-based decision engine
deploy/             Deployment scripts
docs/               Documentation
evaluation/         Evaluation results
feature-store/      Feature store
frontend/           Next.js + TypeScript frontend
infra/              Monitoring (Prometheus, Grafana)
ingestion/          Data ingestion pipeline
knowledge-graph/    Neo4j knowledge graph builder
llm-service/        LLM inference service
mobile/             React Native mobile app (scaffold)
models/             ML model notebooks
scripts/            Utility scripts
stream-processing/  Apache Flink / Kafka Streams (Java)
tests/              Integration tests
```

## Coding Conventions

- **Python**: Follow PEP 8. Use type hints everywhere. Prefer Pydantic for
  validation. Use `structlog` for structured logging.
- **TypeScript**: Use strict mode. Prefer functional components with hooks.
- **Imports**: Group standard library, third-party, then local. Sort alphabetically.
- **Testing**: Write tests for all new features. Use `pytest` for Python and
  `jest` (via Next) for frontend.
- **Documentation**: Keep README up to date. Document public APIs with docstrings.
