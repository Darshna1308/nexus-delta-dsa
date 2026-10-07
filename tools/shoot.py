import asyncio, sys
from playwright.async_api import async_playwright
PAGES = [("home","HOME"),("capability","CAP"),("career","CAREER"),("scanner","SCAN"),("workdna","DNA"),("evidence","EVID"),("about","ABOUT")]
VIEWS = {"tall": (1440,2400), "1920": (1920,1080), "1440": (1440,900), "1366": (1366,768)}
async def main(views, pages, extra=""):
    full = "full" in sys.argv
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium" if False else None)
        for vn in views:
            w,h = VIEWS[vn]; ctx = await b.new_context(viewport={"width":w,"height":h}); pg = await ctx.new_page()
            for slug,_ in PAGES:
                if pages and slug not in pages: continue
                await pg.goto(f"http://localhost:8765/?page={slug}{extra}"); await pg.wait_for_selector("text=NEXUS DELTA", timeout=30000); await pg.wait_for_timeout(2500)
                ov = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                sh = await pg.evaluate("Math.max(document.body.scrollHeight, document.querySelector('[data-testid=stAppViewContainer]').scrollHeight)")
                print(vn, slug, "h-overflow px:", ov, "scrollH:", sh)
                await pg.screenshot(path=f"shots/{slug}_{vn}{'_demo' if extra else ''}{'_full' if full else ''}.png", full_page=full)
            await ctx.close()
        await b.close()
asyncio.run(main(sys.argv[1].split(","), sys.argv[2].split(",") if len(sys.argv)>2 and sys.argv[2] else None, sys.argv[3] if len(sys.argv)>3 else ""))
