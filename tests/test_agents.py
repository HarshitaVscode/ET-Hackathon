from __future__ import annotations

import numpy as np
import pytest
import torch


class TestGraphCastAdapter:
    def test_model_initialization(self):
        from src.agents.aqi_forecast.models.graphcast_adapter import GraphCastAdapter
        model = GraphCastAdapter()
        assert model is not None
        batch_size, num_nodes, feat_dim = 2, 100, model.get_feature_dim()
        x = torch.randn(batch_size, num_nodes, feat_dim)
        edge_index = torch.randint(0, num_nodes, (2, 500))
        output = model(x, edge_index)
        assert "prediction" in output
        assert output["prediction"].shape == (batch_size, num_nodes)

    def test_numpy_inference(self):
        from src.agents.aqi_forecast.models.graphcast_adapter import GraphCastAdapter
        model = GraphCastAdapter()
        model.eval()
        num_nodes = 50
        features = np.random.randn(num_nodes, model.get_feature_dim()).astype(np.float32)
        edge_index = np.array([
            np.random.randint(0, num_nodes, 200),
            np.random.randint(0, num_nodes, 200),
        ], dtype=np.int64)
        result = model.predict_with_uncertainty(features, edge_index, time_idx=96)
        assert "mean" in result
        assert "std" in result
        assert len(result["mean"]) == num_nodes


class TestTemporalFusionTransformer:
    def test_forward_pass(self):
        from src.agents.aqi_forecast.models.temporal_fusion import TemporalFusionTransformer
        model = TemporalFusionTransformer(
            context_length=72, forecast_horizon=72, hidden_dim=64, num_heads=2
        )
        batch, ctx, horizon = 4, 72, 72
        static = torch.randn(batch, 6)
        observed = torch.randn(batch, ctx, 1)
        known = torch.randn(batch, horizon, 6)
        output = model(static, observed, known)
        assert "p10" in output
        assert "p50" in output
        assert "p90" in output
        assert output["p50"].shape == (batch, horizon)


class TestCausalDAG:
    def test_structure_learning(self):
        from src.agents.source_attribution.causal_dag import CausalDAGLearner
        import pandas as pd
        rng = np.random.default_rng(42)
        n = 200
        data = pd.DataFrame({
            "traffic": rng.exponential(50, n),
            "industry": rng.exponential(30, n),
            "burning": rng.exponential(20, n),
            "wind": rng.uniform(0, 10, n),
            "pm25": rng.normal(100, 30, n),
        })
        learner = CausalDAGLearner()
        dag = learner.learn_structure(data)
        assert dag is not None
        assert len(dag.nodes) == 5

    def test_attribution(self):
        from src.agents.source_attribution.causal_dag import CausalDAGLearner
        import pandas as pd
        rng = np.random.default_rng(42)
        n = 200
        data = pd.DataFrame({
            "traffic_emission": rng.exponential(50, n),
            "industrial_emission": rng.exponential(30, n),
            "agricultural_burning": rng.exponential(20, n),
            "wind_speed": rng.uniform(0, 10, n),
            "pm2_5": rng.normal(150, 40, n),
        })
        learner = CausalDAGLearner()
        learner.learn_structure(data)
        current = pd.DataFrame([{
            "traffic_emission": 45.0,
            "industrial_emission": 25.0,
            "agricultural_burning": 15.0,
            "wind_speed": 3.5,
            "pm2_5": 128.0,
        }])
        contributions = learner.attribute_sources(current)
        assert len(contributions) > 0
        pct_sum = sum(c["percentage"] for c in contributions.values())
        assert abs(pct_sum - 100.0) < 2.0


class TestBurnDetection:
    def test_viirs_detector(self):
        from src.agents.burn_detection.detectors.viirs_detector import VIIRSFireDetector
        detector = VIIRSFireDetector()
        h, w = 100, 100
        rng = np.random.default_rng(42)
        bt = rng.normal(290, 10, (h, w))
        bt[45:55, 45:55] += 50
        lats = np.linspace(28.4, 28.88, h)
        lons = np.linspace(76.84, 77.34, w)
        fires = detector.detect(bt, lats, lons)
        assert len(fires) > 0
        assert fires[0]["detection_source"] == "VIIRS"

    def test_plume_tracker(self):
        from src.agents.burn_detection.plume_tracker import PlumeTracker
        tracker = PlumeTracker()
        trajectory = tracker.predict_trajectory(
            fire_lat=28.66, fire_lon=77.35, fire_intensity=50,
            wind_speed_ms=4.0, wind_direction_deg=270,
            pbl_height_m=1200, stability_class="neutral",
        )
        assert len(trajectory) > 0
        assert trajectory[0]["hour"] >= 0


class TestDecisionEngine:
    def test_traffic_optimizer(self):
        from src.decision_engine.optimizer import TrafficRLOptimizer
        opt = TrafficRLOptimizer()
        congestion = {"NH9": 8.5, "Ring_Road": 6.2, "MG_Road": 3.1}
        recs = opt.optimize_timing(congestion, current_aqi=285, wind_speed_ms=3.5, time_hour=18)
        assert len(recs) > 0
        assert recs[0]["priority"] == "high"

    def test_squad_router(self):
        from src.decision_engine.optimizer import SquadRouter
        router = SquadRouter()
        violations = [
            {"id": 1, "latitude": 28.66, "longitude": 77.35, "priority_score": 9, "severity": "high"},
            {"id": 2, "latitude": 28.59, "longitude": 77.05, "priority_score": 6, "severity": "medium"},
            {"id": 3, "latitude": 28.61, "longitude": 77.23, "priority_score": 7, "severity": "high"},
        ]
        plan = router.optimize_route(violations, num_squads=2)
        assert len(plan) > 0

    def test_emergency_assessment(self):
        from src.decision_engine.optimizer import EmergencyResponseOptimizer
        em = EmergencyResponseOptimizer()
        assessment = em.evaluate_severity(
            current_aqi=412, forecast_peak_aqi=450,
            affected_population=500000, duration_hours=48,
            vulnerable_population=120000,
        )
        assert assessment["severity"] == "critical"
        assert assessment["grap_stage"] == 4


class TestCommunicationBus:
    def test_message_construction(self):
        from src.agents.orchestrator.communication_bus import AgentMessage, MessageType, MessagePriority
        msg = AgentMessage(
            sender_id="test",
            target_agent="aqi_forecast",
            message_type=MessageType.REQUEST,
            payload={"query": "forecast"},
            priority=MessagePriority.NORMAL,
        )
        d = msg.to_dict()
        assert d["sender_id"] == "test"
        assert d["message_type"] == "request"
        restored = AgentMessage.from_dict(d)
        assert restored.target_agent == "aqi_forecast"

    @pytest.mark.asyncio
    async def test_conflict_resolution(self):
        from src.agents.orchestrator.communication_bus import CommunicationBus
        bus = CommunicationBus()
        predictions = [
            {"aqi": 300, "source": "traffic", "confidence": 0.8},
            {"aqi": 280, "source": "burning", "confidence": 0.6},
            {"aqi": 310, "source": "traffic", "confidence": 0.7},
        ]
        result = await bus.resolve_conflict(predictions)
        assert "aqi" in result
        assert "source" in result
        assert result["consensus_method"] == "confidence_weighted_vote"
