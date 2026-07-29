# Half your shoppers will pay for more coverage

Every insurer competes on the cheapest quote. But in **97,009 real auto-insurance
shopping sessions**, only a quarter bought the cheapest thing they saw — and nearly
half traded up to richer coverage and paid more for it.

This build tells those shoppers apart with a **Bayesian choice model**, then prices
each one with a **Thompson Sampling engine that learns from clicks**. It runs on a
laptop in minutes — pure numpy/scipy, no GPU, no cloud bill.

> **Read this first — what's real and what's simulated.**
> The shoppers, their menus, their price/coverage preferences, and the price- vs
> coverage-driven split are **real**, from the [Allstate Purchase Prediction
> Challenge](https://www.kaggle.com/c/allstate-purchase-prediction-challenge).
> The one **simulated** piece is *walk-away risk* — whether a shopper abandons at a
> higher price — because the dataset is **buyers-only** and cannot contain it. That
> layer is a logistic conversion model **calibrated to published auto-insurance price
> elasticities**, and its elasticity is **swept** to show the result doesn't hinge on
> one value. Every "lift" number here is **lift in simulation** — the standard way a
> pricing engine is stress-tested before it meets a live customer — **not** a claim
> about Allstate's revenue.

## What shoppers actually do

| | |
|---|---|
| Real shopping sessions | **97,009** |
| Median quotes viewed each | **6** |
| Saw more than one price | **96.8%** |
| **Bought the cheapest they saw** | **24.7%** |
| **Bought the richest coverage** | **45.1%** |
| Median premium | **$634** |

Two populations, hiding behind one quote engine.

## A Bayesian model of the choice

Each shopper picked one offer from the menu they were shown, so the model is a
**conditional logit** fit with a **Laplace posterior** — every coefficient comes with
a 95% credible interval, so we report how *sure* we are, not just a point estimate.
All five coefficients below exclude zero.

| Coefficient | mean | 95% CI |
|---|---|---|
| price | **−0.60** | [−0.71, −0.49] |
| coverage | **+0.12** | [+0.10, +0.13] |
| price × homeowner | −0.52 | [−0.67, −0.37] |
| price × young driver | −0.48 | [−0.62, −0.34] |
| price × car value | +0.43 | [+0.37, +0.49] |

It picks the offer they actually bought **42%** of the time — versus 26% for "assume
everyone takes the cheapest" and 39% for "assume everyone maxes coverage." Price
sensitivity isn't one number: it's sharper for homeowners and young drivers, and it
flips toward coverage for expensive cars.

## Three populations

Split by what they actually did with the menu in front of them — not a demographic guess.

| Segment | Share | Coverage bought | Avg premium |
|---|---|---|---|
| **Price-driven** (bought cheapest) | 24.7% | 53% of max | $626 |
| Balanced | 30.2% | 50% | $634 |
| **Coverage-driven** (bought richest) | 45.1% | **62%** | $638 |

## The engine (in simulation)

Revenue per shopper = P(convert) × premium, on **28,544 held-out shoppers**. The
walk-away response is the calibrated conversion model; the elasticity is swept.

| Strategy | Revenue/shopper | Conversion |
|---|---|---|
| Compete on price (lead cheapest) | $400.74 | 65.0% |
| Blanket upsell (lead richest) | $423.70 | 66.3% |
| **The engine (aim per shopper)** | **$427.48** | **67.2%** |

**+6.7% revenue per shopper over competing on price — and conversion goes up, not
down.** The lift is split on purpose:

- **Price-driven: left alone** (+0.1%; the engine trades up just 13% of them — pushing
  loses the sale).
- **Coverage-driven: traded up** (+11.8%).

**Robust, not cherry-picked:** sweep the calibrated elasticity from 0.5× to 1.5× and
the engine still lifts **5.5–8.2%**, conversion holding near 67%.

## It learns from clicks

The offline run assumed we already knew each segment's response. You don't — you learn
it. A **Thompson Sampling contextual bandit**: context = the segment, arms = lead with
lean / mid / rich coverage, reward = revenue. It explores, then exploits.

The response it learns is the whole story — push a shopper to richer coverage and:

| Segment | lead lean | lead rich |
|---|---|---|
| Price-driven | 65% convert | **48%** (they walk) |
| Coverage-driven | 66% convert | **70%** (they say yes) |

Same offer, opposite result. Streaming 95,070 shoppers through it, the bandit
**converges to within 0.49% of a perfect-knowledge oracle**, locking each segment's
best offer within a few hundred to a few thousand shoppers — while competing-on-price
leaves money on the table the entire time. No elasticities were handed to it.

## Layout

```
data/build_dataset.py     Allstate sessions -> choice sets + revealed behavior
model/choice.py           Bayesian conditional logit (Laplace posterior) + credible intervals
model/segment.py          price-driven vs coverage-driven, from real purchases
engine/simulator.py       THE SIMULATED LAYER — conversion calibrated to published elasticities
engine/optimize.py        three strategies scored head-to-head, elasticity swept
engine/bandit.py          Thompson Sampling: learn each segment's best offer from clicks
scripts/make_rundata.py   consolidate results -> results/rundata.json (demo + video read it)
web/build_demo.py         -> web/demo.html (interactive; embeds rundata)
video/                     the ~2-min narrated explainer
```

## Reproduce

Download `train.csv` from the [Allstate Purchase Prediction
Challenge](https://www.kaggle.com/c/allstate-purchase-prediction-challenge/data)
(Kaggle account + accepting the competition rules required), then:

```bash
cd data && python3 build_dataset.py --train train.csv --out out && cd ..
python3 model/choice.py   --data data/out --out results/choice.json
python3 model/segment.py  --data data/out --choice results/choice.json --out results/segments.json
python3 engine/optimize.py --data data/out --out results/engine.json
python3 engine/bandit.py   --data data/out --out results/bandit.json
python3 scripts/make_rundata.py
python3 web/build_demo.py
```

No accounts, no GPU, no standing infrastructure — the whole pipeline is numpy and
scipy. (The narrated video is the only part that touches AWS, just to synthesize the
voice-over.)

## The one thing to take away

Competing on price means discounting to people who would have paid more. The data can
tell you who they are; the honest move is to label the part the data can't.

*Calibration sources: Guven & McPhail, "Beyond the Cost Model: Understanding Price
Elasticity and Its Applications," Casualty Actuarial Society E-Forum, 2013; Akur8,
"Demand Modeling in Insurance."*
