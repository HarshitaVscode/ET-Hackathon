import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

from ..config import EnforcementConfig
from ..detection.hotspot import HotspotResult
from ..attribution.source_matcher import AttributionResult
from ..enforcement.recommender import EnforcementRecommendation
from ..boundaries import get_india_boundary, get_state_boundaries

cfg = EnforcementConfig()

plt.style.use("dark_background")
COLORS = {
    "Very High": "#ef4444",
    "High": "#f97316",
    "Moderate": "#eab308",
    "Low": "#22c55e",
}
SEVERITY_ORDER = ["Very High", "High", "Moderate", "Low"]


def _draw_india_boundaries(ax, india_color="#00ccff", state_color="#3a5a7a"):
    boundary = get_india_boundary()
    for feat in boundary.get("features", []):
        coords = feat["geometry"]["coordinates"][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        ax.plot(lons, lats, color=india_color, linewidth=2.0, alpha=0.9, zorder=10)

    states = get_state_boundaries()
    for feat in states.get("features", []):
        coords = feat["geometry"]["coordinates"][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        ax.plot(lons, lats, color=state_color, linewidth=0.6, alpha=0.5, zorder=9)


class EnforcementPlots:
    @staticmethod
    def plot_severity_distribution(hotspots: List[HotspotResult],
                                    save_path: Optional[Path] = None) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 5))
        labels = SEVERITY_ORDER
        counts = [sum(1 for h in hotspots if h.severity_label == l) for l in labels]
        colors = [COLORS[l] for l in labels]
        bars = ax.bar(labels, counts, color=colors, alpha=0.85, width=0.6)
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(count), ha="center", fontsize=12, fontweight="bold")
        ax.set_title("Hotspot Severity Distribution", fontsize=14, fontweight="bold", pad=15)
        ax.set_ylabel("Number of Hotspots", fontsize=11)
        ax.set_facecolor("#0f0f2a")
        for sp in ax.spines.values(): sp.set_visible(False)
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    @staticmethod
    def plot_source_attribution(attributions: List[AttributionResult],
                                 save_path: Optional[Path] = None) -> plt.Figure:
        from collections import Counter
        causes = Counter(a.most_probable_cause for a in attributions)
        fig, ax = plt.subplots(figsize=(10, 6))
        labels = [c.replace("_", " ").title() for c in causes.keys()]
        values = list(causes.values())
        colors_plt = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        wedges, texts, autotexts = ax.pie(
            values, labels=None, autopct="%1.1f%%", startangle=90,
            colors=colors_plt, pctdistance=0.85, wedgeprops={"linewidth": 1, "edgecolor": "#0f0f2a"}
        )
        for t in autotexts: t.set_fontsize(9)
        ax.set_title("Source Attribution Distribution", fontsize=14, fontweight="bold", pad=15)
        ax.legend(wedges, labels, title="Source Type", loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    @staticmethod
    def plot_confidence_distribution(attributions: List[AttributionResult],
                                       save_path: Optional[Path] = None) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 5))
        confidences = [a.confidence * 100 for a in attributions]
        ax.hist(confidences, bins=15, color="#3b82f6", alpha=0.7, edgecolor="none")
        ax.axvline(np.mean(confidences), color="#ef4444", linestyle="--",
                    linewidth=2, label=f"Mean: {np.mean(confidences):.1f}%")
        ax.set_title("Attribution Confidence Distribution", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Confidence (%)", fontsize=11)
        ax.set_ylabel("Frequency", fontsize=11)
        ax.set_facecolor("#0f0f2a")
        ax.legend()
        for sp in ax.spines.values(): sp.set_visible(False)
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    @staticmethod
    def plot_priority_ranking(recommendations: List[EnforcementRecommendation],
                               save_path: Optional[Path] = None) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, max(4, len(recommendations) * 0.4)))
        sorted_recs = sorted(recommendations, key=lambda r: r.priority)
        labels = [f"#{r.priority} {r.location_name}" for r in sorted_recs]
        scores = [r.risk_score for r in sorted_recs]
        colors_bar = [COLORS.get(r.severity, "#6366f1") for r in sorted_recs]
        bars = ax.barh(range(len(labels)), scores, color=colors_bar, alpha=0.85)
        for i, (bar, rec) in enumerate(zip(bars, sorted_recs)):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{rec.severity} | {rec.recommendation[:40]}...",
                    va="center", fontsize=8, color="#a0a0a0")
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel("Risk Score", fontsize=11)
        ax.set_title("Enforcement Priority Ranking", fontsize=14, fontweight="bold", pad=15)
        ax.set_facecolor("#0f0f2a")
        ax.invert_yaxis()
        for sp in ax.spines.values(): sp.set_visible(False)
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    @staticmethod
    def plot_hotspot_map(hotspots: List[HotspotResult],
                          save_path: Optional[Path] = None) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(14, 12))
        _draw_india_boundaries(ax, india_color="#00ccff", state_color="#335566")
        for h in hotspots:
            color = COLORS.get(h.severity_label, "#6366f1")
            size = max(20, h.severity_score * 200)
            ax.scatter(h.lon, h.lat, c=color, s=size, alpha=0.7, edgecolors="white",
                        linewidth=0.5, zorder=11)
            ax.annotate(h.location_name, (h.lon, h.lat),
                        textcoords="offset points", xytext=(5, 5),
                        fontsize=7, color="white", alpha=0.8, zorder=12)
        ax.set_xlim(cfg.india_bounds["min_lon"], cfg.india_bounds["max_lon"])
        ax.set_ylim(cfg.india_bounds["min_lat"], cfg.india_bounds["max_lat"])
        ax.set_title("India Pollution Hotspot Map", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Longitude", fontsize=10)
        ax.set_ylabel("Latitude", fontsize=10)
        ax.set_facecolor("#0a0a1a")
        ax.grid(True, alpha=0.1, color="white")
        for sp in ax.spines.values(): sp.set_visible(False)
        legend_elements = [
            mpatches.Patch(color=COLORS[l], label=l) for l in SEVERITY_ORDER
        ]
        ax.legend(handles=legend_elements, title="Severity",
                   loc="lower left", fontsize=8, title_fontsize=9)
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    @staticmethod
    def plot_confidence_by_source(attributions: List[AttributionResult],
                                   save_path: Optional[Path] = None) -> plt.Figure:
        from collections import defaultdict
        source_conf = defaultdict(list)
        for a in attributions:
            source_conf[a.most_probable_cause].append(a.confidence * 100)
        fig, ax = plt.subplots(figsize=(12, 6))
        labels = []
        means = []
        stds = []
        for src in sorted(source_conf.keys(), key=lambda s: np.mean(source_conf[s]), reverse=True):
            labels.append(src.replace("_", " ").title())
            means.append(np.mean(source_conf[src]))
            stds.append(np.std(source_conf[src]))
        x = range(len(labels))
        ax.bar(x, means, yerr=stds, capsize=5, color="#3b82f6", alpha=0.8, width=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
        ax.set_ylabel("Mean Confidence (%)", fontsize=11)
        ax.set_title("Confidence by Source Type", fontsize=14, fontweight="bold", pad=15)
        ax.set_facecolor("#0f0f2a")
        for sp in ax.spines.values(): sp.set_visible(False)
        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig
