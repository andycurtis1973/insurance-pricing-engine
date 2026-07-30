#!/usr/bin/env python3
"""Build web/demo.html from results/rundata.json.

The arc: what shoppers really do (real) -> a model that tells price- from
coverage-driven (real) -> the honest confession that walk-away risk is simulated
-> the engine's lift -> it learning the policy from clicks. Disclosure sits BEFORE
any lift number.

Run data is embedded as <script id="rundata">; video/render.py reads the same
rundata.json, so the demo and the video can't drift.

    python3 web/build_demo.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "results" / "rundata.json").read_text())

HTML = """<title>Half your shoppers will pay for more coverage</title>
<style>
  :root {
    color-scheme: light;
    --bg:#f7f8fa; --card:#ffffff; --rule:#e3e6ec;
    --ink:#12141a; --ink2:#555c6b; --ink3:#858c9a;
    --engine:#2a78d6; --price:#e34948; --cov:#1baf7a; --bal:#9a6bd6; --gold:#c78a1e;
    --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --bg:#0f1218; --card:#161a22; --rule:#252a34;
      --ink:#eef1f6; --ink2:#a6adbb; --ink3:#727988;
      --engine:#3987e5; --price:#e66767; --cov:#199e70; --bal:#a986e0; --gold:#d9a637;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --bg:#0f1218; --card:#161a22; --rule:#252a34;
    --ink:#eef1f6; --ink2:#a6adbb; --ink3:#727988;
    --engine:#3987e5; --price:#e66767; --cov:#199e70; --bal:#a986e0; --gold:#d9a637;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family:var(--sans);
         line-height:1.55; -webkit-font-smoothing:antialiased; }
  .wrap { max-width:1060px; margin:0 auto; padding:48px 24px 96px; }
  .eyebrow { font-family:var(--mono); font-size:11.5px; letter-spacing:.14em;
             text-transform:uppercase; color:var(--ink3); margin:0 0 14px; }
  h1 { font-size:clamp(29px,4.4vw,44px); line-height:1.12; letter-spacing:-.022em;
       margin:0 0 16px; text-wrap:balance; font-weight:640; max-width:20ch; }
  h1 em { font-style:normal; color:var(--cov); }
  h1 u { text-decoration:none; color:var(--price); }
  .lede { font-size:18px; color:var(--ink2); margin:0; max-width:66ch; }
  h2 { font-size:20px; letter-spacing:-.012em; margin:0 0 6px; font-weight:620; }
  .sub { color:var(--ink2); font-size:14.5px; margin:0 0 20px; max-width:76ch; }
  section { margin-top:56px; }
  .card { background:var(--card); border:1px solid var(--rule); border-radius:10px; padding:22px; }
  .facts { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1px;
           background:var(--rule); border:1px solid var(--rule); border-radius:10px;
           overflow:hidden; margin-top:28px; }
  .fact { background:var(--card); padding:15px 16px; }
  .fact b { display:block; font-family:var(--mono); font-size:20px;
            font-variant-numeric:tabular-nums; letter-spacing:-.02em; }
  .fact b.price { color:var(--price); } .fact b.cov { color:var(--cov); }
  .fact span { font-size:11.5px; color:var(--ink3); font-family:var(--mono);
               letter-spacing:.05em; text-transform:uppercase; }
  .segs { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }
  .seg { background:var(--card); border:1px solid var(--rule);
         border-top:3px solid var(--engine); border-radius:8px; padding:16px 18px; }
  .seg.price { border-top-color:var(--price); } .seg.cov { border-top-color:var(--cov); }
  .seg.bal { border-top-color:var(--bal); }
  .seg .nm { font-size:15px; font-weight:640; margin-bottom:2px; }
  .seg .pc { font-family:var(--mono); font-size:26px; letter-spacing:-.02em; }
  .seg .d { font-size:13px; color:var(--ink2); margin-top:8px; }
  .seg .d b { color:var(--ink); font-variant-numeric:tabular-nums; }
  figure { margin:0; } .plot { position:relative; overflow-x:auto; }
  svg { display:block; width:100%; height:auto; }
  .legend { display:flex; flex-wrap:wrap; gap:8px 18px; margin:0 0 14px;
            font-size:12.5px; font-family:var(--mono); color:var(--ink2); }
  .legend i { width:16px; height:10px; border-radius:2px; display:inline-block;
              vertical-align:middle; margin-right:7px; }
  .callout { border-left:3px solid var(--engine); padding:12px 0 12px 16px; margin:22px 0 0;
             color:var(--ink2); font-size:14.5px; max-width:78ch; }
  .callout.warn { border-left-color:var(--price); }
  .callout b { color:var(--ink); }
  .disc { background:var(--card); border:1px solid var(--rule); border-radius:10px;
          padding:20px 22px; display:grid; grid-template-columns:1fr 1fr; gap:24px; }
  .disc h3 { font-family:var(--mono); font-size:12px; letter-spacing:.08em;
             text-transform:uppercase; margin:0 0 10px; }
  .disc .real h3 { color:var(--cov); } .disc .sim h3 { color:var(--gold); }
  .disc ul { margin:0; padding-left:18px; font-size:13.5px; color:var(--ink2); }
  .disc li { margin-bottom:7px; } .disc li b { color:var(--ink); }
  @media (max-width:640px){ .disc { grid-template-columns:1fr; } }
  footer { margin-top:64px; padding-top:22px; border-top:1px solid var(--rule);
           color:var(--ink3); font-size:12.5px; font-family:var(--mono); line-height:1.9; }
  .arch { display:flex; flex-direction:column; gap:18px; margin-top:24px; }
  .arch .lane-k { font-family:var(--mono); font-size:11.5px; letter-spacing:.08em;
                  text-transform:uppercase; display:block; margin-bottom:9px; }
  .arch .row { display:flex; flex-wrap:wrap; align-items:stretch; gap:10px; }
  .arch .row i { align-self:center; color:var(--ink3); font-style:normal; font-family:var(--mono); }
  .abox { background:var(--card); border:1px solid var(--rule); border-top:3px solid var(--engine);
          border-radius:8px; padding:12px 15px; min-width:148px; font-weight:640; font-size:14.5px; }
  .abox small { display:block; font-weight:400; font-size:12px; color:var(--ink2);
                font-family:var(--mono); margin-top:4px; letter-spacing:0; }
  .abox.e { border-top-color:var(--engine); } .abox.g { border-top-color:var(--gold); }
  .abox.c { border-top-color:var(--cov); } .abox.b { border-top-color:var(--bal); }
  .brain { display:flex; align-items:center; gap:12px; padding-left:22px; }
  .brain .updown { color:var(--bal); font-family:var(--mono); font-size:18px; }
  @media (prefers-reduced-motion:reduce){ *{transition:none!important;animation:none!important;} }
