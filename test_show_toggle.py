"""
Test Show component toggle specifically.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def run_test():
    """Test Show component toggle."""
    
    html_path = Path(__file__).parent / "test_linear_page.html"
    
    print("=" * 60)
    print("Show Component Toggle Test")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        await page.goto(f"file://{html_path}")
        await asyncio.sleep(1)
        
        # Get the modal element (bound to sig_5)
        modal_id = await page.evaluate("""
            (() => {
                const bindings = window.__PYNEXT_HYDRATION__.bindings;
                const modalBinding = bindings.find(b => b.signals.includes('sig_5'));
                return modalBinding ? modalBinding.nodeId : null;
            })()
        """)
        print(f"\n1. Modal element ID: {modal_id}")
        
        # Check initial state
        result = await page.evaluate(f"""
            (() => {{
                const el = document.getElementById('{modal_id}');
                if (!el) return {{ error: 'Element not found' }};
                
                const sig5 = window.__pynext__.getSignal('sig_5');
                
                return {{
                    sig5_value: sig5.read(),
                    display: el.style.display,
                    computedDisplay: window.getComputedStyle(el).display,
                    innerHTML: el.innerHTML.substring(0, 100)
                }};
            }})()
        """)
        
        print(f"\n2. Initial state:")
        print(f"   sig_5 value: {result.get('sig5_value')}")
        print(f"   style.display: '{result.get('display')}'")
        print(f"   computedDisplay: '{result.get('computedDisplay')}'")
        
        # Count registered effects
        effect_count = await page.evaluate("Object.keys(window.__pynext__.effects).length")
        print(f"\n3. Registered effects: {effect_count}")
        
        # List effect IDs that start with effect_
        dynamic_effects = await page.evaluate("""
            Object.keys(window.__pynext__.effects).filter(k => k.startsWith('effect_'))
        """)
        print(f"   Dynamic effects: {len(dynamic_effects)}")
        
        # Click the button
        print("\n4. Clicking '+ New Issue' button...")
        await page.click("text='+ New Issue'")
        await asyncio.sleep(0.2)
        
        print("\n5. Console logs after click:")
        for log in console_logs[-5:]:
            print(f"   {log}")
        console_logs.clear()
        
        # Check state after click
        result2 = await page.evaluate(f"""
            (() => {{
                const el = document.getElementById('{modal_id}');
                const sig5 = window.__pynext__.getSignal('sig_5');
                
                return {{
                    sig5_value: sig5.read(),
                    display: el.style.display,
                    computedDisplay: window.getComputedStyle(el).display
                }};
            }})()
        """)
        
        print(f"\n6. State after click:")
        print(f"   sig_5 value: {result2.get('sig5_value')}")
        print(f"   style.display: '{result2.get('display')}'")
        print(f"   computedDisplay: '{result2.get('computedDisplay')}'")
        
        # Check if sig_5 has subscribers
        subscriber_info = await page.evaluate("""
            (() => {
                // We can't directly access subscribers from outside,
                // but we can test if setting the signal triggers an effect
                let effectRan = false;
                const sig5 = window.__pynext__.getSignal('sig_5');
                
                // Create a test effect
                window.__pynext__.createEffect(() => {
                    sig5.read();
                    effectRan = true;
                });
                
                // Reset flag
                effectRan = false;
                
                // Toggle sig5
                sig5.set(false);
                const ran1 = effectRan;
                
                effectRan = false;
                sig5.set(true);
                const ran2 = effectRan;
                
                return { ran1, ran2 };
            })()
        """)
        
        print(f"\n7. Effect subscription test:")
        print(f"   Effect ran after set(false): {subscriber_info.get('ran1')}")
        print(f"   Effect ran after set(true): {subscriber_info.get('ran2')}")
        
        # Final state
        result3 = await page.evaluate(f"""
            (() => {{
                const el = document.getElementById('{modal_id}');
                return {{
                    display: el.style.display,
                    computedDisplay: window.getComputedStyle(el).display
                }};
            }})()
        """)
        
        print(f"\n8. Final state:")
        print(f"   style.display: '{result3.get('display')}'")
        print(f"   computedDisplay: '{result3.get('computedDisplay')}'")
        
        # Check if the modal is actually visible (not just display != none)
        is_visible = await page.is_visible(f"#{modal_id}")
        print(f"   is_visible: {is_visible}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())

