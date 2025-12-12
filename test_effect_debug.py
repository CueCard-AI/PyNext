"""
Debug why effects aren't triggering on signal changes.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def run_test():
    """Test effect registration and triggering."""
    
    html_path = Path(__file__).parent / "test_linear_page.html"
    
    print("=" * 60)
    print("Effect System Debug Test")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"[PAGE ERROR] {err}"))
        
        # Load the HTML file
        await page.goto(f"file://{html_path}")
        await asyncio.sleep(1)
        
        print("\n1. Checking if createEffect exists...")
        has_create_effect = await page.evaluate("typeof createEffect === 'function'")
        print(f"   Global createEffect: {has_create_effect}")
        
        has_pynext_effect = await page.evaluate("typeof window.__pynext__.createEffect === 'function'")
        print(f"   __pynext__.createEffect: {has_pynext_effect}")
        
        # Test creating a simple effect manually
        print("\n2. Testing effect system manually...")
        result = await page.evaluate("""
            (() => {
                const logs = [];
                
                // Get the signal
                const sig5 = window.__pynext__.getSignal('sig_5');
                logs.push('sig_5 value: ' + sig5.read());
                
                // Create a test effect
                let effectRan = 0;
                window.__pynext__.createEffect(() => {
                    effectRan++;
                    const val = sig5.read();
                    logs.push('Effect ran #' + effectRan + ', sig_5 = ' + val);
                });
                
                logs.push('After creating effect, effectRan = ' + effectRan);
                
                // Now change the signal
                sig5.set(true);
                logs.push('After sig5.set(true), effectRan = ' + effectRan);
                
                return logs;
            })()
        """)
        
        for log in result:
            print(f"   {log}")
        
        # Check if the DOM updated
        print("\n3. Checking DOM after manual effect...")
        modal_element = await page.query_selector("#show_2de0b05fb851")
        if modal_element:
            display = await modal_element.evaluate("el => window.getComputedStyle(el).display")
            print(f"   Modal display: {display}")
        
        # Check if existing bindings have effects
        print("\n4. Testing existing show binding...")
        result2 = await page.evaluate("""
            (() => {
                const logs = [];
                const el = document.getElementById('show_2de0b05fb851');
                
                logs.push('Element initial display: ' + window.getComputedStyle(el).display);
                logs.push('Element initial style.display: ' + el.style.display);
                
                // Create a direct effect
                const sig5 = window.__pynext__.getSignal('sig_5');
                logs.push('sig_5 current value: ' + sig5.read());
                
                // Toggle the signal
                sig5.set(false);
                logs.push('After set(false), sig_5 = ' + sig5.read());
                
                sig5.set(true);
                logs.push('After set(true), sig_5 = ' + sig5.read());
                
                // Check DOM
                logs.push('Element display after set(true): ' + window.getComputedStyle(el).display);
                logs.push('Element style.display after set(true): ' + el.style.display);
                
                return logs;
            })()
        """)
        
        for log in result2:
            print(f"   {log}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())

