from __future__ import annotations

import warnings
from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

plt.rcParams.update({
    "figure.facecolor": "#0a0a1a",
    "axes.facecolor": "#0f0f2a",
    "axes.labelcolor": "#9ca3af",
    "text.color": "#d1d5db",
    "xtick.color": "#6b7280",
    "ytick.color": "#6b7280",
    "grid.color": "#1f2937",
    "legend.facecolor": "#1a1a3e",
    "legend.edgecolor": "#374151",
})


AQI_COLORS = {0: "#22c55e", 1: "#84cc16", 2: "#eab308", 3: "#f97316", 4: "#ef4444", 5: "#be123c"}

def _aqi_color(v: float) -> str:
    if v <= 50: return AQI_COLORS[0]
    if v <= 100: return AQI_COLORS[1]
    if v <= 200: return AQI_COLORS[2]
    if v <= 300: return AQI_COLORS[3]
    if v <= 400: return AQI_COLORS[4]
    return AQI_COLORS[5]


def plot_correlation_heatmap(df: pd.DataFrame, save_path: Optional[str] = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 12))
    numeric = df.select_dtypes(include=[np.number]).dropna(axis=1, how="all")
    corr = numeric.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, cmap="RdBu_r", center=0, vmin=-1, vmax=1,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8, "label": "Pearson Correlation"},
                ax=ax, annot=False)
    ax.set_title("Feature Correlation Heatmap", fontsize=14, fontweight="bold", pad=20)
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_feature_importance(fi_df: pd.DataFrame, title: str = "Feature Importance", save_path: Optional[str] = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 8))
    top = fi_df.head(20).sort_values("importance")
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(top)))
    ax.barh(range(len(top)), top["importance"].values, color=colors)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["feature"].values, fontsize=9)
    ax.set_xlabel("Importance", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.invert_yaxis()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_learning_curve(train_loss: list, val_loss: list, save_path: Optional[str] = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(train_loss, label="Training Loss", color="#3b82f6", linewidth=2)
    ax.plot(val_loss, label="Validation Loss", color="#f97316", linewidth=2)
    ax.set_xlabel("Epoch", fontsize=11)
    ax.set_ylabel("Loss", fontsize=11)
    ax.set_title("Learning Curves", fontsize=14, fontweight="bold", pad=15)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2)
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_timeline(historical: pd.Series, forecast: Optional[pd.Series] = None,
                  title: str = "AQI Timeline", save_path: Optional[str] = None,
                  conf_lower: Optional[pd.Series] = None,
                  conf_upper: Optional[pd.Series] = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 6))

    if historical is not None:
        ax.plot(historical.index, historical.values, color="#3b82f6", linewidth=2, label="Historical AQI")

    if forecast is not None:
        if conf_lower is not None and conf_upper is not None:
            ax.fill_between(forecast.index, conf_lower, conf_upper, color="#f97316", alpha=0.15, label="Confidence Band")
        ax.plot(forecast.index, forecast.values, color="#ef4444", linewidth=2.5, linestyle="--", label="Predicted AQI")
        if historical is not None:
            ax.axvline(x=historical.index[-1], color=(1.0, 1.0, 1.0, 0.3), linewidth=1, linestyle=":")

    ax.set_xlabel("Time", fontsize=11)
    ax.set_ylabel("AQI", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.legend(fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate()

    for _, sp in ax.spines.items():
        sp.set_visible(False)
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, save_path: Optional[str] = None) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    residuals = np.array(y_true) - np.array(y_pred)
    axes[0].scatter(y_pred, residuals, alpha=0.5, color="#3b82f6", s=20)
    axes[0].axhline(y=0, color=(1.0, 1.0, 1.0, 0.3), linestyle="--", linewidth=1)
    axes[0].set_xlabel("Predicted AQI", fontsize=11)
    axes[0].set_ylabel("Residual", fontsize=11)
    axes[0].set_title("Residual Plot", fontsize=13, fontweight="bold")

    axes[1].hist(residuals, bins=40, color="#6366f1", alpha=0.7, edgecolor="none")
    axes[1].axvline(x=0, color=(1.0, 1.0, 1.0, 0.3), linestyle="--", linewidth=1)
    axes[1].set_xlabel("Residual", fontsize=11)
    axes[1].set_ylabel("Frequency", fontsize=11)
    axes[1].set_title("Error Distribution", fontsize=13, fontweight="bold")

    for ax in axes:
        for sp in ax.spines.values():
            sp.set_visible(False)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_horizon_comparison(results: dict, save_path: Optional[str] = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    models = list(results.keys())
    horizons = list(results[models[0]].keys()) if models else []

    x = np.arange(len(horizons))
    width = 0.8 / len(models) if models else 0.2

    for i, model_name in enumerate(models):
        rmse_vals = [results[model_name][h].get("RMSE", 0) if isinstance(results[model_name][h], dict) else 0 for h in horizons]
        offset = (i - len(models) / 2 + 0.5) * width
        bars = ax.bar(x + offset, rmse_vals, width, label=model_name)

    ax.set_xlabel("Forecast Horizon", fontsize=11)
    ax.set_ylabel("RMSE", fontsize=11)
    ax.set_title("Model Comparison Across Horizons", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h}h" for h in horizons], fontsize=10)
    ax.legend(fontsize=9, loc="upper left")
    for sp in ax.spines.values():
        sp.set_visible(False)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_shap_summary(shap_values: Any, X: pd.DataFrame, save_path: Optional[str] = None) -> plt.Figure:
    try:
        import shap
        fig = plt.figure(figsize=(12, 6))
        shap.summary_plot(shap_values, X, show=False, plot_type="bar", color=plt.cm.Blues(0.6))
        plt.title("SHAP Feature Importance", fontsize=14, fontweight="bold", pad=15)
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig
    except Exception as e:
        print(f"  SHAP plot failed: {e}")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "SHAP plot unavailable", ha="center", va="center", fontsize=12, color="gray")
        return fig


def plot_partial_dependence(model, X: pd.DataFrame, feature: str, save_path: Optional[str] = None) -> plt.Figure:
    try:
        from sklearn.inspection import PartialDependenceDisplay
        fig, ax = plt.subplots(figsize=(8, 5))
        PartialDependenceDisplay.from_estimator(model, X, [feature], ax=ax, kind="average")
        ax.set_title(f"Partial Dependence: {feature}", fontsize=13, fontweight="bold")
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig
    except Exception as e:
        print(f"  PDP failed: {e}")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "PDP unavailable", ha="center", va="center", fontsize=12, color="gray")
        return fig
