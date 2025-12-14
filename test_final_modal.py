"""
Final modal toggle test with detailed debugging.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def run_test():
    """Test modal toggle."""
    
    html_path = Path(__file__).parent / "test_linear_page.html"
    
    print("=" * 60)
    print("Final Modal Toggle Test")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1400, "height": 900})
        
        console_logs = []
        page.on("console", lambda msg: console_logs.append(msg.text))
        
        await page.goto(f"file://{html_path}")
        await asyncio.sleep(1)
        
        # Get the modal binding
        modal_info = await page.evaluate("""
            (() => {
                const bindings = window.__PYNEXT_HYDRATION__.bindings;
                const modalBinding = bindings.find(b => b.signals.includes('sig_5'));
                if (!modalBinding) return { error: 'Modal binding not found' };
                
                const el = document.getElementById(modalBinding.nodeId);
                if (!el) return { error: 'Modal element not found', id: modalBinding.nodeId };
                
                return {
                    id: modalBinding.nodeId,
                    display: el.style.display,
                    computed: window.getComputedStyle(el).display,
                    rect: el.getBoundingClientRect(),
                    innerHTML: el.innerHTML.substring(0, 200),
                    hasChildren: el.children.length > 0,
                    childCount: el.children.length
                };
            })()
        """)
        
        print(f"\n1. BEFORE CLICK:")
        print(f"   Modal ID: {modal_info.get('id')}")
        print(f"   display: {modal_info.get('display')}")
        print(f"   computed: {modal_info.get('computed')}")
        print(f"   children: {modal_info.get('childCount')}")
        print(f"   rect: {modal_info.get('rect')}")
        
        # Screenshot before
        await page.screenshot(path="screenshot_before.png", full_page=True)
        print("   Screenshot: screenshot_before.png")
        
        # Click the button
        print("\n2. Clicking '+ New Issue' button...")
        await page.click("text='+ New Issue'")
        await asyncio.sleep(0.3)
        
        # Get state after click
        modal_id = modal_info.get('id')
        after_info = await page.evaluate(f"""
            (() => {{
                const el = document.getElementById('{modal_id}');
                if (!el) return {{ error: 'Not found' }};
                
                const sig5 = window.__pynext__.getSignal('sig_5');
                
                return {{
                    sig5: sig5.read(),
                    display: el.style.display,
                    computed: window.getComputedStyle(el).display,
                    rect: el.getBoundingClientRect(),
                    visible: el.offsetWidth > 0 || el.offsetHeight > 0
                }};
            }})()
        """)
        
        print(f"\n3. AFTER CLICK:")
        print(f"   sig_5: {after_info.get('sig5')}")
        print(f"   display: {after_info.get('display')}")
        print(f"   computed: {after_info.get('computed')}")
        print(f"   visible: {after_info.get('visible')}")
        print(f"   rect: {after_info.get('rect')}")
        
        # Screenshot after
        await page.screenshot(path="screenshot_after.png", full_page=True)
        print("   Screenshot: screenshot_after.png")
        
        # Check if we can find the modal overlay
        modal_overlay = await page.query_selector(".modal-overlay")
        if modal_overlay:
            overlay_visible = await modal_overlay.is_visible()
            print(f"\n4. Modal overlay found: visible={overlay_visible}")
        else:
            print("\n4. Modal overlay NOT FOUND")
            
            # List what's visible
            visible_els = await page.evaluate("""
                Array.from(document.querySelectorAll('.modal-overlay, .modal-content'))
                    .map(el => ({
                        class: el.className,
                        display: window.getComputedStyle(el).display,
                        rect: el.getBoundingClientRect()
                    }))
            """)
            print(f"   Modal elements: {visible_els}")
        
        print("\n5. Console logs (last 10):")
        for log in console_logs[-10:]:
            print(f"   {log}")
        
        # SUCCESS CHECK
        rect = after_info.get('rect', {})
        success = (
            after_info.get('sig5') == True and
            after_info.get('computed') == 'block' and
            rect.get('height', 0) > 0
        )
        
        print("\n" + "=" * 60)
        if success:
            print("✅ SUCCESS! Modal is showing correctly!")
        else:
            print("❌ ISSUE: Modal not showing correctly")
            print(f"   - sig_5 is True: {after_info.get('sig5') == True}")
            print(f"   - display is block: {after_info.get('computed') == 'block'}")
            print(f"   - height > 0: {rect.get('height', 0) > 0}")
        print("=" * 60)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())

