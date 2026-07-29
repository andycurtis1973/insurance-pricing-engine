#!/usr/bin/env python3
"""The calibrated environment — the one simulated layer, stated plainly.

Allstate is buyers-only: everybody in the data bought something, so the data
CANNOT tell us who would have walked away at a higher price. That walk-away risk
is the whole reason differentiated pricing pays off, so to test the engine we add
it — a conversion model — and we are loud about it being a model.

What stays REAL (from 97,009 Allstate shoppers):
  * who the shoppers are (their traits)
  * the coverage/price menu each one actually saw
  * which segment they're in — price- vs coverage-driven — from what they bought

What is SIMULATED here (disclosed):
  * P(convert | offered price, coverage) — a logistic response whose price
    elasticity is CALIBRATED to the published auto-insurance literature, which
    reports (a) elasticity is heterogeneous across customers and (b) it is highest
    for direct / aggregator shoppers — i.e. our price-driven segment.
      - Guven & McPhail, "Beyond the Cost Model: Understanding Price Elasticity
        and Its Applications", Casualty Actuarial Society E-Forum, 2013.
      - Akur8, "Demand Modeling in Insurance".
    We do NOT claim a single true elasticity; we pick segment values inside the
    reported band and SWEEP them (see optimize.py) to show the result is robust.

This is exactly how a pricing engine is built and stress-tested BEFORE it is ever
allowed near a live customer. The headline is "lift in simulation", never
"we made Allstate $X".
"""

from __future__ import annotations

import numpy as np

COVMAX = 18                       # max coverage index (sum of options A..G)
BASE_CONVERSION = 0.65            # conversion of an engaged shopper at their cheapest quote

# Segment response, calibrated to the literature (heterogeneous; price-driven the
# most elastic). `elast` is the logit penalty per unit of RELATIVE price increase
# -> arc elasticity ~= elast * P(1-P) / P at the reference. cov_taste is the logit
# reward per unit of relative coverage gain (coverage-driven actually want more).
SEG_PARAMS = {
    "price_driven":    {"elast": 6.0, "cov_taste": 0.2},   # arc elasticity ~ -2.1
    "balanced":        {"elast": 3.5, "cov_taste": 1.0},   # arc elasticity ~ -1.2
    "coverage_driven": {"elast": 1.5, "cov_taste": 2.5},   # arc elasticity ~ -0.5
}


def _logit(p):
    return np.log(p / (1.0 - p))


def p_convert(segment, price, cov, ref_price, ref_cov, escale=1.0):
    """Simulated probability a shopper buys THIS offer, given their cheapest
    viewed quote (ref_price, ref_cov) as the anchor. escale scales all
    elasticities at once (used for the robustness sweep)."""
    prm = SEG_PARAMS[segment]
    rel_price = (price - ref_price) / max(1.0, ref_price)     # 0 at the anchor
    rel_cov = (cov - ref_cov) / COVMAX
    z = (_logit(BASE_CONVERSION)
         - escale * prm["elast"] * rel_price
         + prm["cov_taste"] * rel_cov)
    return 1.0 / (1.0 + np.exp(-z))


def arc_elasticities(escale=1.0):
    """Report the implied arc elasticity per segment at the anchor (for disclosure)."""
    out = {}
    for s, prm in SEG_PARAMS.items():
        p0 = BASE_CONVERSION
        # d(logit)/d(rel_price) = -elast  ->  dP/drel = -elast*p0*(1-p0)
        dP = -escale * prm["elast"] * p0 * (1 - p0)
        out[s] = round(float(dP / p0), 2)                     # (dP/P)/(drel_price)
    return out


def candidate_offers(offers):
    """From the real menu a shopper saw, the three levers the engine can pull:
    LEAN = cheapest, RICH = richest coverage, MID = the middle by coverage."""
    arr = sorted(({"cov": o["cov"], "cost": o["cost"]} for o in offers),
                 key=lambda o: (o["cov"], o["cost"]))
    lean = min(arr, key=lambda o: o["cost"])
    rich = max(arr, key=lambda o: o["cov"])
    mid = arr[len(arr) // 2]
    return {"lean": lean, "mid": mid, "rich": rich}


if __name__ == "__main__":
    # quick self-check: print the calibration so it's inspectable
    import json
    print("BASE_CONVERSION =", BASE_CONVERSION)
    print("implied arc elasticities:", json.dumps(arc_elasticities(), indent=2))
    ref = {"price": 600, "cov": 8}
    for s in SEG_PARAMS:
        rows = []
        for dp in (0.0, 0.05, 0.10, 0.20):
            price = ref["price"] * (1 + dp)
            rows.append(f"+{int(dp*100):>2d}%->{p_convert(s, price, ref['cov'], ref['price'], ref['cov']):.2f}")
        rows.append(f" +6cov@+5%->{p_convert(s, ref['price']*1.05, ref['cov']+6, ref['price'], ref['cov']):.2f}")
        print(f"  {s:16s} " + "  ".join(rows))
