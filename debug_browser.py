"""Interactive Playwright debug script for Linear app."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        print("Loading /issues...")
        await page.goto('http://127.0.0.1:3001/issues', timeout=10000)
        await page.wait_for_load_state('networkidle')
        
        # Check hydration
        hydration = await page.evaluate('''() => ({
            exists: !!window.__PYNEXT_HYDRATION__,
            forms: Object.keys(window.__PYNEXT_HYDRATION__?.forms || {}),
            hydratedForms: Object.keys(window.__pynext__?.forms || {}),
            eventHandlers: window.__PYNEXT_HYDRATION__?.event_handlers || []
        })''')
        print(f"Hydration: {hydration}")
        
        # Print event handlers
        handlers = hydration.get('eventHandlers', [])
        print(f"\nEvent handlers ({len(handlers)}):")
        for h in handlers[:10]:
            code = h.get('code', 'N/A')[:100] if h.get('code') else 'N/A'
            print(f"  {h.get('element_id')}: {code}...")
        
        # Click + New Issue
        print("Clicking + New Issue...")
        await page.click('button:has-text("+ New Issue")')
        await page.wait_for_timeout(1000)
        
        # Fill form
        print("Filling form...")
        await page.fill('input[type="text"]', 'Test Issue')
        await page.fill('textarea', 'Test description')
        await page.wait_for_timeout(500)
        
        # Click Create Issue
        print("Clicking Create Issue...")
        
        # Check button's onclick
        btn_info = await page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Create Issue'));
            if (!btn) return null;
            return {
                id: btn.id,
                onclick: !!btn.onclick,
                textContent: btn.textContent
            };
        }''')
        print(f"Button info: {btn_info}")
        
        await page.click('button:has-text("Create Issue")')
        await page.wait_for_timeout(1000)
        
        print("\nConsole logs:")
        for log in console_logs[-15:]:
            print(f"  {log}")
        
        await page.screenshot(path='/Users/karthikravi/CueGrowth-OpenSource/PyNext/debug.png')
        print("\nScreenshot saved to debug.png")
        
        await page.wait_for_timeout(5000)
        await browser.close()

asyncio.run(main())

