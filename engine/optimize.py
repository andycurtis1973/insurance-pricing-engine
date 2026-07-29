#!/usr/bin/env python3
"""Three pricing strategies, scored on held-out shoppers in the simulator.

For every held-out shopper we know their real menu and their real segment. The
simulator (see simulator.py) says how likely each offer is to convert. Revenue
for an offer = P(convert) x premium. We compare:

    compete_on_price   always lead with the cheapest quote  (max conversion)
    blanket_upsell     always lead with the richest coverage (max premium, reckless)
    engine             lead with the revenue-maximising offer FOR THAT SEGMENT

The point of the engine is the third row: it holds price-driven shoppers on the
lean quote (so they don't walk) and trades coverage-driven shoppers up (they
convert *more* with richer coverage). We report revenue/shopper AND conversion,
so you can see the engine doesn't buy premium by torching conversion the way
blanket upsell does. Elasticity is swept to show the result isn't cherry-picked.

    python3 optimize.py --data ../data/out
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import simulator as S


def shoppers(datadir: Path):
    seg = pd.read_parquet(datadir / "segments.parquet").set_index("customer_ID")["segment"]
    test_ids = set(json.loads((datadir / "split.json").read_text())["test_ids"])
    for line in (datadir / "choices.jsonl").open():
        c = json.loads(line)
        cid = c["customer_ID"]
        if cid not in test_ids or cid not in seg.index or len(c["offers"]) < 2:
            continue
        yield cid, seg.loc[cid], c["offers"]


def evaluate(datadir: Path, escale: float):
    strat = {k: {"rev": 0.0, "conv": 0.0, "prem": 0.0} for k in
             ("compete_on_price", "blanket_upsell", "engine")}
    seg_rev = {s: {"engine": 0.0, "compete_on_price": 0.0, "n": 0} for s in S.SEG_PARAMS}
    up = {s: 0 for s in S.SEG_PARAMS}
    n = 0
    for cid, seg, offers in shoppers(datadir):
        cand = S.candidate_offers(offers)
        ref = cand["lean"]
        rp, rc = ref["cost"], ref["cov"]

        def rev(o):
            p = S.p_convert(seg, o["cost"], o["cov"], rp, rc, escale)
            return p * o["cost"], p

        r_lean, p_lean = rev(cand["lean"])
        r_rich, p_rich = rev(cand["rich"])
        # engine: best expected-revenue offer among the levers, floored at lean price
        best = max((cand["lean"], cand["mid"], cand["rich"]),
                   key=lambda o: rev(o)[0])
        r_eng, p_eng = rev(best)

        strat["compete_on_price"]["rev"] += r_lean
        strat["compete_on_price"]["conv"] += p_lean
        strat["compete_on_price"]["prem"] += cand["lean"]["cost"]
        strat["blanket_upsell"]["rev"] += r_rich
        strat["blanket_upsell"]["conv"] += p_rich
        strat["blanket_upsell"]["prem"] += cand["rich"]["cost"]
        strat["engine"]["rev"] += r_eng
        strat["engine"]["conv"] += p_eng
        strat["engine"]["prem"] += best["cost"]

        seg_rev[seg]["engine"] += r_eng
        seg_rev[seg]["compete_on_price"] += r_lean
        seg_rev[seg]["n"] += 1
        if best["cov"] > cand["lean"]["cov"]:
            up[seg] += 1
        n += 1

    for k in strat:
        strat[k] = {"rev_per_shopper": round(strat[k]["rev"] / n, 2),
                    "conversion": round(strat[k]["conv"] / n, 4),
                    "avg_premium_offered": round(strat[k]["prem"] / n, 2)}
    base = strat["compete_on_price"]["rev_per_shopper"]
    return {
        "escale": escale, "n_test": n,
        "arc_elasticities": S.arc_elasticities(escale),
        "strategies": strat,
        "engine_lift_vs_compete_pct": round((strat["engine"]["rev_per_shopper"] / base - 1) * 100, 2),
        "engine_lift_vs_upsell_pct": round(
            (strat["engine"]["rev_per_shopper"] / strat["blanket_upsell"]["rev_per_shopper"] - 1) * 100, 2),
        "by_segment": {s: {
            "n": v["n"],
            "engine_rev": round(v["engine"] / max(1, v["n"]), 2),
            "compete_rev": round(v["compete_on_price"] / max(1, v["n"]), 2),
            "lift_pct": round((v["engine"] / max(1e-9, v["compete_on_price"]) - 1) * 100, 2),
            "traded_up_pct": round(up[s] / max(1, v["n"]) * 100, 1),
        } for s, v in seg_rev.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data/out")
    ap.add_argument("--out", default="../results/engine.json")
    a = ap.parse_args()
    datadir = Path(a.data)

    print("scoring strategies on held-out shoppers ...", flush=True)
    base = evaluate(datadir, 1.0)
    sweep = [evaluate(datadir, e) for e in (0.5, 0.75, 1.0, 1.25, 1.5)]

    out = {**base,
           "disclosure": "Real Allstate menus + real segments; walk-away response "
                         "is a conversion model calibrated to published auto-insurance "
                         "elasticities (Guven & McPhail, CAS 2013). Lift is in simulation.",
           "elasticity_sweep": [{"escale": s["escale"],
                                 "engine_lift_vs_compete_pct": s["engine_lift_vs_compete_pct"],
                                 "engine_lift_vs_upsell_pct": s["engine_lift_vs_upsell_pct"],
                                 "engine_conversion": s["strategies"]["engine"]["conversion"]}
                                for s in sweep]}
    Path(a.out).write_text(json.dumps(out, indent=2))

    st = base["strategies"]
    print(f"\n  held-out shoppers: {base['n_test']:,}\n")
    print(f"  {'strategy':18s} {'rev/shopper':>12s} {'conversion':>11s} {'avg premium':>12s}")
    print("  " + "-" * 56)
    for k in ("compete_on_price", "blanket_upsell", "engine"):
        v = st[k]
        print(f"  {k:18s} ${v['rev_per_shopper']:>10.2f} {v['conversion']*100:>10.1f}% "
              f"${v['avg_premium_offered']:>10.2f}")
    print(f"\n  engine lift: {base['engine_lift_vs_compete_pct']:+.2f}% vs compete-on-price · "
          f"{base['engine_lift_vs_upsell_pct']:+.2f}% vs blanket-upsell")
    print(f"\n  by segment (engine vs compete-on-price):")
    for s, v in base["by_segment"].items():
        print(f"    {s:16s} {v['lift_pct']:+6.2f}%   traded up {v['traded_up_pct']:>5.1f}%   (n={v['n']:,})")
    print(f"\n  robustness — elasticity swept 0.5x..1.5x:")
    for s in out["elasticity_sweep"]:
        print(f"    x{s['escale']}: {s['engine_lift_vs_compete_pct']:+.2f}% vs compete · "
              f"conv {s['engine_conversion']*100:.1f}%")
    print(f"\n  -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
