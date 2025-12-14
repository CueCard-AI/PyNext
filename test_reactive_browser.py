"""
Playwright browser test for PyNext reactive system.

This script:
1. Starts a simple HTTP server
2. Opens a browser
3. Loads the test page
4. Clicks buttons and captures console logs
5. Reports what happened

Run with: python test_reactive_browser.py
"""

import asyncio
import threading
import http.server
import socketserver
import os
from pathlib import Path

# Try to import playwright
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    exit(1)


def start_server(port=9999):
    """Start a simple HTTP server in a background thread."""
    os.chdir(Path(__file__).parent)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None  # Silence logging
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()


async def run_test():
    """Run the browser test."""
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    await asyncio.sleep(0.5)
    
    print("=" * 60)
    print("PyNext Reactive DOM Browser Test")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        # Load test page
        print("\n1. Loading test page...")
        await page.goto("http://localhost:9999/test_reactive.html")
        await asyncio.sleep(0.5)
        
        print("\n2. Console logs after page load:")
        for log in console_logs:
            print(f"   {log}")
        console_logs.clear()
        
        # Test 1: Click counter button
        print("\n3. Clicking counter button...")
        await page.click("#el_test_1")
        await asyncio.sleep(0.1)
        
        print("\n4. Console logs after counter click:")
        for log in console_logs:
            print(f"   {log}")
        console_logs.clear()
        
        # Get counter value
        count_text = await page.text_content("#el_count")
        print(f"\n5. Counter value: {count_text}")
        
        # Test 2: Click show/hide toggle
        print("\n6. Clicking show/hide toggle...")
        await page.click("#el_toggle_show")
        await asyncio.sleep(0.1)
        
        print("\n7. Console logs after show toggle:")
        for log in console_logs:
            print(f"   {log}")
        console_logs.clear()
        
        # Check if box is hidden
        box_display = await page.evaluate('document.getElementById("show_box_1").style.display')
        print(f"\n8. Box display style: '{box_display}' (empty=visible, 'none'=hidden)")
        
        # Click again to show
        print("\n9. Clicking show/hide toggle again...")
        await page.click("#el_toggle_show")
        await asyncio.sleep(0.1)
        
        box_display = await page.evaluate('document.getElementById("show_box_1").style.display')
        print(f"\n10. Box display style after second click: '{box_display}'")
        
        # Test 3: Class toggle
        print("\n11. Clicking class toggle...")
        await page.click("#el_toggle_class")
        await asyncio.sleep(0.1)
        
        class_name = await page.evaluate('document.getElementById("el_class_target").className')
        border_color = await page.evaluate('document.getElementById("el_class_target").style.borderColor')
        print(f"\n12. Class after toggle: '{class_name}'")
        print(f"    Border color: '{border_color}'")
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✓ Counter incremented: {count_text == '1'}")
        print(f"✓ Show/hide works: {box_display == ''}")  # Empty after second click = visible
        print(f"✓ Class toggle works: {'active' in class_name}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_test())

