#!/usr/bin/env python3
"""Build deck/webinar.html — a self-contained HTML version of the webinar deck.

Reuses the same 15 rendered slides (deck/slides/) and the speaker notes from
build_deck.py, and bakes them into ONE portable HTML file (images embedded as
data URIs, no dependencies). Arrow keys / click to navigate; press N for notes,
F for fullscreen. Runs in any browser and can be published as an artifact.

    python3 deck/build_deck.py         # renders the slides first
    python3 deck/build_webinar_html.py # -> deck/webinar.html
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "deck"))
import build_deck  # noqa: E402  (DECK = [(builder, notes), ...] in slide order)

SLIDES = ROOT / "deck" / "slides"


def main() -> int:
    data = []
    for i, (_, notes) in enumerate(build_deck.DECK):
        png = SLIDES / f"slide_{i:02d}.png"
        if not png.exists():
            print(f"  missing {png} - run build_deck.py first"); return 1
        b64 = base64.b64encode(png.read_bytes()).decode()
        data.append({"img": f"data:image/png;base64,{b64}", "notes": notes})

    html = TEMPLATE.replace("__SLIDES__", json.dumps(data, separators=(",", ":")))
    # keep it pure ASCII so it renders under any served charset
    head, _, tail = html.partition("<script>")
    ent = "".join(ch if ord(ch) < 128 else f"&#{ord(ch)};" for ch in head)
    esc = "".join(ch if ord(ch) < 128 else f"\\u{ord(ch):04x}" for ch in ("<script>" + tail))
    out = ROOT / "deck" / "webinar.html"
    out.write_text(ent + esc, encoding="ascii")
    print(f"  -> {out}  ({len(data)} slides, {out.stat().st_size/1e6:.1f} MB)")
    return 0


TEMPLATE = """<title>Pricing to the customer, not the average - webinar</title>
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  :root { --bg:#0b0d12; --panel:#161a22; --rule:#2a3040; --ink:#eef1f6; --ink2:#9aa2b1; --accent:#3987e5; }
  html,body { height:100%; }
  body { background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         display:flex; flex-direction:column; overflow:hidden; }
  .stage { flex:1; display:flex; align-items:center; justify-content:center; padding:18px; min-height:0; }
  .slide { max-width:100%; max-height:100%; aspect-ratio:16/9; width:auto; height:auto; border-radius:10px;
           box-shadow:0 12px 40px rgba(0,0,0,.5); background:#0d1117; }
  .bar { display:flex; align-items:center; gap:14px; padding:10px 16px; background:var(--panel); border-top:1px solid var(--rule); }
  .bar button { font:inherit; font-size:14px; font-weight:600; color:var(--ink); background:#20263180; border:1px solid var(--rule);
                border-radius:8px; padding:8px 14px; cursor:pointer; }
  .bar button:hover { border-color:var(--accent); } .bar button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
  .count { font-variant-numeric:tabular-nums; font-family:ui-monospace,Menlo,Consolas,monospace; font-size:13px; color:var(--ink2); }
  .dots { display:flex; gap:6px; flex-wrap:wrap; flex:1; }
  .dot { width:9px; height:9px; border-radius:50%; background:var(--rule); border:none; padding:0; cursor:pointer; }
  .dot.on { background:var(--accent); }
  .spacer { flex:1; }
  .notes { display:none; padding:14px 20px; background:#12151c; border-top:1px solid var(--rule); color:var(--ink2);
           font-size:15px; line-height:1.55; max-height:26vh; overflow:auto; }
  .notes.show { display:block; } .notes b { color:var(--ink); }
  .hint { font-family:ui-monospace,Menlo,Consolas,monospace; font-size:11px; color:var(--ink2); opacity:.7; }
  @media (max-width:640px){ .dots{display:none;} .hint{display:none;} }
</style>
<div class="stage"><img class="slide" id="slide" alt="slide"></div>
<div class="notes" id="notes"></div>
<div class="bar">
  <button id="prev" aria-label="previous">&#8592; Prev</button>
  <span class="count" id="count"></span>
  <button id="next" aria-label="next">Next &#8594;</button>
  <div class="dots" id="dots"></div>
  <span class="hint">&#8592;/&#8594; move &#183; N notes &#183; F full</span>
  <button id="notesbtn">Notes</button>
  <button id="full">Full</button>
</div>
<script>
"use strict";
const S = __SLIDES__;
let i = 0, showNotes = false;
const img=document.getElementById("slide"), count=document.getElementById("count"),
      notes=document.getElementById("notes"), dots=document.getElementById("dots");
dots.innerHTML = S.map((_,k)=>`<button class="dot" data-k="${k}" aria-label="slide ${k+1}"></button>`).join("");
const dotEls=[...dots.children];
function render(){
  img.src=S[i].img;
  count.textContent=`${i+1} / ${S.length}`;
  notes.innerHTML=`<b>Slide ${i+1} notes.</b> ${S[i].notes}`;
  notes.classList.toggle("show", showNotes);
  dotEls.forEach((d,k)=>d.classList.toggle("on",k===i));
  if(location.hash!=="#"+(i+1)) history.replaceState(null,"","#"+(i+1));
}
function go(n){ i=Math.max(0,Math.min(S.length-1,n)); render(); }
document.getElementById("prev").onclick=()=>go(i-1);
document.getElementById("next").onclick=()=>go(i+1);
document.getElementById("notesbtn").onclick=()=>{ showNotes=!showNotes; render(); };
document.getElementById("full").onclick=()=>{ if(!document.fullscreenElement) document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen(); else document.exitFullscreen&&document.exitFullscreen(); };
dots.onclick=e=>{ const k=e.target.dataset.k; if(k!==undefined) go(+k); };
img.onclick=()=>go(i+1);
addEventListener("keydown",e=>{
  if(e.key==="ArrowRight"||e.key===" "||e.key==="PageDown"){ e.preventDefault(); go(i+1); }
  else if(e.key==="ArrowLeft"||e.key==="PageUp"){ e.preventDefault(); go(i-1); }
  else if(e.key==="Home"){ go(0); } else if(e.key==="End"){ go(S.length-1); }
  else if(e.key.toLowerCase()==="n"){ showNotes=!showNotes; render(); }
  else if(e.key.toLowerCase()==="f"){ document.getElementById("full").click(); }
});
// swipe on touch
let tx=0; addEventListener("touchstart",e=>tx=e.touches[0].clientX,{passive:true});
addEventListener("touchend",e=>{ const dx=e.changedTouches[0].clientX-tx; if(Math.abs(dx)>50) go(i+(dx<0?1:-1)); },{passive:true});
const fromHash=parseInt((location.hash||"").slice(1)); if(fromHash>=1&&fromHash<=S.length) i=fromHash-1;
render();
</script>
"""


if __name__ == "__main__":
    raise SystemExit(main())
