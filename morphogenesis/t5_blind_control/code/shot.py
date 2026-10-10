import sys,asyncio
from playwright.sync_api import sync_playwright
def shoot(pages,frames_frac=(0.35,),w=1500,h=950):
    with sync_playwright() as p:
        b=p.chromium.launch(); out=[]
        for html,png,frac in pages:
            pg=b.new_page(viewport={'width':w,'height':h}); errs=[]
            pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None); pg.on('pageerror',lambda e: errs.append(str(e)))
            pg.goto('file://'+html); pg.wait_for_timeout(400)
            n=pg.evaluate('times.length'); pg.evaluate(f'frame=Math.floor(times.length*{frac});sl.value=frame;draw()'); pg.wait_for_timeout(200)
            pg.screenshot(path=png,full_page=True); out.append((png,errs)); pg.close()
        b.close(); return out
if __name__=='__main__':
    print(shoot([(sys.argv[1],sys.argv[2],float(sys.argv[3]))]))