</style>

<div class="wrap">
  <header>
    <p class="eyebrow" id="eyebrow"></p>
    <h1>Half your shoppers will pay for <em>more coverage</em>.<br>
      A quarter will <u>walk</u> if you push. Your quote treats them the same.</h1>
    <p class="lede">Every insurer competes on the cheapest quote. But in
      <span id="ncust"></span> real auto-insurance shopping sessions, only a quarter bought the
      cheapest thing they saw — and nearly half traded up to more coverage. Here's a model that
      tells them apart, and an engine that learns which is which from clicks.</p>
    <div class="facts" id="facts"></div>
  </header>

  <section>
    <h2>Two shoppers, one price tag</h2>
    <p class="sub">Each person picked one offer from the menu they were shown. A Bayesian choice
      model — a conditional logit with a Laplace posterior, so every number has a credible
      interval — recovers how much price and coverage drove the pick, and how that shifts with
      who the shopper is. Every coefficient below excludes zero.</p>
    <div class="card">
      <div class="legend">
        <span><i style="background:var(--price)"></i>pushes toward cheaper</span>
        <span><i style="background:var(--cov)"></i>pushes toward more coverage</span>
      </div>
      <figure class="plot" id="plotCoef"></figure>
    </div>
    <p class="callout"><b>It picks the offer they actually bought
      <span id="top1"></span>% of the time</b> — versus <span id="bcheap"></span>% for
      "assume everyone takes the cheapest" and <span id="brich"></span>% for "assume everyone
      maxes coverage." Price sensitivity isn't one number: it's stronger for homeowners and
      young drivers, and it flips toward coverage for expensive cars.</p>
  </section>

  <section>
    <h2>Who's really shopping</h2>
    <p class="sub">Split by what they actually did with the menu in front of them — not a guess
      from demographics. Three populations, and they don't want the same thing.</p>
    <div class="segs" id="segs"></div>
  </section>

  <section>
    <h2>What's real here, and what isn't</h2>
    <p class="sub">Before a single dollar of "lift," the honest part. This dataset is
      buyers-only: everyone in it bought something, so it can't tell us who would have walked
      away at a higher price. That walk-away risk is exactly what makes differentiated pricing
      pay off — so to test the engine, we add it, and we label it.</p>
    <div class="disc">
      <div class="real"><h3>Real — from the data</h3><ul id="real"></ul></div>
      <div class="sim"><h3>Simulated — disclosed</h3><ul id="sim"></ul></div>
    </div>
    <p class="callout warn">Every number past this point is <b>lift in simulation</b> — the
      standard way a pricing engine is stress-tested before it ever meets a live customer.
      It is not a claim about what Allstate earned. The conversion model's elasticity is
      <b>swept</b> below to show the result doesn't hinge on one flattering value.</p>
  </section>

  <section>
    <h2>Three ways to price, scored head-to-head</h2>
    <p class="sub">On <span id="nengtest"></span> held-out shoppers. Revenue per shopper =
      chance they buy &times; the premium. "Compete on price" leads with the cheapest quote.
      "Blanket upsell" pushes the richest coverage at everyone. The engine picks per shopper.</p>
    <div class="card"><figure class="plot" id="plotStrat"></figure></div>
    <p class="callout"><b>The engine lifts revenue per shopper
      <span id="englift"></span>% over competing on price — and conversion goes
      <span id="engconv"></span>, not down.</b> It beats blanket-upsell too, because it doesn't
      shove pricier coverage at the people who'll walk. The lift is split unevenly on purpose:</p>
    <div class="card" style="margin-top:14px"><figure class="plot" id="plotSegLift"></figure></div>
    <p class="callout"><b>Price-driven shoppers: left alone</b> (<span id="pdlift"></span>% —
      the engine trades up just <span id="pdup"></span>% of them, because pushing loses the
      sale). <b>Coverage-driven: traded up</b> (<span id="cdlift"></span>%). That's the whole
      idea — spend the premium ask on the people who'll say yes.</p>
    <p class="callout"><b>Robust, not cherry-picked.</b> Sweep the calibrated elasticity from
      half to 1.5&times; and the engine still lifts <span id="sweeplo"></span>–<span
      id="sweephi"></span>% with conversion holding near <span id="sweepconv"></span>%.</p>
  </section>

  <section>
    <h2>It learns who wants what — from clicks</h2>
    <p class="sub">The offline run assumed we already knew each segment's response. You don't —
      you learn it. This is a Thompson Sampling bandit: context is the segment, the arms are
      lead-with-lean / mid / rich, the reward is revenue. It explores, then exploits.</p>
    <div class="card">
      <div class="legend">
        <span><i style="background:var(--price)"></i>price-driven</span>
        <span><i style="background:var(--bal)"></i>balanced</span>
        <span><i style="background:var(--cov)"></i>coverage-driven</span>
      </div>
      <figure class="plot" id="plotLearn"></figure>
    </div>
    <p class="callout"><b>The response it learns is the whole story:</b> push a price-driven
      shopper to richer coverage and their conversion <b>falls</b>
      (<span id="pdlean"></span>%&rarr;<span id="pdrich"></span>%); push a coverage-driven one
      and it <b>rises</b> (<span id="cdlean"></span>%&rarr;<span id="cdrich"></span>%). Same
      offer, opposite result.</p>
    <div class="card" style="margin-top:14px">
      <div class="legend">
        <span><i style="background:var(--engine)"></i>bandit (learns from clicks)</span>
        <span><i style="background:var(--ink3)"></i>compete on price</span>
        <span><i style="background:var(--gold)"></i>oracle (knows the answer)</span>
      </div>
      <figure class="plot" id="plotCurve"></figure>
    </div>
    <p class="callout"><b>It converges to within <span id="regret"></span>% of a
      perfect-knowledge oracle</b>, locking each segment's best offer within a few hundred to a
      few thousand shoppers — while competing-on-price leaves money on the table the entire
      time. No elasticities were handed to it; it found them.</p>
  </section>

  <section>
    <h2>How you'd ship it</h2>
    <p class="sub">Everything above ran offline on a laptop. In production this is a
      streaming loop: the engine decides in milliseconds and folds every click back into
      its posteriors within minutes. This is the deployment shape — a blueprint, not
      something running on this page.</p>
    <div class="arch">
      <div class="lane">
        <span class="lane-k" style="color:var(--engine)">Decide · a few milliseconds</span>
        <div class="row">
          <div class="abox e">Shopper<small>quote page</small></div><i>&rarr;</i>
          <div class="abox e">API Gateway<small>/price request</small></div><i>&rarr;</i>
          <div class="abox e">Lambda<small>pick the offer to feature</small></div><i>&rarr;</i>
          <div class="abox e">Featured offer<small>lean · mid · rich</small></div>
        </div>
      </div>
      <div class="brain">
        <div class="abox b">DynamoDB<small>Thompson posteriors &alpha;,&beta; / segment&times;arm</small></div>
        <span class="updown">&#8645; Lambda reads &amp; writes</span>
      </div>
      <div class="lane">
        <span class="lane-k" style="color:var(--gold)">Learn · from every click, near-real-time</span>
        <div class="row">
          <div class="abox g">Click events<small>shown · converted · left</small></div><i>&rarr;</i>
          <div class="abox g">Kinesis Data Streams<small>the clickstream backbone</small></div><i>&rarr;</i>
          <div class="abox g">Managed Flink<small>update the posteriors &#8593;</small></div>
        </div>
      </div>
      <div class="lane">
        <span class="lane-k" style="color:var(--cov)">Observe &amp; retrain · offline</span>
        <div class="row">
          <div class="abox c">Firehose &rarr; S3<small>the event lake</small></div><i>&rarr;</i>
          <div class="abox c">Athena · QuickSight<small>revenue · guardrails</small></div>
          <div class="abox c">SageMaker · nightly<small>retrain choice model &rarr; segments + priors</small></div>
        </div>
      </div>
    </div>
    <p class="callout warn"><b>A deployment blueprint.</b> The build you just explored ran
      offline — pure numpy/scipy, no GPU. This is the shape it takes live: decide in
      milliseconds off DynamoDB, learn from the Kinesis clickstream through Flink, retrain
      the choice model nightly on SageMaker. Guardrails — a no-underprice floor and
      human-set caps — are enforced in the decision step, never learned around.</p>
  </section>

  <footer id="foot"></footer>
