import sys, os, glob; sys.path.insert(0, '.')
from playwright.sync_api import sync_playwright
view, outdir = sys.argv[1], sys.argv[2]; pages = sys.argv[3:]
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1500, 'height': 950})
    errs = []
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e)))
    for name in pages:
        pg.goto('file://' + os.path.abspath(os.path.join(view, name)))
        pg.wait_for_timeout(600)
        # move scrubber to ~40% and press play briefly
        pg.evaluate("(()=>{const s=document.getElementById('scrub');if(!s)return;s.value=Math.floor(s.max*0.4);s.dispatchEvent(new Event('input'))})()")
        pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(outdir, name.replace('.html', '.png')), full_page=True)
        print('shot', name, 'errors so far', errs[:3])
    b.close()
