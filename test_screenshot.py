"""
Take screenshots of the Linear app before and after clicking.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def run_test():
    """Take screenshots."""
    
    html_path = Path(__file__).parent / "test_linear_page.html"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_viewport_size({"width": 1400, "height": 900})
        
        await page.goto(f"file://{html_path}")
        await asyncio.sleep(1)
        
        # Screenshot 1: Before click
        await page.screenshot(path="screenshot_1_before.png", full_page=True)
        print("Saved: screenshot_1_before.png")
        
        # Click the button
        await page.click("text='+ New Issue'")
        await asyncio.sleep(0.3)
        
        # Screenshot 2: After click
        await page.screenshot(path="screenshot_2_after.png", full_page=True)
        print("Saved: screenshot_2_after.png")
        
        # Check what's in the modal
        modal_html = await page.evaluate("""
            (() => {
                const el = document.getElementById('show_58983c02e035');
                if (!el) return 'Not found';
                return {
                    tagName: el.tagName,
                    className: el.className,
                    display: el.style.display,
                    parentDisplay: el.parentElement ? window.getComputedStyle(el.parentElement).display : 'N/A',
                    boundingRect: el.getBoundingClientRect()
                };
            })()
        """)
        print(f"\nModal element info: {modal_html}")
        
        # Get the modal binding info
        binding = await page.evaluate("""
            window.__PYNEXT_HYDRATION__.bindings.find(b => b.signals.includes('sig_5'))
        """)
        print(f"Modal binding: {binding}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())

