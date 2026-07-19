# Vayu-Drishti — Smart City Air Quality Intelligence Platform

[![CI](https://github.com/YOUR_ORG/vayu-drishti/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_ORG/vayu-drishti/actions/workflows/ci.yml)

**Vayu-Drishti** ("Air Vision") is an AI-powered platform for real-time air quality
monitoring, forecasting, source attribution, and policy simulation in Indian smart cities.

Built for the ET Hackathon, the platform integrates satellite data, ground sensors,
traffic patterns, weather models, and citizen reports into a unified intelligence layer
driven by a multi-agent AI system.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                       │
│  Maps · Charts · 3D Twin · AI Chat · Alerts · Analytics       │
└──────────────────┬───────────────────────────────────────────┘
                   │ REST / GraphQL / WebSocket
┌──────────────────▼───────────────────────────────────────────┐
│                  API Gateway (FastAPI)                        │
│           Routing · Auth · Rate Limiting · Caching             │
└──────┬──────────────┬──────────────┬─────────────────────────┘
       │              │              │
┌──────▼─────┐ ┌──────▼─────┐ ┌──────▼──────────────────┐
│  Ingestion  │ │  Knowledge │ │   AI Agent Orchestrator   │
│  Pipeline   │ │   Graph    │ │  ┌─────────────────────┐  │
│  CPCB       │ │  Neo4j     │ │  │ AQI Forecast Agent │  │
│  IMD        │ │  Builder   │ │  │ Burn Detection     │  │
│  Sentinel   │ │            │ │  │ Source Attribution │  │
│  Bhuvan     │ │            │ │  │ Health Risk        │  │
│  Citizen    │ │            │ │  │ City Planning      │  │
└─────────────┘ └────────────┘ │  │ ... 13 agents      │  │
                               │  └─────────────────────┘  │
                               └────────┬───────────────────┘
                                        │
                               ┌────────▼───────────────────┐
                               │    Decision Engine (RL)      │
                               │  Traffic · Squad · Emergency │
                               └─────────────────────────────┘
```

### Components

| Component | Stack | Description |
|-----------|-------|-------------|
| **Backend** | Python 3.12, FastAPI, Pydantic | Unified API with REST, GraphQL (Strawberry), WebSocket |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS | Interactive dashboard with MapLibre, Deck.gl, Three.js, ECharts |
| **Agents** | Python, asyncio | 13 specialized AI agents with shared orchestrator |
| **Ingestion** | Python, httpx, STAC | Connectors for CPCB, IMD, Sentinel, Bhuvan, Google Traffic, Citizen |
| **Knowledge Graph** | Python, NetworkX, causalnex | Causal DAG and graph-based reasoning |
| **LLM Service** | Python, OpenAI-compatible | Local LLM inference (Ollama/vLLM) for explainability & chat |
| **Decision Engine** | Python, NumPy | RL-based traffic, squad, and emergency optimization |
| **Monitoring** | Prometheus + Grafana | Service metrics, AQI alerts, Grafana dashboards |
| **Stream Processing** | Java, Apache Flink | Real-time stream processing (Kafka streams) |

---

## Quick Start

### Prerequisites

- **Python 3.12+** ([Install](https://www.python.org/downloads/))
- **Node.js 20+** ([Install](https://nodejs.org/))
- **Git**

### 1. Clone

```bash
git clone https://github.com/YOUR_ORG/vayu-drishti.git
cd vayu-drishti
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (optional for local dev)
```

### 3. Install Dependencies

```bash
# Everything
make install

# Or step-by-step:
pip install -e backend/
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

### 4. Run

Open **two terminals**:

**Terminal 1 — Backend:**
```bash
make backend
# FastAPI running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Terminal 2 — Frontend:**
```bash
make frontend
# Next.js running at http://localhost:3000
```

### 5. Seed Demo Data (Optional)

```bash
make seed-demo
```

---

## Detailed Setup

### Backend Configuration

The backend reads configuration from `.env` (loaded automatically via
`pydantic-settings`). Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `8000` | API server port |
| `APP_DEBUG` | `true` | Enable debug mode |
| `APP_SECRET_KEY` | `change-me-in-production` | JWT/encryption key |
| `DATA_DIR` | `./backend/data` | Runtime data directory |
| `LLM_ENDPOINT` | `http://localhost:8001/v1` | Local LLM endpoint |

All API keys are optional for local development — the app runs with synthetic
data from the seed script.

### Frontend Configuration

| Variable | Location | Description |
|----------|----------|-------------|
| API proxy | `next.config.js` | Proxies `/api/*` and `/graphql` to backend |
| Map tiles | `CityMap.tsx` | Uses free MapLibre/OpenStreetMap tiles |

### Running Individual Agents

Each agent can run independently:

```bash
python -m agents.agent-aqi-forecast.src.main
python -m agents.agent-burn-detection.src.main
# etc.
```

### Monitoring Stack

```bash
# Start Prometheus + Grafana (requires Docker)
docker compose -f infra/docker-compose.yml up
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

---

## Testing

```bash
# Run all tests
make test

# Run specific tests
python -m pytest tests/test_agents.py -v
python -m pytest tests/test_ingestion.py -v

# Frontend lint
cd frontend && npm run lint
```

---

## Project Structure

```
vayu-drishti/
├── agents/                    # 13 AI agents
│   ├── orchestrator/          #   Agent orchestrator
│   ├── agent-aqi-forecast/    #   AQI forecasting
│   ├── agent-burn-detection/  #   Fire/burn detection
│   ├── agent-change-detection/
│   ├── agent-citizen-complaint/
│   ├── agent-city-planning/
│   ├── agent-emergency/
│   ├── agent-enforcement/
│   ├── agent-explainability/
│   ├── agent-health-risk/
│   ├── agent-policy-simulation/
│   ├── agent-resource-allocation/
│   ├── agent-source-attribution/
│   └── agent-traffic/
├── api-gateway/               # API gateway service
├── backend/                   # Unified FastAPI backend
│   ├── src/
│   │   ├── agents/            #   Agent implementations
│   │   ├── api/               #   REST, GraphQL, WebSocket
│   │   ├── decision_engine/   #   RL optimization
│   │   ├── infrastructure/    #   DB, cache, event bus
│   │   ├── ingestion/         #   Data connectors
│   │   ├── knowledge_graph/   #   Graph builder
│   │   └── llm_service/       #   LLM integration
│   ├── data/                  #   Runtime data (gitignored)
│   └── tests/                 #   Backend tests
├── data/                      # External data (gitignored)
├── decision-engine/           # Standalone decision engine
├── deploy/                    # Deployment scripts
├── docs/                      # Documentation
├── evaluation/                # Model evaluation
├── feature-store/             # Feature store
├── frontend/                  # Next.js app
│   ├── src/
│   │   ├── app/               #   Pages
│   │   ├── components/        #   React components
│   │   └── public/data/       #   Static GeoJSON data
├── infra/                     # Monitoring
│   └── monitoring/
│       ├── prometheus/        #   Prometheus config + alerts
│       └── grafana/           #   Grafana dashboards
├── ingestion/                 # Standalone ingestion service
├── knowledge-graph/           # Standalone graph builder
├── llm-service/               # Standalone LLM server
├── mobile/                    # React Native app (scaffold)
├── models/                    # ML models & notebooks
├── scripts/                   # Utility scripts
├── stream-processing/         # Java Flink streams
└── tests/                     # Integration tests
```

---

## Git Workflow

### Branching

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready, protected |
| `develop` | Integration branch |
| `feat/*` | New features |
| `fix/*` | Bug fixes |
| `refactor/*` | Code improvements |
| `docs/*` | Documentation changes |

### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add AQI threshold alerting
fix: correct CPCB API pagination offset
refactor: extract event bus into shared module
docs: update API endpoint documentation
```

### Release Process

1. Merge feature branches into `develop`
2. Run full test suite
3. Create release branch `release/vX.Y.Z`
4. Tag and merge into `main`
5. Add release notes to GitHub Releases

---

## Security

- **Never commit `.env`** — it contains API keys and secrets
- API keys in `.env.example` are placeholders
- The `.gitignore` prevents committing sensitive files
- Report vulnerabilities via our [Security Policy](SECURITY.md)

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Maps & Viz | MapLibre GL, Deck.gl, Three.js, ECharts, D3 |
| ML/AI | PyTorch, scikit-learn, NetworkX, causalnex |
| LLM | llama3-70b (Ollama/vLLM) |
| Data | NumPy, Pandas, rasterio |
| Monitoring | Prometheus, Grafana |
| Streams | Apache Flink, Kafka |
| Mobile | React Native (scaffold) |

---

## License

[MIT](LICENSE)
