#!/usr/bin/env python3
"""Consolidate every result into results/rundata.json — the ONE file the web demo
and the video both read, so they can never drift.

    python3 scripts/make_rundata.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
D = ROOT / "data" / "out"


def load(p):
    return json.loads(Path(p).read_text())


def main() -> int:
    summ = load(D / "summary.json")
    choice = load(R / "choice.json")
    seg = load(R / "segments.json")
    eng = load(R / "engine.json")
    band = load(R / "bandit.json")

    coefs = {c["name"]: c for c in choice["coefficients"]}
    out = {
        "corpus": {
            "n_customers": summ["n_customers"],
            "median_quotes": summ["median_quotes"],
            "premium_p10": summ["cost_p10"], "premium_median": summ["cost_median"],
            "premium_p90": summ["cost_p90"],
            "pct_saw_price_variation": summ["pct_saw_price_variation"],
            "avg_cost_range": summ["avg_cost_range"],
            "pct_bought_cheapest": summ["pct_bought_cheapest"],
            "pct_bought_richest_cov": summ["pct_bought_richest_cov"],
            "coverage_max": summ["coverage_max_index"],
        },
        "choice_model": {
            "model": choice["model"],
            "n_sets": choice["n_sets"], "n_test": choice["n_test"],
            "top1": choice["top1_accuracy"],
            "baseline_cheapest": choice["baseline_cheapest"],
            "baseline_richest": choice["baseline_richest_coverage"],
            "price": coefs["price"], "coverage": coefs["coverage"],
            "price_homeowner": coefs["price:homeowner"],
            "price_young": coefs["price:young"],
            "price_car_value": coefs["price:car_value"],
        },
        "segments": {s: {
            "pct": v["pct"], "n": v["n"],
            "bought_cheapest_pct": v["bought_cheapest_pct"],
            "avg_coverage_pct": v["avg_buy_cov_pct"],
            "avg_premium": v["avg_premium"],
        } for s, v in seg["segments"].items()},
        "engine": {
            "n_test": eng["n_test"],
            "arc_elasticities": eng["arc_elasticities"],
            "strategies": eng["strategies"],
            "lift_vs_compete_pct": eng["engine_lift_vs_compete_pct"],
            "lift_vs_upsell_pct": eng["engine_lift_vs_upsell_pct"],
            "by_segment": eng["by_segment"],
            "elasticity_sweep": eng["elasticity_sweep"],
        },
        "bandit": {
            "n_stream": band["n_stream"],
            "oracle_arm": band["oracle_arm_per_segment"],
            "bandit_arm": band["bandit_best_arm_per_segment"],
            "lock_in": band["shoppers_to_lock_oracle_arm"],
            "learned_conversion": band["learned_conversion_per_arm"],
            "final_rev": band["final_rev_per_shopper"],
            "lift_vs_compete_pct": band["lift_vs_compete_pct"],
            "regret_vs_oracle_pct": band["regret_vs_oracle_pct"],
            "curve": band["curve"],
        },
        "disclosure": {
            "real": ["97,009 real Allstate auto-insurance shopping sessions",
                     "the coverage/price menu each shopper actually saw",
                     "price- vs coverage-driven segment, from what they actually bought",
                     "Bayesian choice-model price & coverage sensitivities (with credible intervals)"],
            "simulated": ["whether a shopper walks away at a higher price — a logistic "
                          "conversion model calibrated to published auto-insurance price "
                          "elasticities (heterogeneous; highest for direct/aggregator shoppers)"],
            "sources": ["Guven & McPhail, \"Beyond the Cost Model\", CAS E-Forum 2013",
                        "Akur8, \"Demand Modeling in Insurance\""],
            "headline_frame": "lift in simulation — not a claim about Allstate's revenue",
        },
    }
    (R / "rundata.json").write_text(json.dumps(out, indent=2))
    print(f"  wrote {R / 'rundata.json'}  ({len(json.dumps(out)):,} bytes)")
    print(f"  engine lift {out['engine']['lift_vs_compete_pct']}% · "
          f"bandit lift {out['bandit']['lift_vs_compete_pct']}% · "
          f"regret {out['bandit']['regret_vs_oracle_pct']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
