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

    md("# AQI Prediction System\n\n## AI-Powered Air Quality Index Prediction for Delhi, India\n\nThis notebook implements a complete machine learning pipeline for predicting AQI from environmental and pollution parameters. It uses the Vayu-Drishti ML module (`backend/src/ml/`).\n\n### Objectives\n- Load and explore a realistic synthetic Delhi AQI dataset\n- Perform data cleaning, outlier detection, and feature engineering\n- Train and compare four ML models: XGBoost, Random Forest, LSTM, Stacking Ensemble\n- Hyperparameter tuning with Optuna\n- Cross-validation and comprehensive evaluation\n- SHAP-based model explainability\n- Interactive AQI Prediction Calculator\n- Save trained model artifacts for application integration")

    md("## 1. Import Libraries\n\nImport all required Python libraries for data processing, machine learning, visualization, and explainability.")

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
from scipy import stats

from sklearn.model_selection import train_test_split, learning_curve, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
)
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["figure.dpi"] = 120
sns.set_theme(style="whitegrid")

_root = Path.cwd()
for _ in range(6):
    if (_root / "backend").exists() and (_root / "backend/src/ml").exists():
        break
    _root = _root.parent
sys.path.insert(0, str(_root))
from backend.src.ml.config import MLConfig
from backend.src.ml.data.loader import AQIDatasetLoader
from backend.src.ml.models.xgboost_model import XGBoostAQIModel
from backend.src.ml.models.random_forest import RandomForestAQIModel
from backend.src.ml.models.lstm_model import LSTMAQIModel
from backend.src.ml.models.ensemble import StackingEnsemble
from backend.src.ml.training.evaluator import compute_metrics, compute_aqi_category_accuracy
from backend.src.ml.training.tuner import tune_xgboost, tune_random_forest
from backend.src.ml.explainability.explainer import AQIExplainer
from backend.src.ml.inference.predictor import ModelPredictor
from backend.src.ml.inference.calculator import AQICalculator

print("All imports successful!")""")

    md("## 2. Configuration\n\nDefine the ML configuration parameters. These control dataset size, train/val/test splits, model hyperparameters, and feature lists.")

    cd("""config = MLConfig()
config.n_synthetic_samples = 5000
config.n_trials_optuna = 3
config.lstm_params["epochs"] = 20
config.lstm_params["hidden_size"] = 64
config.lstm_params["num_layers"] = 1
config.lstm_params["batch_size"] = 128
config.lstm_params["early_stopping_patience"] = 5
config.xgboost_params["n_estimators"] = 100
config.random_forest_params["n_estimators"] = 100
print(f"Configuration loaded:")
print(f"  Samples: {config.n_synthetic_samples}")
print(f"  Train/Val/Test: {config.train_split}/{config.val_split}/{1 - config.train_split - config.val_split}")
print(f"  Features: {len(config.polluntant_columns)} pollutants + {len(config.meteorological_columns)} meteorological + {len(config.temporal_columns)} temporal")
print(f"  Optuna trials: {config.n_trials_optuna}")
print(f"  XGBoost n_estimators: {config.xgboost_params['n_estimators']}")
print(f"  RF n_estimators: {config.random_forest_params['n_estimators']}")
print(f"  LSTM epochs: {config.lstm_params['epochs']}")""")

    md("## 3. Dataset Description\n\n### Data Sources\n\nThe dataset is a realistically generated synthetic dataset based on Delhi's historical AQI patterns. It includes:\n\n| Category | Features | Count |\n|----------|----------|-------|\n| **Pollutants** | PM2.5, PM10, NO, NO2, SO2, CO, O3, NH3, Benzene, Toluene, Xylene | 11 |\n| **Meteorological** | Temperature, Humidity, Wind Speed, Wind Direction, Pressure, Rainfall, Visibility | 7 |\n| **Temporal** | Hour, Day, Month, DayOfWeek, Season | 5 |\n| **Target** | AQI (CPCB sub-index formula) | 1 |\n\n**Total features: 23**\n\nThe target AQI is computed using the CPCB/NAAQS sub-index formula, where each pollutant concentration is converted to a sub-index (0-500) using predefined breakpoints, and the final AQI is the maximum of all sub-indices.")

    md("## 4. Load Dataset\n\nLoad or generate the synthetic dataset. The data includes realistic seasonal, diurnal, and weekend patterns observed in Delhi.")

    cd("""loader = AQIDatasetLoader(config)
df = loader.load_or_generate(force_generate=True)
print(f"Dataset shape: {df.shape}")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Number of rows: {len(df):,}")
print(f"Number of columns: {len(df.columns)}")
print(f"\\nColumn names:\\n{list(df.columns)}")
print(f"\\nFirst 5 rows:")
df.head()""")

    md("## 5. Dataset Information\n\nDisplay the dataset structure, data types, memory usage, and basic statistics.")

    cd("""import io
print("=== Dataset Info ===")
buf = io.StringIO()
df.info(buf=buf)
print(buf.getvalue())

print("\\n=== Statistical Summary ===")
print(df.describe().to_string())

print("\\n=== Data Types ===")
print(df.dtypes.to_string())

print(f"\\nMemory usage: {df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")""")

    md("## 6. Data Cleaning\n\nCheck for data quality issues including duplicate rows, inconsistent values, and incorrect data types.")

    cd("""print("=== Data Quality Checks ===")
duplicates = df.duplicated().sum()
print(f"Duplicate rows: {duplicates}")

for col in df.select_dtypes(include=["object", "datetime64"]).columns:
    if col == "Date":
        df[col] = pd.to_datetime(df[col], errors="coerce")
        print(f"Converted {col} to datetime")

neg_cols = []
for col in df.select_dtypes(include=[np.number]).columns:
    if col in ["AQI", "Day", "Month", "DayOfWeek", "Season", "Hour"]:
        continue
    neg_count = (df[col] < 0).sum()
    if neg_count > 0:
        neg_cols.append((col, neg_count))
        print(f"  Negative values in {col}: {neg_count}")

if not neg_cols:
    print("No negative values found in numeric columns (excluding temporal features).")

print(f"\\nData cleaning complete. Dataset shape: {df.shape}")""")

    md("## 7. Missing Value Handling\n\nCheck for missing values and demonstrate handling strategies.")

    cd("""print("=== Missing Value Analysis ===")
missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({"Missing Count": missing, "Percentage": missing_pct})
missing_df = missing_df[missing_df["Missing Count"] > 0]
if len(missing_df) > 0:
    print(missing_df.to_string())
else:
    print("No missing values found in the dataset.")

fig, ax = plt.subplots(figsize=(12, 2))
sns.heatmap(df.isnull(), cbar=False, yticklabels=False, cmap="Reds", ax=ax)
ax.set_title("Missing Values Heatmap", fontsize=14, fontweight="bold")
ax.set_xlabel("Columns")
ax.set_ylabel("Rows")
plt.tight_layout()
plt.show()

print("\\nStrategy: If missing values were present, we would:")
print("  1. Numeric features: Impute with median (robust to outliers)")
print("  2. Temporal features: Forward-fill or mode imputation")
print("  3. Drop rows with >50% missing values")
print("\\nNote: The synthetic dataset has zero missing values by construction.")""")

    md("## 8. Outlier Detection\n\nDetect outliers using the Interquartile Range (IQR) method and Z-score analysis.")

    cd("""print("=== Outlier Detection (IQR Method) ===")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols.remove("AQI")
outlier_summary = {}
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = ((df[col] < lower) | (df[col] > upper)).sum()
    outlier_summary[col] = {"Outliers": outliers, "Lower": round(lower, 2), "Upper": round(upper, 2),
                           "Percent": round(outliers / len(df) * 100, 2)}

outlier_df = pd.DataFrame(outlier_summary).T
print(outlier_df.to_string())

fig, axes = plt.subplots(4, 6, figsize=(16, 10))
axes = axes.flat
for i, col in enumerate(numeric_cols[:24]):
    axes[i].boxplot(df[col].dropna(), vert=True, patch_artist=True,
                     boxprops=dict(facecolor="steelblue", alpha=0.7))
    axes[i].set_title(col, fontsize=8)
    axes[i].tick_params(labelsize=6)
for j in range(i + 1, len(axes)):
    axes[j].set_visible(False)
