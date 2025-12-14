"""
Playwright browser test for the actual Linear clone issues page.
"""

import asyncio
import subprocess
import time
import sys
sys.path.insert(0, '.')

from playwright.async_api import async_playwright


async def run_test():
    """Run the browser test on the actual Linear app."""
    
    # Start the PyNext dev server
    print("Starting PyNext dev server...")
    server = subprocess.Popen(
        ["python", "-m", "pynext", "dev", "--port", "8765"],
        cwd="/Users/karthikravi/CueGrowth-OpenSource/PyNext/examples/linear",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Give server time to start
    await asyncio.sleep(3)
    
    print("=" * 60)
    print("PyNext Linear Clone Browser Test")
    print("=" * 60)
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Capture console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
            page.on("pageerror", lambda err: console_logs.append(f"[ERROR] {err}"))
            
            # Load issues page
            print("\n1. Loading /issues page...")
            try:
                await page.goto("http://localhost:8765/issues", timeout=10000)
            except Exception as e:
                print(f"   Failed to load page: {e}")
                # Try root page
                print("   Trying root page...")
                await page.goto("http://localhost:8765/", timeout=10000)
            
            await asyncio.sleep(1)
            
            print("\n2. Console logs after page load:")
            for log in console_logs[-20:]:  # Last 20 logs
                print(f"   {log}")
            console_logs.clear()
            
            # Check if runtime loaded
            runtime_loaded = await page.evaluate("typeof window.__pynext__ !== 'undefined'")
            print(f"\n3. PyNext runtime loaded: {runtime_loaded}")
            
            if runtime_loaded:
                # Check signals
                signals = await page.evaluate("Object.keys(window.__pynext__.signals)")
                print(f"\n4. Signals created: {len(signals)}")
                for s in signals[:5]:
                    print(f"   - {s}")
                
                # Check bindings
                bindings_count = await page.evaluate("""
                    window.__PYNEXT_HYDRATION__ ? 
                    (window.__PYNEXT_HYDRATION__.bindings || []).length : 0
                """)
                print(f"\n5. Bindings in hydration data: {bindings_count}")
            
            # Try clicking the "+ New Issue" button
            print("\n6. Looking for '+ New Issue' button...")
            
            new_issue_btn = await page.query_selector("text='+ New Issue'")
            if new_issue_btn:
                print("   Found button! Clicking...")
                await new_issue_btn.click()
                await asyncio.sleep(0.5)
                
                print("\n7. Console logs after click:")
                for log in console_logs[-10:]:
                    print(f"   {log}")
                
                # Check if modal appeared
                modal = await page.query_selector(".modal-overlay")
                if modal:
                    print("\n8. Modal appeared! ✓")
                else:
                    # Check for Show element visibility
                    show_elements = await page.query_selector_all("[data-pynext-show]")
                    print(f"\n8. Modal not found. Show elements on page: {len(show_elements)}")
                    
                    for i, el in enumerate(show_elements[:3]):
                        display = await el.evaluate("el => el.style.display")
                        visible = await el.is_visible()
                        print(f"   Show #{i}: display='{display}', visible={visible}")
            else:
                print("   Button not found!")
                
                # Take screenshot
                await page.screenshot(path="linear_test_screenshot.png")
                print("   Screenshot saved to linear_test_screenshot.png")
            
            await browser.close()
            
    finally:
        # Stop server
        server.terminate()
        server.wait()
        print("\nServer stopped.")


if __name__ == "__main__":
    asyncio.run(run_test())

