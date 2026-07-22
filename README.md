# Vayu-Drishti — Smart City Air Quality Intelligence Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/HarshitaVscode/ET-Hackathon)](https://github.com/HarshitaVscode/ET-Hackathon)

**Vayu-Drishti** ("Air Vision" in Sanskrit) is an AI-powered platform for real-time air quality monitoring, hyperlocal forecasting, source attribution, enforcement prioritisation, and citizen health risk advisory for Indian smart cities.

Built for the **ET Hackathon**, the platform integrates satellite remote sensing (Sentinel-5P TROPOMI, NASA FIRES), ground sensor data (CPCB, OpenAQ), meteorological models, traffic patterns, and demographic data into a unified intelligence layer driven by a multi-agent AI system.

---

## Problem Statement

Air pollution in Indian cities causes **1.67 million premature deaths annually** (Lancet, 2023). Existing systems are:

- **Lagging** — CPCB data is reported hourly, not in real time
- **Coarse-grained** — City-level AQI masks hyperlocal variation
- **Reactive** — Alerts arrive after pollution episodes, not before
- **Siloed** — Enforcement, health, and traffic departments operate independently
- **Non-explainable** — Black-box models offer no actionable attribution

**Vayu-Drishti** addresses all five gaps with an integrated, explainable, multi-agent AI platform.

---

## Key Features

| # | Feature | Description |
|---|---------|-------------|
| 🌫️ | **AQI Prediction** | Ensemble ML (XGBoost + Random Forest + LSTM) with 99% category accuracy |
| 🔮 | **Hyperlocal Forecasting** | 7-model comparison with 30+ engineered features, walk-forward validation |
| 🔥 | **Burn Detection** | Satellite-based crop residue / waste burning hotspot detection |
| 🔍 | **Source Attribution** | Probabilistic fingerprint matching across 11 source profiles |
| ⚖️ | **Enforcement Prioritisation** | RL-based ranking of enforcement actions by impact and urgency |
| 🏥 | **Health Risk Advisory** | Personalized multilingual health advisories for 12 Delhi wards |
| 🗺️ | **GIS Dashboard** | Interactive India map with 20+ layers (folium, Natural Earth boundaries) |
| 🤖 | **Explainable AI (XAI)** | SHAP-based feature importance with natural language explanations |
| 🎮 | **3D Digital Twin** | Three.js city twin with real-time AQI overlay |
| 💬 | **AI Chat** | LLM-powered conversational interface (Ollama/vLLM) |
| 🚦 | **Decision Engine** | RL-based traffic, squad, and emergency optimization |
| 📱 | **Multi-Channel Delivery** | Mobile, web, SMS, IVR, and public display support |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js 14)                       │
│  Dashboard · Maps (MapLibre/Deck.gl) · 3D Twin · AI Chat         │
│  Analytics · Alerts · Citizen Portal · Admin Panel                 │
└────────────────────┬─────────────────────────────────────────────┘
                     │ REST / GraphQL / WebSocket
┌────────────────────▼─────────────────────────────────────────────┐
│                     API Gateway (FastAPI)                         │
│              Routing · Auth · Rate Limiting · Caching              │
└──────┬──────────────────┬──────────────────┬─────────────────────┘
       │                  │                  │
┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────────────────────┐
│  Ingestion   │   │  Knowledge  │   │    AI Agent Orchestrator     │
│  Pipeline    │   │   Graph     │   │  ┌────────────────────────┐ │
│  CPCB/OpenAQ │   │  NetworkX   │   │  │ AQI Forecast Agent    │ │
│  Sentinel-5P │   │  causalnex  │   │  │ Hyperlocal Forecast   │ │
│  NASA FIRES  │   │             │   │  │ Source Attribution    │ │
│  Open-Meteo  │   │             │   │  │ Enforcement           │ │
│  IMD/Bhuvan  │   │             │   │  │ Health Risk           │ │
│  Citizen     │   │             │   │  │ Burn Detection        │ │
└──────────────┘   └──────────────┘   │  │ City Planning         │ │
                                       │  │ Emergency Response   │ │
                                       │  │ Policy Simulation    │ │
                                       │  │ ... 13 agents       │ │
                                       │  └────────────────────────┘ │
                                       └──────────┬──────────────────┘
                                                  │
                                       ┌──────────▼──────────────────┐
                                       │     Decision Engine (RL)     │
                                       │  Traffic · Squad · Emergency │
                                       └─────────────────────────────┘
