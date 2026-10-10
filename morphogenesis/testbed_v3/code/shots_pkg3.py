import sys, os, glob
from playwright.sync_api import sync_playwright
V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'viewer_pkg3'); S = os.path.join(V, 'screenshots'); os.makedirs(S, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1500, 'height': 1400}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    for f in sorted(glob.glob(V + '/*.html')):
        pg.goto('file://' + os.path.abspath(f)); pg.wait_for_timeout(800)
        n = pg.evaluate("document.getElementById('sl').max")
        for tag, frac in (('start', 0.0), ('mid', 0.5), ('end', 1.0)):
            pg.evaluate(f"(()=>{{const s=document.getElementById('sl'); s.value=Math.round({frac}*s.max); s.dispatchEvent(new Event('input'));}})()"); pg.wait_for_timeout(200)
            pg.screenshot(path=os.path.join(S, os.path.basename(f)[:-5] + f'_{tag}.png'))
        print(os.path.basename(f), 'frames', n)
    print('page errors:', errs); b.close()
