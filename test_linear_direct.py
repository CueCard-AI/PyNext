"""
Direct browser test for the generated Linear page.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def run_test():
    """Run the browser test on the generated HTML file."""
    
    html_path = Path(__file__).parent / "test_linear_page.html"
    
    print("=" * 60)
    print("PyNext Linear Clone Direct Browser Test")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture ALL console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"[PAGE ERROR] {err}"))
        
        # Load the HTML file directly
        print(f"\n1. Loading {html_path}...")
        await page.goto(f"file://{html_path}")
        await asyncio.sleep(1)
        
        print("\n2. ALL Console logs after page load:")
        print("-" * 40)
        for log in console_logs:
            print(f"   {log}")
        print("-" * 40)
        
        # Check if runtime loaded
        runtime_loaded = await page.evaluate("typeof window.__pynext__ !== 'undefined'")
        print(f"\n3. PyNext runtime loaded: {runtime_loaded}")
        
        if runtime_loaded:
            # Check signals
            signals = await page.evaluate("Object.keys(window.__pynext__.signals)")
            print(f"\n4. Signals created: {len(signals)}")
            for s in signals[:10]:
                val = await page.evaluate(f"window.__pynext__.signals['{s}'].read()")
                print(f"   - {s} = {val}")
            
            # Check if hydration data exists
            has_hydration = await page.evaluate("typeof window.__PYNEXT_HYDRATION__ !== 'undefined'")
            print(f"\n5. Hydration data exists: {has_hydration}")
            
            if has_hydration:
                bindings = await page.evaluate("window.__PYNEXT_HYDRATION__.bindings || []")
                print(f"\n6. Bindings in hydration data: {len(bindings)}")
                for b in bindings[:5]:
                    print(f"   - {b}")
        
        # Find the "+ New Issue" button
        console_logs.clear()
        print("\n7. Looking for '+ New Issue' button...")
        
        new_issue_btn = await page.query_selector("text='+ New Issue'")
        if new_issue_btn:
            btn_id = await new_issue_btn.get_attribute("id")
            print(f"   Found button with id: {btn_id}")
            
            # Check what event is registered for this button
            if btn_id:
                events = await page.evaluate(f"""
                    window.__PYNEXT_HYDRATION__ && 
                    window.__PYNEXT_HYDRATION__.events && 
                    window.__PYNEXT_HYDRATION__.events['{btn_id}']
                """)
                print(f"   Events registered: {events}")
            
            print("\n   Clicking button...")
            await new_issue_btn.click()
            await asyncio.sleep(0.5)
            
            print("\n8. Console logs after click:")
            for log in console_logs:
                print(f"   {log}")
            
            # Check Show component visibility
            print("\n9. Checking Show components...")
            show_elements = await page.query_selector_all("[data-pynext-show]")
            print(f"   Found {len(show_elements)} Show elements")
            
            for i, el in enumerate(show_elements[:5]):
                el_id = await el.get_attribute("id")
                display = await el.evaluate("el => window.getComputedStyle(el).display")
                condition = await el.get_attribute("data-condition")
                print(f"   #{el_id}: display={display}, condition={condition}")
            
            # Try to manually trigger the signal
            print("\n10. Manually triggering show_add_form signal...")
            
            # Find the signal ID for show_add_form
            show_signal = await page.evaluate("""
                (() => {
                    const hydration = window.__PYNEXT_HYDRATION__;
                    if (!hydration || !hydration.signals) return null;
                    for (const [name, data] of Object.entries(hydration.signals)) {
                        if (name === 'show_add_form') return data.id;
                    }
                    return null;
                })()
            """)
            print(f"   show_add_form signal ID: {show_signal}")
            
            if show_signal:
                # Set the signal to true
                result = await page.evaluate(f"""
                    (() => {{
                        const sig = window.__pynext__.getSignal('{show_signal}');
                        if (!sig) return 'Signal not found';
                        sig.set(true);
                        return 'Signal set to true';
                    }})()
                """)
                print(f"   Result: {result}")
                await asyncio.sleep(0.3)
                
                print("\n11. Console logs after manual signal set:")
                for log in console_logs[-10:]:
                    print(f"   {log}")
                
                # Check visibility again
                print("\n12. Show elements after signal change:")
                for i, el in enumerate(show_elements[:5]):
                    el_id = await el.get_attribute("id")
                    display = await el.evaluate("el => window.getComputedStyle(el).display")
                    print(f"   #{el_id}: display={display}")
        else:
            print("   Button not found!")
            
            # Take screenshot
            await page.screenshot(path="linear_test_screenshot.png")
            print("   Screenshot saved to linear_test_screenshot.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())

