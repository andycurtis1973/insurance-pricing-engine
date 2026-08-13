#!/usr/bin/env python3
"""Build web/lookalikes.json — the REAL demographic prior for the playground.

For each demographic cell (age band x home x car-value tier) with >=150 shoppers,
record what real Allstate customers like that bought: the price/balanced/coverage
segment mix, average coverage and premium. The playground uses this as the warm-start
prior before it tests offers. Demographics predict coverage (avg 42%-67% across cells)
but barely move the price-driven share (18%-34%) — which is exactly why the click test
is needed.

    python3 scripts/make_lookalikes.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def age_band(a):
    a = 40 if pd.isna(a) else a
    return "under25" if a < 25 else "25to44" if a < 45 else "45to64" if a < 65 else "65plus"


def car_band(v):
    v = str(v)
    return "low" if v in list("abc") else "mid" if v in list("def") else "high"


def main() -> int:
    cust = pd.read_parquet(ROOT / "data/out/customers.parquet")
    seg = pd.read_parquet(ROOT / "data/out/segments.parquet").set_index("customer_ID")["segment"]
    d = cust.set_index("customer_ID").join(seg)
    d["ageb"] = d["age_youngest"].map(age_band)
    d["home"] = d["homeowner"].fillna(0).astype(int).map({0: "renter", 1: "owner"})
    d["carb"] = d["car_value"].map(car_band)

    table = {}
    for (ab, hm, cb), g in d.groupby(["ageb", "home", "carb"]):
        if len(g) < 150:
            continue
        mix = g["segment"].value_counts(normalize=True)
        table[f"{ab}|{hm}|{cb}"] = {
            "n": int(len(g)),
            "price": round(float(mix.get("price_driven", 0)), 3),
            "balanced": round(float(mix.get("balanced", 0)), 3),
            "coverage": round(float(mix.get("coverage_driven", 0)), 3),
            "avg_cov_pct": round(float(g["buy_cov_pct"].mean()), 1),
            "avg_premium": int(g["buy_cost"].mean()),
            "pct_cheapest": round(float(g["bought_cheapest"].mean()) * 100, 1),
            "pct_richest": round(float(g["bought_richest_cov"].mean()) * 100, 1),
        }
    out = ROOT / "web/lookalikes.json"
    out.write_text(json.dumps(table, separators=(",", ":")))
    covs = [v["avg_cov_pct"] for v in table.values()]
    prices = [v["price"] for v in table.values()]
    print(f"  {len(table)} cells covering {sum(v['n'] for v in table.values()):,} shoppers -> {out}")
    print(f"  avg coverage {min(covs):.0f}-{max(covs):.0f}% (signal) · "
          f"price-driven {min(prices)*100:.0f}-{max(prices)*100:.0f}% (flat)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