</div>

<script id="rundata" type="application/json">__RUNDATA__</script>
<script>
const D = JSON.parse(document.getElementById('rundata').textContent);
const C=D.corpus, CM=D.choice_model, SG=D.segments, EN=D.engine, BD=D.bandit, DS=D.disclosure;
const fmt = n => n.toLocaleString('en-US');
const svgNS='http://www.w3.org/2000/svg';
const el=(n,a={})=>{const e=document.createElementNS(svgNS,n);
  for(const k in a)e.setAttribute(k,a[k]);return e;};
const txt=(p,x,y,s,o={})=>{const t=el('text',{x,y,'font-family':'var(--mono)',
  'font-size':o.size||12,fill:o.fill||'var(--ink3)','text-anchor':o.anchor||'start',
  ...(o.weight?{'font-weight':o.weight}:{})});t.textContent=s;p.appendChild(t);return t;};
const cvar = c => getComputedStyle(document.documentElement).getPropertyValue(c).trim();

document.getElementById('eyebrow').textContent =
  fmt(C.n_customers)+' real Allstate shopping sessions · median '+C.median_quotes+' quotes each';
document.getElementById('ncust').textContent = fmt(C.n_customers);

document.getElementById('facts').innerHTML = [
  [fmt(C.n_customers), 'shoppers', ''],
  ['$'+C.premium_median, 'median premium', ''],
  [C.pct_bought_cheapest+'%', 'bought the cheapest', 'price'],
  [C.pct_bought_richest_cov+'%', 'bought the richest coverage', 'cov'],
  [C.pct_saw_price_variation+'%', 'saw more than one price', ''],
].map(([b,s,c]) => `<div class="fact"><b class="${c}">${b}</b><span>${s}</span></div>`).join('');