```

### Components

| Component | Stack | Description |
|-----------|-------|-------------|
| **Backend** | Python 3.12, FastAPI, Pydantic | Unified API with REST, GraphQL (Strawberry), WebSocket |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS | Dashboard with MapLibre, Deck.gl, ECharts, Three.js |
| **ML Engine** | Python, scikit-learn, PyTorch, XGBoost | Ensemble models, Optuna tuning, SHAP explainability |
| **Agents** | Python, asyncio | 13 specialized AI agents with shared orchestrator |
| **Ingestion** | Python, httpx, STAC | Connectors for CPCB, OpenAQ, Sentinel, NASA, IMD, Bhuvan |
| **Knowledge Graph** | Python, NetworkX, causalnex | Causal DAG and graph-based reasoning |
| **LLM Service** | Python, OpenAI-compatible | Local LLM (Ollama/vLLM) for explainability & chat |
| **Decision Engine** | Python, NumPy, SciPy | RL-based traffic, squad, and emergency optimization |
| **Stream Processing** | Java, Apache Flink | Real-time stream processing (Kafka) |
| **Monitoring** | Prometheus + Grafana | Service metrics, AQI alerts |

---

## AI Modules (Notebooks)

### 1. AQI Prediction System
**`backend/src/ml/notebooks/aqi_prediction.ipynb`**

| Aspect | Detail |
|--------|--------|
| **Purpose** | Predict AQI from pollutant concentrations and meteorological variables |
| **Models** | XGBoost, Random Forest, LSTM, Stacking Ensemble |
| **Features** | 23 engineered features (11 pollutants, 7 meteorological, 5 temporal) |
| **Performance** | ~99% category accuracy, R² > 0.97 on test set |
| **Tuning** | Optuna hyperparameter optimisation (100+ trials) |
| **Explainability** | SHAP analysis with waterfall and summary plots |
| **UI** | Interactive ipywidgets calculator with real-time prediction |

### 2. Hyperlocal Predictive AQI Forecasting Agent
**`backend/src/hyperlocal_forecast_agent/notebooks/hyperlocal_forecast_agent.ipynb`**

| Aspect | Detail |
|--------|--------|
| **Purpose** | Production-grade hyperlocal AQI forecasting for Delhi NCR |
| **Data** | Real-time OpenAQ + ERA5 reanalysis (Open-Meteo), with fallback |
| **Models** | RF, XGBoost, LightGBM, CatBoost, LSTM, GRU, Temporal Fusion Transformer |
| **Features** | 30+ dynamic features (lag, rolling windows, cyclical encoding) |
| **Validation** | Walk-forward time-series validation |
| **Explainability** | Comprehensive SHAP analysis |
| **UI** | Interactive widget calculator |

### 3. Enforcement Intelligence & Prioritisation Agent
**`backend/src/enforcement_intelligence_agent/notebooks/enforcement_intelligence_agent.ipynb`**

| Aspect | Detail |
|--------|--------|
| **Purpose** | Satellite-driven hotspot detection, source attribution, and enforcement ranking |
| **Data** | Sentinel-5P TROPOMI, NASA FIRES MODIS/VIIRS, emission inventories |
| **Models** | DBSCAN clustering, Random Forest classifier, probabilistic fingerprint matching |
| **Sources** | 11 source profiles (industrial, crop burning, traffic, construction, etc.) |
| **Performance** | ~94% source attribution accuracy, 28 hotspots detected |
| **GIS** | Interactive India map (folium) with 20+ layers, 3 basemaps |
| **Explainability** | SHAP with dropdown-driven XAI panel, evidence chains |
| **UI** | Professional GIS dashboard with search, measurement, draw tools |

### 4. Citizen Health Risk Advisory System
**`backend/src/health_risk_advisory/notebooks/health_risk_advisory.ipynb`**

| Aspect | Detail |
|--------|--------|
| **Purpose** | Transform AQI forecasts into personalized health advisories |
| **Wards** | 12 Delhi wards with demographic vulnerability profiling |
| **Risk Model** | `HealthRisk = f(AQI, Pollutant, Vulnerability, Duration, Seasonality)` |
| **Languages** | English, Hindi, Kannada, Tamil |
| **Channels** | Mobile (push), SMS, IVR, public displays, web portal |
| **Integration** | Consumes from AQI Prediction, Hyperlocal Forecast, Enforcement modules |
| **UI** | Environmental Intelligence Command Centre dashboard |

---

## Project Structure

```
vayu-drishti/
├── backend/                          # Unified Python backend
│   ├── main.py                       # Entry point
│   ├── requirements.txt
│   ├── src/
│   │   ├── api/                      # REST, GraphQL, WebSocket endpoints
│   │   ├── agents/                   # Integrated agent implementations
│   │   │   ├── aqi_forecast/
│   │   │   ├── burn_detection/
│   │   │   ├── orchestrator/
│   │   │   └── source_attribution/
│   │   ├── ml/                       # ML training, inference, models
│   │   │   ├── notebooks/            # Primary ML notebooks
│   │   │   ├── inference/            # Production inference pipeline
│   │   │   ├── training/             # Model training scripts
│   │   │   ├── models/               # Model definitions
│   │   │   ├── explainability/       # SHAP / XAI utilities
│   │   │   └── artifacts/            # Saved model artifacts
│   │   ├── ingestion/                # Data ingestion connectors
│   │   ├── forecasting/              # Forecasting service
│   │   ├── knowledge_graph/          # Graph builder & reasoning
│   │   ├── decision_engine/          # RL optimization
│   │   ├── llm_service/              # LLM integration
│   │   ├── infrastructure/           # DB, cache, event bus
│   │   ├── config.py                 # App configuration
│   │   └── app.py                    # FastAPI application factory
│   ├── enforcement_intelligence_agent/
│   │   └── notebooks/                # Enforcement intelligence notebook
│   ├── health_risk_advisory/
│   │   └── notebooks/                # Health risk advisory notebook
│   └── hyperlocal_forecast_agent/
│       └── notebooks/                # Hyperlocal forecast notebook
├── agents/                           # Standalone AI agent microservices
│   ├── orchestrator/                 # Agent orchestrator
│   ├── agent-aqi-forecast/           # AQI forecasting
│   ├── agent-burn-detection/         # Fire/burn detection
│   ├── agent-source-attribution/     # Source attribution
│   ├── agent-enforcement/            # Enforcement intelligence
│   ├── agent-health-risk/            # Health risk advisory
│   ├── agent-hyperlocal-aqi/         # Hyperlocal forecasting
│   ├── agent-traffic/                # Traffic analysis
│   ├── agent-city-planning/          # Urban planning
│   ├── agent-emergency/              # Emergency response
│   ├── agent-citizen-complaint/      # Citizen complaints
│   ├── agent-explainability/         # XAI agent
│   ├── agent-policy-simulation/      # Policy simulation
│   ├── agent-change-detection/       # Land use change
│   └── agent-resource-allocation/    # Resource allocation
├── frontend/                         # Next.js dashboard
│   └── src/
│       ├── app/                      # Pages (dashboard, admin, chat, etc.)
│       └── components/               # React components
├── api-gateway/                      # API gateway service
├── data/                             # Runtime data mount points
├── decision-engine/                  # Standalone decision engine
├── feature-store/                    # Feature store
├── ingestion/                        # Standalone ingestion service
├── knowledge-graph/                  # Standalone graph builder
├── llm-service/                      # Standalone LLM server
├── stream-processing/                # Apache Flink streams
├── mobile/                           # React Native app (scaffold)
├── evaluation/                       # Model evaluation scripts
├── docs/                             # Additional documentation
├── infra/                            # Infrastructure config
├── Makefile                          # Build automation
├── README.md                         # This file
├── CHANGELOG.md                      # Version history
├── CONTRIBUTING.md                   # Contribution guide
├── SECURITY.md                       # Security policy
├── LICENSE                           # MIT license
└── .env.example                      # Environment template
```

---

## Technologies Used

| Category | Technologies |
|----------|-------------|
| **Languages** | Python 3.12, TypeScript, Java (Flink) |
| **Backend** | FastAPI, Uvicorn, Strawberry GraphQL, Pydantic |
| **Frontend** | Next.js 14, React 18, Tailwind CSS, MapLibre GL, Deck.gl, Three.js, ECharts |
| **ML/AI** | scikit-learn, XGBoost, LightGBM, CatBoost, PyTorch, Optuna, SHAP |
| **Data** | NumPy, Pandas, GeoPandas, rasterio, xarray |
| **Visualization** | Matplotlib, Seaborn, Plotly, Folium |
| **LLM** | Ollama, vLLM, LangChain, OpenAI-compatible API |
| **Knowledge Graph** | NetworkX, causalnex |
| **Decision Engine** | NumPy, SciPy (RL-based optimization) |
| **Monitoring** | Prometheus, Grafana |
| **Stream Processing** | Apache Flink, Apache Kafka |
| **DevOps** | Docker, Docker Compose, Make |
| **Mobile** | React Native (scaffold) |

---

## Installation

### Prerequisites

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **Node.js 20+** ([Download](https://nodejs.org/))
- **Git**

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/HarshitaVscode/ET-Hackathon.git
cd ET-Hackathon

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys (all optional for local development)

# 3. Install all dependencies
make install

# Or step-by-step:
# Backend
pip install -e backend/
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### Running

Open **two terminals**:

**Terminal 1 — Backend:**
```bash
make backend
# FastAPI running at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Terminal 2 — Frontend:**
```bash
make frontend
# Next.js running at http://localhost:3000
```

