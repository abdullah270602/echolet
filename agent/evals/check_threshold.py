"""
Fail (exit 1) if the latest eval run's pass rate is below a threshold.

The dataset deliberately contains cases the agent still fails, so the nightly job gates
on the overall pass rate instead of on every case passing:

    uv run python evals/check_threshold.py 0.55
"""

import json
import sys
from pathlib import Path

runs = sorted((Path(__file__).parent / "results").glob("*.json"))
if not runs:
    sys.exit("no eval results found")
latest = json.loads(runs[-1].read_text(encoding="utf-8"))
threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 0.55
rate = latest["pass_rate"] or 0
print(f"pass rate {rate:.1%} ({latest['passed']}/{latest['total']}), threshold {threshold:.0%}")
for cat, v in latest["by_category"].items():
    print(f"  {cat:18} {v['passed']}/{v['total']}")
sys.exit(0 if rate >= threshold else 1)
