import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from enforcement_intelligence_agent.pipeline import EnforcementPipeline

if __name__ == "__main__":
    pipeline = EnforcementPipeline()
    results = pipeline.run(scan_all=True)
    print(f"\nPipeline completed. {results['total_hotspots']} hotspots analyzed.")
