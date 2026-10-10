/* Appendix A (why the memory can be switched) and B (glossary) */
'use strict';
function loopDiagram(cv,w,h){
  const g=cv.getContext('2d'),d=Math.min(window.devicePixelRatio||1,2);cv.width=w*d;cv.height=h*d;cv.style.width=w+'px';cv.style.height=h+'px';g.setTransform(d,0,0,d,0,0);g.fillStyle='#fff';g.fillRect(0,0,w,h);
  const node=(x,y,r,f)=>{g.fillStyle=f;g.strokeStyle='rgba(0,0,0,.5)';g.lineWidth=1.5;g.beginPath();g.arc(x,y,r,0,6.3);g.fill();g.stroke();};
  const arrow=(a,b,c2,col,wd)=>{g.strokeStyle=col||C.ink;g.fillStyle=col||C.ink;g.lineWidth=wd||2.4;g.beginPath();g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);g.stroke();const an=Math.atan2(b[1]-a[1],b[0]-a[0]);g.beginPath();g.moveTo(b[0],b[1]);g.lineTo(b[0]-10*Math.cos(an-.4),b[1]-10*Math.sin(an-.4));g.lineTo(b[0]-10*Math.cos(an+.4),b[1]-10*Math.sin(an+.4));g.fill();};
  g.textBaseline='top';g.font='700 15px '+FONT;g.fillStyle=C.ink;g.textAlign='left';g.fillText('Model v2: a node reads its own signal',20,10);g.fillText('Model v3: a node reads only its neighbours, as a fraction',w/2+20,10);
  // v2
  node(150,130,30,C.sa);g.strokeStyle=C.ink;g.lineWidth=2.6;g.beginPath();g.arc(150,84,24,Math.PI*0.72,Math.PI*0.28,false);g.stroke();{const ex=150+24*Math.cos(Math.PI*0.28),ey=84+24*Math.sin(Math.PI*0.28);g.fillStyle=C.ink;g.beginPath();g.moveTo(ex+2,ey+4);g.lineTo(ex+9,ey-9);g.lineTo(ex-8,ey-5);g.closePath();g.fill();}g.font='13px '+FONT;g.fillStyle='#333';g.textAlign='center';g.fillText('its own secretion is counted as evidence',150,190);g.fillText('→ self-confirming, rigid',150,208);
  [[40,170],[260,170],[270,95]].forEach(p=>{node(p[0],p[1],14,'#CCC');});
  g.textAlign='left';g.fillStyle=C.bad;g.font='700 13.5px '+FONT;g.fillText('v2: 0 of 560 trials switched',20,34);
  // v3
  const cx=w/2+170,cy=125;node(cx,cy,30,C.sa);[[cx-120,cy-60],[cx-130,cy+40],[cx+110,cy-60],[cx+120,cy+50]].forEach(p=>{node(p[0],p[1],14,C.sa);arrow([p[0]+(p[0]<cx?14:-14)*Math.cos(0),p[1]+(p[1]<cy?8:-8)],[cx+(p[0]<cx?-28:28),cy+(p[1]<cy?-10:10)],0,'#555',2);});
  g.fillStyle='#eee';g.fillRect(cx-70,cy+52,140,12);for(let u=0;u<140;u++){g.fillStyle=rhoColor(u/140);g.fillRect(cx-70+u,cy+52,1,12);}g.fillStyle=C.ink;g.fillRect(cx-70+0.88*139,cy+48,3,20);
  g.font='13px '+FONT;g.fillStyle='#333';g.textAlign='center';g.fillText('f = A / (A + B) over neighbours only',cx,cy+70);g.fillText('no self term → no self-fulfilled evidence → switchable',cx,cy+88);
  g.textAlign='left';g.fillStyle=C.ok;g.font='700 13.5px '+FONT;g.fillText('v3: 93 % of held-out dishes switched',w/2+20,34);
}
Demo.register({id:'A',act:'A',title:'Why the memory can be switched',data:[],duration:0,truthOffered:false,legend:[{color:C.sa,label:'state a'},{color:C.sb,label:'state b'}],
  caption:'A node\'s memory belief l obeys <b>dl/dt = −2r·sinh l + g·(2f − 1)</b>. If the evidence f is the fraction of memory ligand coming from <i>neighbours only</i>, the collective is a double well (bistable when g &gt; 4r) that a brief push can tip. Drag r and g, and click the curve to drop the ball.',
  takeaway:'Don\'t let a node count its own signal as evidence (sensory attenuation).',
  notes:'Symbols: l = memory logit of a node, ρ = σ(l) its belief in state a; r = relaxation rate towards undecided (0.05); g = coupling gain (0.6); f = fraction A/(A+B) of memory ligand sensed from neighbours j ≠ i (kernel-weighted); in the mean field f = ρ, so g(2f−1) = g·tanh(l/2). Potential U(l) = 2r·cosh l − 2g·ln cosh(l/2): two minima at ±l* = ±2·arccosh√(g/4r) = ±2.292 and a barrier at l = 0 when g > 4r (here g/4r = 3, barrier 0.26). Isolated cell: f = ½ exactly, so l relaxes at 2r. The same ratio makes the threshold independent of how many neighbours a cell has (l* equal in every cell to 4·10⁻⁴).',
  sources:[{what:'Memory module equation, parameters r = 0.05, g = 0.6',file:'testbed_v3/ENGINE_SPEC_V3.md',sec:'Model as implemented'},{what:'Mean-field theory: l* = 2.292, barrier 0.259, T1–T5',file:'testbed_v3/MEMORY_V3.md',sec:'H2'},{what:'v2 (self-reading) never switched',file:'testbed_v2/SWITCH.md',sec:'Gate G3'}],
  setup(c){
    c.state.r=0.05;c.state.g=0.6;c.state.ball={l:-0.8,v:0};const top=el('div',{class:'pw',style:'width:100%'},c.vis);c.dg=makeCanvas(top,1060,235);
    const row=el('div',{style:'display:flex;gap:16px;flex-wrap:wrap;justify-content:center;width:100%;margin-top:4px'},c.vis);
    const w1=el('div',{class:'pw'},row);c.cv=makeCanvas(w1,560,300);c.cv.style.cursor='crosshair';
    const w2=el('div',{class:'pw'},row);c.eq=makeCanvas(w2,520,300);
    c.cv.addEventListener('click',e=>{const r=c.cv.getBoundingClientRect(),x=(e.clientX-r.left)*(560/r.width);const l=-5+(x-46)/(560-46-14)*10;c.state.ball={l:Math.max(-5,Math.min(5,l)),v:0};});
    const sl=(lab,min,max,step,val,key)=>{const L=el('label',{},c.ctrls,lab+' <input type="range" min="'+min+'" max="'+max+'" step="'+step+'" value="'+val+'"> <b>'+val+'</b>');L.querySelector('input').oninput=function(){c.state[key]=+this.value;L.querySelector('b').textContent=(+this.value).toFixed(3);};};
    sl('r (relaxation rate)',0.01,0.2,0.005,0.05,'r');sl('g (coupling gain)',0.05,1.2,0.01,0.6,'g');
    const rs=el('button',{class:'btn'},c.ctrls,'reset (r = 0.05, g = 0.6)');rs.onclick=()=>{c.state.r=0.05;c.state.g=0.6;c.ctrls.querySelectorAll('input').forEach((i,k)=>{i.value=k?0.6:0.05;i.nextElementSibling.textContent=k?'0.600':'0.050';});};
    Demo.tickers.push(()=>{const s=c.state,b=s.ball;const dU=(l)=>2*s.r*2*Math.sinh(l)/2*1-0;const F=(l)=>-2*s.r*Math.sinh(l)+s.g*Math.tanh(l/2);for(let k=0;k<4;k++){b.l+=0.04*F(b.l)*2.0;}Demo.redraw();});},
  draw(c){
    loopDiagram(c.dg,1060,235);
    const s=c.state,U=(l)=>2*s.r*Math.cosh(l)-2*s.g*Math.log(Math.cosh(l/2));const g=c.cv.getContext('2d');const ls=[];for(let i=0;i<=200;i++)ls.push(-5+i*0.05);const us=ls.map(U);const ym=Math.min(...us),yM=Math.min(Math.max(...us),ym+3.2);
    const ch=new Chart(c.cv,{w:560,h:300,xlim:[-5,5],ylim:[ym-1.1,yM+0.3],yticks:[],xticks:[-4,-2,0,2,4],title:'potential U(l) = 2r cosh l − 2g ln cosh(l/2)',xlabel:'memory logit l (negative: state b · positive: state a)'});ch.clear();ch.axes();
    ch.line(ls,us.map(u=>Math.min(u,yM+0.25)),{color:C.ink,w:2.6});const bist=s.g>4*s.r,lst=bist?2*Math.acosh(Math.sqrt(s.g/(4*s.r))):0;
    if(bist){[-lst,lst].forEach(v=>{ch.dot(v,U(v),{color:v>0?C.sa:C.sb,r:6});ch.text('l* = '+v.toFixed(2),ch.X(v),ch.Y(U(v))-14,{align:'center',size:12.5,bold:true,color:v>0?'#1f7fb5':'#a0457f'});});ch.dot(0,U(0),{color:'#fff',stroke:C.ink,r:5});ch.text('barrier',ch.X(0),ch.Y(U(0))-12,{align:'center',size:12,color:C.mute});}
    const b=s.ball;ch.dot(b.l,U(b.l),{color:rhoColor(1/(1+Math.exp(-b.l))),stroke:C.ink,r:9});
    ch.text(bist?'g/4r = '+(s.g/(4*s.r)).toFixed(2)+' > 1: BISTABLE':'g/4r = '+(s.g/(4*s.r)).toFixed(2)+' ≤ 1: one well (no memory)',ch.X(0),ch.Y(yM)+4,{size:14,bold:true,align:'center',color:bist?C.ok:C.bad});
    const e=c.eq.getContext('2d'),dpr=Math.min(window.devicePixelRatio||1,2);c.eq.width=520*dpr;c.eq.height=300*dpr;c.eq.style.width='520px';c.eq.style.height='300px';e.setTransform(dpr,0,0,dpr,0,0);e.fillStyle='#fff';e.fillRect(0,0,520,300);
    e.fillStyle=C.ink;e.textAlign='left';e.textBaseline='top';e.font='700 14px '+FONT;e.fillText('The equation and its symbols',12,8);e.font='700 17px '+FONT;e.fillText('dl/dt = −2r·sinh l + g·(2f − 1)',12,32);
    e.font='13.5px '+FONT;['l  memory logit of a node; ρ = σ(l) = belief in state a','r  relaxation rate towards undecided (0.05)','g  coupling gain: how strongly neighbours\' evidence counts (0.6)','f  = A/(A+B): fraction of memory ligand A among what the','    node senses from its neighbours only (j ≠ i)','mean field: f = ρ, so g(2f−1) = g·tanh(l/2)','fixed points: l* = ±2·arccosh√(g/4r) when g > 4r','here r = '+s.r.toFixed(3)+', g = '+s.g.toFixed(3)+(bist?' → l* = ±'+lst.toFixed(2):' → l* = 0'),'isolated cell: f = ½, so l decays at rate 2r'].forEach((t,i)=>e.fillText(t,12,68+i*24));
  }
});

