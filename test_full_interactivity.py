"""
Complete interactivity test for the Linear clone.
Tests all reactive features.
"""

from playwright.sync_api import sync_playwright
from pathlib import Path


def run_tests():
    html_path = Path('test_linear_page.html').absolute()
    
    print("=" * 70)
    print("PyNext Linear Clone - Full Interactivity Test")
    print("=" * 70)
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        page.goto(f'file://{html_path}')
        page.wait_for_timeout(1000)
        
        # =================================================================
        # TEST 1: View Mode Toggle (List <-> Kanban)
        # =================================================================
        print("\n1. VIEW MODE TOGGLE TEST")
        
        # Check initial state (List view)
        list_active = page.evaluate("__pynext__.getSignal('sig_4').read()")
        print(f"   Initial view mode: {list_active}")
        results.append(("Initial view mode is 'list'", list_active == "list"))
        
        # Click Kanban button
        page.click('text="Kanban"')
        page.wait_for_timeout(200)
        
        kanban_active = page.evaluate("__pynext__.getSignal('sig_4').read()")
        print(f"   After Kanban click: {kanban_active}")
        results.append(("Kanban button sets mode to 'kanban'", kanban_active == "kanban"))
        
        # Click List button
        page.click('text="List"')
        page.wait_for_timeout(200)
        
        list_again = page.evaluate("__pynext__.getSignal('sig_4').read()")
        print(f"   After List click: {list_again}")
        results.append(("List button sets mode back to 'list'", list_again == "list"))
        
        # =================================================================
        # TEST 2: Modal Open/Close
        # =================================================================
        print("\n2. MODAL OPEN/CLOSE TEST")
        
        # Check modal is closed
        modal_signal = page.evaluate("__pynext__.getSignal('sig_5').read()")
        print(f"   Initial modal state: {modal_signal}")
        results.append(("Modal initially closed", modal_signal == False))
        
        # Open modal
        page.click('text="+ New Issue"')
        page.wait_for_timeout(300)
        
        modal_opened = page.evaluate("__pynext__.getSignal('sig_5').read()")
        modal_visible = page.query_selector('.modal-content').is_visible()
        print(f"   After open click - signal: {modal_opened}, visible: {modal_visible}")
        results.append(("Modal opens on button click", modal_opened == True and modal_visible))
        
        # Close via X button
        page.click('text="×"')
        page.wait_for_timeout(300)
        
        modal_closed = page.evaluate("__pynext__.getSignal('sig_5').read()")
        print(f"   After close click: {modal_closed}")
        results.append(("Modal closes on X button", modal_closed == False))
        
        # Open again and close via overlay
        page.click('text="+ New Issue"')
        page.wait_for_timeout(300)
        page.click('.modal-overlay', position={'x': 50, 'y': 50})  # Click overlay edge
        page.wait_for_timeout(300)
        
        modal_after_overlay = page.evaluate("__pynext__.getSignal('sig_5').read()")
        print(f"   After overlay click: {modal_after_overlay}")
        results.append(("Modal closes on overlay click", modal_after_overlay == False))
        
        # =================================================================
        # TEST 3: Filter Buttons
        # =================================================================
        print("\n3. FILTER BUTTONS TEST")
        
        # Check initial filter
        filter_status = page.evaluate("__pynext__.getSignal('sig_3').read()")
        print(f"   Initial filter: {filter_status}")
        results.append(("Initial filter is 'all'", filter_status == "all"))
        
        # Click "Todo" filter button (more unique than "In Progress")
        todo_btn = page.locator('button:has-text("Todo")').first
        todo_btn.click()
        page.wait_for_timeout(200)
        
        todo_filter = page.evaluate("__pynext__.getSignal('sig_3').read()")
        print(f"   After 'Todo' click: {todo_filter}")
        results.append(("Filter changes to 'todo'", todo_filter == "todo"))
        
        # Click "All" to reset - find button specifically
        all_btn = page.locator('button:has-text("All")').first
        all_btn.click()
        page.wait_for_timeout(200)
        
        all_filter = page.evaluate("__pynext__.getSignal('sig_3').read()")
        print(f"   After 'All' click: {all_filter}")
        results.append(("Filter resets to 'all'", all_filter == "all"))
        
        # =================================================================
        # TEST 4: Take Final Screenshot
        # =================================================================
        print("\n4. FINAL SCREENSHOT")
        page.screenshot(path='linear_final.png')
        print("   Saved: linear_final.png")
        
        browser.close()
    
    # =================================================================
    # RESULTS SUMMARY
    # =================================================================
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n   TOTAL: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

