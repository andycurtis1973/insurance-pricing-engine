# LinkedIn post

**Attach:** `video/out/insurance_pricing_demo.mp4` (~2 min narrated)
**Links:** repo + demo in the FIRST COMMENT (LinkedIn throttles reach on posts with outbound links).

---

Every insurance company competes on the same thing: the cheapest quote.

But that's not what shoppers actually do.

I took 97,009 real auto-insurance shopping sessions — real people, real quotes, real
purchases — and looked at what they picked.

Only **24.7% bought the cheapest thing they saw.**
Nearly half — **45.1% — traded up to richer coverage** and paid more for it.

Same quote engine. Two completely different shoppers. And if you lead with the
cheapest quote for everyone, you're discounting to the half who'd have paid more.

So I built an engine that tells them apart.

→ A **Bayesian choice model** reads how much price vs coverage drove each purchase —
with credible intervals, so it reports how *sure* it is. Price sensitivity isn't one
number: it's sharper for homeowners and young drivers, and flips for expensive cars.

→ A **Thompson Sampling bandit** then learns, from clicks, which offer to lead with
for each shopper — holding the price-driven on the lean quote so they don't walk, and
trading the coverage-lovers up.

Result: **+6.7% revenue per shopper, with conversion going UP, not down** — and the
bandit converges to within **0.49% of a perfect-knowledge oracle** without anyone
handing it the answer.

Now the part I want to be loud about, because it's where these demos usually cheat:

**The lift number is in simulation, and I'll tell you exactly why.**

The Allstate data is buyers-only — everyone in it bought something. So it physically
cannot tell you who would have *walked away* at a higher price. And that walk-away risk
is the entire reason smart pricing pays off.

So I added it: a conversion model **calibrated to published auto-insurance price
elasticities**, clearly labeled as the one simulated layer, with the elasticity
**swept** so the result doesn't hinge on one flattering value. That's how a real
pricing engine is stress-tested before it ever meets a live customer.

The shoppers are real. The preferences are real. The segments are real. The walk-away
response is a disclosed model. I'd rather show you the seam than hide it.

Two things I keep relearning building these:

1. **Heterogeneity is the whole game.** "The customer" is a fiction. A quarter of yours
are allergic to price; nearly half will pay for more if you stop leading with the
discount.

2. **The honest version is the stronger version.** Labeling the simulated layer didn't
weaken the story — it's the reason you can trust the rest of it.

Runs on a laptop in minutes. numpy and scipy, no GPU, no cloud bill.

If you price anything to a mix of customers: how much are you discounting to people who
were already going to say yes? 👇

#Pricing #Insurance #DataScience #MachineLearning #CFO

---

**First comment:**
> Code, data, and the elasticity sweep (with the simulated layer labeled):
> github.com/andycurtis1973/insurance-pricing-engine
> Interactive walkthrough: https://claude.ai/code/artifact/7cc2d8ed-eabc-4a0c-9d19-713c4577f888
> (artifact is private until you share it from the page's share menu)
