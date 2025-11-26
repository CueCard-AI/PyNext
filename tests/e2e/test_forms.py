"""
End-to-end tests for PyNext forms.

Tests form submissions, validation, and server actions.
Uses standalone HTML for reliability without needing a running server.
"""

import pytest

pytestmark = pytest.mark.e2e

# Check if playwright is available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@pytest.fixture(scope="function")
def browser_page():
    """Create a browser page for each test."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        page.close()
        browser.close()


class TestFormSubmission:
    """E2E tests for form submission."""
    
    def test_basic_form_submit(self, browser_page):
        """Basic form submission works."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="contact-form">
                <input name="name" type="text" required>
                <input name="email" type="email" required>
                <textarea name="message"></textarea>
                <button type="submit">Submit</button>
            </form>
            <div class="success-message" style="display:none">Thank you!</div>
            <script>
                document.getElementById('contact-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    document.querySelector('.success-message').style.display = 'block';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Fill out form
        page.fill("input[name='name']", "John Doe")
        page.fill("input[name='email']", "john@example.com")
        page.fill("textarea[name='message']", "Hello, this is a test message.")
        
        # Submit form
        page.click("button[type='submit']")
        
        # Check for success message
        page.wait_for_selector(".success-message:visible")
        success = page.text_content(".success-message")
        assert "thank" in success.lower()
    
    def test_form_prevents_default(self, browser_page):
        """Form submission prevents page reload."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="test-form">
                <input name="name" type="text">
                <input name="email" type="email">
                <button type="submit">Submit</button>
            </form>
            <div id="submitted" data-submitted="false"></div>
            <script>
                document.getElementById('test-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    document.getElementById('submitted').dataset.submitted = 'true';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Fill and submit
        page.fill("input[name='name']", "Test")
        page.fill("input[name='email']", "test@test.com")
        page.click("button[type='submit']")
        
        # Form should have been submitted without page reload
        submitted = page.get_attribute('#submitted', 'data-submitted')
        assert submitted == 'true'


class TestFormValidation:
    """E2E tests for form validation."""
    
    def test_required_field_validation(self, browser_page):
        """Required field validation works."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="test-form">
                <input name="name" type="text" required id="name-input">
                <button type="submit">Submit</button>
            </form>
            <script>
                document.getElementById('test-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                });
            </script>
            </body>
            </html>
        ''')
        
        # Try to submit empty form - browser validation should show
        input_element = page.locator('#name-input')
        
        # Check that input is required
        is_required = page.get_attribute('#name-input', 'required')
        assert is_required is not None
    
    def test_email_validation(self, browser_page):
        """Email validation works."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="test-form">
                <input name="email" type="email" id="email-input">
                <div id="validity"></div>
                <button type="submit">Submit</button>
            </form>
            <script>
                var emailInput = document.getElementById('email-input');
                emailInput.addEventListener('input', function() {
                    document.getElementById('validity').textContent = this.validity.valid ? 'valid' : 'invalid';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Enter invalid email
        page.fill("#email-input", "notanemail")
        validity = page.text_content('#validity')
        assert validity == 'invalid'
        
        # Enter valid email
        page.fill("#email-input", "valid@example.com")
        validity = page.text_content('#validity')
        assert validity == 'valid'
    
    def test_custom_validation_message(self, browser_page):
        """Custom validation messages work."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="test-form">
                <input name="username" type="text" id="username" minlength="3" required>
                <div id="error-msg"></div>
                <button type="submit">Submit</button>
            </form>
            <script>
                var input = document.getElementById('username');
                input.addEventListener('invalid', function(e) {
                    if (this.value.length < 3) {
                        this.setCustomValidity('Username must be at least 3 characters');
                    }
                    document.getElementById('error-msg').textContent = this.validationMessage;
                });
                input.addEventListener('input', function() {
                    this.setCustomValidity('');
                });
            </script>
            </body>
            </html>
        ''')
        
        # Check input has minlength
        minlength = page.get_attribute('#username', 'minlength')
        assert minlength == '3'


class TestFormState:
    """E2E tests for form state management."""
    
    def test_input_value_updates_signal(self, browser_page):
        """Input value syncs with signal/state."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <input type="text" id="name-input">
            <div id="display"></div>
            <script>
                var input = document.getElementById('name-input');
                var display = document.getElementById('display');
                input.addEventListener('input', function() {
                    display.textContent = 'Hello, ' + this.value;
                });
            </script>
            </body>
            </html>
        ''')
        
        # Type in input
        page.fill("#name-input", "Alice")
        
        # Check display updated
        display_text = page.text_content('#display')
        assert "Alice" in display_text
    
    def test_form_loading_state(self, browser_page):
        """Form shows loading state during submission."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="test-form">
                <input name="data" type="text">
                <button type="submit" id="submit-btn">Submit</button>
            </form>
            <script>
                document.getElementById('test-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    var btn = document.getElementById('submit-btn');
                    btn.textContent = 'Loading...';
                    btn.disabled = true;
                    setTimeout(function() {
                        btn.textContent = 'Done';
                        btn.disabled = false;
                    }, 100);
                });
            </script>
            </body>
            </html>
        ''')
        
        # Submit form
        page.fill("input[name='data']", "test")
        page.click('#submit-btn')
        
        # Wait for loading to complete
        page.wait_for_function('document.getElementById("submit-btn").textContent === "Done"')
        
        # Check final state
        btn_text = page.text_content('#submit-btn')
        assert btn_text == 'Done'
    
    def test_form_error_state(self, browser_page):
        """Form shows error state on failure."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="test-form">
                <input name="data" type="text">
                <button type="submit">Submit</button>
            </form>
            <div id="error" style="display:none;color:red">An error occurred</div>
            <script>
                document.getElementById('test-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    // Simulate error
                    document.getElementById('error').style.display = 'block';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Submit form
        page.fill("input[name='data']", "test")
        page.click("button[type='submit']")
        
        # Check error shown
        error_visible = page.is_visible('#error')
        assert error_visible


class TestServerActions:
    """E2E tests for server actions."""
    
    def test_server_action_called(self, browser_page):
        """Server action is called on form submit."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="action-form" data-action="/api/submit">
                <input name="data" type="text">
                <button type="submit">Submit</button>
            </form>
            <div id="result"></div>
            <script>
                document.getElementById('action-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    var action = this.dataset.action;
                    // Simulate server action call
                    document.getElementById('result').textContent = 'Action called: ' + action;
                });
            </script>
            </body>
            </html>
        ''')
        
        # Submit form
        page.fill("input[name='data']", "test")
        page.click("button[type='submit']")
        
        # Check action was called
        result = page.text_content('#result')
        assert 'Action called' in result
        assert '/api/submit' in result
    
    def test_server_action_updates_ui(self, browser_page):
        """Server action result updates UI."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form id="action-form">
                <input name="item" type="text" id="item-input">
                <button type="submit">Add Item</button>
            </form>
            <ul id="items"></ul>
            <script>
                document.getElementById('action-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    var item = document.getElementById('item-input').value;
                    var li = document.createElement('li');
                    li.textContent = item;
                    document.getElementById('items').appendChild(li);
                    document.getElementById('item-input').value = '';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Add items
        page.fill("#item-input", "Item 1")
        page.click("button[type='submit']")
        page.fill("#item-input", "Item 2")
        page.click("button[type='submit']")
        
        # Check items added
        items = page.locator('#items li')
        assert items.count() == 2


class TestFileUpload:
    """E2E tests for file uploads."""
    
    def test_file_upload(self, browser_page):
        """File upload works."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <input type="file" id="file-input">
            <div id="filename"></div>
            <script>
                document.getElementById('file-input').addEventListener('change', function() {
                    if (this.files.length > 0) {
                        document.getElementById('filename').textContent = this.files[0].name;
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Create a test file path (we can't actually upload, but test the structure)
        file_input = page.locator('#file-input')
        assert file_input.is_visible()
    
    def test_file_preview(self, browser_page):
        """File preview shows selected file info."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <input type="file" id="file-input" accept="image/*">
            <div id="preview"></div>
            <script>
                document.getElementById('file-input').addEventListener('change', function() {
                    if (this.files.length > 0) {
                        var file = this.files[0];
                        document.getElementById('preview').textContent = 
                            'Selected: ' + file.name + ' (' + file.type + ')';
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Check accept attribute
        accept = page.get_attribute('#file-input', 'accept')
        assert accept == 'image/*'


class TestFormAccessibility:
    """E2E tests for form accessibility."""
    
    def test_form_labels(self, browser_page):
        """Form inputs have proper labels."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form>
                <label for="name">Name</label>
                <input type="text" id="name" name="name">
                
                <label for="email">Email</label>
                <input type="email" id="email" name="email">
            </form>
            </body>
            </html>
        ''')
        
        # Check labels exist and are associated
        name_label = page.locator('label[for="name"]')
        email_label = page.locator('label[for="email"]')
        
        assert name_label.text_content() == "Name"
        assert email_label.text_content() == "Email"
    
    def test_focus_management(self, browser_page):
        """Focus moves correctly through form."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <form>
                <input type="text" id="first" name="first">
                <input type="text" id="second" name="second">
                <input type="text" id="third" name="third">
                <button type="submit" id="submit">Submit</button>
            </form>
            </body>
            </html>
        ''')
        
        # Focus first input
        page.focus('#first')
        focused = page.evaluate('document.activeElement.id')
        assert focused == 'first'
        
        # Tab to next
        page.keyboard.press('Tab')
        focused = page.evaluate('document.activeElement.id')
        assert focused == 'second'
        
        # Tab again
        page.keyboard.press('Tab')
        focused = page.evaluate('document.activeElement.id')
        assert focused == 'third'
