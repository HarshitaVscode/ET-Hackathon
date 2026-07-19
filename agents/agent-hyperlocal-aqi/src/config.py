from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    host: str = "0.0.0.0"
    port: int = 8350
    artifacts_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "src", "forecasting", "artifacts")
    )
    forecast_horizon: int = 72