/* ---- coefficient plot with 95% credible intervals ---- */
(function(){
  const rows=[
    ['price', CM.price, 'base'],
    ['coverage', CM.coverage, 'base'],
    ['price × homeowner', CM.price_homeowner, 'int'],
    ['price × young driver', CM.price_young, 'int'],
    ['price × car value', CM.price_car_value, 'int'],
  ];
  const W=980,G=52,H0=52+rows.length*G,P={l:210,r:60,t:20};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H0}`,role:'img',
    'aria-label':'Choice model coefficients with 95% credible intervals'});
  const lo=-0.85, hi=0.65, bw=W-P.l-P.r, x=v=>P.l+(v-lo)/(hi-lo)*bw;
  [-0.75,-0.5,-0.25,0,0.25,0.5].forEach(g=>{
    const gx=x(g), zero=g===0;
    svg.appendChild(el('line',{x1:gx,x2:gx,y1:P.t-4,y2:H0-22,
      stroke:zero?'var(--ink3)':'var(--rule)','stroke-width':zero?1.5:1}));
    txt(svg,gx,H0-6,g.toFixed(2),{anchor:'middle',size:10.5});
  });
  rows.forEach(([nm,c,kind],i)=>{
    const y=P.t+i*G+16, col=c.mean<0?'var(--price)':'var(--cov)';
    txt(svg,P.l-14,y+4,nm,{anchor:'end',fill:'var(--ink2)',size:13});
    svg.appendChild(el('line',{x1:x(c.ci95[0]),x2:x(c.ci95[1]),y1:y,y2:y,
      stroke:col,'stroke-width':2,opacity:.5}));
    [c.ci95[0],c.ci95[1]].forEach(v=>svg.appendChild(el('line',
      {x1:x(v),x2:x(v),y1:y-5,y2:y+5,stroke:col,'stroke-width':2,opacity:.5})));
    svg.appendChild(el('circle',{cx:x(c.mean),cy:y,r:5.5,fill:col}));
    txt(svg,x(c.mean),y-11,c.mean.toFixed(2),{anchor:'middle',fill:'var(--ink)',size:11.5,weight:600});
  });
  document.getElementById('plotCoef').appendChild(svg);
})();
document.getElementById('top1').textContent=Math.round(CM.top1*100);
document.getElementById('bcheap').textContent=Math.round(CM.baseline_cheapest*100);
document.getElementById('brich').textContent=Math.round(CM.baseline_richest*100);

/* ---- segment cards ---- */
(function(){
  const meta={price_driven:['Price-driven','price','Bought the cheapest quote they saw'],
    balanced:['Balanced','bal','In between — not the cheapest, not the richest'],
    coverage_driven:['Coverage-driven','cov','Bought the richest coverage, and paid for it']};
  document.getElementById('segs').innerHTML=['price_driven','balanced','coverage_driven']
    .map(k=>{const v=SG[k],m=meta[k];return `<div class="seg ${m[1]}">
      <div class="nm">${m[0]}</div><div class="pc">${v.pct}%</div>
      <div class="d">${m[2]}.<br><b>${v.avg_coverage_pct}%</b> of max coverage ·
      avg premium <b>$${v.avg_premium}</b></div></div>`;}).join('');
})();

/* ---- disclosure lists ---- */
document.getElementById('real').innerHTML = DS.real.map(s=>`<li>${s}</li>`).join('');
document.getElementById('sim').innerHTML = DS.simulated.map(s=>`<li>${s}</li>`).join('');

/* ---- three strategies (rev/shopper) ---- */
(function(){
  const S=EN.strategies, order=[['compete_on_price','Compete on price','var(--ink3)'],
    ['blanket_upsell','Blanket upsell','var(--price)'],['engine','The engine','var(--engine)']];
  const W=980,BH=64,H0=30+order.length*BH,P={l:170,r:220,t:14};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H0}`,role:'img','aria-label':'Revenue per shopper by strategy'});
  const max=Math.max(...order.map(o=>S[o[0]].rev_per_shopper))*1.02, bw=W-P.l-P.r;
  order.forEach(([k,lbl,col],i)=>{
    const v=S[k],y=P.t+i*BH,w=v.rev_per_shopper/max*bw;
    txt(svg,P.l-14,y+26,lbl,{anchor:'end',fill:'var(--ink2)',size:13.5});
    svg.appendChild(el('rect',{x:P.l,y:y+8,width:Math.max(w,3),height:34,rx:5,fill:col}));
    txt(svg,P.l+w+12,y+22,'$'+v.rev_per_shopper.toFixed(2),{fill:'var(--ink)',size:15,weight:600});
    txt(svg,P.l+w+12,y+38,(v.conversion*100).toFixed(1)+'% convert · $'
      +Math.round(v.avg_premium_offered)+' offered',{size:11});
  });
  document.getElementById('plotStrat').appendChild(svg);
})();
document.getElementById('nengtest').textContent=fmt(EN.n_test);
document.getElementById('englift').textContent=EN.lift_vs_compete_pct;
const engConvUp = EN.strategies.engine.conversion > EN.strategies.compete_on_price.conversion;
document.getElementById('engconv').textContent = engConvUp ? 'up' : 'down';

