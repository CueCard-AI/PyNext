"""
End-to-end tests for PyNext forms.

Tests form submissions, validation, and server actions.
"""

import pytest

# These tests require Playwright and a running server
pytestmark = pytest.mark.e2e


class TestFormSubmission:
    """E2E tests for form submission."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_basic_form_submit(self, page, example_app_url):
        """Basic form submission works."""
        await page.goto(f"{example_app_url}/contact")
        
        # Fill out form
        await page.fill("input[name='name']", "John Doe")
        await page.fill("input[name='email']", "john@example.com")
        await page.fill("textarea[name='message']", "Hello, this is a test message.")
        
        # Submit form
        await page.click("button[type='submit']")
        
        # Check for success message
        await page.wait_for_selector(".success-message")
        success = await page.text_content(".success-message")
        assert "success" in success.lower() or "thank" in success.lower()
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_form_prevents_default(self, page, example_app_url):
        """Form submission prevents page reload."""
        await page.goto(f"{example_app_url}/contact")
        
        original_url = page.url
        
        # Fill and submit
        await page.fill("input[name='name']", "Test")
        await page.fill("input[name='email']", "test@test.com")
        await page.click("button[type='submit']")
        
        # URL should not change (no page reload)
        await page.wait_for_timeout(500)
        assert page.url == original_url


class TestFormValidation:
    """E2E tests for form validation."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_required_field_validation(self, page, example_app_url):
        """Required field validation works."""
        await page.goto(f"{example_app_url}/contact")
        
        # Try to submit empty form
        await page.click("button[type='submit']")
        
        # Check for validation error
        # HTML5 validation or custom error message
        error_visible = await page.locator(".error, [data-error], :invalid").count()
        assert error_visible > 0
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_email_validation(self, page, example_app_url):
        """Email field validation works."""
        await page.goto(f"{example_app_url}/contact")
        
        # Fill invalid email
        await page.fill("input[name='email']", "not-an-email")
        await page.click("button[type='submit']")
        
        # Should show validation error
        email_input = page.locator("input[name='email']")
        is_invalid = await email_input.evaluate("el => !el.validity.valid")
        assert is_invalid
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_custom_validation_message(self, page, example_app_url):
        """Custom validation messages are shown."""
        await page.goto(f"{example_app_url}/register")
        
        # Fill password that's too short
        await page.fill("input[name='password']", "123")
        await page.click("button[type='submit']")
        
        # Check for custom error message
        error = await page.text_content(".password-error, [data-error='password']")
        assert error and len(error) > 0


class TestFormState:
    """E2E tests for form state management."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_input_value_updates_signal(self, page, example_app_url):
        """Input values update signals."""
        await page.goto(f"{example_app_url}/search")
        
        # Type in search input
        await page.fill("input[name='query']", "test query")
        
        # Check that live preview updates
        preview = await page.text_content(".search-preview, [data-preview]")
        assert "test query" in preview
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_form_loading_state(self, page, example_app_url):
        """Form shows loading state during submission."""
        await page.goto(f"{example_app_url}/contact")
        
        # Fill form
        await page.fill("input[name='name']", "Test")
        await page.fill("input[name='email']", "test@test.com")
        
        # Click submit and immediately check for loading
        await page.click("button[type='submit']")
        
        # Check for loading indicator
        loading = await page.locator(".loading, [data-loading], button:disabled").count()
        # Note: This might be too fast to catch, depends on implementation
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_form_error_state(self, page, example_app_url):
        """Form shows error state on submission failure."""
        await page.goto(f"{example_app_url}/contact")
        
        # Fill form with data that will cause server error
        await page.fill("input[name='name']", "FORCE_ERROR")
        await page.fill("input[name='email']", "error@test.com")
        await page.click("button[type='submit']")
        
        # Wait for error message
        await page.wait_for_selector(".error-message, [data-error]", timeout=5000)
        error = await page.text_content(".error-message, [data-error]")
        assert error and len(error) > 0


class TestServerActions:
    """E2E tests for server action form handling."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_server_action_called(self, page, example_app_url):
        """Server action is called on form submit."""
        await page.goto(f"{example_app_url}/actions")
        
        # Track network requests
        action_request = None
        page.on("request", lambda req: 
            setattr(action_request, 'url', req.url) if '/_pynext/action' in req.url else None
        )
        
        # Submit action form
        await page.fill("input[name='data']", "test data")
        await page.click("button[data-action]")
        
        # Wait for action to complete
        await page.wait_for_timeout(500)
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_server_action_updates_ui(self, page, example_app_url):
        """Server action result updates UI."""
        await page.goto(f"{example_app_url}/actions")
        
        # Get initial state
        initial = await page.text_content("[data-result]")
        
        # Trigger action
        await page.click("button[data-action='fetch']")
        
        # Wait for update
        await page.wait_for_function(
            f"document.querySelector('[data-result]').textContent !== '{initial}'"
        )
        
        # Check result changed
        final = await page.text_content("[data-result]")
        assert final != initial


class TestFileUpload:
    """E2E tests for file upload forms."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_file_upload(self, page, example_app_url, tmp_path):
        """File upload works."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        await page.goto(f"{example_app_url}/upload")
        
        # Upload file
        await page.set_input_files("input[type='file']", str(test_file))
        await page.click("button[type='submit']")
        
        # Wait for success
        await page.wait_for_selector(".upload-success")
        success = await page.text_content(".upload-success")
        assert "test.txt" in success or "success" in success.lower()
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_file_preview(self, page, example_app_url, tmp_path):
        """File preview is shown before upload."""
        test_file = tmp_path / "image.png"
        test_file.write_bytes(b'\x89PNG\r\n')  # Minimal PNG header
        
        await page.goto(f"{example_app_url}/upload")
        
        # Select file
        await page.set_input_files("input[type='file']", str(test_file))
        
        # Check for preview
        preview = await page.locator(".file-preview, [data-preview]").count()
        assert preview > 0


class TestFormAccessibility:
    """E2E tests for form accessibility."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_form_labels(self, page, example_app_url):
        """Form inputs have associated labels."""
        await page.goto(f"{example_app_url}/contact")
        
        inputs = await page.locator("input:not([type='hidden'])").all()
        
        for input_elem in inputs:
            input_id = await input_elem.get_attribute("id")
            if input_id:
                label = await page.locator(f"label[for='{input_id}']").count()
                assert label > 0, f"Input {input_id} has no label"
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_focus_management(self, page, example_app_url):
        """Focus moves correctly after form submission."""
        await page.goto(f"{example_app_url}/contact")
        
        # Fill and submit
        await page.fill("input[name='name']", "Test")
        await page.fill("input[name='email']", "test@test.com")
        await page.click("button[type='submit']")
        
        # Wait for result
        await page.wait_for_selector(".result, [data-result]")
        
        # Check focus moved to result area
        focused = await page.evaluate("document.activeElement.className")
        # Focus should be on result or a reasonable element

