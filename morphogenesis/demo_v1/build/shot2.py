import asyncio,sys
from playwright.async_api import async_playwright
D='/home/hkhurana/work/code/fuzzy-blankets/morphogenesis/demo_v1'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1600,'height':1250}); errs=[]
        pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        await pg.goto('file://'+D+'/index.html'); await pg.wait_for_timeout(500)
        for a in sys.argv[1:]:
            cid,_,pi=a.partition(':')
            await pg.evaluate("(id)=>{location.hash='#'+id}",cid); await pg.wait_for_timeout(1200)
            if pi!='': await pg.evaluate("(i)=>Demo.seekPause(+i)",pi); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f'/tmp/shot_{cid.replace(".","_")}_{pi}.png')
        print(errs[:5]); await b.close()
asyncio.run(main())
