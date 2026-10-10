"""Playwright helper: python3 build/shot.py <chapter> [pause indexes]  -> screenshots/<chapter>_*.png and console errors"""
import sys, os, asyncio, json
from playwright.async_api import async_playwright
DEMO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
async def main(ids, W=1600, H=1250, presenter=False):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': W, 'height': H}); errs = []
        pg.on('console', lambda m: errs.append(('console', m.type, m.text)) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: errs.append(('pageerror', str(e))))
        await pg.goto('file://' + DEMO + '/index.html'); await pg.wait_for_timeout(500)
        for cid in ids:
            await pg.evaluate("(id)=>{location.hash='#'+id}", cid); await pg.wait_for_timeout(900)
            n = await pg.evaluate("()=>{const d=Demo.cur;return (d.pauses||[]).length}"); nv = await pg.evaluate("()=>{const d=Demo.cur;return (d.views||[]).length}")
            os.makedirs(DEMO + '/screenshots', exist_ok=True)
            nvar = await pg.evaluate("()=>(Demo.cur.variants||[]).length")
            if nvar:
                for j in range(nvar):
                    await pg.evaluate("(j)=>Demo.cur.variants[j].apply(Demo.c)", j); await pg.wait_for_timeout(200)
                    npz = await pg.evaluate("()=>(Demo.cur.pauses||[]).length")
                    for i in range(npz):
                        await pg.evaluate("(i)=>Demo.seekPause(i)", i); await pg.wait_for_timeout(250); await pg.screenshot(path=f'{DEMO}/screenshots/{cid.replace(".","_")}_{j+1}_p{i+1}.png')
            elif n:
                for i in range(n):
                    await pg.evaluate("(i)=>Demo.seekPause(i)", i); await pg.wait_for_timeout(250); await pg.screenshot(path=f'{DEMO}/screenshots/{cid.replace(".","_")}_p{i+1}.png')
            elif nv:
                for i in range(nv):
                    await pg.evaluate("(i)=>Demo.showView(i)", i); await pg.wait_for_timeout(250); await pg.screenshot(path=f'{DEMO}/screenshots/{cid.replace(".","_")}_v{i+1}.png')
            else:
                await pg.wait_for_timeout(300); await pg.screenshot(path=f'{DEMO}/screenshots/{cid.replace(".","_")}.png')
        print(json.dumps(errs, indent=1)[:3000]); await b.close()
if __name__ == '__main__': asyncio.run(main(sys.argv[1:]))
