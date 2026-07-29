#!/usr/bin/env python3
"""Turn Allstate shopping sessions into choice sets + revealed behavior.

The Allstate Purchase Prediction data is real: 97,009 people shopping for auto
insurance. Each viewed a series of quotes (record_type 0) — a 7-part coverage
bundle A..G at a real cost — and bought one (record_type 1). That sequence is the
"clickstream": it reveals whether a shopper chased the cheapest price or traded
up to more coverage.

We reduce each session to a choice set — the distinct offers seen, and which was
bought — plus the customer's features and their revealed price/coverage behavior.

Outputs (out/):
    customers.parquet   one row per customer: features, purchase, session summary
    choices.jsonl       per customer: [{coverage, cost, chosen}] over offers seen
    split.json          train/test customer ids (70/30 by customer)
    summary.json        corpus facts for the story

    python3 build_dataset.py --train train.csv --out out
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

OPTS = list("ABCDEFG")
# max level per option -> a coverage index in [0, 1]
MAXLVL = {"A": 2, "B": 1, "C": 4, "D": 3, "E": 1, "F": 3, "G": 4}
COVMAX = sum(MAXLVL.values())          # 18
FEATS = ["group_size", "homeowner", "car_age", "car_value", "risk_factor",
         "age_oldest", "age_youngest", "married_couple", "C_previous",
         "duration_previous", "state"]


def coverage_index(row) -> int:
    return int(sum(int(row[o]) for o in OPTS))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="train.csv")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    df = pd.read_csv(a.train)
    df["cov"] = df[OPTS].sum(axis=1).astype(int)
    df["bundle"] = df[OPTS].astype(int).astype(str).agg("".join, axis=1)

    cust_rows, choices = [], []
    n = df["customer_ID"].nunique()
    print(f"  {len(df):,} rows, {n:,} customers -> building choice sets", flush=True)

    for cid, g in df.groupby("customer_ID", sort=False):
        buy = g[g.record_type == 1]
        if len(buy) != 1:
            continue
        buy = buy.iloc[0]
        quotes = g[g.record_type == 0]
        if len(quotes) == 0:
            continue

        # the choice set = distinct (bundle, cost) offers the shopper actually saw
        seen = quotes[["bundle", "cov", "cost"]].drop_duplicates()
        bought_bundle = buy["bundle"]
        offers = []
        for _, o in seen.iterrows():
            offers.append({"cov": int(o["cov"]), "cost": int(o["cost"]),
                           "chosen": int(o["bundle"] == bought_bundle)})
        # if the purchased bundle wasn't among the viewed quotes, add it as chosen
        if not any(x["chosen"] for x in offers):
            offers.append({"cov": int(buy["cov"]), "cost": int(buy["cost"]), "chosen": 1})
        choices.append({"customer_ID": int(cid), "offers": offers})

        costs = quotes["cost"].to_numpy()
        covs = quotes["cov"].to_numpy()
        rec = {"customer_ID": int(cid),
               "n_quotes": int(len(quotes)),
               "cost_min": int(costs.min()), "cost_max": int(costs.max()),
               "cost_range": int(costs.max() - costs.min()),
               "cov_min": int(covs.min()), "cov_max": int(covs.max()),
               "buy_cost": int(buy["cost"]), "buy_cov": int(buy["cov"]),
               "buy_cov_pct": round(buy["cov"] / COVMAX * 100, 1),
               # revealed behaviour: did they buy near the cheapest, or near the richest?
               "bought_cheapest": int(buy["cost"] <= costs.min() + 1),
               "bought_richest_cov": int(buy["cov"] >= covs.max()),
               # where the purchase sits in the seen cost/coverage range (0..1)
               "cost_pos": round((buy["cost"] - costs.min()) / max(1, costs.max() - costs.min()), 3),
               "cov_pos": round((buy["cov"] - covs.min()) / max(1, covs.max() - covs.min()), 3)}
        for f in FEATS:
            rec[f] = buy[f]
        cust_rows.append(rec)

    cust = pd.DataFrame(cust_rows)
    print(f"  usable customers: {len(cust):,}", flush=True)

    # 70/30 split by customer
    rng = np.random.default_rng(42)
    ids = cust["customer_ID"].to_numpy().copy()
    rng.shuffle(ids)
    cut = int(0.7 * len(ids))
    split = {"train": ids[:cut].tolist(), "test": ids[cut:].tolist()}

    cust.to_parquet(out / "customers.parquet", index=False)
    with (out / "choices.jsonl").open("w") as f:
        for c in choices:
            f.write(json.dumps(c) + "\n")
    (out / "split.json").write_text(json.dumps({"train": split["train"][:0] and split["train"],
                                                "n_train": cut, "n_test": len(ids) - cut,
                                                "train_ids": split["train"], "test_ids": split["test"]}))

    summary = {
        "n_customers": int(len(cust)),
        "median_quotes": int(cust["n_quotes"].median()),
        "avg_quotes": round(float(cust["n_quotes"].mean()), 1),
        "cost_median": int(cust["buy_cost"].median()),
        "cost_p10": int(cust["buy_cost"].quantile(.1)),
        "cost_p90": int(cust["buy_cost"].quantile(.9)),
        "pct_bought_cheapest": round(float(cust["bought_cheapest"].mean()) * 100, 1),
        "pct_bought_richest_cov": round(float(cust["bought_richest_cov"].mean()) * 100, 1),
        "pct_saw_price_variation": round(float((cust["cost_range"] > 0).mean()) * 100, 1),
        "avg_cost_range": int(cust["cost_range"].mean()),
        "coverage_max_index": COVMAX,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))

    print("\n  === real shopping behaviour ===")
    print(f"  customers                     {summary['n_customers']:,}")
    print(f"  quotes viewed (median/avg)    {summary['median_quotes']} / {summary['avg_quotes']}")
    print(f"  premium (p10/median/p90)      ${summary['cost_p10']} / ${summary['cost_median']} / ${summary['cost_p90']}")
    print(f"  saw >1 price in their session {summary['pct_saw_price_variation']}%  (avg spread ${summary['avg_cost_range']})")
    print(f"  bought the cheapest they saw  {summary['pct_bought_cheapest']}%")
    print(f"  bought the richest coverage   {summary['pct_bought_richest_cov']}%")
    print(f"  -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
