"""Source Attribution Agent configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AttributionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_port: int = 8302
    app_debug: bool = True

    causal_structure_learning_method: str = "pc"  # pc, fci, gs, or exhaustive
    causal_alpha: float = 0.05
    causal_min_samples: int = 100

    n_bootstrap_samples: int = 100
    confidence_ci_level: float = 0.95

    source_categories: list[str] = [
        "traffic", "industry", "construction", "agricultural_burning",
        "waste_burning", "domestic", "dust", "power_plant", "brick_kiln",
    ]

    contribution_lookback_hours: int = 24


attribution_config = AttributionConfig()