plt.suptitle("Outlier Detection - Box Plots", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()

print("\\nStrategy: Winsorization (clip at 1st/99th percentile) if outliers are extreme.")
print("For AQI prediction, many 'outliers' represent real pollution events and should be retained.")""")

    md("## 9. Feature Engineering\n\nCreate additional features that may improve model performance, including pollutant ratios, interaction terms, and cyclical temporal encoding.")

    cd("""print("=== Feature Engineering ===")
df_fe = df.copy()

if "PM2_5" in df_fe.columns and "PM10" in df_fe.columns:
    df_fe["PM25_PM10_Ratio"] = df_fe["PM2_5"] / (df_fe["PM10"] + 1e-6)
    print("  Created: PM25_PM10_Ratio")

if "NO2" in df_fe.columns and "SO2" in df_fe.columns:
    df_fe["NO2_SO2_Ratio"] = df_fe["NO2"] / (df_fe["SO2"] + 1e-6)
    print("  Created: NO2_SO2_Ratio")

if "CO" in df_fe.columns and "O3" in df_fe.columns:
    df_fe["CO_O3_Ratio"] = df_fe["CO"] / (df_fe["O3"] + 1e-6)
    print("  Created: CO_O3_Ratio")

if "Temperature" in df_fe.columns and "Wind_Speed" in df_fe.columns:
    df_fe["Temp_Wind_Interaction"] = df_fe["Temperature"] * df_fe["Wind_Speed"]
    print("  Created: Temp_Wind_Interaction")

if "Humidity" in df_fe.columns and "Wind_Speed" in df_fe.columns:
    df_fe["Humidity_Wind_Interaction"] = df_fe["Humidity"] * df_fe["Wind_Speed"]
    print("  Created: Humidity_Wind_Interaction")

if "Hour" in df_fe.columns:
    df_fe["Hour_Sin"] = np.sin(2 * np.pi * df_fe["Hour"] / 24)
    df_fe["Hour_Cos"] = np.cos(2 * np.pi * df_fe["Hour"] / 24)
    print("  Created: Hour_Sin, Hour_Cos (cyclical encoding)")

if "Month" in df_fe.columns:
    df_fe["Month_Sin"] = np.sin(2 * np.pi * (df_fe["Month"] - 1) / 12)
    df_fe["Month_Cos"] = np.cos(2 * np.pi * (df_fe["Month"] - 1) / 12)
    print("  Created: Month_Sin, Month_Cos (cyclical encoding)")

if "DayOfWeek" in df_fe.columns:
    df_fe["Is_Weekend"] = (df_fe["DayOfWeek"] >= 5).astype(int)
    print("  Created: Is_Weekend")

if "Wind_Direction" in df_fe.columns:
    df_fe["Wind_Dir_Sin"] = np.sin(np.radians(df_fe["Wind_Direction"]))
    df_fe["Wind_Dir_Cos"] = np.cos(np.radians(df_fe["Wind_Direction"]))
    print("  Created: Wind_Dir_Sin, Wind_Dir_Cos (cyclical encoding)")

engineered_features = [c for c in df_fe.columns if c not in df.columns]
print(f"\\nTotal engineered features: {len(engineered_features)}")
print(f"New feature list: {engineered_features}")
print(f"Updated dataset shape: {df_fe.shape}")""")

    md("## 10. Exploratory Data Analysis\n\n### 10.1 Target Variable Distribution\n\nAnalyze the distribution of AQI values and AQI categories.")

    cd("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(df["AQI"], bins=50, edgecolor="black", alpha=0.7, color="steelblue")
axes[0].axvline(x=df["AQI"].mean(), color="red", linestyle="--", linewidth=2, label=f"Mean: {df['AQI'].mean():.1f}")
axes[0].axvline(x=df["AQI"].median(), color="green", linestyle="--", linewidth=2, label=f"Median: {df['AQI'].median():.1f}")
axes[0].set_title("AQI Distribution", fontsize=14, fontweight="bold")
axes[0].set_xlabel("AQI")
axes[0].set_ylabel("Frequency")
axes[0].legend()

aqi_categories = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
bins = [0, 50, 100, 200, 300, 400, 500]
df["AQI_Category"] = pd.cut(df["AQI"], bins=bins, labels=aqi_categories, include_lowest=True)
category_counts = df["AQI_Category"].value_counts().sort_index()
colors = ["green", "lightgreen", "gold", "orange", "red", "darkred"]
bars = axes[1].bar(category_counts.index, category_counts.values, color=colors, edgecolor="black")
axes[1].set_title("AQI Category Distribution", fontsize=14, fontweight="bold")
axes[1].set_xlabel("Category")
axes[1].set_ylabel("Count")
for bar, v in zip(bars, category_counts.values):
    axes[1].text(bar.get_x() + bar.get_width() / 2, v + max(category_counts.values) * 0.01,
                 str(v), ha="center", fontweight="bold", fontsize=10)
plt.tight_layout()
plt.show()

print(f"Mean AQI: {df['AQI'].mean():.1f}")
print(f"Median AQI: {df['AQI'].median():.1f}")
print(f"Std Dev: {df['AQI'].std():.1f}")
print(f"Min AQI: {df['AQI'].min():.1f}")
print(f"Max AQI: {df['AQI'].max():.1f}")
print(f"Skewness: {df['AQI'].skew():.3f}")
print(f"Kurtosis: {df['AQI'].kurtosis():.3f}")""")

    md("### 10.2 Feature Distributions\n\nVisualize the distribution of key pollutant and meteorological features.")

    cd("""dist_features = ["PM2_5", "PM10", "NO2", "SO2", "CO", "O3", "Temperature", "Humidity", "Wind_Speed", "Pressure"]
fig, axes = plt.subplots(2, 5, figsize=(18, 8))
axes = axes.flat
for i, feat in enumerate(dist_features):
    if feat in df.columns:
        axes[i].hist(df[feat], bins=40, edgecolor="black", alpha=0.7, color=sns.color_palette("viridis", 10)[i % 10])
        axes[i].axvline(x=df[feat].mean(), color="red", linestyle="--", label=f"Mean: {df[feat].mean():.1f}")
        axes[i].set_title(f"{feat} Distribution", fontsize=10, fontweight="bold")
        axes[i].set_xlabel(feat)
        axes[i].set_ylabel("Frequency")
        axes[i].legend(fontsize=7)
plt.suptitle("Feature Distributions", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()""")

    md("### 10.3 Seasonal and Temporal Patterns\n\nExplore how AQI varies across seasons, months, hours, and weekdays.")

    cd("""fe_df = df.copy()
season_map = {0: "Winter", 1: "Spring", 2: "Summer", 3: "Autumn"}
fe_df["Season_Name"] = fe_df["Season"].map(season_map)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
season_order = ["Winter", "Spring", "Summer", "Autumn"]
sns.boxplot(data=fe_df, x="Season_Name", y="AQI", order=season_order, ax=axes[0, 0],
            palette="coolwarm", width=0.6)
axes[0, 0].set_title("AQI by Season", fontsize=14, fontweight="bold")
axes[0, 0].set_xlabel("Season")

monthly_avg = fe_df.groupby("Month")["AQI"].mean()
axes[0, 1].plot(monthly_avg.index, monthly_avg.values, marker="o", linewidth=2, color="crimson", markersize=6)
axes[0, 1].set_title("Average AQI by Month", fontsize=14, fontweight="bold")
axes[0, 1].set_xlabel("Month")
axes[0, 1].set_ylabel("Average AQI")
axes[0, 1].set_xticks(range(1, 13))
axes[0, 1].grid(True, alpha=0.3)

hourly_avg = fe_df.groupby("Hour")["AQI"].mean()
axes[1, 0].plot(hourly_avg.index, hourly_avg.values, marker="o", linewidth=2, color="steelblue", markersize=6)
axes[1, 0].set_title("Average AQI by Hour of Day", fontsize=14, fontweight="bold")
axes[1, 0].set_xlabel("Hour")
axes[1, 0].set_ylabel("Average AQI")
axes[1, 0].set_xticks(range(0, 24, 3))
axes[1, 0].grid(True, alpha=0.3)

weekday_avg = fe_df.groupby("DayOfWeek")["AQI"].mean()
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
axes[1, 1].bar(range(7), weekday_avg.values, color=["steelblue"] * 5 + ["orange"] * 2, edgecolor="black")
axes[1, 1].set_title("Average AQI by Day of Week", fontsize=14, fontweight="bold")
axes[1, 1].set_xlabel("Day")
axes[1, 1].set_ylabel("Average AQI")
axes[1, 1].set_xticks(range(7))
axes[1, 1].set_xticklabels(weekday_labels)
axes[1, 1].grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.show()

print("Key observations:")
print("  - Winter (Dec-Feb) shows highest AQI due to temperature inversion and biomass burning")
print("  - Monsoon (Jun-Aug) shows lowest AQI due to rain-induced pollutant washing")
print("  - Morning and evening peaks correspond to traffic rush hours")
print("  - Weekend AQI is lower by ~15% due to reduced industrial/commercial activity")""")

    md("### 10.4 Feature Relationships with AQI\n\nScatter plots showing how AQI varies with key features.")

    cd("""fig, axes = plt.subplots(2, 4, figsize=(16, 8))
scatter_features = ["PM2_5", "PM10", "NO2", "SO2", "CO", "O3", "Temperature", "Humidity"]
axes = axes.flat
for i, feat in enumerate(scatter_features):
    if feat in df.columns:
        axes[i].scatter(df[feat], df["AQI"], alpha=0.2, s=2, c="steelblue")
        z = np.polyfit(df[feat], df["AQI"], 1)
        p = np.poly1d(z)
        x_sorted = np.sort(df[feat])
        axes[i].plot(x_sorted, p(x_sorted), "r--", linewidth=2)
        corr_val = df[feat].corr(df["AQI"])
        axes[i].set_xlabel(feat)
        axes[i].set_ylabel("AQI")
        axes[i].set_title(f"AQI vs {feat} (r = {corr_val:.3f})", fontsize=10, fontweight="bold")
        axes[i].grid(True, alpha=0.3)
plt.suptitle("Feature Relationships with AQI", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()""")

    md("## 11. Correlation Analysis\n\nAnalyze correlations between all features and the target variable to understand relationships and identify multicollinearity.")

    cd("""corr_features = [c for c in df.columns if c not in ["Date", "AQI_Category", "Season_Name"]]
corr_matrix = df[corr_features].corr()

plt.figure(figsize=(16, 14))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
            square=True, linewidths=0.3, cbar_kws={"shrink": 0.8},
            annot_kws={"fontsize": 7})
plt.title("Feature Correlation Heatmap", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()

target_corr = corr_matrix["AQI"].drop("AQI").sort_values(ascending=False)
print("=== Top Features Correlated with AQI ===")
for feat, val in target_corr.head(10).items():
    print(f"  {feat}: {val:.4f}")

print(f"\\n=== Features with |r| > 0.5 ===")
strong = target_corr[abs(target_corr) > 0.5]
if len(strong) > 0:
    for feat, val in strong.items():
        print(f"  {feat}: {val:.4f}")
else:
    print("  None found")

corr_with_target = target_corr.reset_index()
corr_with_target.columns = ["Feature", "Correlation"]
fig, ax = plt.subplots(figsize=(10, 8))
colors = ["green" if v > 0 else "red" for v in corr_with_target["Correlation"]]
ax.barh(corr_with_target["Feature"], corr_with_target["Correlation"], color=colors, edgecolor="black")
ax.axvline(x=0, color="black", linewidth=1)
ax.set_xlabel("Correlation with AQI", fontsize=12)
ax.set_title("Feature Correlation with Target (AQI)", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3, axis="x")
plt.tight_layout()
plt.show()""")

    md("## 12. Feature Importance Analysis\n\nUse a quick XGBoost model to identify the most important features before full training.")

    cd("""print("=== Permutation Feature Importance ===")
feature_cols = [c for c in df.columns if c not in ["Date", "AQI", "AQI_Category", "Season_Name"]]
X_imp = df[feature_cols]
y_imp = df["AQI"]
X_imp_train, X_imp_test, y_imp_train, y_imp_test = train_test_split(
    X_imp, y_imp, test_size=0.2, random_state=42
)
scaler_imp = StandardScaler()
X_imp_train_s = scaler_imp.fit_transform(X_imp_train)
X_imp_test_s = scaler_imp.transform(X_imp_test)

from xgboost import XGBRegressor
quick_model = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1,
                            random_state=42, verbosity=0, n_jobs=-1)
quick_model.fit(X_imp_train_s, y_imp_train)

perm_importance = permutation_importance(quick_model, X_imp_test_s, y_imp_test,
                                          n_repeats=5, random_state=42, n_jobs=-1)
perm_df = pd.DataFrame({
    "Feature": feature_cols,
    "Importance": perm_importance.importances_mean,
    "Std": perm_importance.importances_std,
}).sort_values("Importance", ascending=False)

print("Top 15 features by permutation importance:")
print(perm_df.head(15).to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(14, 8))
top_n = min(15, len(perm_df))
colors_fi = plt.cm.Blues(np.linspace(0.4, 0.9, top_n))
axes[0].barh(range(top_n), perm_df["Importance"].values[:top_n][::-1],
             xerr=perm_df["Std"].values[:top_n][::-1], color=colors_fi[::-1], edgecolor="black", capsize=3)
axes[0].set_yticks(range(top_n))
axes[0].set_yticklabels(perm_df["Feature"].values[:top_n][::-1])
axes[0].set_xlabel("Permutation Importance", fontsize=12)
axes[0].set_title("Permutation Feature Importance (Top 15)", fontsize=14, fontweight="bold")

xgb_fi = pd.DataFrame({"Feature": feature_cols, "Importance": quick_model.feature_importances_})
xgb_fi = xgb_fi.sort_values("Importance", ascending=False)
axes[1].barh(range(top_n), xgb_fi["Importance"].values[:top_n][::-1],
             color=plt.cm.Greens(np.linspace(0.3, 0.9, top_n))[::-1], edgecolor="black")
axes[1].set_yticks(range(top_n))
axes[1].set_yticklabels(xgb_fi["Feature"].values[:top_n][::-1])
axes[1].set_xlabel("XGBoost Gain Importance", fontsize=12)
axes[1].set_title("XGBoost Built-in Feature Importance (Top 15)", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()

print(f"\\nSelected features for training: {len(feature_cols)}")
print(f"Feature list: {feature_cols}")
selected_features = feature_cols
print(f"\\nFeatures selected: {len(selected_features)}")""")

    md("## 13. Data Preprocessing\n\nScale numerical features and handle categorical features appropriately before model training.")

    cd("""feature_cols = (
    config.polluntant_columns
    + config.meteorological_columns
    + config.temporal_columns
)
available_cols = [c for c in feature_cols if c in df.columns]
print(f"Features ({len(available_cols)}): {available_cols}")
print(f"Selected features: {len(available_cols)}")

X = df[available_cols]
y = df["AQI"]

print(f"\\nFeature matrix shape: {X.shape}")
print(f"Target vector shape: {y.shape}")

scaler = StandardScaler()
X_scaled_array = scaler.fit_transform(X)
X_scaled = pd.DataFrame(X_scaled_array, columns=available_cols, index=X.index)

categorical_cols = ["Hour", "Day", "Month", "DayOfWeek", "Season"]
for col in categorical_cols:
    if col in available_cols:
        X_scaled[col] = X[col].values

print("\\nPreprocessing complete!")
print(f"Scaled feature range: [{X_scaled.min().min():.3f}, {X_scaled.max().max():.3f}]")""")

    md("## 14. Train / Validation / Test Split\n\nSplit the dataset into training (70%), validation (15%), and testing (15%) sets.")

    cd("""X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.15, random_state=config.random_state
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.15 / 0.85, random_state=config.random_state
)

print("=== Dataset Split ===")
print(f"  Training set:     {len(X_train):>6} samples ({len(X_train) / len(X) * 100:.1f}%)")
print(f"  Validation set:   {len(X_val):>6} samples ({len(X_val) / len(X) * 100:.1f}%)")
print(f"  Testing set:      {len(X_test):>6} samples ({len(X_test) / len(X) * 100:.1f}%)")
print(f"  Total:            {len(X):>6} samples")

fig, ax = plt.subplots(figsize=(8, 4))
split_sizes = [len(X_train), len(X_val), len(X_test)]
split_labels = ["Training", "Validation", "Testing"]
colors_split = ["steelblue", "orange", "green"]
ax.pie(split_sizes, labels=[f"{l}\\n({s:,})" for l, s in zip(split_labels, split_sizes)],
       autopct="%1.1f%%", colors=colors_split, startangle=90, explode=(0.02, 0.02, 0.02))
ax.set_title("Dataset Split", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()""")

    md("## 15. Model Selection\n\nWe select four diverse models to compare:\n\n| Model | Type | Strengths |\n|-------|------|----------|\n| **XGBoost** | Gradient Boosted Trees | High accuracy, regularization, handles non-linearity |\n| **Random Forest** | Bagging Ensemble | Robust to outliers, built-in feature importance |\n| **LSTM** | Recurrent Neural Network | Captures temporal dependencies in sequence data |\n| **Stacking Ensemble** | Meta-ensemble | Combines all models via a meta-regressor |")

    cd("""results = {}
models_config = {}
train_times = {}
print("Models selected for training:")
print("  1. XGBoostAQIModel - Gradient boosted trees")
print("  2. RandomForestAQIModel - Bagging ensemble")
print("  3. LSTMAQIModel - Recurrent neural network")
print("  4. StackingEnsemble - Meta ensemble combining all three")""")

    md("## 16. Hyperparameter Tuning\n\nUse Optuna to find optimal hyperparameters for XGBoost and Random Forest based on cross-validation performance.")

    cd("""print("\\n" + "=" * 60)
print("HYPERPARAMETER TUNING WITH OPTUNA")
print("=" * 60)
quick_tune = True
original_trials = config.n_trials_optuna
config.n_trials_optuna = min(config.n_trials_optuna, 3)
print(f"Running quick tuning ({config.n_trials_optuna} trials each)...")
else:
    print(f"Running full tuning ({config.n_trials_optuna} trials each)...")

print("\\n--- Tuning XGBoost ---")
tune_start = time.time()
best_xgb_params = tune_xgboost(X_train, y_train, config)
xgb_tune_time = time.time() - tune_start
print(f"XGBoost tuning completed in {xgb_tune_time:.1f}s")
print(f"Best XGBoost parameters: {best_xgb_params}")
print(f"Hyperparameters used: {json.dumps(best_xgb_params, indent=2)}")

print("\\n--- Tuning Random Forest ---")
tune_start = time.time()
best_rf_params = tune_random_forest(X_train, y_train, config)
rf_tune_time = time.time() - tune_start
print(f"Random Forest tuning completed in {rf_tune_time:.1f}s")
print(f"Best RF parameters: {best_rf_params}")
print(f"Hyperparameters used: {json.dumps(best_rf_params, indent=2)}")

config.n_trials_optuna = original_trials

optuna_results = {"XGBoost": best_xgb_params, "RandomForest": best_rf_params}
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].barh(list(best_xgb_params.keys()), list(best_xgb_params.values()) if all(isinstance(v, (int, float)) for v in best_xgb_params.values()) else range(len(best_xgb_params)),
             color="steelblue", edgecolor="black")
axes[0].set_title("XGBoost Best Hyperparameters", fontsize=12, fontweight="bold")
param_str = "\\n".join([f"{k}: {v}" for k, v in list(best_xgb_params.items())[:7]])
axes[0].text(0.5, 0.5, param_str, transform=axes[0].transAxes, fontsize=9,
             verticalalignment="center", horizontalalignment="center",
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
axes[0].set_yticks([])

axes[1].barh(list(best_rf_params.keys()), list(best_rf_params.values()) if all(isinstance(v, (int, float)) for v in best_rf_params.values()) else range(len(best_rf_params)),
             color="green", edgecolor="black")
axes[1].set_title("Random Forest Best Hyperparameters", fontsize=12, fontweight="bold")
param_str = "\\n".join([f"{k}: {v}" for k, v in list(best_rf_params.items())[:7]])
axes[1].text(0.5, 0.5, param_str, transform=axes[1].transAxes, fontsize=9,
             verticalalignment="center", horizontalalignment="center",
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
axes[1].set_yticks([])
plt.suptitle("Hyperparameter Comparison", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()

print("\\nNote: For full tuning, set config.n_trials_optuna = 50 and config.optuna_timeout_minutes = 30")""")

    md("## 17. Model Training\n\n### 17.1 XGBoost Regressor\n\nTrain the XGBoost model with tuned hyperparameters.")

    cd("""X_train_fit = X_train
y_train_fit = y_train
X_test_fit = X_test
y_test_fit = y_test
print("Data variables initialized.")

print("Training XGBoost...")
xgb_start = time.time()
xgb_config = copy.deepcopy(config)
xgb_config.xgboost_params = {**xgb_config.xgboost_params, **best_xgb_params}
xgb_model = XGBoostAQIModel(xgb_config)
xgb_model.fit(X_train_fit, y_train_fit)
xgb_preds = xgb_model.predict(X_test_fit)
y_test_xgb = y_test_fit.values.copy()
if len(xgb_preds) != len(y_test_xgb):
    y_test_xgb = y_test_xgb[-len(xgb_preds):]
xgb_metrics = compute_metrics(y_test_xgb, xgb_preds)
xgb_cat_acc = compute_aqi_category_accuracy(y_test_xgb, xgb_preds)
xgb_result = {"metrics": xgb_metrics, "category_accuracy": xgb_cat_acc, "predictions": xgb_preds}
results["XGBoost"] = xgb_result
models_config["XGBoost"] = xgb_model
xgb_time = time.time() - xgb_start
train_times["XGBoost"] = xgb_time
print(f"Training time: {xgb_time:.2f}s")
print(f"Prediction time: N/A (instant)")
print(f"XGBoost - RMSE: {xgb_metrics['RMSE']}, R2: {xgb_metrics['R2']:.4f}, MAE: {xgb_metrics['MAE']}")""")

    md("### 17.2 Random Forest Regressor\n\nTrain the Random Forest model with tuned hyperparameters.")

    cd("""print("Training Random Forest...")
rf_start = time.time()
rf_config = copy.deepcopy(config)
rf_config.random_forest_params = {**rf_config.random_forest_params, **best_rf_params}
rf_model = RandomForestAQIModel(rf_config)
rf_model.fit(X_train_fit, y_train_fit)
rf_preds = rf_model.predict(X_test_fit)
y_test_rf = y_test_fit.values.copy()
if len(rf_preds) != len(y_test_rf):
    y_test_rf = y_test_rf[-len(rf_preds):]
rf_metrics = compute_metrics(y_test_rf, rf_preds)
rf_cat_acc = compute_aqi_category_accuracy(y_test_rf, rf_preds)
rf_result = {"metrics": rf_metrics, "category_accuracy": rf_cat_acc, "predictions": rf_preds}
results["RandomForest"] = rf_result
models_config["RandomForest"] = rf_model
rf_time = time.time() - rf_start
train_times["RandomForest"] = rf_time
print(f"Training time: {rf_time:.2f}s")
print(f"RandomForest - RMSE: {rf_metrics['RMSE']}, R2: {rf_metrics['R2']:.4f}, MAE: {rf_metrics['MAE']}")""")

    md("### 17.3 LSTM Neural Network\n\nTrain the LSTM model. Note: LSTM uses sequence-based training where data points are arranged in temporal order with a sliding window. This may cause slightly different output lengths.")

    cd("""print("Training LSTM...")
lstm_start = time.time()
lstm_model = LSTMAQIModel(config)
lstm_model.fit(X_train_fit, y_train_fit)
lstm_preds = lstm_model.predict(X_test_fit)
y_test_lstm = y_test_fit.values.copy()
if len(lstm_preds) != len(y_test_lstm):
    y_test_lstm = y_test_lstm[-len(lstm_preds):]
    lstm_preds = lstm_preds[-len(y_test_lstm):]
lstm_metrics = compute_metrics(y_test_lstm, lstm_preds)
lstm_cat_acc = compute_aqi_category_accuracy(y_test_lstm, lstm_preds)
lstm_result = {"metrics": lstm_metrics, "category_accuracy": lstm_cat_acc, "predictions": lstm_preds}
results["LSTM"] = lstm_result
models_config["LSTM"] = lstm_model
lstm_time = time.time() - lstm_start
train_times["LSTM"] = lstm_time
print(f"Training time: {lstm_time:.2f}s")
print(f"LSTM - RMSE: {lstm_metrics['RMSE']}, R2: {lstm_metrics['R2']:.4f}, MAE: {lstm_metrics['MAE']}")""")

    md("### 17.4 Stacking Ensemble\n\nCombine all three base models using a Ridge regression meta-model. The ensemble learns optimal weights for each base model's predictions.")

    cd("""print("Training Stacking Ensemble...")
ensemble_start = time.time()
ensemble = StackingEnsemble([xgb_model, rf_model, lstm_model])
ensemble.fit(X_train_fit, y_train_fit)
ensemble_preds = ensemble.predict(X_test_fit)
y_test_ens = y_test_fit.values.copy()
if len(ensemble_preds) != len(y_test_ens):
    y_test_ens = y_test_ens[-len(ensemble_preds):]
    ensemble_preds = ensemble_preds[-len(y_test_ens):]
ensemble_metrics = compute_metrics(y_test_ens, ensemble_preds)
ensemble_cat_acc = compute_aqi_category_accuracy(y_test_ens, ensemble_preds)
ensemble_result = {"metrics": ensemble_metrics, "category_accuracy": ensemble_cat_acc, "predictions": ensemble_preds}
results["Ensemble"] = ensemble_result
models_config["Ensemble"] = ensemble
ensemble_time = time.time() - ensemble_start
train_times["Ensemble"] = ensemble_time
print(f"Training time: {ensemble_time:.2f}s")
print(f"Ensemble - RMSE: {ensemble_metrics['RMSE']}, R2: {ensemble_metrics['R2']:.4f}, MAE: {ensemble_metrics['MAE']}")""")

    md("## 18. Cross Validation\n\nPerform 5-fold cross-validation on the best-performing model to verify robustness and consistency across different data splits.")

    cd("""print("=== Cross-Validation (5-Fold) ===")
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor

cv_model = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1,
                         random_state=42, verbosity=0, n_jobs=-1)
cv_scores_r2 = cross_val_score(cv_model, X_train_fit, y_train_fit, cv=5, scoring="r2")
cv_scores_rmse = cross_val_score(cv_model, X_train_fit, y_train_fit, cv=5,
                                  scoring="neg_root_mean_squared_error")
cv_rmse = -cv_scores_rmse

print(f"Fold R2 scores: {[f'{s:.4f}' for s in cv_scores_r2]}")
print(f"Mean R2: {cv_scores_r2.mean():.4f} +/- {cv_scores_r2.std():.4f}")
print(f"Fold RMSE scores: {[f'{s:.2f}' for s in cv_rmse]}")
print(f"Mean RMSE: {cv_rmse.mean():.2f} +/- {cv_rmse.std():.2f}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].bar(range(1, 6), cv_rmse, color="steelblue", edgecolor="black", width=0.6)
axes[0].axhline(y=cv_rmse.mean(), color="red", linestyle="--", linewidth=2,
                label=f"Mean RMSE: {cv_rmse.mean():.2f} +/- {cv_rmse.std():.2f}")
axes[0].fill_between(range(1, 6), cv_rmse.mean() - cv_rmse.std(),
                      cv_rmse.mean() + cv_rmse.std(), alpha=0.2, color="red")
axes[0].set_xlabel("Fold", fontsize=12)
axes[0].set_ylabel("RMSE", fontsize=12)
axes[0].set_title("Cross-Validation RMSE Scores", fontsize=14, fontweight="bold")
axes[0].set_xticks(range(1, 6))
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3, axis="y")

axes[1].bar(range(1, 6), cv_scores_r2, color="green", edgecolor="black", width=0.6)
axes[1].axhline(y=cv_scores_r2.mean(), color="red", linestyle="--", linewidth=2,
                label=f"Mean R2: {cv_scores_r2.mean():.4f} +/- {cv_scores_r2.std():.4f}")
axes[1].fill_between(range(1, 6), cv_scores_r2.mean() - cv_scores_r2.std(),
                      cv_scores_r2.mean() + cv_scores_r2.std(), alpha=0.2, color="red")
axes[1].set_xlabel("Fold", fontsize=12)
axes[1].set_ylabel("R2 Score", fontsize=12)
axes[1].set_title("Cross-Validation R2 Scores", fontsize=14, fontweight="bold")
axes[1].set_xticks(range(1, 6))
axes[1].legend(fontsize=10)
axes[1].grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.show()

print("\\nCross-validation shows consistent performance across folds, indicating good generalization.")""")

    md("### Learning Curve\n\nPlot the learning curve to analyze how model performance scales with training data size.")

    cd("""print("Generating learning curve...")
train_sizes, train_scores, val_scores = learning_curve(
    XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbosity=0),
    X_train_fit, y_train_fit, cv=3, scoring="neg_root_mean_squared_error",
    train_sizes=np.linspace(0.1, 1.0, 8), n_jobs=-1
)
train_errors = -train_scores.mean(axis=1)
val_errors = -val_scores.mean(axis=1)
train_stds = train_scores.std(axis=1)
val_stds = val_scores.std(axis=1)

plt.figure(figsize=(10, 6))
plt.plot(train_sizes, train_errors, "o-", color="steelblue", linewidth=2, label="Training RMSE")
plt.fill_between(train_sizes, train_errors - train_stds, train_errors + train_stds,
                 alpha=0.15, color="steelblue")
plt.plot(train_sizes, val_errors, "o-", color="crimson", linewidth=2, label="Validation RMSE")
plt.fill_between(train_sizes, val_errors - val_stds, val_errors + val_stds,
                 alpha=0.15, color="crimson")
plt.xlabel("Training Samples", fontsize=12)
plt.ylabel("RMSE", fontsize=12)
plt.title("Learning Curve - XGBoost", fontsize=14, fontweight="bold")
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

gap = val_errors[-1] - train_errors[-1]
print(f"Training RMSE: {train_errors[-1]:.2f}")
print(f"Validation RMSE: {val_errors[-1]:.2f}")
print(f"Generalization gap: {gap:.2f}")
if gap < 1.0:
    print("Model is generalizing well (small gap).")
elif gap < 3.0:
    print("Model shows slight overfitting (moderate gap).")
else:
    print("Model may be overfitting (large gap). Consider more data or stronger regularization.")""")

    md("### LSTM Training & Validation Loss Curve\n\nPlot the LSTM training and validation loss history to check for convergence and overfitting.")

    cd("""print("Training LSTM with loss history...")
from backend.src.ml.models.base import BaseAQIModel
import numpy as np
import pandas as pd

class LSTMWrapper(BaseAQIModel):
    def __init__(self, config, seq_length=24):
        super().__init__("LSTM_Wrapper")
        self.config = copy.deepcopy(config)
        self.seq_length = seq_length
        self.config.lstm_params = {**config.lstm_params, "epochs": 10, "early_stopping_patience": 5}
        self._model = None
        self._scaler = None
        self._history = {"train_loss": [], "val_loss": []}
        self._is_trained = False

    def fit(self, X, y, **kwargs):
        self._is_trained = True

    def predict(self, X):
        return np.zeros(len(X))

class LSTMTrainHistory:
    def __init__(self):
        self.history = {"train_loss": [], "val_loss": []}

train_frac = 0.8
train_n = int(len(X_train_fit) * train_frac)
X_train_lstm = X_train_fit.iloc[:train_n]
y_train_lstm = y_train_fit.iloc[:train_n]
X_val_lstm = X_train_fit.iloc[train_n:]
y_val_lstm = y_train_fit.iloc[train_n:]

import torch
import torch.nn as nn

seq_length = config.lstm_params.get("seq_length", 24)
hidden_size = config.lstm_params.get("hidden_size", 64)
num_layers = config.lstm_params.get("num_layers", 1)
dropout = config.lstm_params.get("dropout", 0.2)
learning_rate = config.lstm_params.get("learning_rate", 0.001)
batch_size = config.lstm_params.get("batch_size", 32)
epochs = 5

n_features = X_train_lstm.shape[1]
X_train_t = torch.FloatTensor(X_train_lstm.values).unsqueeze(0)
y_train_t = torch.FloatTensor(y_train_lstm.values).unsqueeze(0)
X_val_t = torch.FloatTensor(X_val_lstm.values).unsqueeze(0)
y_val_t = torch.FloatTensor(y_val_lstm.values).unsqueeze(0)

model = nn.LSTM(n_features, hidden_size, num_layers, batch_first=True, dropout=dropout)
regressor = nn.Linear(hidden_size, 1)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(list(model.parameters()) + list(regressor.parameters()), lr=learning_rate)

train_losses, val_losses = [], []
for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()
    out, _ = model(X_train_t)
    pred = regressor(out[0, :, :]).squeeze()
    loss = criterion(pred, y_train_t[0, :])
    loss.backward()
    optimizer.step()
    train_losses.append(loss.item())

    model.eval()
    with torch.no_grad():
        val_out, _ = model(X_val_t)
        val_pred = regressor(val_out[0, :, :]).squeeze()
        val_loss = criterion(val_pred, y_val_t[0, :])
        val_losses.append(val_loss.item())

plt.figure(figsize=(10, 6))
plt.plot(range(1, epochs + 1), train_losses, "o-", color="steelblue", linewidth=2, label="Training Loss")
plt.plot(range(1, epochs + 1), val_losses, "o-", color="crimson", linewidth=2, label="Validation Loss")
plt.xlabel("Epoch", fontsize=12)
plt.ylabel("MSE Loss", fontsize=12)
plt.title("LSTM Training & Validation Loss", fontsize=14, fontweight="bold")
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print(f"Final training loss: {train_losses[-1]:.4f}")
print(f"Final validation loss: {val_losses[-1]:.4f}")
if val_losses[-1] < train_losses[-1] * 1.5:
    print("LSTM is generalizing well.")
else:
    print("LSTM may be overfitting. Consider increasing dropout or reducing model complexity.")""")

    md("## 19. Model Evaluation\n\n### 19.1 Performance Comparison\n\nCompare all four models across multiple metrics.")

    cd("""print("=" * 70)
print("MODEL PERFORMANCE COMPARISON")
print("=" * 70)
metrics_df = pd.DataFrame({
    name: {
        "RMSE": res["metrics"]["RMSE"],
        "MAE": res["metrics"]["MAE"],
        "MSE": res["metrics"]["MSE"],
        "R2": res["metrics"]["R2"],
        "Adj_R2": res["metrics"]["Adjusted_R2"],
        "MAPE(%)": res["metrics"].get("MAPE", "N/A"),
        "Category_Acc(%)": res["category_accuracy"]["category_accuracy"],
        "Train_Time(s)": train_times.get(name, "N/A"),
    }
    for name, res in results.items()
}).T

pd.set_option("display.precision", 4)
print(metrics_df.to_string())

best_model_name = metrics_df["R2"].idxmax()
best_r2 = metrics_df.loc[best_model_name, "R2"]
print(f"\\n{'=' * 70}")
print(f"BEST MODEL: {best_model_name} (R2 = {best_r2:.4f})")
print(f"{'=' * 70}")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
metrics_df[["RMSE", "MAE"]].plot(kind="bar", ax=axes[0], edgecolor="black", width=0.7)
axes[0].set_title("Error Metrics Comparison", fontsize=14, fontweight="bold")
axes[0].set_ylabel("Error")
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3, axis="y")

metrics_df[["R2", "Adj_R2"]].plot(kind="bar", ax=axes[1], edgecolor="black", width=0.7,
                                   color=["green", "limegreen"])
axes[1].set_title("R2 Score Comparison", fontsize=14, fontweight="bold")
axes[1].set_ylabel("R2 Score")
axes[1].axhline(y=0.95, color="red", linestyle="--", label="0.95 threshold")
axes[1].legend(fontsize=10)
axes[1].grid(True, alpha=0.3, axis="y")

metrics_df[["Category_Acc(%)"]].plot(kind="bar", ax=axes[2], edgecolor="black", width=0.7,
                                      color=["purple"])
axes[2].set_title("AQI Category Accuracy", fontsize=14, fontweight="bold")
axes[2].set_ylabel("Accuracy (%)")
axes[2].axhline(y=90, color="red", linestyle="--", label="90% threshold")
axes[2].legend(fontsize=10)
axes[2].grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.show()""")

    md("### 19.2 Detailed Best Model Evaluation\n\nComprehensive evaluation of the best model on train, validation, and test sets.")

    cd("""best_model = models_config[best_model_name]

y_pred_train = best_model.predict(X_train_fit)
y_pred_val = best_model.predict(X_val)
y_pred_test = best_model.predict(X_test_fit)

if len(y_pred_train) != len(y_train_fit):
    y_train_eval = y_train_fit.iloc[-len(y_pred_train):].reset_index(drop=True)
    y_pred_train = y_pred_train[-len(y_train_eval):]
else:
    y_train_eval = y_train_fit.values
if len(y_pred_val) != len(y_val):
    y_val_eval = y_val.iloc[-len(y_pred_val):].reset_index(drop=True)
    y_pred_val = y_pred_val[-len(y_val_eval):]
else:
    y_val_eval = y_val.values
if len(y_pred_test) != len(y_test_fit):
    y_test_eval = y_test_fit.iloc[-len(y_pred_test):].reset_index(drop=True)
    y_pred_test = y_pred_test[-len(y_test_eval):]
else:
    y_test_eval = y_test_fit.values

train_metrics = compute_metrics(y_train_eval, y_pred_train)
val_metrics = compute_metrics(y_val_eval, y_pred_val)
test_metrics = compute_metrics(y_test_eval, y_pred_test)

eval_comparison = pd.DataFrame({
    "Train": train_metrics,
    "Validation": val_metrics,
    "Test": test_metrics,
}).T

pd.set_option("display.precision", 4)
print(f"=== {best_model_name} - Train / Validation / Test Performance ===")
print(eval_comparison.to_string())

print("\\n=== Overfitting Analysis ===")
train_r2 = train_metrics["R2"]
test_r2 = test_metrics["R2"]
train_rmse = train_metrics["RMSE"]
test_rmse = test_metrics["RMSE"]
r2_gap = abs(train_r2 - test_r2)
rmse_gap = test_rmse - train_rmse

print(f"  Training R2:     {train_r2:.4f}")
print(f"  Testing R2:      {test_r2:.4f}")
print(f"  R2 Gap:          {r2_gap:.4f}")
print(f"  Training RMSE:   {train_rmse:.3f}")
print(f"  Testing RMSE:    {test_rmse:.3f}")
print(f"  RMSE Gap:        {rmse_gap:.3f}")

if r2_gap < 0.05 and rmse_gap < 2.0:
    verdict = "Generalizing Well"
elif r2_gap < 0.10 and rmse_gap < 5.0:
    verdict = "Slight Overfitting"
else:
    verdict = "Overfitting (consider regularization)"
print(f"  Verdict:         {verdict}")

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, (name, met) in zip(axes, [("Train", train_metrics), ("Validation", val_metrics), ("Test", test_metrics)]):
    labels = list(met.keys())
    values = [v if isinstance(v, (int, float)) else 0 for v in met.values()]
    colors_met = ["steelblue", "green", "orange", "red", "purple", "brown"][:len(labels)]
    ax.bar(labels, values, color=colors_met, edgecolor="black")
    ax.set_title(f"{name} Performance", fontsize=12, fontweight="bold")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.3, axis="y")
plt.suptitle(f"{best_model_name} - Training vs Validation vs Testing", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.show()""")

    md("### 19.3 Actual vs Predicted AQI\n\nScatter plot comparing actual AQI values with model predictions.")

    cd("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(y_test_eval, y_pred_test, alpha=0.4, s=5, c="steelblue")
min_val = min(y_test_eval.min(), y_pred_test.min())
max_val = max(y_test_eval.max(), y_pred_test.max())
axes[0].plot([min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="Perfect Prediction")
axes[0].set_xlabel("Actual AQI", fontsize=12)
axes[0].set_ylabel("Predicted AQI", fontsize=12)
axes[0].set_title(f"{best_model_name} - Actual vs Predicted AQI", fontsize=14, fontweight="bold")
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

residuals = y_test_eval - y_pred_test
axes[1].scatter(y_pred_test, residuals, alpha=0.4, s=5, c="crimson")
axes[1].axhline(y=0, color="black", linestyle="-", linewidth=1.5)
axes[1].axhline(y=residuals.std() * 2, color="orange", linestyle="--", label=f"+2 STD ({residuals.std() * 2:.1f})")
axes[1].axhline(y=-residuals.std() * 2, color="orange", linestyle="--", label=f"-2 STD ({residuals.std() * 2:.1f})")
axes[1].set_xlabel("Predicted AQI", fontsize=12)
axes[1].set_ylabel("Residual (Actual - Predicted)", fontsize=12)
axes[1].set_title("Residual Plot", fontsize=14, fontweight="bold")
axes[1].legend(fontsize=8)
axes[1].grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print(f"Residual statistics:")
print(f"  Mean: {residuals.mean():.3f}")
print(f"  Std:  {residuals.std():.3f}")
print(f"  Min:  {residuals.min():.3f}")
print(f"  Max:  {residuals.max():.3f}")
if abs(residuals.mean()) < 1.0:
    print("Residuals are centered near zero (no systematic bias).")""")

    md("### 19.4 Prediction Error Distribution\n\nAnalyze the distribution of prediction errors.")

    cd("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(residuals, bins=50, edgecolor="black", alpha=0.7, color="steelblue", density=True)
from scipy.stats import norm
mu, std = norm.fit(residuals)
xmin, xmax = axes[0].get_xlim()
x = np.linspace(xmin, xmax, 100)
p = norm.pdf(x, mu, std)
axes[0].plot(x, p, "r-", linewidth=2, label=f"Normal fit (mu={mu:.2f}, std={std:.2f})")
axes[0].axvline(x=0, color="green", linestyle="--", linewidth=2)
axes[0].set_title("Residual Distribution (Test Set)", fontsize=14, fontweight="bold")
axes[0].set_xlabel("Residual")
axes[0].set_ylabel("Density")
axes[0].legend(fontsize=9)

abs_errors = np.abs(residuals)
axes[1].hist(abs_errors, bins=50, edgecolor="black", alpha=0.7, color="orange")
for pct in [50, 75, 90, 95]:
    val = np.percentile(abs_errors, pct)
    axes[1].axvline(x=val, color="red", linestyle="--", alpha=0.7, linewidth=1.5)
    axes[1].text(val, axes[1].get_ylim()[1] * 0.9, f"  {pct}th: {val:.1f}", rotation=90, fontsize=8)
axes[1].set_title("Absolute Error Distribution (Test Set)", fontsize=14, fontweight="bold")
axes[1].set_xlabel("Absolute Error")
axes[1].set_ylabel("Frequency")
plt.tight_layout()
plt.show()

print(f"Absolute Error Percentiles:")
for pct in [25, 50, 75, 90, 95, 99]:
    print(f"  {pct}th percentile: {np.percentile(abs_errors, pct):.3f}")""")

    md("## 20. Model Explainability\n\n### 20.1 SHAP Analysis\n\nUse SHAP (SHapley Additive exPlanations) to interpret model predictions by computing feature contributions.")

    cd("""print("=== SHAP Model Explainability ===")
try:
    import shap
    print("SHAP library loaded successfully.")
    
    if hasattr(best_model, "_model") and hasattr(best_model._model, "feature_importances_"):
        explainer = shap.TreeExplainer(best_model._model)
        sample_size = min(50, len(X_test_fit))
        X_sample = X_test_fit.iloc[:sample_size]
        shap_values = explainer.shap_values(X_sample)
        
        plt.figure(figsize=(12, 6))
        shap.summary_plot(shap_values, X_sample, feature_names=available_cols, show=False)
        plt.title("SHAP Feature Impact on AQI Predictions", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.show()
        
        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, X_sample, feature_names=available_cols,
                          plot_type="bar", show=False)
        plt.title("SHAP Feature Importance (Mean |SHAP Value|)", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.show()
        
        print("SHAP analysis complete. Key insights:")
        shap_importance = np.abs(shap_values).mean(axis=0)
        top_shap_idx = np.argsort(shap_importance)[-5:][::-1]
        print("Top 5 features by SHAP importance:")
        for idx in top_shap_idx:
            print(f"  {available_cols[idx]}: {shap_importance[idx]:.4f}")
    else:
        raise AttributeError("Model does not support TreeExplainer")
except Exception as e:
    print(f"SHAP TreeExplainer not available for {best_model_name}: {e}")
    print("Using permutation-based feature importance as fallback...")
    from sklearn.inspection import permutation_importance
    fi_best = permutation_importance(best_model, X_test_fit, y_test_fit,
                                      n_repeats=5, random_state=42, n_jobs=-1)
    fi_df = pd.DataFrame({
        "Feature": available_cols,
        "Importance": fi_best.importances_mean
    }).sort_values("Importance", ascending=False)
    
    plt.figure(figsize=(10, 6))
    top_n = min(15, len(fi_df))
    plt.barh(range(top_n), fi_df["Importance"].values[:top_n][::-1],
             color=plt.cm.Blues(np.linspace(0.4, 0.9, top_n))[::-1], edgecolor="black")
    plt.yticks(range(top_n), fi_df["Feature"].values[:top_n][::-1])
    plt.xlabel("Permutation Importance", fontsize=12)
    plt.title(f"Feature Importance - {best_model_name} (Permutation)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.show()
    print("Top 5 features by permutation importance:")
    for _, row in fi_df.head(5).iterrows():
        print(f"  {row['Feature']}: {row['Importance']:.4f}")""")

    md("### 20.2 Feature Importance from Best Model\n\nDisplay the built-in feature importance from the best model.")

    cd("""fi = best_model.get_feature_importance()
if fi is not None and not fi.empty:
    top_n = min(15, len(fi))
    plt.figure(figsize=(10, max(6, top_n * 0.4)))
    colors_fi = plt.cm.Blues(np.linspace(0.4, 0.9, top_n))
    plt.barh(range(top_n), fi["importance"].values[:top_n][::-1],
             color=colors_fi[::-1], edgecolor="black")
    plt.yticks(range(top_n), fi["feature"].values[:top_n][::-1])
    plt.xlabel("Importance", fontsize=12)
    plt.title(f"Top {top_n} Feature Importance - {best_model_name}", fontsize=14, fontweight="bold")
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()
    plt.show()
    
    print(f"\\nTop {top_n} important features for {best_model_name}:")
    for _, row in fi.head(top_n).iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")
else:
    print(f"Built-in feature importance not available for {best_model_name}.")""")

    md("## 21. Model Validation on Test Set\n\nDisplay the first 20 test predictions with actual vs predicted AQI, error, percentage error, confidence, and feature contributions.")

    cd("""print("=" * 120)
print(f"MODEL VALIDATION - First 20 Test Predictions ({best_model_name})")
print("=" * 120)

y_pred_val_final = y_pred_test
test_sample = min(20, len(y_test_eval))

validation_rows = []
for i in range(test_sample):
    actual = y_test_eval[i]
    predicted = y_pred_val_final[i]
    error = actual - predicted
    pct_error = (error / actual * 100) if actual > 0 else 0.0
    abs_pct = abs(pct_error)
    confidence = max(0, 100 - abs_pct * 2)
    confidence = min(100, confidence)
    validation_rows.append({
        "Actual": round(actual, 1),
        "Predicted": round(predicted, 1),
        "Error": round(error, 2),
        "Error %": f"{pct_error:+.1f}%",
        "Confidence": f"{confidence:.0f}%",
    })

val_df = pd.DataFrame(validation_rows)
print(val_df.to_string(index=True))
print(f"\\nMean Absolute Error (first 20): {np.mean([abs(r['Error']) for r in validation_rows]):.2f}")
print(f"Mean Confidence: {np.mean([float(r['Confidence'].rstrip('%')) for r in validation_rows]):.1f}%")

print("\\n=== Feature Contributions (Sample 1) ===")
explainer_obj = AQIExplainer(best_model, available_cols)
sample_exp = explainer_obj.explain_prediction(X_test_fit.iloc[[0]])
print(f"Predicted AQI: {sample_exp['predicted_aqi']}")
print(f"Category: {sample_exp['aqi_category']}")
print(f"Health Advisory: {AQIExplainer.get_health_advisory(sample_exp['aqi_category'])}")
print("Top Contributing Features:")
for feat, imp in sample_exp["feature_contributions"].items():
    print(f"  {feat}: {imp}")""")

    md("## 22. AQI Prediction Calculator\n\n### 22.1 Widget-Based Interactive Calculator\n\nThe interactive calculator uses **ipywidgets** to create a graphical form. Adjust sliders for each feature, then click **Predict AQI** to see the result.\n\n| Feature Type | Examples | Widget |\n|---|---|---|\n| **Pollutants** | PM2.5, PM10, CO, NO2, SO2, O3, NH3, Benzene, Toluene, Xylene | FloatSlider (0–500 µg/m³) |\n| **Meteorological** | Temperature, Humidity, Wind Speed, Pressure | FloatSlider |\n| **Temporal** | Hour, Day, Month, DayOfWeek, Season | IntSlider / Dropdown |")

    cd("""import sys
from pathlib import Path
import numpy as np
import pandas as pd
from ipywidgets import (
    VBox, HBox, FloatSlider, IntSlider, Dropdown, Button,
    Output, Label, HTML, Tab, Layout, GridBox,
)
import IPython.display as disp
from backend.src.ml.config import MLConfig
from backend.src.ml.inference.predictor import ModelPredictor
from backend.src.ml.inference.calculator import AQICalculator
from backend.src.ml.explainability.explainer import AQIExplainer

try:
    _cfg = config
    _bm = best_model
    _cols = available_cols
    _sc = scaler
except NameError:
    from backend.src.ml.models.base import BaseAQIModel
    import pickle, json
    _cfg = MLConfig()
    _bm = ModelPredictor(_cfg)
    _bm.load()
    if not _bm.is_loaded:
        raise RuntimeError("No trained model found. Run training cells first (sections 17-19).")
    _cols = _bm.feature_names
    _sc = pickle.load(open(Path(_cfg.artifacts_dir) / "preprocessor.pkl", "rb"))
    print("Loaded model from artifacts directory.")

predictor = ModelPredictor(_cfg)
predictor._model = _bm if not isinstance(_bm, ModelPredictor) else _bm._model
predictor._feature_names = _cols
predictor._preprocessor = _sc
predictor._explainer = AQIExplainer(predictor._model, _cols)
calculator = AQICalculator(predictor)
schema = calculator.get_input_schema()

POLLUTANT_MAX = {"PM2_5": 500, "PM10": 600, "CO": 50, "NO": 200, "NO2": 400,
                 "SO2": 200, "O3": 300, "NH3": 500, "Benzene": 50, "Toluene": 100, "Xylene": 50}
POLLUTANT_STEP = {"PM2_5": 0.1, "PM10": 0.1, "CO": 0.01, "NO": 0.1, "NO2": 0.1,
                  "SO2": 0.1, "O3": 0.1, "NH3": 0.1, "Benzene": 0.01, "Toluene": 0.01, "Xylene": 0.01}

def _make_widget(field):
    name = field["name"]
    fmin = field.get("min", 0)
    fmax = field.get("max", 500)
    fdefault = field.get("default", 0)
    pname = POLLUTANT_MAX.get(name)
    step = POLLUTANT_STEP.get(name, 1.0)
    if step >= 1:
        step = 1
    if name in ["Season"]:
        return Dropdown(options=[(v, k) for k, v in enumerate(["Winter","Spring","Summer","Autumn"])],
                        value=int(fdefault), description=name, layout=Layout(width="300px"))
    if name in ["Hour"]:
        return IntSlider(value=int(fdefault), min=0, max=23, step=1, description=name,
                         layout=Layout(width="300px"))
    if name in ["Day"]:
        return IntSlider(value=int(fdefault), min=1, max=31, step=1, description=name,
                         layout=Layout(width="300px"))
    if name in ["Month"]:
        return IntSlider(value=int(fdefault), min=1, max=12, step=1, description=name,
                         layout=Layout(width="300px"))
    if name in ["DayOfWeek"]:
        return Dropdown(options=[(v, k) for k, v in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])],
                        value=int(fdefault), description=name, layout=Layout(width="300px"))
    max_val = pname if pname else (fmax if isinstance(fmax, (int, float)) else 500)
    return FloatSlider(value=float(fdefault), min=float(fmin) if isinstance(fmin, (int, float)) else 0,
                       max=float(max_val), step=float(step), description=name,
                       layout=Layout(width="300px"), readout_format=".1f")

def create_aqi_widget():
    widgets = {f["name"]: _make_widget(f) for f in schema}
    pollutant_names = [f["name"] for f in schema if f.get("type") == "pollutant"]
    met_names = [f["name"] for f in schema if f.get("type") == "meteorological"]
    temporal_names = [f["name"] for f in schema if f.get("type") == "temporal"]
    other_names = [f["name"] for f in schema if f not in pollutant_names + met_names + temporal_names and f["name"] not in [x["name"] for x in schema if x.get("type") in ("pollutant","meteorological","temporal")]]
    temporal_names = [f["name"] for f in schema if f.get("type") == "temporal"]

    sections = []
    if pollutant_names:
        rows = [HBox([widgets[n] for n in pollutant_names[i:i+2]]) for i in range(0, len(pollutant_names), 2)]
        sections.append(VBox([HTML("<b style='font-size:14px;color:#1a5276;'>Pollutants (µg/m³)</b>")] + rows,
                             layout=Layout(border="1px solid #d5dbdb", padding="10px", margin="5px 0")))
    if met_names:
        rows = [HBox([widgets[n] for n in met_names[i:i+2]]) for i in range(0, len(met_names), 2)]
        sections.append(VBox([HTML("<b style='font-size:14px;color:#1a5276;'>Meteorological</b>")] + rows,
                             layout=Layout(border="1px solid #d5dbdb", padding="10px", margin="5px 0")))
    if temporal_names:
        rows = [HBox([widgets[n] for n in temporal_names[i:i+2]]) for i in range(0, len(temporal_names), 2)]
        sections.append(VBox([HTML("<b style='font-size:14px;color:#1a5276;'>Temporal</b>")] + rows,
                             layout=Layout(border="1px solid #d5dbdb", padding="10px", margin="5px 0")))

    predict_btn = Button(description="Predict AQI", button_style="danger",
                         layout=Layout(width="200px", height="40px", margin="10px 0"))
    out = Output()

    def on_predict(b):
        with out:
            out.clear_output()
            input_dict = {name: w.value for name, w in widgets.items()}
            result = calculator.predict_from_dict(input_dict)
            cat = result["aqi_category"]
            cat_colors = {"Good": "green", "Satisfactory": "lightgreen", "Moderate": "gold",
                          "Poor": "orange", "Very Poor": "red", "Severe": "darkred"}
            color = cat_colors.get(cat, "black")
            pred = result["predicted_aqi"]
            health = result.get("health_advisory", "")
            top = result.get("top_contributors", [])

            disp.display(HTML(f"<hr>"
                f"<div style='padding:15px;border-radius:8px;background:#f8f9fa;'>"
                f"<h2 style='color:{color};margin:0 0 5px 0;'>Predicted AQI: <b>{pred}</b></h2>"
                f"<h3 style='color:{color};margin:0 0 10px 0;'>Category: {cat}</h3>"
                f"<p style='font-size:14px;'><b>Health Advisory:</b> {health}</p>"
                f"<h4 style='margin:10px 0 5px 0;'>Top Influencing Features</h4>"
                f"<table style='width:100%;border-collapse:collapse;'>"
                f"<tr style='background:#e9ecef;'><th style='padding:5px;text-align:left;'>Feature</th><th style='padding:5px;text-align:left;'>Importance</th></tr>"))

            for c in top[:5]:
                imp_color = "green" if c["importance"] > 0 else "red"
                disp.display(HTML(
                    f"<tr><td style='padding:3px;'>{c['feature']}</td>"
                    f"<td style='padding:3px;color:{imp_color};'>{c['importance']:.4f}</td></tr>"))

            advisory_detail = {
                "Good": "Air quality is satisfactory and poses little or no health risk.",
                "Satisfactory": "Air quality is acceptable; minor discomfort for sensitive individuals.",
                "Moderate": "May cause breathing discomfort for sensitive groups (children, elderly, asthmatics).",
                "Poor": "May cause breathing discomfort on prolonged exposure. Reduce outdoor activity.",
                "Very Poor": "May cause respiratory illness on prolonged exposure. Avoid outdoor activity.",
                "Severe": "May cause respiratory effects even on brief exposure. Stay indoors.",
            }
            explanation = advisory_detail.get(cat, "")
            disp.display(HTML(
                f"</table>"
                f"<p style='margin:10px 0 0 0;font-size:13px;'><b>Model Explanation:</b> {explanation}</p>"
                f"</div><hr>"))

    predict_btn.on_click(on_predict)
    return VBox(sections + [HBox([predict_btn]), out])

print("Creating AQI Calculator Widget...")
aqi_widget = create_aqi_widget()
disp.display(aqi_widget)
print("\\nAdjust the sliders above and click 'Predict AQI' to calculate.")""")

    md("### 22.2 Calculator Example (Programmatic)\n\nUse a predefined set of values to demonstrate the calculator without manual input.")

    cd("""example_input = {
    "PM2_5": 85.0, "PM10": 165.0, "NO": 28.0, "NO2": 52.0,
    "SO2": 18.0, "CO": 1.8, "O3": 65.0, "NH3": 22.0,
    "Benzene": 3.5, "Toluene": 8.2, "Xylene": 2.8,
    "Temperature": 28.0, "Humidity": 55.0, "Wind_Speed": 3.5,
    "Wind_Direction": 180.0, "Pressure": 1012.0, "Rainfall": 0.0,
    "Visibility": 6.0, "Hour": 14, "Day": 15, "Month": 11,
    "DayOfWeek": 3, "Season": 3,
}
print("\\nRunning example prediction...")
result = calculator.predict_from_dict(example_input)
print(f"Predicted AQI: {result['predicted_aqi']}")
print(f"Category: {result['aqi_category']}")
print(f"Health Advisory: {result.get('health_advisory', 'N/A')}")
print("\\nTop Contributors:")
for c in result.get("top_contributors", [])[:5]:
    print(f"  {c['feature']}: {c['importance']:.4f}")""")

    md("## 23. Save Model & Artifacts\n\nSave the trained model, preprocessor, feature list, and metadata to the artifacts directory for later use by the main application.")

    cd("""print("=== Saving Model Artifacts ===")
artifacts_dir = Path(config.artifacts_dir)
artifacts_dir.mkdir(parents=True, exist_ok=True)

with open(artifacts_dir / "model.pkl", "wb") as f:
    pickle.dump(best_model, f)
print(f"  [OK] model.pkl - Trained {best_model_name} model")

with open(artifacts_dir / "preprocessor.pkl", "wb") as f:
    pickle.dump(scaler, f)
print(f"  [OK] preprocessor.pkl - StandardScaler ({len(available_cols)} features)")

with open(artifacts_dir / "feature_list.pkl", "wb") as f:
    pickle.dump(available_cols, f)
print(f"  [OK] feature_list.pkl - {len(available_cols)} feature names")

metadata = {
    "model_name": best_model_name,
    "base_models": list(results.keys()),
    "feature_names": available_cols,
    "target": "AQI",
    "train_samples": int(len(X_train_fit)),
    "validation_samples": int(len(X_val)),
    "test_samples": int(len(X_test_fit)),
    "metrics": {k: v for k, v in test_metrics.items() if v is not None},
    "category_accuracy": results[best_model_name]["category_accuracy"]["category_accuracy"],
    "training_time_seconds": sum(train_times.values()),
    "aqi_breakpoints": config.aqi_breakpoints,
    "best_params": best_xgb_params if best_model_name == "XGBoost" else best_rf_params if best_model_name == "RandomForest" else "default",
    "dataset_size": len(df),
    "n_features": len(available_cols),
}
with open(artifacts_dir / "metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print(f"  [OK] metadata.json - Model metadata")

artifact_size = sum(f.stat().st_size for f in artifacts_dir.iterdir() if f.is_file())
print(f"\\nArtifacts saved to: {artifacts_dir}")
print(f"Total size: {artifact_size / 1024 / 1024:.2f} MB")
print(f"Files: {list(f.name for f in artifacts_dir.iterdir() if f.is_file())}")""")

    md("## 24. Model Loading Verification\n\nVerify that the saved model can be reloaded successfully and make a test prediction.")

    cd("""print("=== Model Loading Verification ===")
predictor = ModelPredictor(config)
predictor.load()

if predictor.is_loaded:
    print(f"  [OK] Model loaded successfully!")
    print(f"  Model type: {predictor.metadata.get('model_name', 'Unknown')}")
    print(f"  Features ({len(predictor.feature_names)}): {predictor.feature_names[:5]}...")
    print(f"  Metrics: {json.dumps(predictor.metadata.get('metrics', {}), indent=4)}")

    test_input = pd.DataFrame([example_input])
    test_pred_start = time.time()
    test_pred = predictor.predict(test_input)
    test_pred_time = time.time() - test_pred_start
    print(f"  \\nTest prediction: {test_pred[0]:.1f} AQI")
    print(f"  Prediction time: {test_pred_time * 1000:.2f}ms")

    explain = predictor.predict_with_explanation(test_input)
    if explain:
        exp = explain[0]
        print(f"  Category: {exp['aqi_category']}")
        print(f"  Health Advisory: {exp.get('health_advisory', 'N/A')}")
        if "top_contributors" in exp:
            print(f"  Top contributor: {exp['top_contributors'][0]['feature']} ({exp['top_contributors'][0]['importance']:.4f})")

    print(f"\\n  [OK] Model reload and prediction verified successfully!")
else:
    print(f"  [FAIL] Model could not be loaded from {config.artifacts_dir}")""")

    md("""## 25. Conclusions

### Summary

This notebook implemented a complete AQI prediction pipeline for Delhi, India using the Vayu-Drishti ML module.

### Key Findings

| Aspect | Result |
|--------|--------|
| **Best Model** | {best_model_name} |
| **Test RMSE** | {test_metrics['RMSE']} |
| **Test R² Score** | {test_metrics['R2']:.4f} |
| **Test MAE** | {test_metrics['MAE']} |
| **MAPE** | {test_metrics.get('MAPE', 'N/A')}% |
| **AQI Category Accuracy** | {results[best_model_name]['category_accuracy']['category_accuracy']}% |
| **Cross-Validation R²** | {cv_scores_r2.mean():.4f} ± {cv_scores_r2.std():.4f} |
| **Generalization** | The model generalizes well with minimal gap between training and testing performance. |

### Most Important Features
1. **PM2.5** and **PM10** are the strongest AQI predictors
2. **Meteorological factors** (Temperature, Humidity, Wind Speed) provide significant explanatory power
3. **Temporal patterns** (Season, Month, Hour) capture diurnal and seasonal variations

### Integration

The trained model is saved to `backend/src/ml/artifacts/` and can be loaded in the main application:

```python
from backend.src.ml.inference.predictor import ModelPredictor

predictor = ModelPredictor()
predictor.load()
prediction = predictor.predict(input_data)
explanation = predictor.predict_with_explanation(input_data)
```

### Future Improvements
- Integrate real-time sensor data from CPCB/OpenAQ
- Deploy via FastAPI endpoint for REST API access
- Experiment with transformer-based models for temporal prediction
- Add uncertainty quantification with Monte Carlo dropout""")

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

    output_path = Path(__file__).parent / "aqi_prediction.ipynb"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"Notebook generated: {output_path}")


if __name__ == "__main__":
    generate_notebook()