/* ---- per-segment lift ---- */
(function(){
  const bs=EN.by_segment, order=[['price_driven','Price-driven','var(--price)'],
    ['balanced','Balanced','var(--bal)'],['coverage_driven','Coverage-driven','var(--cov)']];
  const W=980,BH=52,H0=40+order.length*BH,P={l:170,r:250,t:16};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H0}`,role:'img','aria-label':'Engine revenue lift by segment'});
  const max=Math.max(...order.map(o=>bs[o[0]].lift_pct)), bw=W-P.l-P.r;
  txt(svg,P.l,12,'REVENUE LIFT vs COMPETE-ON-PRICE, BY SEGMENT',{size:11});
  order.forEach(([k,lbl,col],i)=>{
    const v=bs[k],y=P.t+i*BH,w=Math.max(v.lift_pct/max*bw,2);
    txt(svg,P.l-14,y+22,lbl,{anchor:'end',fill:'var(--ink2)',size:13});
    svg.appendChild(el('rect',{x:P.l,y:y+8,width:w,height:28,rx:5,fill:col}));
    txt(svg,P.l+w+12,y+27,'+'+v.lift_pct.toFixed(1)+'%  · traded up '+v.traded_up_pct+'%',
      {fill:'var(--ink)',size:13,weight:600});
  });
  document.getElementById('plotSegLift').appendChild(svg);
})();
document.getElementById('pdlift').textContent='+'+EN.by_segment.price_driven.lift_pct.toFixed(1);
document.getElementById('pdup').textContent=EN.by_segment.price_driven.traded_up_pct;
document.getElementById('cdlift').textContent='+'+EN.by_segment.coverage_driven.lift_pct.toFixed(1);
(function(){
  const sw=EN.elasticity_sweep.map(s=>s.engine_lift_vs_compete_pct);
  document.getElementById('sweeplo').textContent=Math.min(...sw).toFixed(1);
  document.getElementById('sweephi').textContent=Math.max(...sw).toFixed(1);
  document.getElementById('sweepconv').textContent=Math.round(
    EN.elasticity_sweep.reduce((a,s)=>a+s.engine_conversion,0)/EN.elasticity_sweep.length*100);
})();

/* ---- learned conversion per arm (grouped bars) ---- */
(function(){
  const LC=BD.learned_conversion, segs=[['price_driven','var(--price)'],
    ['balanced','var(--bal)'],['coverage_driven','var(--cov)']], arms=['lean','mid','rich'];
  const W=980,H0=300,P={l:52,r:20,t:20,b:64}, gw=(W-P.l-P.r)/segs.length;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H0}`,role:'img',
    'aria-label':'Conversion by offer richness, per segment'});
  const y0=H0-P.b, yh=y0-P.t, sc=v=>y0-((v-0.4)/(0.75-0.4))*yh;
  [0.4,0.5,0.6,0.7].forEach(g=>{
    svg.appendChild(el('line',{x1:P.l,x2:W-P.r,y1:sc(g),y2:sc(g),stroke:'var(--rule)','stroke-width':1}));
    txt(svg,P.l-8,sc(g)+4,(g*100).toFixed(0)+'%',{anchor:'end',size:10.5});
  });
  segs.forEach(([s,col],gi)=>{
    const gx=P.l+gi*gw+18, bw=(gw-46)/arms.length;
    arms.forEach((arm,ai)=>{
      const v=LC[s][arm], x=gx+ai*bw, h=y0-sc(v);
      svg.appendChild(el('rect',{x,y:sc(v),width:bw-10,height:h,rx:3,fill:col,
        opacity:0.45+0.28*ai}));
      txt(svg,x+(bw-10)/2,sc(v)-6,(v*100).toFixed(0),{anchor:'middle',fill:'var(--ink)',size:11,weight:600});
      txt(svg,x+(bw-10)/2,y0+16,arm,{anchor:'middle',size:10.5});
    });
    txt(svg,gx+(gw-46)/2,y0+40,s.replace('_',' '),{anchor:'middle',fill:'var(--ink2)',size:12.5,weight:600});
  });
  txt(svg,P.l,12,'CONVERSION as you lead with a RICHER offer (lean → rich)',{size:11});
  document.getElementById('plotLearn').appendChild(svg);
})();
document.getElementById('pdlean').textContent=Math.round(BD.learned_conversion.price_driven.lean*100);
document.getElementById('pdrich').textContent=Math.round(BD.learned_conversion.price_driven.rich*100);
document.getElementById('cdlean').textContent=Math.round(BD.learned_conversion.coverage_driven.lean*100);
document.getElementById('cdrich').textContent=Math.round(BD.learned_conversion.coverage_driven.rich*100);

