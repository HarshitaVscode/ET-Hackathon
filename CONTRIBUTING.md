# Contributing to Vayu-Drishti

Thank you for your interest in Vayu-Drishti! We welcome contributions of all kinds.

## Code of Conduct

Be respectful, inclusive, and constructive. Do not tolerate harassment or discrimination.

## How to Contribute

### Reporting Bugs

1. Check the [issue tracker](https://github.com/HarshitaVscode/ET-Hackathon/issues) for existing reports
2. If not found, open a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behaviour
   - Environment details (OS, Python version, browser)

### Suggesting Features

Open a GitHub Issue with the `enhancement` label describing the feature, its use case, and how it aligns with the project.

### Submitting Code

1. Fork the repository
2. Create a branch from `main`:
   - `feat/` for new features
   - `fix/` for bug fixes
   - `refactor/` for code improvements
   - `docs/` for documentation changes
3. Make your changes
4. Run tests: `make test`
5. Run linters: `make lint`
6. Commit using [Conventional Commits](https://www.conventionalcommits.org/):

   ```
   feat: add AQI threshold alerting
   fix: correct CPCB API pagination offset
   refactor: extract event bus into shared module
   docs: update API endpoint documentation
   ```

7. Push to your fork and open a pull request

### Pull Request Guidelines

- One feature or fix per PR
- Clear title and description
- Reference related issues
- Include tests for new functionality
- Update documentation if needed

## Project Structure

```
vayu-drishti/
├── backend/              # Unified Python backend (FastAPI)
│   ├── src/
│   │   ├── api/          # REST, GraphQL, WebSocket endpoints
│   │   ├── agents/       # Integrated agent implementations
│   │   ├── ml/           # ML training, inference, notebooks
│   │   ├── ingestion/    # Data ingestion connectors
│   │   ├── forecasting/  # Forecasting service
│   │   ├── knowledge_graph/
│   │   ├── decision_engine/
│   │   ├── llm_service/
│   │   └── infrastructure/
│   ├── enforcement_intelligence_agent/
│   │   └── notebooks/
│   ├── health_risk_advisory/
│   │   └── notebooks/
│   └── hyperlocal_forecast_agent/
│       └── notebooks/
├── agents/               # Standalone AI agent microservices
├── frontend/             # Next.js dashboard
├── api-gateway/
├── data/
├── decision-engine/
├── feature-store/
├── ingestion/
├── knowledge-graph/
├── llm-service/
├── stream-processing/
├── mobile/
├── evaluation/
└── infra/
```

## Coding Conventions

### Python

- [PEP 8](https://peps.python.org/pep-0008/) style
- Type hints for all function signatures
- Pydantic models for data validation
- `structlog` for structured logging

### TypeScript / JavaScript

- Strict TypeScript mode
- Functional components with hooks
- Tailwind CSS for styling

### Testing

- Python: `pytest` with verbose output
- Frontend: `jest` + React Testing Library

### Linting

- Python: `ruff` (`make lint`)
- Frontend: `next lint` (`cd frontend && npm run lint`)

## Questions?

Open a [GitHub Discussion](https://github.com/HarshitaVscode/ET-Hackathon/discussions) for questions, ideas, or general discussion.
