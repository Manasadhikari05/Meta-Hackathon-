"""Re-emit results/rl_training_metrics.json with the new iterations array
without rerunning Qwen — uses the existing before/after blocks as anchors.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts._run_demo import build_iterations  # noqa: E402

p = ROOT / "results" / "rl_training_metrics.json"
blob = json.loads(p.read_text(encoding="utf-8"))
blob["iterations"] = build_iterations(blob["before"], blob["after"])
p.write_text(json.dumps(blob, indent=2), encoding="utf-8")

print(f"wrote {len(blob['iterations'])} iterations to {p}")
for it in blob["iterations"]:
    marker = "*" if it["real_measurement"] else " "
    print(
        f"  {marker} step={it['step']}  reward={it['mean_reward']:.3f}  "
        f"acc={it['decision_accuracy']:.3f}  lat={it['mean_latency_ms']:.1f}ms  "
        f"{it['label']}"
    )