### Running Notebooks

The four primary notebooks are in `backend/src/`:

```bash
# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Launch Jupyter
jupyter notebook
# Or JupyterLab
jupyter lab
```

Navigate to the notebook location and execute cells in order.

---

## Machine Learning Models

| Model | Application | Performance |
|-------|-------------|-------------|
| **XGBoost Regressor** | AQI Prediction | R² > 0.97, MAPE ~8.5% |
| **Random Forest Regressor** | AQI Prediction | R² > 0.95, MAPE ~10.2% |
| **LSTM Neural Network** | AQI Prediction | R² > 0.93, MAPE ~12.1% |
| **Stacking Ensemble** | AQI Prediction | R² > 0.98, MAPE ~7.8% (best) |
| **XGBoost (Hyperlocal)** | Hyperlocal Forecast | 30+ features, walk-forward validated |
| **LightGBM** | Hyperlocal Forecast | 7-model comparison |
| **CatBoost** | Hyperlocal Forecast | Categorical feature handling |
| **GRU / TFT** | Hyperlocal Forecast | Deep learning baselines |
| **Random Forest Classifier** | Source Attribution | ~94% accuracy (11 source types) |
| **DBSCAN** | Hotspot Detection | 28 hotspots identified |
| **Probabilistic Fingerprint** | Source Attribution | 11 emission source profiles |
| **Health Risk Model** | Risk Advisory | 5-level risk classification |

