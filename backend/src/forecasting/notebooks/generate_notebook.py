from __future__ import annotations

import json
import uuid
from pathlib import Path


def _cell(source: str | list[str], cell_type: str = "code") -> dict:
    if isinstance(source, str):
        source = source.split("\n")
    return {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source],
        "id": uuid.uuid4().hex[:8],
    } | ({"execution_count": None, "outputs": []} if cell_type == "code" else {})


def generate_notebook() -> None:
    cells = []

    md = lambda s: cells.append(_cell(s, "markdown"))
    cd = lambda s: cells.append(_cell(s, "code"))

    md("# Hyperlocal AQI Forecasting\n\n## 24\u201372 Hour Predictive AQI Forecasting at Ward Level\n\nThis notebook implements a complete **time-series forecasting pipeline** for predicting AQI at hyperlocal (ward) level 24\u201372 hours ahead. Unlike the instantaneous AQI prediction model (which predicts current AQI from pollutant readings), this system forecasts future AQI using historical time-series patterns.\n\n### Objectives\n- Generate multi-location hourly AQI time-series data\n- Build lag-based and rolling-window features\n- Train SARIMA, Prophet, LSTM, and Ensemble forecasters per location\n- Evaluate using time-series metrics (RMSE, MASE, sMAPE)\n- Compare forecast accuracy across locations\n- Visualize 72-hour forecasts with uncertainty\n- Save trained models for API deployment")

    md("## 1. Import Libraries")

    cd("""import sys
import warnings
import time
import json
import pickle
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["figure.dpi"] = 120
sns.set_theme(style="whitegrid")

_root = Path.cwd()
for _ in range(6):
    if (_root / "backend").exists() and (_root / "backend/src/forecasting").exists():
        break
    _root = _root.parent
sys.path.insert(0, str(_root))

from backend.src.forecasting.config import ForecastingConfig
from backend.src.forecasting.data.generator import HyperlocalDataGenerator
from backend.src.forecasting.features.builder import build_features
from backend.src.forecasting.models.naive import NaiveForecast
from backend.src.forecasting.models.arima_model import ARIMAForecast
from backend.src.forecasting.models.prophet_model import ProphetForecast
from backend.src.forecasting.models.lstm_forecaster import LSTMHorizonForecast
from backend.src.forecasting.models.ensemble import ForecastEnsemble
from backend.src.forecasting.training.evaluator import compute_forecast_metrics, aqi_category_accuracy
from backend.src.forecasting.inference.forecaster import Forecaster

print("All imports successful!")""")

    md("## 2. Configuration")

    cd("""config = ForecastingConfig()
config.n_locations = 5
config.n_hours = 8760
config.forecast_horizon = 72
config.lstm_params["epochs"] = 20
config.lstm_params["hidden_size"] = 64
config.lstm_params["num_layers"] = 1
config.lstm_params["batch_size"] = 128
config.lstm_params["early_stopping_patience"] = 5
print(f"Configuration:")
print(f"  Locations: {config.n_locations}")
print(f"  Hours per location: {config.n_hours:,}")
print(f"  Forecast horizon: {config.forecast_horizon}h")
print(f"  Features: {len(config.feature_columns)}")
print(f"  LSTM epochs: {config.lstm_params['epochs']}")""")

    md("## 3. Data Generation\n\nGenerate synthetic hyperlocal AQI time-series data for Delhi wards. Each location has hourly AQI readings with seasonal, diurnal, and weekend patterns reflecting real Delhi conditions.")

    cd("""print("Generating multi-location data...")
gen = HyperlocalDataGenerator(config)
df = gen.generate_and_save(force=True)
print(f"Total rows: {len(df):,}")
print(f"Locations: {df['location_id'].nunique()}")
print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
print(f"\\nLocation summary:")
loc_summary = df[["location_id","ward","zone","latitude","longitude"]].drop_duplicates().sort_values("location_id")
print(loc_summary.to_string(index=False))
print(f"\\nSample rows:")
df.head()""")

    md("## 4. Exploratory Data Analysis\n\n### 4.1 AQI Distribution by Location")

    cd("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for loc_id in df["location_id"].unique():
    loc_data = df[df["location_id"] == loc_id]["AQI"]
    axes[0].hist(loc_data, bins=40, alpha=0.5, label=f"Loc {loc_id}", density=True)
axes[0].set_title("AQI Distribution by Location", fontsize=14, fontweight="bold")
axes[0].set_xlabel("AQI")
axes[0].set_ylabel("Density")
axes[0].legend(fontsize=8)

loc_means = df.groupby("ward")["AQI"].mean().sort_values()
colors_ward = plt.cm.viridis(np.linspace(0.2, 0.9, len(loc_means)))
axes[1].barh(loc_means.index, loc_means.values, color=colors_ward, edgecolor="black")
axes[1].set_title("Mean AQI by Ward", fontsize=14, fontweight="bold")
axes[1].set_xlabel("Mean AQI")
plt.tight_layout()
plt.show()

print(f"Global mean AQI: {df['AQI'].mean():.1f}")
print(f"Global std AQI: {df['AQI'].std():.1f}")""")

    md("### 4.2 Time-Series Visualization")

    cd("""fig, axes = plt.subplots(2, 1, figsize=(14, 8))
loc0 = df[df["location_id"] == 0].sort_values("datetime")
axes[0].plot(loc0["datetime"].values[:500], loc0["AQI"].values[:500], linewidth=0.8, color="steelblue")
axes[0].set_title("AQI Time Series - Location 0 (First 500 Hours)", fontsize=14, fontweight="bold")
axes[0].set_xlabel("Time")
axes[0].set_ylabel("AQI")
axes[0].grid(True, alpha=0.3)

loc0_week = loc0.iloc[:168]
axes[1].plot(loc0_week["datetime"].values, loc0_week["AQI"].values, marker="o", markersize=2, linewidth=1, color="crimson")
axes[1].set_title("AQI Time Series - Location 0 (First Week)", fontsize=14, fontweight="bold")
axes[1].set_xlabel("Time")
axes[1].set_ylabel("AQI")
axes[1].grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print(f"Hourly AQI stats for Location 0:")
print(f"  Mean: {loc0['AQI'].mean():.1f}, Min: {loc0['AQI'].min():.1f}, Max: {loc0['AQI'].max():.1f}")""")

    md("### 4.3 Seasonal and Diurnal Patterns")

    cd("""season_map = {0:"Winter",1:"Spring",2:"Summer",3:"Autumn"}
df["Season_Name"] = df["Season"].map(season_map)
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
sns.boxplot(data=df, x="Season_Name", y="AQI", order=["Winter","Spring","Summer","Autumn"],
            ax=axes[0], palette="coolwarm")
axes[0].set_title("AQI by Season", fontweight="bold")

hourly_mean = df.groupby("Hour")["AQI"].mean()
axes[1].plot(hourly_mean.index, hourly_mean.values, marker="o", color="steelblue", linewidth=2)
axes[1].set_title("Average AQI by Hour", fontweight="bold")
axes[1].set_xlabel("Hour")
axes[1].grid(True, alpha=0.3)

weekly_mean = df.groupby("DayOfWeek")["AQI"].mean()
labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
axes[2].bar(range(7), weekly_mean.values, color=["steelblue"]*5+["orange"]*2, edgecolor="black")
axes[2].set_title("Average AQI by Day", fontweight="bold")
axes[2].set_xticks(range(7))
axes[2].set_xticklabels(labels)
plt.tight_layout()
plt.show()""")

    md("## 5. Feature Engineering\n\nCreate lag features, rolling window statistics, cyclical encoding, and indicator variables.")

    cd("""sample_loc = df[df["location_id"] == 0].sort_values("datetime").head(200)
df_feat = build_features(sample_loc)
print(f"Original columns: {list(sample_loc.columns)}")
print(f"\\nAfter feature engineering: {list(df_feat.columns)}")
print(f"\\nShape: {df_feat.shape}")
print(f"\\nFeature columns ({len(config.feature_columns)}):")
for i, col in enumerate(config.feature_columns):
    print(f"  {i+1:2d}. {col}")
print(f"\\nSample feature values:")
df_feat[config.feature_columns[:8] + ["AQI"]].head(10)""")

    md("## 6. Model Training\n\nTrain separate models for each location using time-series cross-validation.")

    cd("""all_results = {}
model_registry = [
    ("Naive", NaiveForecast, {}),
    ("SARIMA", ARIMAForecast, {"config": config}),
    ("Prophet", ProphetForecast, {"config": config}),
    ("LSTM", LSTMHorizonForecast, {"config": config}),
]

from backend.src.forecasting.training.trainer import train_all_locations

for name, cls, kwargs in model_registry:
    print(f"\\n{'='*50}")
    print(f"Training {name}...")
    print(f"{'='*50}")
    t0 = time.time()
    model = cls(**kwargs) if kwargs else cls()
    results = train_all_locations(model, df, config)
    all_results[name] = results
    print(f"Total time: {time.time()-t0:.1f}s")

print(f"\\n{'='*50}")
print(f"Training Ensemble...")
print(f"{'='*50}")
base_models = []
for name in ["SARIMA", "Prophet", "LSTM"]:
    for cls_name, cls, kwargs in model_registry:
        if cls_name == name:
            base_models.append(cls(**kwargs) if kwargs else cls())
            break
ensemble = ForecastEnsemble(base_models, config)
ensemble_results = {}
from backend.src.forecasting.training.trainer import train_location
for loc_id, grp in df.groupby("location_id"):
    grp = grp.sort_values("datetime").reset_index(drop=True)
    t0 = time.time()
    r = train_location(ensemble, grp, config.feature_columns, config.target_column, config.forecast_horizon)
    r["training_time"] = round(time.time() - t0, 2)
    ensemble_results[int(loc_id)] = r
    print(f"  Location {int(loc_id)}: RMSE={r['metrics']['RMSE']}, R2={r['metrics']['R2']} ({r['training_time']:.1f}s)")
all_results["Ensemble"] = ensemble_results""")

    md("## 7. Model Comparison")

    cd("""from backend.src.forecasting.training.trainer import summarize_results
summary = summarize_results(all_results, config.n_locations)
print("=== Model Performance Summary ===")
print(summary.to_string(index=False))

best_model_name = summary.iloc[0]["Model"]
print(f"\\n{'='*50}")
print(f"BEST MODEL: {best_model_name}")
print(f"{'='*50}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].bar(summary["Model"], summary["Mean_RMSE"], yerr=summary["Std_RMSE"],
            capsize=5, color=["steelblue","green","orange","red","purple"], edgecolor="black")
axes[0].set_title("Mean RMSE by Model", fontsize=14, fontweight="bold")
axes[0].set_ylabel("RMSE")
axes[0].grid(True, alpha=0.3, axis="y")

axes[1].bar(summary["Model"], summary["Mean_R2"], yerr=summary["Std_R2"],
            capsize=5, color=["steelblue","green","orange","red","purple"], edgecolor="black")
axes[1].axhline(y=0.5, color="red", linestyle="--", label="0.5 threshold")
axes[1].set_title("Mean R2 by Model", fontsize=14, fontweight="bold")
axes[1].set_ylabel("R2")
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.show()""")

    md("## 8. Best Model Evaluation\n\n### 8.1 Forecast vs Actual")

    cd("""best_results = all_results[best_model_name]
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flat
for i, loc_id in enumerate(sorted(best_results.keys())[:6]):
    r = best_results[loc_id]
    actual = r["actual"]
    pred = r["predictions"]
    axes[i].plot(range(len(actual)), actual, label="Actual", color="steelblue", linewidth=1.5)
    axes[i].plot(range(len(pred)), pred, label="Forecast", color="crimson", linewidth=1.5, linestyle="--")
    axes[i].set_title(f"Location {loc_id} - {r['metrics']['RMSE']:.1f} RMSE", fontsize=10, fontweight="bold")
    axes[i].set_xlabel("Hour")
    axes[i].set_ylabel("AQI")
    axes[i].legend(fontsize=7)
    axes[i].grid(True, alpha=0.3)
for j in range(i+1, len(axes)):
    axes[j].set_visible(False)
plt.suptitle(f"{best_model_name} - Forecast vs Actual (First 6 Locations)", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()""")

    md("### 8.2 Scatter: Predicted vs Actual")

    cd("""fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flat
for i, loc_id in enumerate(sorted(best_results.keys())[:6]):
    r = best_results[loc_id]
    axes[i].scatter(r["actual"], r["predictions"], alpha=0.5, s=5, c="steelblue")
    mn = min(r["actual"].min(), r["predictions"].min())
    mx = max(r["actual"].max(), r["predictions"].max())
    axes[i].plot([mn, mx], [mn, mx], "r--", linewidth=1.5)
    axes[i].set_xlabel("Actual AQI")
    axes[i].set_ylabel("Predicted AQI")
    axes[i].set_title(f"Loc {loc_id} (R2={r['metrics']['R2']})", fontsize=10)
    axes[i].grid(True, alpha=0.3)
for j in range(i+1, len(axes)):
    axes[j].set_visible(False)
plt.suptitle(f"{best_model_name} - Predicted vs Actual AQI", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()""")

    md("### 8.3 Residual Distribution")

    cd("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))
all_residuals = []
for r in best_results.values():
    all_residuals.extend((r["actual"] - r["predictions"]).tolist())
res = np.array(all_residuals)
axes[0].hist(res, bins=50, edgecolor="black", alpha=0.7, color="steelblue", density=True)
axes[0].axvline(x=0, color="red", linestyle="--", linewidth=2)
axes[0].set_title("Residual Distribution (All Locations)", fontsize=14, fontweight="bold")
axes[0].set_xlabel("Residual")
axes[0].set_ylabel("Density")

abs_err = np.abs(res)
axes[1].hist(abs_err, bins=50, edgecolor="black", alpha=0.7, color="orange")
for pct in [50, 75, 90]:
    val = np.percentile(abs_err, pct)
    axes[1].axvline(x=val, color="red", linestyle="--", alpha=0.7)
    axes[1].text(val, axes[1].get_ylim()[1]*0.85, f"  {pct}th: {val:.1f}", rotation=90, fontsize=8)
axes[1].set_title("Absolute Error Distribution", fontsize=14, fontweight="bold")
axes[1].set_xlabel("Absolute Error")
plt.tight_layout()
plt.show()

print(f"Mean residual: {res.mean():.3f}")
print(f"Residual std: {res.std():.3f}")
print(f"50th percentile abs error: {np.percentile(abs_err, 50):.3f}")
print(f"90th percentile abs error: {np.percentile(abs_err, 90):.3f}")""")

    md("## 9. 72-Hour Forecast Visualization\n\nGenerate and display the 72-hour forecast for all locations.")

    cd("""loc_ids = sorted(best_results.keys())
n_loc = min(5, len(loc_ids))
fig, axes = plt.subplots(n_loc, 1, figsize=(14, 3*n_loc))
if n_loc == 1:
    axes = [axes]
for i, loc_id in enumerate(loc_ids[:n_loc]):
    loc_data = df[df["location_id"] == loc_id].sort_values("datetime")
    history = loc_data["AQI"].values[-168:]
    forecast = best_results[loc_id]["predictions"][:72]
    axes[i].plot(range(-168, 0), history, color="steelblue", linewidth=1, label="History (168h)")
    axes[i].plot(range(0, len(forecast)), forecast, color="crimson", linewidth=2, label="Forecast (72h)")
    axes[i].axvline(x=0, color="gray", linestyle="--", alpha=0.5)
    ward_name = loc_data["ward"].iloc[0]
    axes[i].set_title(f"{ward_name} - 72-Hour AQI Forecast", fontsize=12, fontweight="bold")
    axes[i].set_ylabel("AQI")
    axes[i].legend(fontsize=9)
    axes[i].grid(True, alpha=0.3)
axes[-1].set_xlabel("Hours from now")
plt.tight_layout()
plt.show()

print("72-Hour Forecast Summary:")
for loc_id in loc_ids[:n_loc]:
    r = best_results[loc_id]
    loc_data = df[df["location_id"] == loc_id]
    ward = loc_data["ward"].iloc[0]
    preds = r["predictions"][:72]
    print(f"  {ward}: Current={loc_data['AQI'].iloc[-1]:.0f}, "
          f"24h={preds[23] if len(preds)>23 else preds[-1]:.0f}, "
          f"48h={preds[47] if len(preds)>47 else preds[-1]:.0f}, "
          f"72h={preds[-1]:.0f}")""")

    md("## 10. Save Artifacts")

    cd("""import pickle, json
from pathlib import Path

artifacts_dir = Path(config.artifacts_dir)
artifacts_dir.mkdir(parents=True, exist_ok=True)
models_dir = artifacts_dir / "models"
models_dir.mkdir(exist_ok=True)

for loc_id in sorted(best_results.keys()):
    loc_data = df[df["location_id"] == loc_id].sort_values("datetime")
    feat_df = build_features(loc_data).dropna().reset_index(drop=True)
    split_idx = int(len(feat_df) * 0.8)
    X_train = feat_df.iloc[:split_idx][config.feature_columns]
    y_train = feat_df.iloc[:split_idx][config.target_column]

    if best_model_name == "Ensemble":
        model_to_save = copy.deepcopy(ensemble)
    else:
        for nm, cls, kw in model_registry:
            if nm == best_model_name:
                model_to_save = cls(**kw) if kw else cls()
                break
    model_to_save.fit(loc_id, X_train, y_train)
    with open(models_dir / f"location_{loc_id}.pkl", "wb") as f:
        pickle.dump(model_to_save, f)

loc_meta = {}
for _, row in df[["location_id","ward","zone","latitude","longitude"]].drop_duplicates().iterrows():
    loc_meta[int(row["location_id"])] = {"ward": row["ward"], "zone": row["zone"],
                                          "latitude": float(row["latitude"]), "longitude": float(row["longitude"])}

metadata = {
    "best_model": best_model_name,
    "trained_models": list(all_results.keys()),
    "feature_columns": config.feature_columns,
    "forecast_horizon": config.forecast_horizon,
    "n_locations": config.n_locations,
    "location_metadata": loc_meta,
}
with open(artifacts_dir / "metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Artifacts saved to {artifacts_dir}")
for p in sorted(models_dir.glob("*.pkl")):
    print(f"  {p.name}")
print(f"  metadata.json")""")

    md("## 11. Load and Verify")

    cd("""forecaster = Forecaster(config)
forecaster.load()
if forecaster.is_loaded:
    print(f"Forecaster loaded successfully!")
    print(f"  Locations: {len(forecaster._models)}")
    results_all = forecaster.predict_all(72)
    for r in results_all[:3]:
        print(f"  {r['ward']} (Loc {r['location_id']}): Latest AQI={r['latest_aqi']}, Category={r['category']}")
else:
    print("Failed to load forecaster.")""")

    md("""## 12. Conclusions

### Key Findings

| Aspect | Result |
|--------|--------|
| **Best Model** | Varies by location |
| **Forecast Horizon** | 72 hours |
| **Features** | 30 lag/rolling/cyclical features |
| **Locations** | Multi-ward Delhi coverage |

The Hyperlocal AQI Forecasting system provides ward-level 72-hour AQI forecasts using time-series models. This complements the existing AQI prediction system (which predicts current AQI from pollutant readings) by adding future forecast capability.

### Integration

The forecasting module is at `backend/src/forecasting/` and the API agent is at `agents/agent-hyperlocal-aqi/`. Use the `Forecaster` class to load trained models and generate predictions:

```python
from backend.src.forecasting.inference.forecaster import Forecaster

f = Forecaster()
f.load()
result = f.predict_location(location_id=0, steps=72)
```""")

    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
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
        "cells": cells,
    }

    output_path = Path(__file__).parent / "hyperlocal_forecast.ipynb"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"Notebook generated: {output_path}")


if __name__ == "__main__":
    generate_notebook()
