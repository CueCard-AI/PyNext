"""
PyNext Reactive System Tests

600 comprehensive tests covering:
- test_signal.py: 100 tests for Signal primitive
- test_effect.py: 100 tests for Effect side effects
- test_memo.py: 100 tests for Memo computations
- test_store.py: 100 tests for Store deep reactivity
- test_batch_context.py: 100 tests for batching and context
- test_integration.py: 100 tests for real-world patterns

Run all tests:
    pytest tests/unit/reactive/ -v

Run specific module:
    pytest tests/unit/reactive/test_signal.py -v

Run with coverage:
    pytest tests/unit/reactive/ --cov=pynext.reactive --cov-report=html
"""

