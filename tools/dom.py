import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width":1440,"height":900})
        await pg.goto("http://localhost:8765/?page=home"); await pg.wait_for_selector(".st-key-shell"); await pg.wait_for_timeout(2000)
        r = await pg.evaluate("""() => { const out=[]; let e=document.querySelector('.st-key-shell'); 
          for(let i=0;i<7&&e;i++){ const cs=getComputedStyle(e), r=e.getBoundingClientRect(); out.push([e.tagName, (e.getAttribute('data-testid')||'')+' '+(e.className||'').toString().slice(0,60), Math.round(r.top), Math.round(r.height), cs.paddingTop, cs.marginTop, cs.gap]); e=e.parentElement; }
          const h=document.querySelector('.st-key-hero').getBoundingClientRect(); out.push(['hero top', Math.round(h.top)]); const s=document.querySelector('.st-key-shell').getBoundingClientRect(); out.push(['shell bottom', Math.round(s.bottom)]);
          return out; }""")
        for x in r: print(x)
        await b.close()
asyncio.run(main())
