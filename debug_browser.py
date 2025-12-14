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
        await page.goto('http://127.0.0.1:3005/issues', timeout=10000)
        await page.wait_for_load_state('networkidle')
        
        # Check hydration data
        hydration = await page.evaluate('''() => ({
            exists: !!window.__PYNEXT_HYDRATION__,
            forms: Object.keys(window.__PYNEXT_HYDRATION__?.forms || {}),
            hydratedForms: Object.keys(window.__pynext__?.forms || {}),
            events: Object.keys(window.__PYNEXT_HYDRATION__?.events || {})
        })''')
        print(f"Hydration: {hydration}")
        
        # Print event info
        event_count = len(hydration.get('events', []))
        print(f"Event handlers: {event_count} elements with handlers")
        
        # Click + New Issue
        print("\nClicking + New Issue...")
        await page.click('button:has-text("+ New Issue")')
        await page.wait_for_timeout(1000)
        
        # Fill form
        print("Filling form...")
        await page.fill('input[type="text"]', 'Test Issue')
        await page.fill('textarea', 'Test description')
        await page.wait_for_timeout(500)
        
        # Check button state before clicking
        print("\nChecking Create Issue button...")
        btn_info = await page.evaluate('''() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Create Issue'));
            if (!btn) return {found: false};
            return {
                found: true,
                id: btn.id,
                hasOnclick: !!btn.onclick,
                listeners: btn._listeners || 'unknown'
            };
        }''')
        print(f"Button: {btn_info}")
        
        # Click Create Issue
        print("\nClicking Create Issue...")
        await page.click('button:has-text("Create Issue")')
        await page.wait_for_timeout(1500)
        
        print("\nConsole logs:")
        for log in console_logs[-20:]:
            print(f"  {log}")
        
        await page.screenshot(path='/Users/karthikravi/CueGrowth-OpenSource/PyNext/debug.png')
        print("\nScreenshot saved to debug.png")
        
        await page.wait_for_timeout(3000)
        await browser.close()

asyncio.run(main())
