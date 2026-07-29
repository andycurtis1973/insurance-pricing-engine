#!/usr/bin/env python3
"""The online engine: learn each segment's best offer from clicks. No elasticities given.

The offline run assumed we already knew how each segment responds. In the real
world you don't — you learn it from who converts. This is a Thompson Sampling
contextual bandit: the context is the shopper's segment, the arms are the offers
we can lead with (lean / mid / rich), and the reward is revenue (premium if they
convert, 0 if they walk).

For each shopper the engine keeps a Beta posterior on conversion for every
(segment, arm), samples a conversion rate from each, multiplies by THIS shopper's
premium for that arm, and leads with the best draw. Then it sees convert / no-
convert (simulated — see simulator.py) and updates. Early on it explores; as the
posteriors sharpen it exploits. We watch it converge to the offline oracle while
a fixed "compete on price" policy leaves money on the table the whole time.

    python3 bandit.py --data ../data/out
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import simulator as S

ARMS = ["lean", "mid", "rich"]


def stream(datadir: Path):
    seg = pd.read_parquet(datadir / "segments.parquet").set_index("customer_ID")["segment"]
    rows = []
    for line in (datadir / "choices.jsonl").open():
        c = json.loads(line)
        cid = c["customer_ID"]
        if cid not in seg.index or len(c["offers"]) < 2:
            continue
        cand = S.candidate_offers(c["offers"])
        rows.append((seg.loc[cid], cand))
    return rows


def true_p(seg, offer, cand):
    ref = cand["lean"]
    return S.p_convert(seg, offer["cost"], offer["cov"], ref["cost"], ref["cov"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data/out")
    ap.add_argument("--out", default="../results/bandit.json")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    datadir = Path(a.data)

    rows = stream(datadir)
    rng = np.random.default_rng(a.seed)
    order = rng.permutation(len(rows))
    print(f"streaming {len(rows):,} shoppers through the bandit ...", flush=True)

    # Beta(1,1) prior on conversion for each (segment, arm)
    ab = {s: {arm: [1.0, 1.0] for arm in ARMS} for s in S.SEG_PARAMS}

    # per-segment revenue and average premium for each arm, in ONE pass:
    #   oracle_arm = the true revenue-maximising arm (uses simulated response)
    #   avg_prem   = mean premium of each arm (used for the greedy lock-in check)
    sc = {s: {arm: 0.0 for arm in ARMS} for s in S.SEG_PARAMS}
    prem_sum = {s: {arm: 0.0 for arm in ARMS} for s in S.SEG_PARAMS}
    seg_cnt = {s: 0 for s in S.SEG_PARAMS}
    for seg, cand in rows:
        for arm in ARMS:
            sc[seg][arm] += true_p(seg, cand[arm], cand) * cand[arm]["cost"]
            prem_sum[seg][arm] += cand[arm]["cost"]
        seg_cnt[seg] += 1
    oracle_arm = {s: (max(ARMS, key=lambda arm: sc[s][arm]) if seg_cnt[s] else "lean")
                  for s in S.SEG_PARAMS}
    avg_prem = {s: {arm: prem_sum[s][arm] / max(1, seg_cnt[s]) for arm in ARMS}
                for s in S.SEG_PARAMS}

    cum = {"bandit": 0.0, "compete": 0.0, "blanket": 0.0, "oracle": 0.0}
    curve = []
    snap_every = max(1, len(order) // 60)
    first_lock = {s: None for s in S.SEG_PARAMS}     # when greedy pick == oracle & stays

    for t, idx in enumerate(order, 1):
        seg, cand = rows[idx]
        # Thompson: sample a conversion rate per arm, score by this shopper's premium
        draw = {arm: rng.beta(ab[seg][arm][0], ab[seg][arm][1]) for arm in ARMS}
        pick = max(ARMS, key=lambda arm: draw[arm] * cand[arm]["cost"])
        offer = cand[pick]
        p = true_p(seg, offer, cand)
        convert = 1.0 if rng.random() < p else 0.0
        ab[seg][pick][0] += convert
        ab[seg][pick][1] += (1 - convert)
        cum["bandit"] += convert * offer["cost"]

        # reference policies are scored by EXPECTED revenue (deterministic, no coin
        # noise) so the oracle is a true ceiling; only the bandit learns from coins
        for name, arm in (("compete", "lean"), ("blanket", "rich"), ("oracle", oracle_arm[seg])):
            o = cand[arm]
            cum[name] += true_p(seg, o, cand) * o["cost"]

        # has the bandit's greedy choice matched the oracle for this segment?
        greedy = max(ARMS, key=lambda arm: (ab[seg][arm][0] / (ab[seg][arm][0] + ab[seg][arm][1]))
                     * avg_prem[seg][arm])
        if greedy == oracle_arm[seg] and first_lock[seg] is None and t > 200:
            first_lock[seg] = t

        if t % snap_every == 0 or t == len(order):
            curve.append({"t": t,
                          "bandit": round(cum["bandit"] / t, 2),
                          "compete": round(cum["compete"] / t, 2),
                          "blanket": round(cum["blanket"] / t, 2),
                          "oracle": round(cum["oracle"] / t, 2)})

    learned = {s: {arm: round(ab[s][arm][0] / (ab[s][arm][0] + ab[s][arm][1]), 3) for arm in ARMS}
               for s in S.SEG_PARAMS}
    n = len(order)
    out = {
        "n_stream": n, "arms": ARMS,
        "oracle_arm_per_segment": oracle_arm,
        "shoppers_to_lock_oracle_arm": first_lock,
        "learned_conversion_per_arm": learned,
        "final_rev_per_shopper": {k: round(cum[k] / n, 2) for k in cum},
        "regret_vs_oracle_pct": round((1 - cum["bandit"] / cum["oracle"]) * 100, 2),
        "lift_vs_compete_pct": round((cum["bandit"] / cum["compete"] - 1) * 100, 2),
        "curve": curve,
        "disclosure": "Conversions simulated by the calibrated model in simulator.py; "
                      "real Allstate menus + real segments. Online lift is in simulation.",
    }
    Path(a.out).write_text(json.dumps(out, indent=2))

    f = out["final_rev_per_shopper"]
    # the bandit's own decision rule is conversion x premium, so rank the same way
    out["bandit_best_arm_per_segment"] = {
        s: max(ARMS, key=lambda arm: learned[s][arm] * avg_prem[s][arm]) for s in S.SEG_PARAMS}
    Path(a.out).write_text(json.dumps(out, indent=2))

    print(f"\n  learned best offer per segment (bandit vs oracle):")
    for s in S.SEG_PARAMS:
        best = out["bandit_best_arm_per_segment"][s]
        tag = "OK" if best == oracle_arm[s] else "x"
        print(f"    {s:16s} bandit->{best:5s}  oracle->{oracle_arm[s]:5s}  [{tag}]")
    print(f"\n  revenue / shopper (after {n:,} shoppers):")
    print(f"    compete-on-price ${f['compete']:.2f}   blanket-upsell ${f['blanket']:.2f}")
    print(f"    bandit           ${f['bandit']:.2f}   oracle         ${f['oracle']:.2f}")
    print(f"\n  bandit: {out['lift_vs_compete_pct']:+.2f}% vs compete-on-price · "
          f"{out['regret_vs_oracle_pct']:.2f}% short of oracle")
    print(f"  -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
