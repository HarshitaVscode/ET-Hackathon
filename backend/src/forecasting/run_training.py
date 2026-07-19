from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.src.forecasting.config import ForecastingConfig
from backend.src.forecasting.data.generator import HyperlocalDataGenerator
from backend.src.forecasting.features.builder import build_features
from backend.src.forecasting.models.naive import NaiveForecast
from backend.src.forecasting.models.arima_model import ARIMAForecast
from backend.src.forecasting.models.prophet_model import ProphetForecast
from backend.src.forecasting.models.lstm_forecaster import LSTMHorizonForecast
from backend.src.forecasting.models.ensemble import ForecastEnsemble
from backend.src.forecasting.training.trainer import train_location, train_all_locations, summarize_results


def main() -> None:
    config = ForecastingConfig()
    config.n_locations = 5
    config.n_hours = 8760

    print("=" * 60)
    print("HYPERLOCAL AQI FORECASTING TRAINING")
    print("=" * 60)

    print("\nGenerating multi-location time-series data...")
    gen = HyperlocalDataGenerator(config)
    df = gen.generate_and_save(force=True)
    print(f"  Generated {len(df):,} rows across {df['location_id'].nunique()} locations")
    print(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"  Locations: {df[['location_id','ward','zone']].drop_duplicates().to_string(index=False)}")

    print("\nBuilding features...")
    sample_loc = df[df["location_id"] == 0].sort_values("datetime").head(100)
    df_feat_sample = build_features(sample_loc)
    print(f"  Feature columns ({len(config.feature_columns)}): {config.feature_columns}")
    print(f"  Sample feature shape: {df_feat_sample.shape}")

    print("\n" + "=" * 60)
    print("TRAINING MODELS PER LOCATION")
    print("=" * 60)

    all_results: dict[str, dict[int, dict]] = {}
    models_to_train: list[tuple[str, type]] = [
        ("Naive", NaiveForecast),
        ("SARIMA", ARIMAForecast),
        ("Prophet", ProphetForecast),
        ("LSTM", LSTMHorizonForecast),
    ]

    for name, model_cls in models_to_train:
        print(f"\n--- {name} ---")
        if name == "LSTM":
            m = model_cls(config)
        else:
            m = model_cls(config) if name != "Naive" else model_cls()
        results = train_all_locations(m, df, config)
        all_results[name] = results

    print("\n--- Ensemble ---")
    models_list = []
    config_map = {"SARIMA": ARIMAForecast, "Prophet": ProphetForecast, "LSTM": LSTMHorizonForecast}
    for name in ["SARIMA", "Prophet", "LSTM"]:
        models_list.append(config_map[name](config))
    ensemble = ForecastEnsemble(models_list, config)
    ensemble_results = {}
    for loc_id, grp in df.groupby("location_id"):
        grp = grp.sort_values("datetime").reset_index(drop=True)
        t0 = time.time()
        r = train_location(ensemble, grp, config.feature_columns, config.target_column, config.forecast_horizon)
        elapsed = time.time() - t0
        r["training_time"] = round(elapsed, 2)
        ensemble_results[int(loc_id)] = r
        print(f"  Location {int(loc_id)}: RMSE={r['metrics']['RMSE']}, R2={r['metrics']['R2']} ({elapsed:.1f}s)")
    all_results["Ensemble"] = ensemble_results

    print("\n" + "=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)
    summary = summarize_results(all_results, config.n_locations)
    print(summary.to_string(index=False))

    best_model_name = summary.iloc[0]["Model"]
    print(f"\nBest model: {best_model_name}")

    if best_model_name == "Ensemble":
        best_model = ensemble
    else:
        for name, model_cls in models_to_train:
            if name == best_model_name:
                best_model = model_cls(config) if name != "Naive" else model_cls()
                break

    print("\n" + "=" * 60)
    print("SAVING ARTIFACTS")
    print("=" * 60)
    artifacts_dir = Path(config.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    models_dir = artifacts_dir / "models"
    models_dir.mkdir(exist_ok=True)

    for loc_id in sorted(all_results[best_model_name].keys()):
        if best_model_name == "Ensemble":
            models_sub = [ARIMAForecast(config), ProphetForecast(config), LSTMHorizonForecast(config)]
            m = ForecastEnsemble(models_sub, config)
            loc_df = df[df["location_id"] == loc_id].sort_values("datetime")
            feat_df = build_features(loc_df).dropna().reset_index(drop=True)
            split = int(len(feat_df) * 0.8)
            m.fit(loc_id, feat_df.iloc[:split][config.feature_columns], feat_df.iloc[:split][config.target_column])
            with open(models_dir / f"location_{loc_id}.pkl", "wb") as f:
                pickle.dump(m, f)
            print(f"  [OK] location_{loc_id}.pkl (Ensemble)")
        else:
            for name in models_to_train:
                if name[0] == best_model_name:
                    m = name[1](config) if name[0] != "Naive" else name[1]()
                    loc_df = df[df["location_id"] == loc_id].sort_values("datetime")
                    feat_df = build_features(loc_df).dropna().reset_index(drop=True)
                    split = int(len(feat_df) * 0.8)
                    m.fit(loc_id, feat_df.iloc[:split][config.feature_columns], feat_df.iloc[:split][config.target_column])
                    with open(models_dir / f"location_{loc_id}.pkl", "wb") as f:
                        pickle.dump(m, f)
                    print(f"  [OK] location_{loc_id}.pkl")

    loc_meta = {}
    for _, row in df[["location_id", "ward", "zone", "latitude", "longitude"]].drop_duplicates().iterrows():
        loc_meta[int(row["location_id"])] = {"ward": row["ward"], "zone": row["zone"],
                                              "latitude": float(row["latitude"]), "longitude": float(row["longitude"])}

    metadata = {
        "best_model": best_model_name,
        "trained_models": list(all_results.keys()),
        "feature_columns": config.feature_columns,
        "target_column": config.target_column,
        "forecast_horizon": config.forecast_horizon,
        "n_locations": config.n_locations,
        "location_metadata": loc_meta,
        "model_performance": summary.to_dict(orient="records"),
    }
    with open(artifacts_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  [OK] metadata.json")

    total_size = sum(f.stat().st_size for f in artifacts_dir.rglob("*") if f.is_file())
    print(f"\nArtifacts saved to: {artifacts_dir}")
    print(f"Total size: {total_size / 1024:.1f} KB")
    print("\nTraining complete!")


if __name__ == "__main__":
    main()