/* ---- bandit learning curve ---- */
(function(){
  const cur=BD.curve, W=980,H0=320,P={l:56,r:20,t:18,b:40};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H0}`,role:'img','aria-label':'Bandit learning curve'});
  const xs=cur.map(p=>p.t), tmax=Math.max(...xs);
  const all=cur.flatMap(p=>[p.bandit,p.compete,p.oracle]);
  const ylo=Math.min(...all)*0.999, yhi=Math.max(...all)*1.001;
  const X=t=>P.l+t/tmax*(W-P.l-P.r), Y=v=>P.t+(1-(v-ylo)/(yhi-ylo))*(H0-P.t-P.b);
  [ylo,(ylo+yhi)/2,yhi].forEach(g=>{
    svg.appendChild(el('line',{x1:P.l,x2:W-P.r,y1:Y(g),y2:Y(g),stroke:'var(--rule)','stroke-width':1}));
    txt(svg,P.l-8,Y(g)+4,'$'+g.toFixed(0),{anchor:'end',size:10.5});
  });
  [4,3,2,1,0].forEach(f=>{const t=tmax*f/4;
    txt(svg,X(t),H0-8,fmt(Math.round(t/1000))+'k',{anchor:'middle',size:10.5});});
  const line=(key,col,w,dash)=>{
    const d=cur.map((p,i)=>(i?'L':'M')+X(p.t).toFixed(1)+' '+Y(p[key]).toFixed(1)).join(' ');
    svg.appendChild(el('path',{d,fill:'none',stroke:col,'stroke-width':w,
      ...(dash?{'stroke-dasharray':dash}:{})}));};
  line('oracle','var(--gold)',2,'5 4');
  line('compete','var(--ink3)',2,'2 4');
  line('bandit','var(--engine)',2.6);
  txt(svg,P.l,12,'REVENUE PER SHOPPER as the bandit learns (running average)',{size:11});
  document.getElementById('plotCurve').appendChild(svg);
})();
document.getElementById('regret').textContent=BD.regret_vs_oracle_pct;

document.getElementById('foot').innerHTML = `
  Data: Allstate Purchase Prediction Challenge — ${fmt(C.n_customers)} real auto-insurance
  shopping sessions (Kaggle). Coverage A–G, premium, and every quote viewed are real.<br>
  Model: Bayesian conditional logit (Laplace posterior) on ${fmt(CM.n_sets)} choice sets;
  segments from revealed purchases; engine is a Thompson Sampling contextual bandit.<br>
  <b>Simulated &amp; disclosed:</b> walk-away / conversion is a logistic model calibrated to
  published auto-insurance price elasticities — ${DS.sources.join('; ')}. Elasticity is swept.
  All "lift" is in simulation, not a claim about Allstate's revenue.<br>
  Runs on a laptop in minutes; pure numpy/scipy, no GPU. Full code + this page: the repo.
`;
</script>
"""

out = ROOT / "web" / "demo.html"
out.write_text(HTML.replace("__RUNDATA__", json.dumps(DATA, separators=(",", ":"))))
print(f"  -> {out}  ({out.stat().st_size:,} bytes)")
