# Testing Guide

This guide covers testing PyNext applications using pytest and Playwright.

## Table of Contents

- [Setup](#setup)
- [Unit Testing](#unit-testing)
- [Testing Components](#testing-components)
- [Testing Server Actions](#testing-server-actions)
- [Integration Testing](#integration-testing)
- [E2E Testing](#e2e-testing)
- [Coverage](#coverage)
- [CI/CD](#cicd)

---

## Setup

### Install Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov httpx

# For E2E testing
pip install playwright
playwright install
```

### Project Structure

```
my-app/
├── pages/
├── components/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── test_signals.py      # Signal tests
│   ├── test_components.py   # Component tests
│   ├── test_actions.py      # Server action tests
│   └── e2e/
│       └── test_app.py      # End-to-end tests
├── pytest.ini
└── pynext.config.py
```

### pytest.ini

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

### conftest.py

```python
# tests/conftest.py

import pytest
from httpx import AsyncClient, ASGITransport
from pynext.server.app import create_app

@pytest.fixture
def app():
    """Create test application."""
    return create_app(pages_dir="pages", debug=True)

@pytest.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

---

## Unit Testing

### Testing Signals

```python
# tests/test_signals.py

import pytest
from pynext import Signal, Computed, Effect, batch

class TestSignal:
    def test_create_signal(self):
        count = Signal(0)
        assert count() == 0
    
    def test_set_value(self):
        count = Signal(0)
        count.set(5)
        assert count() == 5
    
    def test_update_value(self):
        count = Signal(0)
        count.update(lambda x: x + 1)
        assert count() == 1
    
    def test_subscribe(self):
        count = Signal(0)
        values = []
        
        count.subscribe(lambda v: values.append(v))
        count.set(1)
        count.set(2)
        
        assert values == [1, 2]

class TestComputed:
    def test_derived_value(self):
        count = Signal(5)
        doubled = Computed(lambda: count() * 2)
        
        assert doubled() == 10
    
    def test_auto_update(self):
        count = Signal(5)
        doubled = Computed(lambda: count() * 2)
        
        count.set(10)
        assert doubled() == 20
    
    def test_multiple_dependencies(self):
        a = Signal(1)
        b = Signal(2)
        sum_ab = Computed(lambda: a() + b())
        
        assert sum_ab() == 3
        
        a.set(5)
        assert sum_ab() == 7

class TestEffect:
    def test_effect_runs(self):
        count = Signal(0)
        results = []
        
        @Effect
        def track():
            results.append(count())
        
        count.set(1)
        count.set(2)
        
        assert results == [0, 1, 2]

class TestBatch:
    def test_batched_updates(self):
        a = Signal(0)
        b = Signal(0)
        updates = []
        
        sum_ab = Computed(lambda: a() + b())
        sum_ab.subscribe(lambda v: updates.append(v))
        
        batch(lambda: (a.set(1), b.set(2)))
        
        # Only one update, not two
        assert len(updates) == 1
        assert updates[-1] == 3
```

### Testing Stores

```python
# tests/test_stores.py

from pynext import Store

class TestStore:
    def test_create_store(self):
        user = Store({"name": "Alice", "age": 30})
        assert user.name == "Alice"
        assert user.age == 30
    
    def test_update_property(self):
        user = Store({"name": "Alice"})
        user.name = "Bob"
        assert user.name == "Bob"
    
    def test_nested_store(self):
        user = Store({
            "profile": {
                "name": "Alice",
                "settings": {"theme": "dark"}
            }
        })
        
        assert user.profile.settings.theme == "dark"
        
        user.profile.settings.theme = "light"
        assert user.profile.settings.theme == "light"
```

---

## Testing Components

### Render Testing

```python
# tests/test_components.py

from pynext import component, div, h1, p, span, Signal

class TestComponentRendering:
    def test_basic_element(self):
        element = div()["Hello"]
        html = element.render()
        
        assert "<div>" in html
        assert "Hello" in html
        assert "</div>" in html
    
    def test_with_attributes(self):
        element = div(class_="container", id="main")["Content"]
        html = element.render()
        
        assert 'class="container"' in html
        assert 'id="main"' in html
    
    def test_nested_elements(self):
        element = div()[
            h1()["Title"],
            p()["Paragraph"]
        ]
        html = element.render()
        
        assert "<h1>Title</h1>" in html
        assert "<p>Paragraph</p>" in html
    
    def test_component_decorator(self):
        @component
        def Greeting(name: str):
            return div()[f"Hello, {name}!"]
        
        element = Greeting("World")
        html = element.render()
        
        assert "Hello, World!" in html

class TestSignalRendering:
    def test_signal_in_element(self):
        count = Signal(42)
        element = span()[count]
        html = element.render()
        
        assert "42" in html
        assert "data-signal" in html
    
    def test_signal_updates_html(self):
        count = Signal(0)
        element = span()[count]
        
        html1 = element.render()
        assert "0" in html1
        
        count.set(5)
        html2 = element.render()
        assert "5" in html2
```

### Page Testing

```python
# tests/test_pages.py

import pytest
from pages.index import index

class TestIndexPage:
    def test_page_renders(self):
        page = index()
        html = page.render()
        
        assert "<html" in html
        assert "</html>" in html
    
    def test_page_has_title(self):
        page = index()
        html = page.render()
        
        assert "<title>" in html
```

---

## Testing Server Actions

### Basic Action Tests

```python
# tests/test_actions.py

import pytest
from pynext import server_action

@server_action
async def add_numbers(a: int, b: int) -> dict:
    return {"sum": a + b}

@server_action
async def fetch_user(user_id: int) -> dict:
    # Simulated database lookup
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    return users.get(user_id, {"error": "Not found"})

class TestServerActions:
    @pytest.mark.asyncio
    async def test_add_numbers(self):
        result = await add_numbers.call(a=2, b=3)
        assert result == {"sum": 5}
    
    @pytest.mark.asyncio
    async def test_fetch_user_exists(self):
        result = await fetch_user.call(user_id=1)
        assert result == {"name": "Alice"}
    
    @pytest.mark.asyncio
    async def test_fetch_user_not_found(self):
        result = await fetch_user.call(user_id=999)
        assert result == {"error": "Not found"}
```

### Mocking Dependencies

```python
# tests/test_actions_mock.py

import pytest
from unittest.mock import AsyncMock, patch

@server_action
async def process_payment(amount: float) -> dict:
    from services.stripe import charge_card
    result = await charge_card(amount)
    return {"success": result.success}

class TestPaymentAction:
    @pytest.mark.asyncio
    async def test_payment_success(self):
        mock_result = AsyncMock()
        mock_result.success = True
        
        with patch('services.stripe.charge_card', return_value=mock_result):
            result = await process_payment.call(amount=99.99)
            assert result == {"success": True}
    
    @pytest.mark.asyncio
    async def test_payment_failure(self):
        mock_result = AsyncMock()
        mock_result.success = False
        
        with patch('services.stripe.charge_card', return_value=mock_result):
            result = await process_payment.call(amount=99.99)
            assert result == {"success": False}
```

### HTTP Action Tests

```python
# tests/test_action_endpoints.py

import pytest

class TestActionEndpoints:
    @pytest.mark.asyncio
    async def test_action_endpoint(self, client):
        response = await client.post(
            "/_pynext/action",
            json={
                "actionId": "add_numbers_action_id",
                "args": {"a": 2, "b": 3}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == {"sum": 5}
        assert data["error"] is None
    
    @pytest.mark.asyncio
    async def test_unknown_action(self, client):
        response = await client.post(
            "/_pynext/action",
            json={
                "actionId": "unknown_action",
                "args": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is not None
```

---

## Integration Testing

### Route Testing

```python
# tests/test_routes.py

import pytest

class TestRoutes:
    @pytest.mark.asyncio
    async def test_index_page(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_about_page(self, client):
        response = await client.get("/about")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_dynamic_route(self, client):
        response = await client.get("/users/123")
        assert response.status_code == 200
        assert "123" in response.text
    
    @pytest.mark.asyncio
    async def test_404(self, client):
        response = await client.get("/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_static_files(self, client):
        response = await client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
```

### API Testing

```python
# tests/test_api.py

import pytest

class TestAPI:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/_pynext/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
```

---

## E2E Testing

### Playwright Setup

```python
# tests/e2e/conftest.py

import pytest
from playwright.sync_api import sync_playwright
import subprocess
import time

@pytest.fixture(scope="session")
def server():
    """Start the dev server for E2E tests."""
    proc = subprocess.Popen(
        ["pynext", "dev", "--port", "3001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for server to start
    yield "http://localhost:3001"
    proc.terminate()

@pytest.fixture
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    page = browser.new_page()
    yield page
    page.close()
```

### E2E Tests

```python
# tests/e2e/test_app.py

import pytest

class TestE2E:
    def test_homepage_loads(self, page, server):
        page.goto(server)
        assert page.title() != ""
    
    def test_navigation(self, page, server):
        page.goto(server)
        page.click("a[href='/about']")
        assert "/about" in page.url
    
    def test_counter_component(self, page, server):
        page.goto(server)
        
        # Find counter element
        counter = page.locator(".counter .count")
        initial = counter.text_content()
        
        # Click increment
        page.click("button:has-text('Increment')")
        
        # Verify count increased
        assert counter.text_content() != initial
    
    def test_form_submission(self, page, server):
        page.goto(f"{server}/contact")
        
        page.fill("input[name='name']", "Test User")
        page.fill("input[name='email']", "test@example.com")
        page.fill("textarea[name='message']", "Hello!")
        page.click("button[type='submit']")
        
        # Wait for success message
        success = page.locator(".success-message")
        assert success.is_visible()
    
    def test_server_action(self, page, server):
        page.goto(f"{server}/dashboard")
        
        # Trigger server action
        page.click("button:has-text('Load Data')")
        
        # Wait for response
        page.wait_for_selector(".data-loaded")
        
        data = page.locator(".data-content")
        assert data.text_content() != ""
```

---

## Coverage

### Running with Coverage

```bash
# Run tests with coverage
pytest --cov=pynext --cov-report=html tests/

# View report
open htmlcov/index.html
```

### Coverage Configuration

```ini
# .coveragerc

[run]
source = pynext, pages, components
omit = 
    tests/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:

[html]
directory = htmlcov
```

---

## CI/CD

### GitHub Actions

```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx
      
      - name: Run tests
        run: pytest --cov=pynext --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml

  e2e:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Playwright
        run: |
          pip install playwright
          playwright install chromium
      
      - name: Run E2E tests
        run: pytest tests/e2e/
```

---

## Quick Reference

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_signals.py

# Run specific test
pytest tests/test_signals.py::TestSignal::test_create_signal

# Run with coverage
pytest --cov=pynext

# Run E2E tests
pytest tests/e2e/

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run marked tests
pytest -m "not slow"
```

---

## Next Steps

- [Configuration](CONFIGURATION.md) - Test configuration
- [CI/CD](DEPLOYMENT.md) - Deployment pipelines
- [Server Actions](SERVER_ACTIONS.md) - Action testing patterns

