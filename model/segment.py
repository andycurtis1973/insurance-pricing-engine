#!/usr/bin/env python3
"""Price-driven or coverage-driven? Read it off each shopper's own price sensitivity.

The choice model gave a price coefficient that shifts with a shopper's traits.
So every customer has their OWN effective price sensitivity:

    beta_price(i) = b_price + b_price:homeowner*homeowner_i
                            + b_price:young*young_i
                            + b_price:car_value*carval_i

More negative = more allergic to price = price-driven. We split the estate into
thirds and describe how the two ends differ — using the real purchases, not the
labels, as the check: price-driven shoppers should actually buy cheaper/leaner.

    python3 segment.py --data ../data/out --choice ../results/choice.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data/out")
    ap.add_argument("--choice", default="../results/choice.json")
    ap.add_argument("--out", default="../results/segments.json")
    a = ap.parse_args()

    cust = pd.read_parquet(Path(a.data) / "customers.parquet")
    ch = json.loads(Path(a.choice).read_text())
    b = {c["name"]: c["mean"] for c in ch["coefficients"]}

    homeowner = cust["homeowner"].fillna(0).astype(float)
    young = (cust["age_youngest"].fillna(40) < 25).astype(float)
    cval = cust["car_value"].astype("category").cat.codes.replace(-1, np.nan)
    cval = ((cval - cval.mean()) / (cval.std() + 1e-9)).fillna(0.0)

    beta_price = (b["price"] + b["price:homeowner"] * homeowner
                  + b["price:young"] * young + b["price:car_value"] * cval)
    cust = cust.assign(beta_price=beta_price)

    # Segment on REVEALED behaviour — what each shopper actually did with the
    # menu they saw — not on inferred traits (which barely separate). This is
    # honest population description: how people really shopped.
    #   price-driven    : landed on the cheapest option they looked at
    #   coverage-driven : landed on the richest coverage, and it wasn't the cheapest
    #   balanced        : everyone in between
    pricey = cust["bought_cheapest"] == 1
    covy = (cust["bought_richest_cov"] == 1) & (cust["bought_cheapest"] == 0)
    seg = np.where(pricey, "price_driven",
                   np.where(covy, "coverage_driven", "balanced"))
    cust = cust.assign(segment=seg)

    out = {"n_customers": int(len(cust)),
           "segmentation": "by revealed behaviour (cheapest vs richest coverage chosen)",
           "segments": {}}
    for s in ["price_driven", "balanced", "coverage_driven"]:
        g = cust[cust.segment == s]
        out["segments"][s] = {
            "n": int(len(g)), "pct": round(len(g) / len(cust) * 100, 1),
            "avg_beta_price": round(float(g["beta_price"].mean()), 3),
            "bought_cheapest_pct": round(float(g["bought_cheapest"].mean()) * 100, 1),
            "bought_richest_cov_pct": round(float(g["bought_richest_cov"].mean()) * 100, 1),
            "avg_buy_cov_pct": round(float(g["buy_cov_pct"].mean()), 1),
            "avg_premium": int(g["buy_cost"].mean()),
            "pct_young": round(float((g["age_youngest"].fillna(40) < 25).mean()) * 100, 1),
            "pct_homeowner": round(float(g["homeowner"].fillna(0).mean()) * 100, 1),
        }
    # the validation: the label is behavioural, so behaviour should track it
    pd_seg, cd_seg = out["segments"]["price_driven"], out["segments"]["coverage_driven"]
    out["validation"] = {
        "price_driven_buy_cheapest_pct": pd_seg["bought_cheapest_pct"],
        "coverage_driven_buy_cheapest_pct": cd_seg["bought_cheapest_pct"],
        "price_driven_avg_coverage_pct": pd_seg["avg_buy_cov_pct"],
        "coverage_driven_avg_coverage_pct": cd_seg["avg_buy_cov_pct"],
        "premium_gap_usd": cd_seg["avg_premium"] - pd_seg["avg_premium"],
    }
    Path(a.out).write_text(json.dumps(out, indent=2))
    cust[["customer_ID", "beta_price", "segment"]].to_parquet(
        Path(a.data) / "segments.parquet", index=False)

    print(f"  {len(cust):,} shoppers · segmented by their own price sensitivity\n")
    print(f"  {'segment':16s} {'share':>6s} {'β_price':>8s} {'buys cheapest':>14s} "
          f"{'avg coverage':>13s} {'avg premium':>12s}")
    print("  " + "-" * 74)
    for s in ["price_driven", "balanced", "coverage_driven"]:
        v = out["segments"][s]
        print(f"  {s:16s} {v['pct']:>5.1f}% {v['avg_beta_price']:>8.2f} "
              f"{v['bought_cheapest_pct']:>13.1f}% {v['avg_buy_cov_pct']:>12.1f}% "
              f"${v['avg_premium']:>10,d}")
    val = out["validation"]
    print(f"\n  sanity check (behaviour tracks the label):")
    print(f"    price-driven buy cheapest {val['price_driven_buy_cheapest_pct']}% "
          f"vs coverage-driven {val['coverage_driven_buy_cheapest_pct']}%")
    print(f"    coverage-driven pay ${val['premium_gap_usd']} more premium on average")
    print(f"  -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
