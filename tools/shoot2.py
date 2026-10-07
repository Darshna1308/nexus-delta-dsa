import asyncio
from playwright.async_api import async_playwright
async def login(pg, u):
    await pg.goto("http://localhost:8765/"); await pg.wait_for_selector("text=SIGN IN", timeout=30000); await pg.wait_for_timeout(1500)
    await pg.get_by_role("textbox", name="Username").fill(u); await pg.keyboard.press("Tab"); await pg.wait_for_timeout(900); await pg.get_by_role("textbox", name="Password").fill("Demo#2026pw"); await pg.keyboard.press("Tab"); await pg.wait_for_timeout(1200)
    await pg.get_by_role("button", name="SIGN IN ›").click(); await pg.wait_for_timeout(2500)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width":1440,"height":900}); pg = await ctx.new_page()
        await pg.goto("http://localhost:8765/"); await pg.wait_for_selector("text=SIGN IN", timeout=30000); await pg.wait_for_timeout(2000); await pg.screenshot(path="../shots/login.png")
        for u in ["demo_candidate","demo_org","demo_employee"]:
            c2 = await b.new_context(viewport={"width":1440,"height":2200}); pg = await c2.new_page(); await login(pg, u)
            await pg.screenshot(path="../shots/dbg2.png"); await pg.get_by_role("button", name="CULTURE", exact=True).click(); await pg.wait_for_timeout(2500); await pg.screenshot(path=f"../shots/culture_{u}.png"); await c2.close()
        await b.close()
asyncio.run(main())
