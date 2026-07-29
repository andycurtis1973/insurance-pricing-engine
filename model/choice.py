#!/usr/bin/env python3
"""A Bayesian choice model of how people shop for insurance.

Each shopper picked ONE offer from the set they saw, so the right model is a
conditional logit: the offer's utility is linear in its price and its coverage
(relative to the others in that set), and the shopper picks the highest-utility
one. We fit it Bayesianly with a Laplace approximation — MAP under a Gaussian
prior, then the Hessian gives a Gaussian posterior — so every coefficient comes
with a credible interval. We report how *sure* we are of the price sensitivity,
not just a point estimate.

Interactions of price with customer traits (homeowner, young driver, car value)
let sensitivity differ across people — that heterogeneity is what tells the
price-driven shoppers apart from the coverage-driven ones.

    python3 choice.py --data ../data/out --out ../results/choice.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def load(datadir: Path):
    cust = pd.read_parquet(datadir / "customers.parquet").set_index("customer_ID")
    split = json.loads((datadir / "split.json").read_text())
    train_ids = set(split["train_ids"])

    # customer traits used to modulate price sensitivity (0/1 or ordinal, filled)
    homeowner = cust["homeowner"].fillna(0).astype(float)
    young = (cust["age_youngest"].fillna(40) < 25).astype(float)
    cval = cust["car_value"].astype("category").cat.codes.replace(-1, np.nan)
    cval = ((cval - cval.mean()) / (cval.std() + 1e-9)).fillna(0.0)
    traits = pd.DataFrame({"homeowner": homeowner, "young": young, "car_value": cval})

    sets, y_idx, meta = [], [], []
    for line in (datadir / "choices.jsonl").open():
        c = json.loads(line)
        cid = c["customer_ID"]
        offs = c["offers"]
        if len(offs) < 2 or cid not in cust.index:
            continue
        cost = np.array([o["cost"] for o in offs], float)
        cov = np.array([o["cov"] for o in offs], float)
        chosen = np.array([o["chosen"] for o in offs])
        if chosen.sum() != 1:
            continue
        # within-set centering — utility is about how an offer compares to the
        # others the shopper actually saw
        cost_c = (cost - cost.mean()) / 100.0        # in $100s
        cov_c = cov - cov.mean()
        tr = traits.loc[cid]
        X = np.column_stack([
            cost_c,                                  # price
            cov_c,                                   # coverage
            cost_c * tr["homeowner"],                # price x homeowner
            cost_c * tr["young"],                    # price x young driver
            cost_c * tr["car_value"],                # price x car value
            cov_c * tr["homeowner"],                 # coverage x homeowner
        ])
        sets.append((X, int(cid) in train_ids))
        y_idx.append(int(np.argmax(chosen)))
        meta.append(cid)
    names = ["price", "coverage", "price:homeowner", "price:young",
             "price:car_value", "coverage:homeowner"]
    return sets, np.array(y_idx), meta, names


def neglogpost(beta, sets_X, y_idx, train_mask, prior_sd=5.0):
    """Conditional-logit negative log-posterior (Gaussian prior)."""
    nll = 0.0
    grad = np.zeros_like(beta)
    for k in np.where(train_mask)[0]:
        X = sets_X[k]
        u = X @ beta
        u -= u.max()
        e = np.exp(u)
        p = e / e.sum()
        nll -= np.log(p[y_idx[k]] + 1e-12)
        grad += X.T @ p - X[y_idx[k]]
    # Gaussian prior  N(0, prior_sd^2)
    nll += 0.5 * np.sum(beta ** 2) / prior_sd ** 2
    grad += beta / prior_sd ** 2
    return nll, grad


def laplace_cov(beta, sets_X, y_idx, train_mask, prior_sd=5.0):
    """Posterior covariance = inverse of the Hessian at the MAP."""
    d = len(beta)
    Hbar = np.eye(d) / prior_sd ** 2
    for k in np.where(train_mask)[0]:
        X = sets_X[k]
        u = X @ beta
        u -= u.max()
        e = np.exp(u)
        p = e / e.sum()
        # Hessian of -loglik for a softmax choice: X'(diag(p) - pp')X
        A = np.diag(p) - np.outer(p, p)
        Hbar += X.T @ A @ X
    return np.linalg.inv(Hbar)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data/out")
    ap.add_argument("--out", default="../results/choice.json")
    a = ap.parse_args()

    print("loading choice sets ...", flush=True)
    sets, y_idx, meta, names = load(Path(a.data))
    sets_X = [s[0] for s in sets]
    train_mask = np.array([s[1] for s in sets])
    print(f"  {len(sets):,} choice sets ({train_mask.sum():,} train / "
          f"{(~train_mask).sum():,} test), {len(names)} params", flush=True)

    d = len(names)
    print("fitting conditional logit (MAP) ...", flush=True)
    res = minimize(lambda b: neglogpost(b, sets_X, y_idx, train_mask),
                   np.zeros(d), jac=True, method="L-BFGS-B",
                   options={"maxiter": 300})
    beta = res.x
    cov = laplace_cov(beta, sets_X, y_idx, train_mask)
    sd = np.sqrt(np.diag(cov))

    # ---- evaluate: does it pick the offer they actually bought? -------------
    def top1(mask):
        correct = tot = 0
        for k in np.where(mask)[0]:
            X = sets_X[k]
            if X.shape[0] == 0:
                continue
            pred = np.argmax(X @ beta)
            correct += (pred == y_idx[k]); tot += 1
        return correct / tot, tot

    # baselines: pick the cheapest / the richest coverage
    def baseline(mask, col):
        correct = tot = 0
        for k in np.where(mask)[0]:
            X = sets_X[k]
            pred = (np.argmin(X[:, 0]) if col == "cheapest" else np.argmax(X[:, 1]))
            correct += (pred == y_idx[k]); tot += 1
        return correct / tot

    acc, ntest = top1(~train_mask)
    base_cheap = baseline(~train_mask, "cheapest")
    base_rich = baseline(~train_mask, "richest")

    coefs = []
    for i, nm in enumerate(names):
        lo, hi = beta[i] - 1.96 * sd[i], beta[i] + 1.96 * sd[i]
        coefs.append({"name": nm, "mean": round(float(beta[i]), 4),
                      "sd": round(float(sd[i]), 4),
                      "ci95": [round(float(lo), 4), round(float(hi), 4)],
                      "significant": bool(lo > 0 or hi < 0)})

    out = {
        "model": "Bayesian conditional logit (Laplace posterior)",
        "n_sets": len(sets), "n_test": ntest, "n_params": d,
        "top1_accuracy": round(float(acc), 4),
        "baseline_cheapest": round(float(base_cheap), 4),
        "baseline_richest_coverage": round(float(base_rich), 4),
        "coefficients": coefs,
        # price sensitivity for a reference shopper (renter, older, avg car)
        "price_coef": coefs[0], "coverage_coef": coefs[1],
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2))

    print(f"\n  top-1 accuracy (picks the bought offer): {acc:.3f}")
    print(f"    vs cheapest-always {base_cheap:.3f} · richest-coverage-always {base_rich:.3f}")
    print(f"\n  {'coefficient':22s} {'mean':>8s} {'95% credible interval':>26s}")
    print("  " + "-" * 60)
    for c in coefs:
        star = " *" if c["significant"] else ""
        print(f"  {c['name']:22s} {c['mean']:>8.3f}   [{c['ci95'][0]:>7.3f}, {c['ci95'][1]:>7.3f}]{star}")
    print(f"\n  -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