/* ---------------- B glossary ---------------- */
const GLOSS=[
 ['collective','a group of nodes treated as one organism: the connected set of nodes found by single linkage (outline = who belongs).'],
 ['node (= cell)','one cell of the model; has a position, secretes signals, senses its neighbours and holds hidden beliefs.'],
 ['interior / exterior','hidden beliefs of a node (interior) versus everyone else including the experimenter (exterior).'],
 ['blanket','a node\'s sensory + active states: what it senses and what it does; it shields the interior from the exterior (statistical boundary).'],
 ['outline','alpha hull around the member set: a geometric boundary, not a blanket.'],
 ['interface','where an intervention couples into the collective (here: the body centre for the memory-secretion light).'],
 ['material identity','who is in the collective (set of cell ids); 1 − Jaccard to the baseline members.'],
 ['geometry identity','size, cohesion (largest bridge ≤ 1.40) and shape (≤ 4.9 % / 6.6 % change); one linked component of 24 cells.'],
 ['pattern identity','the channel patterns across the body (14 state-independent features), compared with the dish\'s own baseline.'],
 ['state identity','which of the two persistent collective memories (a or b) the collective is in; reported separately from the body.'],
 ['V_body','true while material and geometry stay inside their natural bands since the start (latches at the first violation).'],
 ['V_body_conservative','V_body and no SPLIT / EXTRUSION / LOSS / ARRIVAL event ever flagged (audit: logically identical to V_body in T5).'],
 ['efficacy','how much more often the target state is reached with the intervention than with the CRN twin.'],
 ['selectivity','whether where/what you push matters: controller versus random placement at matched dose, with a permutation null.'],
 ['persistence / release window','the state change must still hold ≥ 120 tu after the last action (last 40 tu sure).'],
 ['CRN twin','an untreated copy of the dish that shares every random event (common random numbers).'],
 ['sham','the same procedure with the delivered light set to zero; identical to the twin.'],
 ['held-out','dishes and seeds never used for development; locked until the analysis is frozen (freeze(hash)).'],
 ['reporter','a pure readout: lights one body row according to the collective state; no cell senses it (package column c0).'],
 ['memory ligands A / B','secreted signals whose neighbour fraction is the evidence for the collective state (c4, c5).'],
 ['ρ','a node\'s belief that the collective is in state a (σ of the memory logit l); hidden.'],
 ['dose','amplitude × duration × number of lit cells (nominal).'],
 ['quorum','how many cells a group needs to keep the memory: lifetime grows exponentially with group size.'],
 ['tipping point','the barrier in the double well: pushes beyond it complete the switch by themselves.'],
 ['package labels','c0–c6: reporter, three body-type signals, memory ligands A and B, head-to-tail gradient (c1–c3 = ch2, ch1, ch3; c6 = ch0). L1–L5: lights (L1 migration, L2 structural secretion, L3 memory-A secretion, L4 memory-B secretion, L5 receptor gain). O1–O3: tracked cells / unlabelled points / images (O3a, O3b fields, O3c cell markers).']];
Demo.register({id:'B',act:'A',title:'Glossary',data:[],duration:0,truthOffered:false,legend:[],
  caption:'Plain-language definitions of every term used in the demo, with the package labels (c0–c6, L1–L5, O1–O3) as secondary names.',takeaway:'Plain names first; opaque package labels second.',
  notes:'The package labels were opaque to the blind analysts; the mapping shown here comes from the hidden tier (AUDIT_T4 and AUDIT_T5).',
  sources:[{what:'Definitions',file:'t5_blind_control/MONITOR.md, t5_blind_control/CONTROLLER.md, testbed_v3/ENGINE_SPEC_V3.md'},{what:'Package-label mapping',file:'testbed_v3/audit_t4/AUDIT_T4.md',sec:'Unsealed mapping; AUDIT_T5 A5'}],
  setup(c){const g=el('div',{class:'tcap',style:'display:grid;grid-template-columns:200px 1fr;gap:6px 14px;max-width:1100px;margin:0 auto;font-size:14.5px;line-height:1.35'},c.vis);GLOSS.forEach(t=>{el('div',{style:'font-weight:700;text-align:right'},g,t[0]);el('div',{},g,t[1]);});},
  draw(){}
});
