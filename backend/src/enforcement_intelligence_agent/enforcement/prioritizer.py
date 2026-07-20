from typing import List, Dict
from .recommender import EnforcementRecommendation


class HotspotPrioritizer:
    def prioritize(self, recommendations: List[EnforcementRecommendation]) -> List[EnforcementRecommendation]:
        scored = [(r.risk_score, r) for r in recommendations]
        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for i, (_, rec) in enumerate(scored):
            rec.priority = i + 1
            result.append(rec)
        return result

    def get_summary(self, recommendations: List[EnforcementRecommendation]) -> Dict:
        prioritized = self.prioritize(recommendations)
        return {
            "total_hotspots": len(prioritized),
            "critical_count": sum(1 for r in prioritized if r.priority <= 5),
            "high_count": sum(1 for r in prioritized if 5 < r.priority <= 15),
            "top_priority": prioritized[0].to_dict() if prioritized else None,
            "recommendations": [r.to_dict() for r in prioritized],
        }