---

## Data Sources

| Source | Data | Coverage | Refresh |
|--------|------|----------|---------|
| **CPCB** | Hourly AQI, pollutant concentrations | Delhi NCR | Hourly |
| **OpenAQ** | Aggregated air quality data | Global | Real-time |
| **Sentinel-5P TROPOMI** | NO₂, CO, SO₂, HCHO, Aerosol Index | Delhi NCR | Daily |
| **NASA FIRES (MODIS/VIIRS)** | Active fire / thermal anomalies | India | Daily |
| **Open-Meteo ERA5** | Meteorological reanalysis | Delhi NCR | Hourly |
| **IMD** | Weather observations | India | Hourly |
| **Emission Inventories** | Industrial, transport, residential sources | Delhi NCR | Annual |

---

## Dashboard Overview

The frontend dashboard (`frontend/src/app/`) includes:

| Route | Feature |
|-------|---------|
| `/dashboard` | Main command centre with AQI overview, maps, stats |
| `/forecast-dashboard` | Hyperlocal AQI forecasting visualizations |
| `/analytics` | Trend analysis and comparative charts |
| `/map` | Interactive GIS map with pollutant overlays |
| `/hyperlocal` | Street-level AQI resolution |
| `/emergency` | Emergency response coordination |
| `/citizen` | Citizen portal with health advisories |
| `/admin` | System administration panel |
| `/chat` | AI-powered conversational interface |
| `/twin3d` | 3D digital city twin |
| `/reports` | Generated reports and exports |
| `/login` | Authentication |

---

## Results & Achievements

| Metric | Value |
|--------|-------|
| **AQI Category Accuracy** | ~99% (Stacking Ensemble) |
| **AQI Regression R²** | > 0.98 |
| **Hotspots Detected** | 28 across Delhi NCR |
| **Source Profiles** | 11 distinct emission types |
| **Attribution Accuracy** | ~94% |
| **Enforcement Actions** | 28 recommendations generated |
| **Delhi Wards Modelled** | 12 wards with demographic profiles |
| **Risk Levels** | 5-level (Minimal → Critical) |
| **Languages Supported** | 4 (English, Hindi, Kannada, Tamil) |
| **Delivery Channels** | 5 (Mobile, SMS, IVR, Web, Public Displays) |
| **Model Architectures Compared** | 7 (Hyperlocal Forecast benchmark) |

---

## Explainable AI

All models include SHAP (SHapley Additive exPlanations) analysis:

- **Global Feature Importance** — Which pollutants and meteorological factors drive AQI
- **Local Explanations** — Per-prediction SHAP waterfall plots
- **Partial Dependence** — How individual features affect predictions
- **Source Attribution** — Probabilistic fingerprint matching with evidence chains
- **Health Advisory Reasoning** — Transparent risk calculation logic

---

## Future Scope

- **Real-time API integration** with live CPCB/OpenAQ streams
- **Deep learning enhancements** (Transformers, Graph Neural Networks for spatial dependencies)
- **Causal inference** for policy intervention simulation
- **Multi-city deployment** (Mumbai, Bengaluru, Chennai, Kolkata)
- **Public dashboard** with open data API
- **Mobile app** (React Native scaffold ready)
- **Integration with smart city command centres**
- **Expanded language support** (all 22 scheduled Indian languages)

---

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

Key points:
- Fork the repository and create a branch from `main`
- Use [Conventional Commits](https://www.conventionalcommits.org/)
- Run `make test` and `make lint` before submitting PRs
- One feature/fix per pull request

---

## License

Distributed under the [MIT License](LICENSE). See `LICENSE` for more information.

---

## Acknowledgements

- **ET Hackathon** — Platform and opportunity
- **CPCB** — Air quality data access
- **OpenAQ** — Global air quality data aggregation
- **ESA Copernicus** — Sentinel-5P satellite data
- **NASA FIRES** — Fire detection data
- **Open-Meteo** — Meteorological reanalysis
- **Natural Earth** — GIS boundary data
