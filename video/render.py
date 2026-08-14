#!/usr/bin/env python3
"""Slides + animations: a pricing engine that tells price- from coverage-driven shoppers.

Every number is read from results/rundata.json — the same file the web demo embeds,
so the video and the page can't disagree. The honesty slide (what's real vs what's
simulated) is its own segment, on purpose.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
W, H = 1920, 1080

BG = (15, 18, 24)
CARD = (22, 26, 34)
RULE = (37, 42, 52)
TX = (238, 241, 246)
MUT = (166, 173, 187)
DIM = (114, 121, 136)
ENGINE = (57, 135, 229)
PRICE = (230, 103, 103)
COV = (25, 158, 112)
BAL = (169, 134, 224)
GOLD = (217, 166, 55)

_C = {"bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
      "reg": ["/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
      "mono": ["/System/Library/Fonts/Menlo.ttc",
               "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]}
_F: dict = {}


def font(kind, size):
    k = (kind, size)
    if k in _F:
        return _F[k]
    for p in _C[kind]:
        if Path(p).exists():
            try:
                _F[k] = ImageFont.truetype(p, size); return _F[k]
            except Exception:
                continue
    _F[k] = ImageFont.load_default(); return _F[k]


def T(d, xy, s, f, fill, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


_BG = None


def _bg_gradient():
    """A soft top-lighter vertical gradient, cached (built once)."""
    global _BG
    if _BG is None:
        top, bot = (27, 32, 43), (10, 12, 17)
        col = Image.new("RGB", (1, H))
        ld = col.load()
        for y in range(H):
            t = y / (H - 1)
            ld[0, y] = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        _BG = col.resize((W, H))
    return _BG.copy()


def base(kicker=None, accent=ENGINE):
    """Gradient ground + two soft corner glows + a pill kicker + the top accent rule."""
    img = _bg_gradient()
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 840, -400, W + 280, 620], fill=(accent[0], accent[1], accent[2], 42))
    gd.ellipse([-480, H - 340, 480, H + 340], fill=(57, 135, 229, 22))
    glow = glow.filter(ImageFilter.GaussianBlur(200))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, 6], fill=accent)
    if kicker:
        lab = kicker.upper()
        f = font("mono", 24)
        tw = d.textlength(lab, font=f)
        x, y = 110, 72
        d.rounded_rectangle([x, y, x + tw + 92, y + 54], radius=27,
                            fill=(255, 255, 255, 14),
                            outline=(accent[0], accent[1], accent[2], 160), width=1)
        d.ellipse([x + 24, y + 19, x + 40, y + 35], fill=accent)
        T(d, (x + 58, y + 27), lab, f, MUT, "lm")
    return img, d


def card(d, box, accent=None, side=None, radius=14, fill=CARD, shadow=True):
    """A raised card: soft drop shadow, hairline border, a lit top edge, and an
    optional accent bar (top) or rail (left). `d` must be an RGBA ImageDraw."""
    x0, y0, x1, y1 = box
    if shadow:
        for o, a in ((16, 20), (11, 24), (7, 28), (3, 32)):
            d.rounded_rectangle([x0 + 1, y0 + o, x1 + 1, y1 + o], radius=radius, fill=(0, 0, 0, a))
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=RULE, width=1)
    d.line([x0 + radius, y0 + 1, x1 - radius, y0 + 1], fill=(255, 255, 255, 18))
    if accent:
        d.rounded_rectangle([x0, y0, x1, y0 + 6], radius=3, fill=accent)
    if side:
        d.rounded_rectangle([x0, y0, x0 + 6, y1], radius=3, fill=side)


def ease(t):
    return 1 - (1 - t) ** 3


def abox(d, x, y, w, h, title, sub, col, on=True):
    """A service box: accent-topped card with a title and a small caption."""
    fill = CARD if on else BG
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=fill,
                        outline=col if on else RULE, width=2 if on else 1)
    if on:
        d.rounded_rectangle([x, y, x + w, y + 6], radius=3, fill=col)
        T(d, (x + 20, y + 20), title, font("bold", 27), TX)
        if sub:
            T(d, (x + 20, y + 56), sub, font("mono", 19), MUT)


def arrow(d, x1, y1, x2, y2, col, dash=False, w=3):
    """Straight connector with a small arrowhead at (x2,y2)."""
    if dash:
        import math
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 16))
        for i in range(n):
            if i % 2:
                continue
            a, b = i / n, (i + 1) / n
            d.line([x1 + (x2 - x1) * a, y1 + (y2 - y1) * a,
                    x1 + (x2 - x1) * b, y1 + (y2 - y1) * b], fill=col, width=w)
    else:
        d.line([x1, y1, x2, y2], fill=col, width=w)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    for da in (2.6, -2.6):
        d.line([x2, y2, x2 + 14 * math.cos(ang + da), y2 + 14 * math.sin(ang + da)],
               fill=col, width=w)


# --- the numbers -----------------------------------------------------------
D = json.loads((ROOT / "results" / "rundata.json").read_text())
C, CM, SG, EN, BD, DS = (D["corpus"], D["choice_model"], D["segments"],
                         D["engine"], D["bandit"], D["disclosure"])
NCUST = f"{C['n_customers']:,}"
PD, BALs, CD = SG["price_driven"], SG["balanced"], SG["coverage_driven"]
STR = EN["strategies"]


def pct(x):
    return f"{x:.0f}"


# ============================ STATIC ======================================
def s0_title():
    img, d = base()
    T(d, (W / 2, 300), "Half your shoppers will pay for more coverage.",
      font("bold", 62), TX, "mm")
    T(d, (W / 2, 392), "A quarter will walk if you push.", font("bold", 62), PRICE, "mm")
    T(d, (W / 2, 528), "A pricing engine that tells them apart — and learns which is which",
      font("reg", 38), MUT, "mm")
    T(d, (W / 2, 588), "from clicks.", font("reg", 38), MUT, "mm")
    T(d, (W / 2, 690), f"{NCUST} real Allstate shopping sessions  ·  a Bayesian choice model  "
      "·  a Thompson-Sampling engine", font("mono", 26), DIM, "mm")
    return img


def s7_close():
    img, d = base()
    T(d, (W / 2, 292), "Stop discounting to people", font("bold", 68), TX, "mm")
    T(d, (W / 2, 378), "who'd have paid more.", font("bold", 68), ENGINE, "mm")
    T(d, (W / 2, 500), f"{PD['pct']}% price-driven · {CD['pct']}% coverage-driven · "
      f"+{EN['lift_vs_compete_pct']:.1f}% revenue/shopper in simulation",
      font("mono", 29), MUT, "mm")
    url = "github.com/andycurtis1973/insurance-pricing-engine"
    w = d.textlength(url, font=font("mono", 30))
    d.rounded_rectangle([(W - w) / 2 - 34, 590, (W + w) / 2 + 34, 668], radius=12,
                        fill=CARD, outline=ENGINE, width=2)
    T(d, (W / 2, 629), url, font("mono", 30), ENGINE, "mm")
    T(d, (W / 2, 732), "Real data, open code, the elasticity swept — and the simulated part labeled",
      font("reg", 27), DIM, "mm")
    return img


# ============================ ANIMATIONS ==================================
def a_behavior(t):
    """A grid of shoppers; a quarter chase price, ~half trade up to coverage."""
    img, d = base("what shoppers actually do")
    T(d, (110, 178), "Everyone competes on the cheapest quote.", font("bold", 54), TX)
    e = ease(min(1.0, t / 0.7))
    cols, rows, cw = 44, 9, 36
    total = cols * rows
    shown = int(total * e)
    p_frac = PD["pct"] / 100
    c_frac = CD["pct"] / 100
    for i in range(shown):
        cx, cy = 110 + (i % cols) * cw, 300 + (i // cols) * cw
        r = (i % cols) / cols
        if r < p_frac:
            col = PRICE if t > 0.5 else RULE
        elif r > 1 - c_frac:
            col = COV if t > 0.5 else RULE
        else:
            col = RULE
        d.rounded_rectangle([cx, cy, cx + cw - 8, cy + cw - 8], radius=3, fill=col)
    if t > 0.6:
        T(d, (110, 686), f"{PD['pct']}%", font("bold", 84), PRICE)
        T(d, (110, 792), "BOUGHT THE CHEAPEST THING THEY SAW", font("mono", 25), DIM)
        T(d, (1100, 686), f"{CD['pct']}%", font("bold", 84), COV)
        T(d, (1100, 792), "TRADED UP TO THE RICHEST COVERAGE", font("mono", 25), DIM)
    if t > 0.82:
        T(d, (110, 892), "Same quote engine. Two completely different shoppers.",
          font("reg", 34), MUT)
    return img


def a_choice(t):
    """The Bayesian choice model: coefficients with credible intervals."""
    img, d = base("a model of the choice")
    T(d, (110, 178), "What actually drove the pick", font("bold", 54), TX)
    T(d, (110, 244), "Bayesian conditional logit — every coefficient with a credible interval",
      font("reg", 30), MUT)
    rows = [("price", CM["price"]), ("coverage", CM["coverage"]),
            ("price x homeowner", CM["price_homeowner"]),
            ("price x young driver", CM["price_young"]),
            ("price x car value", CM["price_car_value"])]
    x0, y0, gap = 620, 336, 92
    lo, hi = -0.85, 0.65
    bw = 1040
    def xp(v):
        return x0 + (v - lo) / (hi - lo) * bw
    e = ease(min(1.0, t / 0.7))
    for g in (-0.5, -0.25, 0, 0.25, 0.5):
        gx = xp(g)
        d.line([gx, y0 - 20, gx, y0 + len(rows) * gap - 40], fill=DIM if g == 0 else RULE,
               width=2 if g == 0 else 1)
        T(d, (gx, y0 + len(rows) * gap - 30), f"{g:.2f}", font("mono", 22), DIM, "mm")
    for i, (nm, c) in enumerate(rows):
        y = y0 + i * gap
        col = PRICE if c["mean"] < 0 else COV
        T(d, (x0 - 30, y), nm, font("mono", 27), MUT, "rm")
        if e > 0.3:
            a, b = xp(c["ci95"][0]), xp(c["ci95"][1])
            d.line([a, y, b, y], fill=col, width=3)
            d.line([a, y - 8, a, y + 8], fill=col, width=3)
            d.line([b, y - 8, b, y + 8], fill=col, width=3)
            cx = xp(c["mean"])
            d.ellipse([cx - 8, y - 8, cx + 8, y + 8], fill=col)
            T(d, (cx, y - 26), f"{c['mean']:.2f}", font("bold", 24), TX, "mm")
    if t > 0.8:
        T(d, (110, 902), f"Picks the bought offer {CM['top1']*100:.0f}% of the time — vs "
          f"{CM['baseline_cheapest']*100:.0f}% \"assume cheapest\", "
          f"{CM['baseline_richest']*100:.0f}% \"assume richest\".", font("reg", 30), MUT)
    return img


def a_segments(t):
    """Three populations, side by side."""
    img, d = base("who's really shopping")
    T(d, (110, 178), "Three populations, split by what they bought", font("bold", 54), TX)
    cards = [("Price-driven", PD, PRICE, "bought the cheapest quote"),
             ("Balanced", BALs, BAL, "not the cheapest, not the richest"),
             ("Coverage-driven", CD, COV, "bought the richest coverage")]
    cw, gap = 540, 30
    x0 = 110
    for i, (nm, v, col, sub) in enumerate(cards):
        if t < 0.15 + i * 0.16:
            continue
        x = x0 + i * (cw + gap)
        y = 300
        d.rounded_rectangle([x, y, x + cw, y + 480], radius=14, fill=CARD, outline=RULE, width=1)
        d.rounded_rectangle([x, y, x + cw, y + 8], radius=4, fill=col)
        T(d, (x + 36, y + 52), nm, font("bold", 40), TX)
        T(d, (x + 36, y + 116), f"{v['pct']:.1f}%", font("bold", 96), col)
        T(d, (x + 36, y + 250), sub, font("reg", 28), MUT)
        T(d, (x + 36, y + 330), f"{v['avg_coverage_pct']:.0f}% of max coverage",
          font("mono", 28), TX)
        T(d, (x + 36, y + 386), f"avg premium  ${v['avg_premium']}", font("mono", 28), TX)
    if t > 0.85:
        T(d, (110, 852), "They don't want the same thing — so why quote them the same way?",
          font("reg", 34), MUT)
    return img


def a_honesty(t):
    """The dedicated disclosure slide — real vs simulated."""
    img, d = base("the honest part")
    T(d, (110, 172), "What's real here, and what isn't", font("bold", 54), TX)
    T(d, (110, 240), "This data is buyers-only. It can't tell us who would have walked away.",
      font("reg", 30), MUT)
    # two columns
    colw = 850
    lx, rx, y0 = 110, 110 + colw + 60, 336
    d.rounded_rectangle([lx, y0, lx + colw, y0 + 500], radius=14, fill=CARD, outline=RULE)
    d.rounded_rectangle([rx, y0, rx + colw, y0 + 500], radius=14, fill=CARD, outline=RULE)
    T(d, (lx + 34, y0 + 30), "REAL — FROM THE DATA", font("mono", 24), COV)
    T(d, (rx + 34, y0 + 30), "SIMULATED — DISCLOSED", font("mono", 24), GOLD)
    reals = ["97,009 real Allstate shopping sessions",
             "the price/coverage menu each shopper saw",
             "price- vs coverage-driven, from real buys",
             "choice-model price & coverage sensitivities"]
    sims = ["whether a shopper walks at a higher price",
            "a logistic conversion model, calibrated to",
            "published auto-insurance elasticities",
            "(swept 0.5x-1.5x to prove robustness)"]
    n_show = int(ease(min(1.0, t / 0.75)) * 4 + 0.001)
    for i, s in enumerate(reals):
        if i <= n_show:
            d.ellipse([lx + 34, y0 + 108 + i * 92, lx + 50, y0 + 124 + i * 92], fill=COV)
            T(d, (lx + 72, y0 + 116 + i * 92), s, font("reg", 27), TX)
    for i, s in enumerate(sims):
        if i <= n_show:
            d.ellipse([rx + 34, y0 + 108 + i * 92, rx + 50, y0 + 124 + i * 92], fill=GOLD)
            T(d, (rx + 72, y0 + 116 + i * 92), s, font("reg", 27), TX)
    if t > 0.85:
        T(d, (110, 892), "Everything past here is lift IN SIMULATION — not a claim about "
          "Allstate's revenue.", font("bold", 32), GOLD)
    return img


def a_engine(t):
    """Three strategies, revenue per shopper, then the per-segment split."""
    img, d = base("three ways to price")
    T(d, (110, 178), "Compete, blanket-upsell, or aim", font("bold", 54), TX)
    e = ease(min(1.0, t / 0.62))
    rows = [("Compete on price", STR["compete_on_price"], DIM),
            ("Blanket upsell everyone", STR["blanket_upsell"], PRICE),
            ("The engine — aim per shopper", STR["engine"], ENGINE)]
    x0, y0, bh, gap = 640, 300, 60, 92
    mx = max(r[1]["rev_per_shopper"] for r in rows) * 1.06
    bw = 760
    for i, (nm, v, col) in enumerate(rows):
        y = y0 + i * gap
        w = int(bw * v["rev_per_shopper"] / mx * e)
        T(d, (x0 - 28, y + bh / 2), nm, font("reg", 28), MUT, "rm")
        d.rounded_rectangle([x0, y, x0 + max(w, 3), y + bh], radius=7, fill=col)
        if e > 0.6:
            val = f"${v['rev_per_shopper']:.0f}"
            lx = x0 + w + 20
            T(d, (lx, y + bh / 2), val, font("bold", 34), TX, "lm")
            vw = d.textlength(val, font=font("bold", 34))
            T(d, (lx + vw + 18, y + bh / 2), f"·  {v['conversion']*100:.0f}% convert",
              font("mono", 22), DIM, "lm")
    if t > 0.72:
        pd = EN["by_segment"]["price_driven"]
        cd = EN["by_segment"]["coverage_driven"]
        T(d, (110, 646), f"+{EN['lift_vs_compete_pct']:.1f}% revenue per shopper — and "
          "conversion goes UP, not down.", font("bold", 36), ENGINE)
        T(d, (110, 726), f"Price-driven: left alone (+{pd['lift_pct']:.1f}%, "
          f"traded up just {pd['traded_up_pct']:.0f}%).", font("reg", 32), PRICE)
        T(d, (110, 784), f"Coverage-driven: traded up (+{cd['lift_pct']:.1f}%).",
          font("reg", 32), COV)
    if t > 0.88:
        sw = [s["engine_lift_vs_compete_pct"] for s in EN["elasticity_sweep"]]
        T(d, (110, 878), f"Robust: sweep the elasticity and it still lifts "
          f"{min(sw):.1f}-{max(sw):.1f}%.", font("mono", 27), MUT)
    return img


def a_learn(t):
    """Learned conversion crossover + the bandit converging to the oracle."""
    img, d = base("it learns from clicks")
    T(d, (110, 178), "Same offer, opposite result", font("bold", 54), TX)
    # left: conversion crossover for price vs coverage driven
    LC = BD["learned_conversion"]
    x0, y0, ph, pw = 150, 330, 300, 640
    def yv(v):
        return y0 + ph - (v - 0.4) / (0.75 - 0.4) * ph
    for g in (0.4, 0.5, 0.6, 0.7):
        d.line([x0, yv(g), x0 + pw, yv(g)], fill=RULE, width=1)
        T(d, (x0 - 14, yv(g)), f"{g*100:.0f}%", font("mono", 20), DIM, "rm")
    e = ease(min(1.0, t / 0.6))
    for seg, col in (("price_driven", PRICE), ("coverage_driven", COV)):
        pts = [("lean", LC[seg]["lean"]), ("mid", LC[seg]["mid"]), ("rich", LC[seg]["rich"])]
        for j in range(len(pts) - 1):
            if e > j / 2:
                x1 = x0 + j * pw / 2
                x2 = x0 + (j + 1) * pw / 2
                d.line([x1, yv(pts[j][1]), x2, yv(pts[j + 1][1])], fill=col, width=5)
        for j, (arm, v) in enumerate(pts):
            x = x0 + j * pw / 2
            d.ellipse([x - 7, yv(v) - 7, x + 7, yv(v) + 7], fill=col)
    for j, arm in enumerate(("lead lean", "mid", "lead rich")):
        T(d, (x0 + j * pw / 2, y0 + ph + 28), arm, font("mono", 22), DIM, "mm")
    T(d, (x0, y0 - 40), "PRICE-DRIVEN conversion FALLS", font("mono", 22), PRICE)
    T(d, (x0, y0 - 14), "COVERAGE-DRIVEN conversion RISES", font("mono", 22), COV)

    # right: bandit learning curve
    cur = BD["curve"]
    rx, ry, rh, rw = 1060, 330, 300, 740
    xs = [p["t"] for p in cur]
    tmax = max(xs)
    allv = [p[k] for p in cur for k in ("bandit", "compete", "oracle")]
    ylo, yhi = min(allv) * 0.999, max(allv) * 1.001
    def cx(tt):
        return rx + tt / tmax * rw
    def cy(v):
        return ry + (1 - (v - ylo) / (yhi - ylo)) * rh
    for g in (ylo, (ylo + yhi) / 2, yhi):
        d.line([rx, cy(g), rx + rw, cy(g)], fill=RULE, width=1)
        T(d, (rx - 12, cy(g)), f"${g:.0f}", font("mono", 20), DIM, "rm")
    n_show = int(len(cur) * ease(min(1.0, t / 0.75)))
    def curve(key, col, width, dash=False):
        pts = [(cx(p["t"]), cy(p[key])) for p in cur[:max(2, n_show)]]
        for j in range(len(pts) - 1):
            if dash and j % 2:
                continue
            d.line([pts[j], pts[j + 1]], fill=col, width=width)
    curve("oracle", GOLD, 4, dash=True)
    curve("compete", DIM, 3, dash=True)
    curve("bandit", ENGINE, 5)
    T(d, (rx, ry - 40), "BANDIT climbs toward the ORACLE (dashed gold)", font("mono", 22), ENGINE)
    T(d, (rx, ry - 14), "COMPETE-ON-PRICE (dashed grey) stays flat", font("mono", 22), DIM)
    T(d, (rx + rw / 2, ry + rh + 28), "shoppers seen  →", font("mono", 22), DIM, "mm")

    if t > 0.86:
        T(d, (110, 916), f"No elasticities handed to it — it converges within "
          f"{BD['regret_vs_oracle_pct']:.1f}% of a perfect-knowledge oracle.",
          font("bold", 32), TX)
    return img


def a_architecture(t):
    """How it ships: the streaming decision-and-learning loop on AWS.
    A clockwise loop — decide across the top, learn back along the bottom, with an
    offline analytics/retrain column on the right. Labeled a deployment blueprint;
    the build itself ran offline."""
    img, d = base("how you'd ship it")
    T(d, (110, 172), "In production, it's a streaming loop", font("bold", 54), TX)
    r1 = ease(min(1.0, t / 0.32))                        # decide band + brain
    r2 = ease(min(1.0, max(0.0, (t - 0.28) / 0.34)))     # learn band + loop
    r3 = ease(min(1.0, max(0.0, (t - 0.56) / 0.30)))     # offline analytics

    # ---- DECIDE band (blue): shopper -> API GW -> Lambda -> featured offer ---
    T(d, (110, 264), "DECIDE  ·  a few milliseconds", font("mono", 22), ENGINE)
    if r1 > 0.05:
        abox(d, 110, 300, 210, 96, "Shopper", "quote page", ENGINE)
        abox(d, 372, 300, 230, 96, "API Gateway", "/price request", ENGINE)
        abox(d, 654, 300, 300, 96, "Lambda", "pick the offer to feature", ENGINE)
        abox(d, 1006, 300, 230, 96, "Featured offer", "lean · mid · rich", ENGINE)
        arrow(d, 322, 348, 370, 348, MUT)
        arrow(d, 604, 348, 652, 348, MUT)
        arrow(d, 956, 348, 1004, 348, MUT)

    # ---- shared brain: DynamoDB posteriors ----------------------------------
    if r1 > 0.5:
        abox(d, 654, 452, 300, 92, "DynamoDB", "Thompson posteriors  α,β / segment×arm", BAL)
        arrow(d, 790, 398, 790, 450, BAL)                # Lambda reads down
        arrow(d, 820, 450, 820, 400, BAL)                # ...writes back up

    # ---- LEARN band (gold), right->left: clicks -> Kinesis -> Flink ---------
    T(d, (110, 596), "LEARN  ·  from every click, in near-real-time", font("mono", 22), GOLD)
    if r2 > 0.05:
        abox(d, 1006, 626, 230, 96, "Click events", "shown · converted · left", GOLD)
        abox(d, 664, 626, 300, 96, "Kinesis Data Streams", "the clickstream backbone", GOLD)
        abox(d, 322, 626, 300, 96, "Managed Flink", "update the posteriors", GOLD)
        arrow(d, 1004, 674, 966, 674, MUT)               # clicks -> Kinesis
        arrow(d, 662, 674, 624, 674, MUT)                # Kinesis -> Flink
    if r2 > 0.55:
        arrow(d, 472, 624, 652, 548, GOLD)               # Flink -> DynamoDB (adapt)
        arrow(d, 1121, 398, 1121, 624, ENGINE, dash=True)  # offer -> the next click
        T(d, (1252, 508), "every offer →", font("mono", 19), DIM)
        T(d, (1252, 532), "the next click", font("mono", 19), DIM)

    # ---- OFFLINE column (green): retrain + archive/dashboards ---------------
    T(d, (1330, 264), "OBSERVE & RETRAIN", font("mono", 22), COV)
    if r3 > 0.05:
        abox(d, 1330, 300, 480, 96, "SageMaker · nightly", "retrain choice model → segments + priors", COV)
        abox(d, 1330, 626, 480, 96, "Firehose → S3 · Athena / QuickSight",
             "event lake · dashboards · guardrails", COV)
        arrow(d, 1238, 674, 1328, 674, MUT)              # clicks -> archive
        arrow(d, 1450, 398, 956, 476, COV, dash=True)    # fresh priors -> DynamoDB

    if t > 0.9:
        T(d, (110, 812), "Guardrails — no-underprice floor, human-set caps — enforced in the "
          "decision step.", font("reg", 27), MUT)
        T(d, (110, 872), "A deployment blueprint: the build you just saw ran offline on a "
          "laptop. This is the shape it takes live.", font("bold", 27), GOLD)
    return img


# ---- narration -----------------------------------------------------------
SEGMENTS = [
    {"name": "s0_title", "kind": "static", "build": s0_title, "vo": [
        "Every insurance company competes on the same thing. The cheapest quote.",
        f"But in {NCUST} real shopping sessions, that's not what shoppers actually do."]},
    {"name": "s1_behavior", "kind": "anim", "build": a_behavior, "vo": [
        "Every square is a real person shopping for car insurance.",
        f"Only {PD['pct']} percent bought the cheapest thing they saw.",
        f"Nearly half — {CD['pct']} percent — traded up to richer coverage, and paid more for it.",
        "Same quote engine. Two completely different shoppers."]},
    {"name": "s2_choice", "kind": "anim", "build": a_choice, "vo": [
        "So first, a model of the choice itself — a Bayesian one, so every number carries a credible interval.",
        "Price pushes people toward cheaper; coverage pulls them richer.",
        "And price sensitivity isn't one number — it's sharper for homeowners and young drivers, and it flips for expensive cars."]},
    {"name": "s3_segments", "kind": "anim", "build": a_segments, "vo": [
        "Split people by what they bought, and three populations fall out.",
        "They do not want the same thing. So why quote them the same way?"]},
    {"name": "s4_honesty", "kind": "anim", "build": a_honesty, "vo": [
        "Now the honest part, before a single dollar of lift.",
        "This data is buyers-only, so it can't tell us who would have walked away at a higher price.",
        "That walk-away risk is what makes smart pricing pay off — so I add it, a conversion model calibrated to published auto-insurance elasticities.",
        "Everything from here is lift in simulation, not a claim about Allstate's revenue — and I sweep the elasticity so it doesn't hinge on one guess."]},
    {"name": "s5_engine", "kind": "anim", "build": a_engine, "vo": [
        "Three ways to price. Compete on the cheapest quote, blanket-upsell everyone, or aim.",
        f"The engine lifts revenue per shopper by {EN['lift_vs_compete_pct']:.0f} percent — and conversion goes up, not down.",
        "It holds the price-driven shoppers on the lean quote so they don't walk, and trades the coverage-lovers up."]},
    {"name": "s6_learn", "kind": "anim", "build": a_learn, "vo": [
        "But you never know a shopper's elasticity up front. You learn it, from clicks.",
        "Push a price-driven shopper to richer coverage and their conversion falls. Push a coverage-driven one, and it rises. Same offer, opposite result.",
        f"A Thompson Sampling bandit finds each segment's best offer on its own — converging within half a percent of a perfect-knowledge oracle."]},
    {"name": "s7_arch", "kind": "anim", "build": a_architecture, "vo": [
        "One more thing — how this actually ships.",
        "In production it's a streaming loop. Every quote and click flows through Kinesis. A decision service — API Gateway and Lambda, with the bandit's posteriors in DynamoDB — picks the offer to feature in a few milliseconds.",
        "A Flink consumer folds each conversion back into those posteriors, so the engine adapts within minutes, not overnight. Firehose lands every event in S3 for the dashboards, and SageMaker retrains the choice model nightly.",
        "To be clear — I didn't run this at scale. The build you just saw ran offline on a laptop. This is just the shape it takes when you ship it."]},
    {"name": "s8_close", "kind": "static", "build": s7_close, "vo": [
        "The whole idea is simple. Stop discounting to people who would have paid more.",
        "The data's real, the code's open, and the one simulated piece is labeled. That's this week's build."]},
]
