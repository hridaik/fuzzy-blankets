"""Automated checks of the demo in headless Chromium: console errors, pause-point screenshots (all chapters), callout vs node overlap, legend presence, caption rules,
keyboard navigation, presenter mode, notes, T toggle, export of key frames, hash navigation."""
import sys, os, asyncio, json, re
from playwright.async_api import async_playwright
DEMO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); SHOT = DEMO + '/screenshots'
async def main(W=1600, H=1250):
    os.makedirs(SHOT, exist_ok=True); report = dict(errors=[], chapters={}, keys={}, export={}, overlap=[])
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width': W, 'height': H}, accept_downloads=True); pg = await ctx.new_page()
        pg.on('console', lambda m: report['errors'].append(('console', m.type, m.text)) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: report['errors'].append(('pageerror', str(e))))
        t0 = await pg.evaluate("0"); await pg.goto('file://' + DEMO + '/index.html'); await pg.wait_for_timeout(700)
        ids = await pg.evaluate("()=>Demo.chapters.map(c=>c.id)")
        for cid in ids:
            await pg.evaluate("(id)=>{location.hash='#'+id}", cid); await pg.wait_for_timeout(1000)
            info = await pg.evaluate("""()=>{const d=Demo.cur;const cap=document.getElementById('caption');const fs=parseFloat(getComputedStyle(cap).fontSize);const txt=cap.innerText;const sents=txt.split(/(?<=[.!?])\\s+(?=[A-Z“])/).length;
              return {id:d.id,fs:fs,sentences:sents,legend:document.querySelectorAll('#legend .chip').length,pauses:(d.pauses||[]).length,views:(d.views||[]).length,variants:(d.variants||[]).length,truth:!!d.truthOffered,sources:(d.sources||[]).length,take:document.getElementById('takeaway').innerText.length}}""")
            report['chapters'][cid] = info; nvar = info['variants']
            async def shots(tag):
                n = await pg.evaluate("()=>(Demo.cur.pauses||[]).length")
                for i in range(n):
                    await pg.evaluate("(i)=>Demo.seekPause(i)", i); await pg.wait_for_timeout(250)
                    ov = await pg.evaluate("""()=>{const c=Demo.c,b=Demo._bubble;if(!b)return null;const sw=document.getElementById('stagewrap').getBoundingClientRect();const hits=[];
                        c.panels.forEach(p=>{if(p.avoidAll)return;const r=p.rect(),k=r.w/p.w;(p._nodes||[]).forEach(n=>{const q=p.w2p(n[0],n[1]),rr=n[2]*p.scale*k,x=r.x+q[0]*k,y=r.y+q[1]*(r.h/p.h);if(x+rr>b.x&&x-rr<b.x+b.w&&y+rr>b.y&&y-rr<b.y+b.h)hits.push([Math.round(x),Math.round(y)]);});});return {n:hits.length}}""")
                    if ov and ov['n']: report['overlap'].append((cid, tag, i, ov['n']))
                    await pg.screenshot(path=f"{SHOT}/{cid.replace('.','_')}{('_'+tag) if tag else ''}_p{i+1}.png")
            if nvar:
                for j in range(nvar):
                    nm = await pg.evaluate("(j)=>{Demo.cur.variants[j].apply(Demo.c);return Demo.cur.variants[j].name}", j); await pg.wait_for_timeout(300); await shots(nm)
            elif info['pauses']: await shots('')
            elif info['views']:
                for i in range(info['views']):
                    await pg.evaluate("(i)=>Demo.showView(i)", i); await pg.wait_for_timeout(250); await pg.screenshot(path=f"{SHOT}/{cid.replace('.','_')}_v{i+1}.png")
            else: await pg.screenshot(path=f"{SHOT}/{cid.replace('.','_')}.png")
        # keyboard & modes
        await pg.evaluate("()=>{location.hash='#1.1'}"); await pg.wait_for_timeout(600)
        await pg.keyboard.press('ArrowRight'); await pg.wait_for_timeout(600); report['keys']['arrow_right_hash'] = await pg.evaluate("()=>location.hash")
        await pg.keyboard.press('ArrowLeft'); await pg.wait_for_timeout(600); report['keys']['arrow_left_hash'] = await pg.evaluate("()=>location.hash")
        await pg.evaluate("()=>{Demo.hideCallout();Demo.seek(2);}"); await pg.keyboard.press('Space'); await pg.wait_for_timeout(400); report['keys']['space_playing'] = await pg.evaluate("()=>Demo.playing"); await pg.keyboard.press('Space'); await pg.wait_for_timeout(200); report['keys']['space_paused'] = not await pg.evaluate("()=>Demo.playing")
        await pg.keyboard.press('f'); await pg.wait_for_timeout(700); report['keys']['presenter_on'] = await pg.evaluate("()=>document.body.classList.contains('presenter')&&getComputedStyle(document.getElementById('side')).display==='none'")
        await pg.screenshot(path=f"{SHOT}/presenter_1_1.png"); await pg.keyboard.press('f'); await pg.wait_for_timeout(500); report['keys']['presenter_off'] = await pg.evaluate("()=>!document.body.classList.contains('presenter')")
        await pg.keyboard.press('n'); await pg.wait_for_timeout(200); report['keys']['notes_visible'] = await pg.evaluate("()=>getComputedStyle(document.getElementById('notes')).display==='block'"); await pg.screenshot(path=f"{SHOT}/notes_1_1.png"); await pg.keyboard.press('n')
        for cid in ('3.4', '4.3', '4.2', '2.2'):
            await pg.evaluate("(id)=>{location.hash='#'+id}", cid); await pg.wait_for_timeout(900); await pg.keyboard.press('t'); await pg.wait_for_timeout(300)
            report['keys']['truth_'+cid] = await pg.evaluate("()=>document.body.classList.contains('truth')"); await pg.screenshot(path=f"{SHOT}/{cid.replace('.','_')}_truth.png"); await pg.keyboard.press('t')
        # export: count downloads per chapter
        dl = []; pg.on('download', lambda d: dl.append(d.suggested_filename))
        for cid in ids:
            await pg.evaluate("(id)=>{location.hash='#'+id}", cid); await pg.wait_for_timeout(900); dl.clear(); got = dl
            await pg.click('#bExport'); await pg.wait_for_timeout(2500 + 700 * (await pg.evaluate("()=>(Demo.cur.pauses||[]).length*Math.max(1,(Demo.cur.variants||[]).length)")))
            report['export'][cid] = list(got)
        await b.close()
    json.dump(report, open(DEMO + '/build/test_report.json', 'w'), indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != 'chapters'}, indent=1)[:4000])
    for cid, i in report['chapters'].items(): print(cid, i)
if __name__ == '__main__': asyncio.run(main())
