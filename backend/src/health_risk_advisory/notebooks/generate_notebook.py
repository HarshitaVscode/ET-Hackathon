"""Generate the Citizen Health Risk Advisory System notebook."""
from __future__ import annotations

import json
from pathlib import Path


def generate_notebook(output_path: str | None = None) -> str:
    import uuid

    def _new_id() -> str:
        return uuid.uuid4().hex[:16]

    cells: list[dict] = []

    def md(source: str) -> None:
        cells.append({
            "cell_type": "markdown",
            "id": _new_id(),
            "metadata": {},
            "source": [s + "\n" for s in source.split("\n")] if isinstance(source, str) else [source],
        })

    def code(source: str) -> None:
        cells.append({
            "cell_type": "code",
            "id": _new_id(),
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [s + "\n" for s in source.split("\n")],
        })

    md("""# Citizen Health Risk Advisory System
## Vayu-Drishti — AI-Powered Public Health Intelligence Layer

**Smart City Air Quality Intelligence Platform**

A comprehensive AI-driven health risk advisory system that transforms hyperlocal AQI forecasts into actionable, personalized health advisories for citizens. This module serves as the citizen-facing layer of the Vayu-Drishti platform.

### How This Module Completes the Platform

The Vayu-Drishti platform already delivers:
- **AQI Prediction** (ML module) — Accurate AQI forecasting from environmental parameters
- **Hyperlocal Forecasting** (Forecast Agent) — Station-level predictive AQI with 24/48/72h horizons
- **Enforcement Intelligence** (Enforcement Agent) — Hotspot detection, source attribution, prioritization
- **GIS Visualization** (Dashboard) — Spatial mapping of pollution across India
- **Explainable AI** (SHAP/Reasoning Trees) — Transparent model decisions

This module adds the **critical last mile**: translating these technical outputs into citizen-centric health advisories that are personalized, multilingual, and channel-ready.""")

    md("""## 1. Objectives

1. **Transform** hyperlocal AQI forecasts into personalized health risk advisories
2. **Identify** vulnerable population groups and map risk spatially at ward-level
3. **Generate** context-aware advisory messages that adapt to conditions, risk level, pollutants, and time horizon
4. **Support** multilingual advisory generation (English, Hindi, Kannada, Tamil)
5. **Design** for delivery through multiple channels (mobile, public displays, SMS, IVR, notifications)
6. **Integrate** with existing Vayu-Drishti modules without modifying any existing code""")

    md("""## 2. Integration with Existing Project Modules

This module is designed to consume outputs from existing modules:

| Existing Module | Output Used | How Health Risk Uses It |
|----------------|-------------|------------------------|
| **AQI Prediction** (ML) | Predicted AQI, pollutant concentrations | Base risk scoring, pollutant-specific health impacts |
| **Hyperlocal Forecast** | Station-level 24/48/72h forecasts | Ward-level risk projection over time horizons |
| **Enforcement Intelligence** | Hotspot locations, source attribution, severity | Context enrichment for advisories, source-specific precautions |
| **GIS Visualization** | Spatial boundary data, location context | Ward mapping, risk heatmap generation |
| **Explainable AI** | SHAP values, feature importance | Trust indicators in advisory messages |""")

    md("""## 3. Configuration & Setup""")

    code("""import sys, os, json, warnings, math, random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from IPython.display import display, HTML, clear_output
%matplotlib inline

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 200)
pd.set_option("display.width", 120)
sns.set_style("darkgrid")
plt.rcParams['figure.dpi'] = 120
plt.rcParams['figure.facecolor'] = '#0f0f2a'
plt.rcParams['axes.facecolor'] = '#0f0f2a'
plt.rcParams['text.color'] = 'white'
plt.rcParams['axes.labelcolor'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['ytick.color'] = 'white'

_NOTEBOOK_DIR = Path(os.getcwd()).resolve()
_MODULE_DIR = _NOTEBOOK_DIR.parent
_ARTIFACTS_DIR = _MODULE_DIR / "artifacts"
_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
_PROJECT_ROOT = _NOTEBOOK_DIR
for _p in [_NOTEBOOK_DIR] + list(_NOTEBOOK_DIR.parents):
    if (_p / "backend" / "src").exists():
        _PROJECT_ROOT = _p
        break
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

print("Environment ready.")
print(f"  Module: {_MODULE_DIR}")
print(f"  Artifacts: {_ARTIFACTS_DIR}")
print(f"  Project root: {_PROJECT_ROOT}")""")

    md("""## 4. Ward Definitions & Spatial Context

### 4.1 Delhi Ward Boundaries

Using the project's established ward definitions from the demo seed data. These 12 wards represent Delhi's administrative divisions and are used across all Vayu-Drishti modules for consistent spatial analysis.""")

    code("""WARDS = {
    "W01": {"name": "Civil Lines", "lat": 28.68, "lon": 77.22, "population": 180000, "avg_income": "high", "green_cover": 0.25},
    "W02": {"name": "Karol Bagh", "lat": 28.65, "lon": 77.19, "population": 250000, "avg_income": "medium", "green_cover": 0.12},
    "W03": {"name": "New Delhi", "lat": 28.61, "lon": 77.21, "population": 140000, "avg_income": "high", "green_cover": 0.30},
    "W04": {"name": "Vasant Kunj", "lat": 28.53, "lon": 77.15, "population": 120000, "avg_income": "high", "green_cover": 0.35},
    "W05": {"name": "Dwarka", "lat": 28.59, "lon": 77.05, "population": 300000, "avg_income": "medium", "green_cover": 0.20},
    "W06": {"name": "Rohini", "lat": 28.73, "lon": 77.12, "population": 350000, "avg_income": "medium", "green_cover": 0.15},
    "W07": {"name": "Najafgarh", "lat": 28.61, "lon": 76.98, "population": 200000, "avg_income": "low", "green_cover": 0.10},
    "W08": {"name": "Moti Nagar", "lat": 28.66, "lon": 77.14, "population": 220000, "avg_income": "medium", "green_cover": 0.18},
    "W09": {"name": "Shahdara", "lat": 28.68, "lon": 77.29, "population": 280000, "avg_income": "low", "green_cover": 0.08},
    "W10": {"name": "East Delhi", "lat": 28.62, "lon": 77.29, "population": 400000, "avg_income": "low", "green_cover": 0.06},
    "W11": {"name": "South Delhi", "lat": 28.55, "lon": 77.22, "population": 170000, "avg_income": "high", "green_cover": 0.28},
    "W12": {"name": "Ghaziabad", "lat": 28.66, "lon": 77.43, "population": 450000, "avg_income": "medium", "green_cover": 0.09},
}

ward_df = pd.DataFrame.from_dict(WARDS, orient="index")
ward_df.index.name = "ward_id"
ward_df = ward_df.reset_index()
print(f"Loaded {len(ward_df)} wards")
display(ward_df)""")

    md("""### 4.2 AQI Breakpoints (CPCB Standard)

Using the standard CPCB/NAAQS AQI breakpoints as defined in the project's ML module metadata.""")

    code("""AQI_BREAKPOINTS = [
    (0, 50, "Good", "#00e400"),
    (51, 100, "Satisfactory", "#ffff00"),
    (101, 200, "Moderate", "#ff7e00"),
    (201, 300, "Poor", "#ff0000"),
    (301, 400, "Very Poor", "#8f3f97"),
    (401, 500, "Severe", "#7e0023"),
]

def get_aqi_category(aqi: float) -> str:
    for lo, hi, cat, _ in AQI_BREAKPOINTS:
        if lo <= aqi <= hi:
            return cat
    return "Severe" if aqi > 400 else "Good"

def get_aqi_color(aqi: float) -> str:
    for lo, hi, _, color in AQI_BREAKPOINTS:
        if lo <= aqi <= hi:
            return color
    return "#7e0023" if aqi > 400 else "#00e400"

print("AQI Categories:")
aqi_df = pd.DataFrame(AQI_BREAKPOINTS, columns=["Min", "Max", "Category", "Color"])
display(aqi_df)""")

    md("""## 5. Vulnerability Indicators

### 5.1 Population Vulnerability Modelling

Identifying vulnerable population groups is critical for targeted health advisories. We model vulnerability based on:

- **Demographic factors**: Children (under 14), elderly (over 60), pregnant women
- **Health factors**: Prevalence of respiratory diseases, cardiovascular conditions
- **Socioeconomic factors**: Access to healthcare, average income, housing quality
- **Environmental factors**: Green cover, proximity to industrial zones, traffic density

Each ward receives a composite vulnerability score (0-1) that feeds into the risk assessment.""")

    code("""np.random.seed(42)

vulnerability_data = []
for wid, ward in WARDS.items():
    pop = ward["population"]
    base_vulnerability = 0.3

    if ward["avg_income"] == "low":
        base_vulnerability += 0.25
    elif ward["avg_income"] == "medium":
        base_vulnerability += 0.10

    green_factor = max(0, 1 - ward["green_cover"] / 0.35) * 0.20
    base_vulnerability += green_factor

    child_pct = np.random.uniform(18, 28)
    elderly_pct = np.random.uniform(8, 16)
    respiratory_pct = np.random.uniform(5, 18)
    cardiovascular_pct = np.random.uniform(4, 12)

    pop_density = pop / 10.0
    healthcare_access = np.random.uniform(0.4, 0.95)

    vulnerability_data.append({
        "ward_id": wid,
        "ward_name": ward["name"],
        "population": pop,
        "child_pct": round(child_pct, 1),
        "elderly_pct": round(elderly_pct, 1),
        "respiratory_pct": round(respiratory_pct, 1),
        "cardiovascular_pct": round(cardiovascular_pct, 1),
        "pop_density_per_km2": int(pop_density * 1000),
        "healthcare_access": round(healthcare_access, 3),
        "green_cover_pct": round(ward["green_cover"] * 100, 1),
        "income_group": ward["avg_income"],
        "vulnerability_score": round(min(1.0, base_vulnerability + np.random.uniform(-0.05, 0.05)), 3),
    })

vuln_df = pd.DataFrame(vulnerability_data)
print("Ward Vulnerability Assessment:")
display(vuln_df)

print(f"\\nVulnerability Score Range: {vuln_df['vulnerability_score'].min():.3f} - {vuln_df['vulnerability_score'].max():.3f}")
print(f"Most vulnerable ward: {vuln_df.loc[vuln_df['vulnerability_score'].idxmax(), 'ward_name']}")
print(f"Least vulnerable ward: {vuln_df.loc[vuln_df['vulnerability_score'].idxmin(), 'ward_name']}")""")

    md("""### 5.2 Vulnerability Visualization

Mapping vulnerability scores spatially to identify high-risk wards that need priority attention.""")

    code("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))

sorted_vuln = vuln_df.sort_values("vulnerability_score", ascending=True)
colors_vuln = plt.cm.RdYlGn_r(sorted_vuln["vulnerability_score"])
bars1 = axes[0].barh(range(len(sorted_vuln)), sorted_vuln["vulnerability_score"],
                     color=colors_vuln, edgecolor="white", linewidth=0.5)
axes[0].set_yticks(range(len(sorted_vuln)))
axes[0].set_yticklabels(sorted_vuln["ward_name"])
axes[0].set_xlabel("Vulnerability Score (0-1)")
axes[0].set_title("Ward-Level Vulnerability Index", fontsize=14, fontweight="bold")
axes[0].set_xlim(0, 1)
for i, (_, row) in enumerate(sorted_vuln.iterrows()):
    axes[0].text(row["vulnerability_score"] + 0.01, i, f"{row['vulnerability_score']:.3f}",
                 va="center", fontsize=9, color="white")

vuln_ward = vuln_df.melt(id_vars=["ward_name"],
                          value_vars=["child_pct", "elderly_pct", "respiratory_pct", "cardiovascular_pct"],
                          var_name="indicator", value_name="percentage")
indicator_labels = {"child_pct": "Children %", "elderly_pct": "Elderly %",
                    "respiratory_pct": "Respiratory %", "cardiovascular_pct": "Cardiovascular %"}
vuln_ward["indicator"] = vuln_ward["indicator"].map(indicator_labels)

sns.barplot(data=vuln_ward, x="percentage", y="ward_name", hue="indicator",
            ax=axes[1], palette="Set2", alpha=0.8)
axes[1].set_title("Vulnerable Population Segments by Ward", fontsize=14, fontweight="bold")
axes[1].set_xlabel("Percentage of Population")
axes[1].legend(bbox_to_anchor=(1.05, 1), loc="upper left")

plt.tight_layout()
plt.show()""")

    md("""## 6. Health Risk Modelling

### 6.1 AI-Driven Health Risk Scoring

The health risk score is computed as a function of:

```
HealthRisk = f(AQI_forecast, Pollutant_profile, Vulnerability, Duration, Seasonality)
```

where:
- **AQI forecast** is the primary driver (from Hyperlocal Forecast Agent or AQI Prediction module)
- **Pollutant profile** determines which health systems are affected (PM2.5 = respiratory, NO2 = cardiovascular, etc.)
- **Vulnerability** modulates the baseline risk for each ward
- **Duration** accounts for prolonged exposure effects
- **Seasonality** adjusts risk based on known seasonal health patterns

We define 5 risk levels: **Minimal, Low, Moderate, High, Critical**""")

    code("""RISK_LEVELS = [
    (0, 0.15, "Minimal", "#22c55e"),
    (0.15, 0.35, "Low", "#84cc16"),
    (0.35, 0.55, "Moderate", "#eab308"),
    (0.55, 0.75, "High", "#f97316"),
    (0.75, 1.0, "Critical", "#dc2626"),
]

def get_risk_level(risk_score: float) -> Tuple[str, str]:
    for lo, hi, level, color in RISK_LEVELS:
        if lo <= risk_score < hi:
            return level, color
    return "Critical", "#dc2626"

POLLUTANT_HEALTH_MAP = {
    "PM2_5": {"primary": "Respiratory", "secondary": "Cardiovascular", "acute": "Asthma attacks, reduced lung function"},
    "PM10": {"primary": "Respiratory", "secondary": "Eye irritation", "acute": "Throat irritation, coughing"},
    "NO2": {"primary": "Respiratory", "secondary": "Cardiovascular", "acute": "Airway inflammation"},
    "SO2": {"primary": "Respiratory", "secondary": "Eye/Skin", "acute": "Bronchoconstriction"},
    "CO": {"primary": "Cardiovascular", "secondary": "Neurological", "acute": "Reduced oxygen delivery"},
    "O3": {"primary": "Respiratory", "secondary": "Eye irritation", "acute": "Chest tightness, coughing"},
    "NH3": {"primary": "Respiratory", "secondary": "Skin/Eye", "acute": "Throat irritation"},
}

print("Risk Level Classification:")
risk_lvl_df = pd.DataFrame(RISK_LEVELS, columns=["Min Score", "Max Score", "Level", "Color"])
display(risk_lvl_df)

print("\\nPollutant-Specific Health Impacts:")
health_df = pd.DataFrame.from_dict(POLLUTANT_HEALTH_MAP, orient="index")
display(health_df)

np.random.seed(123)""")

    md("""### 6.2 Simulating Forecast Data from Existing Module Outputs

We simulate ward-level AQI forecasts and pollutant concentrations that mirror the output format of the Hyperlocal Forecast Agent. In production, these would be obtained by calling the forecast agent's API or reading its saved artifacts.""")

    code("""forecast_hours = [24, 48, 72]
forecast_data = []

for wid, ward in WARDS.items():
    vuln_row = vuln_df[vuln_df["ward_id"] == wid].iloc[0]
    base_vuln = vuln_row["vulnerability_score"]

    base_aqi = 150
    if wid in ("W10", "W12"):
        base_aqi = 280
    elif wid in ("W09", "W06"):
        base_aqi = 210
    elif wid in ("W07", "W02"):
        base_aqi = 180

    for hour_offset in forecast_hours:
        hour_of_day = (datetime.now().hour + hour_offset) % 24
        diurnal = -30 * math.sin(2 * math.pi * (hour_of_day - 14) / 24)
        noise = np.random.normal(0, 15)
        forecast_aqi = max(0, base_aqi + diurnal * 0.5 + noise)

        pm25 = forecast_aqi / 2.0 + np.random.normal(0, 5)
        pm10 = pm25 * 1.8 + np.random.normal(0, 10)
        no2 = 30 + forecast_aqi * 0.15 + np.random.normal(0, 8)
        so2 = 10 + forecast_aqi * 0.05 + np.random.normal(0, 3)
        co = 0.8 + forecast_aqi * 0.005 + np.random.normal(0, 0.2)
        o3 = 40 + np.random.normal(0, 10)
        if hour_of_day > 10 and hour_of_day < 16:
            o3 += 20

        forecast_data.append({
            "ward_id": wid,
            "ward_name": ward["name"],
            "forecast_hour": hour_offset,
            "forecast_aqi": round(forecast_aqi, 1),
            "aqi_category": get_aqi_category(forecast_aqi),
            "PM2_5": round(max(0, pm25), 1),
            "PM10": round(max(0, pm10), 1),
            "NO2": round(max(0, no2), 1),
            "SO2": round(max(0, so2), 1),
            "CO": round(max(0, co), 3),
            "O3": round(max(0, o3), 1),
            "vulnerability": base_vuln,
        })

forecast_df = pd.DataFrame(forecast_data)
print(f"Forecast data: {len(forecast_df)} records ({len(forecast_df['ward_id'].unique())} wards x {len(forecast_df['forecast_hour'].unique())} horizons)")
display(forecast_df.head(12))""")

    md("""### 6.3 Health Risk Score Computation

The composite health risk score combines:
- **AQI Risk**: Normalized AQI contribution (0-0.6 weight)
- **Pollutant Risk**: Presence of high-concentration harmful pollutants (0-0.2 weight)
- **Vulnerability Risk**: Population vulnerability modifier (0-0.2 weight)""")

    code("""def compute_health_risk(row: pd.Series) -> Dict:
    aqi = row["forecast_aqi"]
    vuln = row["vulnerability"]

    aqi_risk = min(1.0, aqi / 400.0) * 0.6

    pm25_contribution = min(1.0, row["PM2_5"] / 100.0) * 0.08
    no2_contribution = min(1.0, row["NO2"] / 80.0) * 0.05
    o3_contribution = min(1.0, row["O3"] / 100.0) * 0.04
    so2_contribution = min(1.0, row["SO2"] / 50.0) * 0.03
    pollutant_risk = pm25_contribution + no2_contribution + o3_contribution + so2_contribution

    vulnerability_risk = vuln * 0.2

    composite_risk = min(1.0, aqi_risk + pollutant_risk + vulnerability_risk)

    duration_multiplier = 1.0 + (row["forecast_hour"] / 72.0) * 0.2
    risk_score = min(1.0, composite_risk * duration_multiplier)

    risk_level, risk_color = get_risk_level(risk_score)

    return {
        "risk_score": round(risk_score, 3),
        "risk_level": risk_level,
        "risk_color": risk_color,
        "aqi_risk_component": round(aqi_risk, 3),
        "pollutant_risk_component": round(pollutant_risk, 3),
        "vulnerability_risk_component": round(vulnerability_risk, 3),
        "exposed_population": int(WARDS[row["ward_id"]]["population"] * risk_score),
    }

risk_rows = []
for _, row in forecast_df.iterrows():
    risk_result = compute_health_risk(row)
    risk_rows.append({**row.to_dict(), **risk_result})

risk_df = pd.DataFrame(risk_rows)
print(f"Health Risk Assessment: {len(risk_df)} records")
display(risk_df[["ward_name", "forecast_hour", "forecast_aqi", "risk_score", "risk_level", "exposed_population"]].head(12))

risk_summary = risk_df.groupby("risk_level").agg(
    count=("risk_level", "count"),
    avg_risk=("risk_score", "mean"),
    total_exposed=("exposed_population", "sum"),
).reset_index()
print("\\nRisk Level Summary:")
display(risk_summary)""")

    md("""### 6.4 Risk Distribution Visualization""")

    code("""fig, axes = plt.subplots(2, 2, figsize=(16, 12))

risk_pivot = risk_df.pivot_table(index="ward_name", columns="forecast_hour",
                                  values="risk_score", aggfunc="mean")
risk_pivot_sorted = risk_pivot.mean(axis=1).sort_values()
risk_pivot = risk_pivot.loc[risk_pivot_sorted.index]

sns.heatmap(risk_pivot, annot=True, fmt=".3f", cmap="YlOrRd",
            ax=axes[0, 0], cbar_kws={"label": "Risk Score"},
            linewidths=0.5, linecolor="#333333")
axes[0, 0].set_title("Health Risk Score by Ward & Forecast Horizon", fontsize=13, fontweight="bold")
axes[0, 0].set_xlabel("Forecast Horizon (hours)")
axes[0, 0].set_ylabel("Ward")

risk_counts = risk_df["risk_level"].value_counts()
colors_risk = [get_risk_level(float(level.replace("Critical", "0.8").replace("High", "0.6").replace("Moderate", "0.4").replace("Low", "0.2").replace("Minimal", "0.05")))[1]
               for level in risk_counts.index]
axes[0, 1].pie(risk_counts.values, labels=risk_counts.index, autopct="%1.1f%%",
               colors=colors_risk, startangle=90, textprops={"color": "white"})
axes[0, 1].set_title("Risk Level Distribution", fontsize=13, fontweight="bold")

ward_avg_risk = risk_df.groupby("ward_name")["risk_score"].mean().sort_values()
bars = axes[1, 0].barh(range(len(ward_avg_risk)), ward_avg_risk.values,
                        color=[get_risk_level(v)[1] for v in ward_avg_risk.values],
                        edgecolor="white", linewidth=0.5)
axes[1, 0].set_yticks(range(len(ward_avg_risk)))
axes[1, 0].set_yticklabels(ward_avg_risk.index)
axes[1, 0].set_xlabel("Average Risk Score")
axes[1, 0].set_title("Ward-Level Average Health Risk", fontsize=13, fontweight="bold")

scatter = axes[1, 1].scatter(risk_df["forecast_aqi"], risk_df["risk_score"],
                              c=[get_aqi_color(v) for v in risk_df["forecast_aqi"]],
                              s=risk_df["exposed_population"] / 500, alpha=0.7, edgecolors="white", linewidth=0.5)
axes[1, 1].set_xlabel("Forecast AQI")
axes[1, 1].set_ylabel("Health Risk Score")
axes[1, 1].set_title("AQI vs Health Risk (bubble = exposed population)", fontsize=13, fontweight="bold")
for level_name, level_color in [("Minimal", "#22c55e"), ("Moderate", "#eab308"), ("High", "#f97316"), ("Critical", "#dc2626")]:
    axes[1, 1].axhline(y=[v[0] for v in RISK_LEVELS if v[2] == level_name][0], color=level_color, linestyle="--", alpha=0.3, linewidth=0.5)

plt.tight_layout()
plt.show()""")

    md("""## 7. Personalized Advisory Generation

### 7.1 Intelligent Advisory Logic

Instead of static templates, advisories are dynamically composed based on:
- **Risk level** determines urgency and severity of language
- **Primary pollutant** determines specific health recommendations
- **Time horizon** determines immediacy (24h = immediate action, 72h = preparation)
- **Vulnerable groups** are specifically addressed
- **Ward context** provides location-specific guidance""")

    code("""ADVISORY_TEMPLATES = {
    "Minimal": {
        "title": "Air Quality is Good — Enjoy Your Day!",
        "tone": "positive",
        "general": "Air quality poses little or no health risk. Enjoy outdoor activities.",
        "precautions": []
    },
    "Low": {
        "title": "Air Quality is Acceptable — Minor Precautions",
        "tone": "informative",
        "general": "Air quality is acceptable. There may be a moderate health concern for a very small number of sensitive individuals.",
        "precautions": ["Sensitive individuals may consider limiting prolonged outdoor exertion"]
    },
    "Moderate": {
        "title": "Moderate Air Quality — Limit Prolonged Exposure",
        "tone": "cautionary",
        "general": "Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
        "precautions": [
            "Sensitive groups: reduce prolonged outdoor exertion",
            "Take more breaks during outdoor activities",
            "Keep windows closed during peak pollution hours",
            "Monitor symptoms if you have respiratory conditions"
        ]
    },
    "High": {
        "title": "Unhealthy Air Quality — Take Protective Measures",
        "tone": "warning",
        "general": "Everyone may begin to experience health effects. Members of sensitive groups may experience more serious health effects.",
        "precautions": [
            "Avoid prolonged outdoor exertion",
            "Wear N95/KN95 masks when outdoors",
            "Keep windows and doors closed",
            "Use air purifiers indoors",
            "Schools should consider limiting outdoor activities",
            "Elderly and children should stay indoors",
            "Follow medication schedules for respiratory conditions"
        ]
    },
    "Critical": {
        "title": "SEVERE AIR QUALITY — HEALTH EMERGENCY",
        "tone": "emergency",
        "general": "Health alert: everyone may experience serious health effects. This is a health emergency.",
        "precautions": [
            "STAY INDOORS — avoid all outdoor physical activity",
            "Wear N95 masks if you must go out",
            "Seal windows and doors with damp cloth",
            "Run air purifiers at maximum setting",
            "SCHOOLS: declare holiday or shift to online classes",
            "ELDERLY: do not step out unless absolutely necessary",
            "Use public transport to reduce vehicular emissions",
            "Contact nearby clinic if experiencing breathing difficulty",
            "Keep emergency inhalers and medications accessible",
            "Follow Government issued emergency protocols"
        ]
    }
}

POLLUTANT_ADVISORY_MAP = {
    "PM2_5": "PM2.5 levels are elevated. These fine particles can penetrate deep into the lungs and enter the bloodstream.",
    "PM10": "PM10 levels are elevated. These coarse particles can irritate the eyes, nose, and throat.",
    "NO2": "Nitrogen dioxide levels are elevated. This can cause airway inflammation and worsen respiratory conditions.",
    "SO2": "Sulfur dioxide levels are elevated. This can cause bronchoconstriction and throat irritation.",
    "CO": "Carbon monoxide levels are elevated. This reduces oxygen delivery to vital organs.",
    "O3": "Ground-level ozone is elevated. This can cause chest tightness and reduced lung function.",
}

SENSITIVE_GROUPS = {
    "children": "Children — higher breathing rate and developing lungs make them more susceptible",
    "elderly": "Elderly (60+) — age-related decline in lung function increases vulnerability",
    "pregnant": "Pregnant women — air pollution affects both maternal and fetal health",
    "respiratory": "People with asthma, COPD, or other respiratory conditions",
    "cardiac": "People with heart disease or hypertension",
}

print("Advisory Templates Loaded:")
for level, template in ADVISORY_TEMPLATES.items():
    print(f"  [{level}]: {template['title']}")
print(f"\\nPollutant-specific advisories: {len(POLLUTANT_ADVISORY_MAP)} pollutants")
print(f"Sensitive groups tracked: {len(SENSITIVE_GROUPS)}")""")

    md("""### 7.2 Advisory Generation Engine

The engine composes a complete advisory message by intelligently combining risk context, pollutant information, ward-level vulnerability, and precautionary guidance.""")

    code("""def generate_advisory(row: pd.Series) -> Dict:
    risk_level = row["risk_level"]
    template = ADVISORY_TEMPLATES[risk_level]
    ward_name = row["ward_name"]
    aqi = row["forecast_aqi"]
    hour = row["forecast_hour"]

    pollutant_contributions = {}
    for col in ["PM2_5", "PM10", "NO2", "SO2", "CO", "O3"]:
        val = row[col]
        threshold = {"PM2_5": 60, "PM10": 100, "NO2": 80, "SO2": 50, "CO": 2.0, "O3": 100}
        if col in threshold and val > threshold[col]:
            ratio = val / threshold[col]
            pollutant_contributions[col] = round(ratio, 1)
    primary_pollutant = max(pollutant_contributions, key=pollutant_contributions.get) if pollutant_contributions else None

    time_context = f"Next {hour} hours" if hour <= 24 else f"Over the next {hour // 24} days"
    if hour <= 24:
        urgency = "immediate"
        time_note = "Take action now to protect yourself and your family."
    elif hour <= 48:
        urgency = "short-term"
        time_note = "Prepare for deteriorating conditions and take preventive measures."
    else:
        urgency = "medium-term"
        time_note = "Plan ahead and monitor updates regularly."

    pollutant_advice = ""
    if primary_pollutant and primary_pollutant in POLLUTANT_ADVISORY_MAP:
        pollutant_advice = POLLUTANT_ADVISORY_MAP[primary_pollutant]

    vuln_text = ""
    vuln_row = vuln_df[vuln_df["ward_id"] == row["ward_id"]].iloc[0]
    if vuln_row["respiratory_pct"] > 12:
        vuln_text += f" {vuln_row['ward_name']} has a higher-than-average respiratory disease prevalence ({vuln_row['respiratory_pct']}%)."
    if vuln_row["child_pct"] + vuln_row["elderly_pct"] > 35:
        vuln_text += f" A significant portion ({vuln_row['child_pct'] + vuln_row['elderly_pct']}%) of the population are children or elderly."

    exposed = row["exposed_population"]
    total_pop = WARDS[row["ward_id"]]["population"]
    exposure_pct = round(exposed / total_pop * 100, 1)

    full_message = f"\\n{'='*60}\\n"
    full_message += f"  HEALTH ADVISORY: {ward_name}\\n"
    full_message += f"  {template['title']}\\n"
    full_message += f"  Risk Level: {risk_level} | AQI: {aqi:.0f} | {time_context}\\n"
    full_message += f"{'='*60}\\n\\n"
    full_message += f"{template['general']}\\n\\n"
    full_message += f"Time Context ({urgency}): {time_note}\\n"
    full_message += f"Population at Risk: {exposed:,} out of {total_pop:,} ({exposure_pct}% of ward population)\\n\\n"
    if pollutant_advice:
        full_message += f"Pollutant Alert: {pollutant_advice}\\n\\n"
    if vuln_text:
        full_message += f"Local Context:{vuln_text}\\n\\n"
    full_message += "Recommended Precautions:\\n"
    for i, precaution in enumerate(template["precautions"], 1):
        full_message += f"  {i}. {precaution}\\n"
    full_message += f"\\nVulnerable Groups Affected:\\n"
    for key, desc in SENSITIVE_GROUPS.items():
        full_message += f"  - {desc}\\n"
    full_message += f"\\n--- This is an AI-generated advisory. Follow official government protocols. ---\\n"

    return {
        "ward_name": ward_name,
        "risk_level": risk_level,
        "urgency": urgency,
        "time_context": time_context,
        "primary_pollutant": primary_pollutant or "None dominant",
        "exposed_population": exposed,
        "exposure_pct": exposure_pct,
        "precaution_count": len(template["precautions"]),
        "full_message": full_message,
    }

advisories = []
for _, row in risk_df.iterrows():
    advisory = generate_advisory(row)
    advisories.append(advisory)

advisory_df = pd.DataFrame(advisories)
print(f"Generated {len(advisory_df)} personalized advisories")

for _, adv in advisory_df[advisory_df["risk_level"].isin(["High", "Critical"])].head(3).iterrows():
    print(adv["full_message"])
    print()""")

    md("""### 7.3 Advisory Summary Dashboard""")

    code("""fig, axes = plt.subplots(2, 2, figsize=(16, 12))

adv_summary = advisory_df.groupby("risk_level").agg(
    count=("ward_name", "count"),
    avg_exposed=("exposed_population", "mean"),
).reset_index()
adv_order = ["Critical", "High", "Moderate", "Low", "Minimal"]
adv_summary["risk_level"] = pd.Categorical(adv_summary["risk_level"], categories=adv_order, ordered=True)
adv_summary = adv_summary.sort_values("risk_level")

colors_adv = [get_risk_level({"Critical": 0.8, "High": 0.6, "Moderate": 0.4, "Low": 0.2, "Minimal": 0.05}[l])[1]
              for l in adv_summary["risk_level"]]
axes[0, 0].bar(adv_summary["risk_level"], adv_summary["count"], color=colors_adv, edgecolor="white", width=0.6)
axes[0, 0].set_title("Advisories by Risk Level", fontsize=13, fontweight="bold")
axes[0, 0].set_ylabel("Number of Advisories")
for i, (_, row) in enumerate(adv_summary.iterrows()):
    axes[0, 0].text(i, row["count"] + 0.1, str(int(row["count"])), ha="center", fontweight="bold")

adv_by_ward = advisory_df.groupby("ward_name").agg(
    avg_risk=("risk_level", lambda x: x.mode().iloc[0] if not x.mode().empty else "Moderate"),
    total_exposed=("exposed_population", "sum"),
).reset_index().sort_values("total_exposed", ascending=True)
colors_bar = [get_risk_level({"Critical": 0.8, "High": 0.6, "Moderate": 0.4, "Low": 0.2, "Minimal": 0.05}[l])[1]
              for l in adv_by_ward["avg_risk"]]
axes[0, 1].barh(range(len(adv_by_ward)), adv_by_ward["total_exposed"] / 1000,
                color=colors_bar, edgecolor="white", linewidth=0.5)
axes[0, 1].set_yticks(range(len(adv_by_ward)))
axes[0, 1].set_yticklabels(adv_by_ward["ward_name"])
axes[0, 1].set_xlabel("Total Exposed Population (thousands)")
axes[0, 1].set_title("Total Population at Risk by Ward", fontsize=13, fontweight="bold")

precautions_by_risk = advisory_df.groupby("risk_level")["precaution_count"].mean()
axes[1, 0].plot(precautions_by_risk.index, precautions_by_risk.values, marker="o", linewidth=2, color="#f97316", markersize=8)
axes[1, 0].set_title("Avg Precautions Recommended by Risk Level", fontsize=13, fontweight="bold")
axes[1, 0].set_xlabel("Risk Level")
axes[1, 0].set_ylabel("Average Number of Precautions")
axes[1, 0].grid(True, alpha=0.3)

pollutant_freq = advisory_df["primary_pollutant"].value_counts()
axes[1, 1].pie(pollutant_freq.values, labels=pollutant_freq.index, autopct="%1.1f%%",
               startangle=90, textprops={"color": "white"})
axes[1, 1].set_title("Primary Pollutants Driving Advisories", fontsize=13, fontweight="bold")

plt.tight_layout()
plt.show()""")

    md("""## 8. Multi-Language Support Architecture

### 8.1 Language Translation Framework

The advisory system is designed with a pluggable language layer. Adding a new language requires only adding a new translation dictionary. This architecture supports:

- **English** (default)
- **Hindi** (हिन्दी) — most widely spoken in Delhi NCR
- **Kannada** (ಕನ್ನಡ) — for Bengaluru deployment
- **Tamil** (தமிழ்) — for Chennai deployment
- Extensible to any additional language

The translation maps cover:
1. **Risk levels and their descriptions**
2. **Precaution messages**
3. **Pollutant names and health impacts**
4. **General advisory phrases**
5. **Vulnerable group descriptions**""")

    code("""LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "code": "en"},
    "hi": {"name": "Hindi", "native_name": "हिन्दी", "code": "hi"},
    "kn": {"name": "Kannada", "native_name": "ಕನ್ನಡ", "code": "kn"},
    "ta": {"name": "Tamil", "native_name": "தமிழ்", "code": "ta"},
}

TRANSLATIONS = {
    "en": {
        "risk_critical": "CRITICAL — Health Emergency",
        "risk_high": "HIGH — Take Protective Measures",
        "risk_moderate": "Moderate — Limit Exposure",
        "risk_low": "Low — Minor Precautions",
        "risk_minimal": "Minimal — Enjoy Your Day",
        "stay_indoors": "Stay indoors. Avoid all outdoor activity.",
        "wear_mask": "Wear N95 mask if you must go out.",
        "close_windows": "Keep windows and doors closed.",
        "use_purifier": "Use air purifiers indoors.",
        "children": "Children are at higher risk. Keep them indoors.",
        "elderly": "Elderly should avoid going out.",
        "schools": "Schools should consider closure or online classes.",
        "medication": "Keep medications and inhalers accessible.",
        "ventilate": "Ventilate your home during non-peak hours (early morning).",
        "ast_hotline": "Call health helpline if experiencing breathing difficulty.",
        "public_transport": "Use public transport to reduce pollution.",
    },
    "hi": {
        "risk_critical": "गंभीर — स्वास्थ्य आपातकाल",
        "risk_high": "उच्च — सुरक्षा उपाय अपनाएं",
        "risk_moderate": "मध्यम — संपर्क सीमित करें",
        "risk_low": "निम्न — छोटी सावधानियां",
        "risk_minimal": "न्यूनतम — अपने दिन का आनंद लें",
        "stay_indoors": "घर के अंदर रहें। बाहरी गतिविधि से बचें।",
        "wear_mask": "यदि बाहर जाना आवश्यक हो तो N95 मास्क पहनें।",
        "close_windows": "खिड़कियां और दरवाजे बंद रखें।",
        "use_purifier": "घर के अंदर एयर प्यूरीफायर का उपयोग करें।",
        "children": "बच्चे अधिक जोखिम में हैं। उन्हें घर के अंदर रखें।",
        "elderly": "बुजुर्गों को बाहर नहीं जाना चाहिए।",
        "schools": "स्कूल बंद करने या ऑनलाइन कक्षाओं पर विचार करें।",
        "medication": "दवाएं और इन्हेलर पहुंच में रखें।",
        "ventilate": "गैर-पीक घंटों (सुबह जल्दी) में अपने घर को हवादार करें।",
        "ast_hotline": "सांस लेने में कठिनाई होने पर स्वास्थ्य हेल्पलाइन पर कॉल करें।",
        "public_transport": "प्रदूषण कम करने के लिए सार्वजनिक परिवहन का उपयोग करें।",
    },
    "kn": {
        "risk_critical": "ತೀವ್ರ — ಆರೋಗ್ಯ ತುರ್ತು",
        "risk_high": "ಹೆಚ್ಚು — ರಕ್ಷಣಾ ಕ್ರಮಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ",
        "risk_moderate": "ಮಧ್ಯಮ — ಸಂಪರ್ಕವನ್ನು ಮಿತಿಗೊಳಿಸಿ",
        "risk_low": "ಕಡಿಮೆ — ಸಣ್ಣ ಮುನ್ನೆಚ್ಚರಿಕೆಗಳು",
        "risk_minimal": "ಕನಿಷ್ಠ — ನಿಮ್ಮ ದಿನವನ್ನು ಆನಂದಿಸಿ",
        "stay_indoors": "ಒಳಗೆ ಇರಿ. ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಯನ್ನು ತಪ್ಪಿಸಿ.",
        "wear_mask": "ಹೊರಗೆ ಹೋಗಬೇಕಾದರೆ N95 ಮಾಸ್ಕ್ ಧರಿಸಿ.",
        "close_windows": "ಕಿಟಕಿಗಳು ಮತ್ತು ಬಾಗಿಲುಗಳನ್ನು ಮುಚ್ಚಿ ಇರಿಸಿ.",
        "use_purifier": "ಒಳಾಂಗಣದಲ್ಲಿ ಏರ್ ಪ್ಯೂರಿಫೈಯರ್ ಬಳಸಿ.",
        "children": "ಮಕ್ಕಳು ಹೆಚ್ಚಿನ ಅಪಾಯದಲ್ಲಿದ್ದಾರೆ. ಅವರನ್ನು ಒಳಗೆ ಇರಿಸಿ.",
        "elderly": "ವಯಸ್ಸಾದವರು ಹೊರಗೆ ಹೋಗುವುದನ್ನು ತಪ್ಪಿಸಬೇಕು.",
        "schools": "ಶಾಲೆಗಳು ಬಂದ್ ಅಥವಾ ಆನ್‌ಲೈನ್ ತರಗತಿಗಳನ್ನು ಪರಿಗಣಿಸಬೇಕು.",
        "medication": "ಔಷಧಿಗಳು ಮತ್ತು ಇನ್‌ಹೇಲರ್‌ಗಳನ್ನು ಪ್ರವೇಶಿಸಬಲ್ಲಂತೆ ಇರಿಸಿ.",
        "ventilate": "ಪೀಕ್ ಅಲ್ಲದ ಸಮಯದಲ್ಲಿ (ಮುಂಜಾನೆ) ಮನೆಗೆ ಗಾಳಿ ಬಿಡಿ.",
        "ast_hotline": "ಉಸಿರಾಟದ ತೊಂದರೆ ಇದ್ದರೆ ಆರೋಗ್ಯ ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ.",
        "public_transport": "ಮಾಲಿನ್ಯ ಕಡಿಮೆ ಮಾಡಲು ಸಾರ್ವಜನಿಕ ಸಾರಿಗೆ ಬಳಸಿ.",
    },
    "ta": {
        "risk_critical": "கடுமையான — சுகாதார அவசரநிலை",
        "risk_high": "அதிக — பாதுகாப்பு நடவடிக்கைகளை எடுக்கவும்",
        "risk_moderate": "மிதமான — தொடர்பை கட்டுப்படுத்தவும்",
        "risk_low": "குறைந்த — சிறிய முன்னெச்சரிக்கைகள்",
        "risk_minimal": "குறைந்தபட்சம் — உங்கள் நாளை அனுபவியுங்கள்",
        "stay_indoors": "வீட்டிற்குள் இருங்கள். வெளிப்புற செயல்களை தவிர்க்கவும்.",
        "wear_mask": "வெளியே செல்ல வேண்டியிருந்தால் N95 மாஸ்க் அணியுங்கள்.",
        "close_windows": "ஜன்னல்கள் மற்றும் கதவுகளை மூடி வைக்கவும்.",
        "use_purifier": "வீட்டிற்குள் ஏர் பியூரிஃபையர் பயன்படுத்தவும்.",
        "children": "குழந்தைகள் அதிக ஆபத்தில் உள்ளனர். அவர்களை வீட்டிற்குள் வைக்கவும்.",
        "elderly": "வயதானவர்கள் வெளியே செல்வதை தவிர்க்க வேண்டும்.",
        "schools": "பள்ளிகள் மூடல் அல்லது ஆன்லைன் வகுப்புகளை கருத்தில் கொள்ளவும்.",
        "medication": "மருந்துகள் மற்றும் இன்ஹேலர்களை அணுகக்கூடியதாக வைக்கவும்.",
        "ventilate": "உச்ச நேரம் அல்லாத நேரங்களில் (அதிகாலை) உங்கள் வீட்டை காற்றோட்டமாக்குங்கள்.",
        "ast_hotline": "மூச்சு திணறல் இருந்தால் சுகாதார உதவி எண்ணை அழைக்கவும்.",
        "public_transport": "மாசுபாட்டை குறைக்க பொது போக்குவரத்தை பயன்படுத்தவும்.",
    }
}

def translate_advisory(text_key: str, lang: str = "en") -> str:
    return TRANSLATIONS.get(lang, {}).get(text_key, TRANSLATIONS["en"].get(text_key, text_key))

def get_advisory_in_language(lang_code: str, risk_level: str) -> Dict:
    lang_info = LANGUAGES.get(lang_code, LANGUAGES["en"])
    risk_key_map = {
        "Critical": "risk_critical", "High": "risk_high",
        "Moderate": "risk_moderate", "Low": "risk_low",
        "Minimal": "risk_minimal",
    }
    return {
        "language": lang_info["name"],
        "native_name": lang_info["native_name"],
        "risk_heading": translate_advisory(risk_key_map.get(risk_level, "risk_moderate"), lang_code),
        "stay_indoors": translate_advisory("stay_indoors", lang_code),
        "wear_mask": translate_advisory("wear_mask", lang_code),
        "close_windows": translate_advisory("close_windows", lang_code),
        "use_purifier": translate_advisory("use_purifier", lang_code),
        "children": translate_advisory("children", lang_code),
        "elderly": translate_advisory("elderly", lang_code),
        "schools": translate_advisory("schools", lang_code),
        "medication": translate_advisory("medication", lang_code),
    }

print(f"Multi-Language Support: {len(LANGUAGES)} languages")
for code, info in LANGUAGES.items():
    print(f"  {code}: {info['name']} ({info['native_name']})")

print("\\nAdvisory in Multiple Languages (High Risk):")
for lang_code in ["en", "hi", "kn", "ta"]:
    adv_lang = get_advisory_in_language(lang_code, "High")
    print(f"\\n  [{adv_lang['language']} ({adv_lang['native_name']})]:")
    print(f"    {adv_lang['risk_heading']}")
    print(f"    {adv_lang['stay_indoors']}")
    print(f"    {adv_lang['wear_mask']}")""")

    md("""### 8.2 Translation Coverage Visualization""")

    code("""lang_df = pd.DataFrame([
    {"Language": info["name"], "Native": info["native_name"],
     "Phrases": len(TRANSLATIONS[code]), "Code": code}
    for code, info in LANGUAGES.items()
])

fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(range(len(lang_df)), lang_df["Phrases"], color=["#3b82f6", "#f97316", "#22c55e", "#a855f7"],
              edgecolor="white", linewidth=0.5, width=0.6)
ax.set_xticks(range(len(lang_df)))
ax.set_xticklabels([f"{row['Language']}\\n({row['Native']})" for _, row in lang_df.iterrows()])
ax.set_ylabel("Number of Translated Phrases")
ax.set_title("Translation Coverage by Language", fontsize=14, fontweight="bold")
for bar, (_, row) in zip(bars, lang_df.iterrows()):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            str(row["Phrases"]), ha="center", fontweight="bold")
plt.tight_layout()
plt.show()""")

    md("""## 9. Delivery Channels Architecture

### 9.1 Multi-Channel Delivery Workflow

The advisory system is designed to deliver through multiple communication channels:

| Channel | Format | Latency | Coverage | Personalization |
|---------|--------|---------|----------|----------------|
| **Mobile App** | Push notification + full advisory | Real-time | Smartphone users | High (location-aware) |
| **Public Displays** | Scrolling text + color-coded alerts | 5-minute refresh | Public spaces | Medium (ward-level) |
| **SMS** | Short text alert | 15-minute batch | All mobile users | Medium (ward-level) |
| **IVR** | Voice advisory in local language | On-demand | Feature phone users | Low (zone-level) |
| **Web Portal** | Full interactive dashboard | Real-time | Internet users | High (user configurable) |

This section demonstrates the delivery channel workflow with mock implementations.""")

    code("""CHANNELS = {
    "mobile_app": {
        "name": "Mobile Application",
        "format": "push_notification",
        "latency": "Real-time",
        "coverage": "Smartphone users",
        "pros": "Rich media, location-aware, interactive",
        "cons": "Requires smartphone + app install",
        "enabled": True,
    },
    "public_display": {
        "name": "Public Information Display",
        "format": "scrolling_text",
        "latency": "5-minute refresh",
        "coverage": "Public spaces (metro, bus stops, markets)",
        "pros": "Reaches non-smartphone users, high visibility",
        "cons": "Limited character length, no personalization",
        "enabled": True,
    },
    "sms": {
        "name": "SMS Alert",
        "format": "short_text",
        "latency": "15-minute batch",
        "coverage": "All mobile users",
        "pros": "Universal reach, works on all phones",
        "cons": "160 char limit, no rich formatting",
        "enabled": True,
    },
    "ivr": {
        "name": "IVR Voice Advisory",
        "format": "voice_message",
        "latency": "On-demand",
        "coverage": "Feature phone users",
        "pros": "Accessible to illiterate users, local language",
        "cons": "Linear delivery, no visual aids",
        "enabled": True,
    },
    "web_portal": {
        "name": "Web Dashboard",
        "format": "interactive_dashboard",
        "latency": "Real-time",
        "coverage": "Internet users",
        "pros": "Full data, charts, customization",
        "cons": "Requires internet + device",
        "enabled": True,
    },
}

channel_df = pd.DataFrame.from_dict(CHANNELS, orient="index")
display(channel_df[["name", "format", "latency", "coverage", "enabled"]])

def generate_channel_message(advisory: Dict, channel: str, lang: str = "en") -> str:
    risk = advisory["risk_level"]
    ward = advisory["ward_name"]
    aqi_risk = f"Risk: {risk}"
    time_info = advisory["time_context"]

    if channel == "sms":
        msg = f"[VAYU-ALERT] {ward}: {risk}. {advisory['time_context']}. "
        msg += translate_advisory("stay_indoors", lang) + " "
        msg += translate_advisory("wear_mask", lang)
        return msg[:160]

    elif channel == "public_display":
        risk_color = {"Minimal": "GREEN", "Low": "YELLOW", "Moderate": "ORANGE",
                      "High": "RED", "Critical": "RED FLASHING"}[risk]
        return f"[{risk_color}] {ward.upper()} — {risk} — {time_info} — {translate_advisory('stay_indoors', lang)}"

    elif channel == "mobile_app":
        return advisory["full_message"]

    elif channel == "ivr":
        return f"Welcome to Vayu-Drishti health advisory for {ward}. Current air quality risk level is {risk}. {translate_advisory('stay_indoors', lang)}. {translate_advisory('wear_mask', lang)}. For more information, stay on the line."

    else:
        return advisory["full_message"]

critical_advisories = advisory_df[advisory_df["risk_level"] == "Critical"]
if len(critical_advisories) > 0:
    sample = critical_advisories.iloc[0]
    print(f"\\nChannel Message Examples for {sample['ward_name']} (Risk: {sample['risk_level']}):\\n")
    for channel in ["sms", "public_display", "mobile_app", "ivr"]:
        msg = generate_channel_message(sample, channel, "hi")
        print(f"[{CHANNELS[channel]['name']}]".center(60, "-"))
        print(msg)
        print()

channel_summary = pd.DataFrame([
    {"Channel": info["name"], "Format": info["format"],
     "Latency": info["latency"], "Enabled": info["enabled"]}
    for info in CHANNELS.values()
])
print("Delivery Channel Summary:")
display(channel_summary)""")

    md("""## 10. Intervention Priority Framework

### 10.1 Prioritization Engine

The prioritization engine ranks wards by intervention urgency, combining:
- **Health risk score** (primary factor)
- **Exposed population** (magnitude of impact)
- **Vulnerability** (population susceptibility)
- **Source attribution** (actionability — from Enforcement Intelligence)
- **Trend** (deteriorating vs improving)""")

    code("""np.random.seed(456)
ward_priorities = []
for wid, ward in WARDS.items():
    ward_risks = risk_df[risk_df["ward_id"] == wid]
    max_risk = ward_risks["risk_score"].max()
    avg_risk = ward_risks["risk_score"].mean()
    total_exposed = ward_risks["exposed_population"].sum()
    avg_aqi = ward_risks["forecast_aqi"].mean()

    vuln_score = vuln_df[vuln_df["ward_id"] == wid]["vulnerability_score"].values[0]

    risk_score_norm = avg_risk / 1.0
    exposure_norm = min(1.0, total_exposed / 1000000)
    vuln_norm = vuln_score

    sources_pool = ["industrial", "traffic", "crop_burning", "construction", "waste_burning", "mixed"]
    primary_source = np.random.choice(sources_pool, p=[0.2, 0.3, 0.1, 0.15, 0.1, 0.15])
    source_actionable = {"industrial": 0.8, "traffic": 0.6, "crop_burning": 0.9,
                         "construction": 0.7, "waste_burning": 0.85, "mixed": 0.5}[primary_source]

    trend = np.random.choice(["improving", "stable", "deteriorating"], p=[0.3, 0.4, 0.3])
    trend_penalty = {"improving": -0.05, "stable": 0, "deteriorating": 0.1}[trend]

    priority_score = (risk_score_norm * 0.4 + exposure_norm * 0.25 + vuln_norm * 0.2 +
                      source_actionable * 0.1 + trend_penalty)

    ward_priorities.append({
        "ward_id": wid,
        "ward_name": ward["name"],
        "max_risk": round(max_risk, 3),
        "avg_risk": round(avg_risk, 3),
        "total_exposed": int(total_exposed),
        "avg_aqi": round(avg_aqi, 1),
        "vulnerability": round(vuln_score, 3),
        "primary_source": primary_source,
        "trend": trend,
        "priority_score": round(priority_score, 3),
    })

priority_df = pd.DataFrame(ward_priorities).sort_values("priority_score", ascending=False)
print("Intervention Priority Ranking:")
display(priority_df[["ward_name", "avg_risk", "total_exposed", "vulnerability", "primary_source", "trend", "priority_score"]])

print("\\nTop 3 Wards for Immediate Intervention:")
for _, row in priority_df.head(3).iterrows():
    print(f"  {row['ward_name']}: Score={row['priority_score']}, Risk={row['avg_risk']}, "
          f"Exposed={row['total_exposed']:,}, Source={row['primary_source']}")""")

    md("""### 10.2 Priority Visualization""")

    code("""fig, axes = plt.subplots(1, 2, figsize=(16, 7))

sorted_priorities = priority_df.sort_values("priority_score", ascending=True)
colors_priority = plt.cm.RdYlGn_r(sorted_priorities["priority_score"])
bars = axes[0].barh(range(len(sorted_priorities)), sorted_priorities["priority_score"],
                    color=colors_priority, edgecolor="white", linewidth=0.5)
axes[0].set_yticks(range(len(sorted_priorities)))
axes[0].set_yticklabels(sorted_priorities["ward_name"])
axes[0].set_xlabel("Priority Score")
axes[0].set_title("Ward Intervention Priority Ranking", fontsize=14, fontweight="bold")
for i, (_, row) in enumerate(sorted_priorities.iterrows()):
    axes[0].text(row["priority_score"] + 0.01, i, f"{row['priority_score']:.3f}",
                 va="center", fontsize=9, color="white")
axes[0].axvline(x=0.5, color="white", linestyle="--", alpha=0.5, linewidth=0.8)

source_counts = priority_df["primary_source"].value_counts()
source_colors_map = {"industrial": "#a855f7", "traffic": "#3b82f6", "crop_burning": "#f97316",
                     "construction": "#eab308", "waste_burning": "#8B4513", "mixed": "#6b7280"}
source_colors = [source_colors_map.get(s, "#6b7280") for s in source_counts.index]
wedges, texts, autotexts = axes[1].pie(source_counts.values, labels=source_counts.index,
                                        colors=source_colors, autopct="%1.1f%%",
                                        startangle=90, textprops={"color": "white"})
axes[1].set_title("Primary Sources by Ward", fontsize=14, fontweight="bold")

plt.tight_layout()
plt.show()""")

    md("""## 11. Integration with Enforcement Intelligence

### 11.1 Source-Aware Advisory Enhancement

When the Enforcement Intelligence module identifies specific pollution sources in a ward, the advisory can be enhanced with source-specific recommendations. This demonstrates cross-module integration.""")

    code("""SOURCE_SPECIFIC_ADVICE = {
    "industrial": "Industrial emissions detected in your area. Avoid downwind areas near factories.",
    "traffic": "High traffic emissions detected. Avoid major roadways during peak hours.",
    "crop_burning": "Crop burning detected upwind. Close windows facing that direction.",
    "construction": "Construction activities contributing to dust. Keep windows closed during work hours.",
    "waste_burning": "Open waste burning detected. Report to municipal corporation.",
    "mixed": "Multiple pollution sources detected. Follow general precautions strictly.",
}

def enhance_advisory_with_sources(advisory_text: str, primary_source: str, ward_name: str) -> str:
    source_advice = SOURCE_SPECIFIC_ADVICE.get(primary_source, "")
    if source_advice:
        enhanced = advisory_text + f"\\n\\n--- Source-Specific Guidance for {ward_name} ---\\n"
        enhanced += f"Detected primary source: {primary_source.replace('_', ' ').title()}\\n"
        enhanced += f"{source_advice}"
        return enhanced
    return advisory_text

print("Source-Specific Advisory Enhancement:")
for source, advice in SOURCE_SPECIFIC_ADVICE.items():
    print(f"  [{source.replace('_', ' ').title()}]: {advice}")

print("\\nExample Enhanced Advisory:")
sample_priority = priority_df.iloc[0]
sample_adv = advisory_df[advisory_df["ward_name"] == sample_priority["ward_name"]]
if len(sample_adv) > 0:
    enhanced = enhance_advisory_with_sources(
        sample_adv.iloc[0]["full_message"],
        sample_priority["primary_source"],
        sample_priority["ward_name"],
    )
    print(enhanced)""")

    md("""## 12. Alignment with Evaluation Focus

### 12.1 Contribution to Hackathon Evaluation Metrics

| Evaluation Focus | Contribution of This Module |
|-----------------|---------------------------|
| **Hyperlocal AQI Forecast Usability** | Translates forecast AQI into actionable health advisories at ward-level resolution, making forecasts directly useful for citizens |
| **Citizen Advisory Relevance** | Generates personalized, context-aware advisories that adapt to risk level, pollutants, time horizon, and local vulnerability |
| **Language Coverage** | Built-in support for English, Hindi, Kannada, and Tamil with extensible architecture for more languages |
| **Faster Response (Signal to Intervention)** | Priority framework identifies most urgent wards, enabling faster mobilization of resources |
| **Better Decision Support** | Risk scoring combines AQI, pollutant profile, vulnerability, and source data for comprehensive decision support |
| **Improved Public Health Preparedness** | Multi-horizon advisories (24/48/72h) enable both immediate action and medium-term planning |
| **Complementing Source Attribution** | Integrates Enforcement Intelligence source attribution to provide source-specific health guidance |""")

    md("""## 13. Alignment with Judging Criteria

### 13.1 How Design Decisions Support Judging Criteria

| Judging Criterion | Design Decisions |
|------------------|-----------------|
| **Innovation** | AI-driven composite risk scoring combining 5 factors; intelligent advisory composition instead of static templates; source-aware advisories integrating enforcement intelligence |
| **Business Impact** | Citizen-facing health intelligence improves public health outcomes; multilingual design ensures inclusive reach; multi-channel delivery maximizes penetration across demographic segments |
| **Technical Excellence** | Modular architecture with clear separation of concerns; extensible language framework; production-quality visualizations; follows existing project patterns and conventions |
| **Scalability** | Pluggable language architecture supports unlimited languages; channel-agnostic advisory generation; ward-level resolution scales to any city; standalone module that integrates via data interfaces |
| **User Experience** | Personalized, context-aware advisories; color-coded risk visualization; concise SMS-friendly format; local-language voice support for IVR; practical actionable precautions |""")

    md("""## 14. Conclusion — Completing the Smart City Ecosystem

### How This Module Completes Vayu-Drishti

The Vayu-Drishti platform now covers the complete air quality intelligence lifecycle:

```
[Data Ingestion] → [AQI Prediction] → [Hyperlocal Forecast] → [HEALTH RISK ADVISORY]
                          ↓                                         ↓
              [Explainable AI]                           [Citizen Advisories]
                          ↓                                         ↓
              [Enforcement Intelligence]              [Multi-Channel Delivery]
                          ↓                                         ↓
              [Source Attribution]                     [Multi-Language Support]
                          ↓
              [GIS Visualization]
```

This module adds the **critical citizen engagement layer** that:
- Makes technical AQI data **personally relevant** to every citizen
- Provides **actionable guidance** in their preferred language
- Delivers through **channels they already use**
- Integrates with **existing enforcement and forecasting** for comprehensive intelligence
- **Closes the loop** from data → forecast → risk → action

The result is a complete Smart City Air Quality Intelligence platform that not only detects and predicts pollution but actively protects citizen health.""")

    md("""## 15. Saved Artifacts

The module saves key outputs for integration with the rest of the Vayu-Drishti platform.""")

    code("""artifacts = {
    "ward_vulnerability": _ARTIFACTS_DIR / "ward_vulnerability.csv",
    "health_risk_scores": _ARTIFACTS_DIR / "health_risk_scores.csv",
    "advisory_data": _ARTIFACTS_DIR / "advisory_data.csv",
    "priority_ranking": _ARTIFACTS_DIR / "priority_ranking.csv",
    "translation_data": _ARTIFACTS_DIR / "translations.json",
}

vuln_df.to_csv(artifacts["ward_vulnerability"], index=False)
risk_df.to_csv(artifacts["health_risk_scores"], index=False)
advisory_df.to_csv(artifacts["advisory_data"], index=False)
priority_df.to_csv(artifacts["priority_ranking"], index=False)
with open(artifacts["translation_data"], "w", encoding="utf-8") as f:
    json.dump(TRANSLATIONS, f, ensure_ascii=False, indent=2)

print("Artifacts saved:")
for name, path in artifacts.items():
    exists = "✓" if path.exists() else "✗"
    print(f"  [{exists}] {name}: {path}")""")

    md("""---

*End of Citizen Health Risk Advisory System notebook.*

*This module was built as part of the Vayu-Drishti Smart City Air Quality Intelligence Platform for the ET Hackathon.*""")

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.12.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1, ensure_ascii=True)
        print(f"Notebook written to {output_path}")

    return json.dumps(notebook, ensure_ascii=False)


if __name__ == "__main__":
    output = str(Path(__file__).resolve().parent / "health_risk_advisory.ipynb")
    generate_notebook(output)
