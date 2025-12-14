"""
Unit tests for PyNext Resource primitive.

Tests async data fetching, state management, caching, and hydration.
"""

import pytest
import asyncio
from pynext.core.resource import (
    Resource,
    create_resource,
    ResourceState,
    ResourceRegistry,
    get_resource_registry,
    suspend_until_ready,
    is_pending,
)
from pynext.reactive import Signal


class TestResourceBasics:
    """Basic Resource functionality tests."""
    
    @pytest.mark.asyncio
    async def test_create_resource(self):
        """Resource can be created."""
        async def fetcher():
            return "data"
        
        resource = Resource(fetcher)
        
        assert resource() is None  # Not fetched yet
        assert resource.state() == ResourceState.UNRESOLVED
    
    @pytest.mark.asyncio
    async def test_resource_fetch(self):
        """Resource can fetch data."""
        async def fetcher():
            return {"name": "Alice", "age": 30}
        
        resource = Resource(fetcher)
        
        result = await resource.fetch()
        
        assert result == {"name": "Alice", "age": 30}
        assert resource() == {"name": "Alice", "age": 30}
        assert resource.state() == ResourceState.READY
    
    @pytest.mark.asyncio
    async def test_resource_with_initial_value(self):
        """Resource can have an initial value."""
        async def fetcher():
            return "fetched"
        
        resource = Resource(fetcher, initial_value="initial")
        
        assert resource() == "initial"
        
        await resource.fetch()
        
        assert resource() == "fetched"
    
    @pytest.mark.asyncio
    async def test_resource_loading_state(self):
        """Resource tracks loading state."""
        async def slow_fetcher():
            await asyncio.sleep(0.01)
            return "data"
        
        resource = Resource(slow_fetcher)
        
        # Start fetch (don't await)
        task = asyncio.create_task(resource.fetch())
        
        # Should be loading
        await asyncio.sleep(0.001)
        assert resource.loading()
        assert resource.state() in (ResourceState.PENDING, ResourceState.REFRESHING)
        
        # Wait for completion
        await task
        
        assert not resource.loading()
        assert resource.state() == ResourceState.READY


class TestResourceWithSource:
    """Tests for Resource with reactive source."""
    
    @pytest.mark.asyncio
    async def test_resource_with_signal_source(self):
        """Resource refetches when source signal changes."""
        user_id = Signal(1)
        fetch_calls = []
        
        async def fetch_user(id):
            fetch_calls.append(id)
            return {"id": id, "name": f"User {id}"}
        
        resource = Resource(fetch_user, source=user_id)
        
        # First fetch
        await resource.fetch()
        assert resource()["id"] == 1
        assert len(fetch_calls) == 1
        
        # Change source and refetch
        user_id.set(2)
        await resource.fetch()
        assert resource()["id"] == 2
        assert len(fetch_calls) == 2
    
    @pytest.mark.asyncio
    async def test_resource_with_callable_source(self):
        """Resource works with callable source."""
        current_id = 1
        
        async def fetch_item(id):
            return {"id": id}
        
        resource = Resource(fetch_item, source=lambda: current_id)
        
        await resource.fetch()
        assert resource()["id"] == 1


class TestResourceError:
    """Tests for Resource error handling."""
    
    @pytest.mark.asyncio
    async def test_resource_error_state(self):
        """Resource tracks error state."""
        async def failing_fetcher():
            raise ValueError("Fetch failed")
        
        resource = Resource(failing_fetcher)
        
        with pytest.raises(ValueError):
            await resource.fetch()
        
        assert resource.state() == ResourceState.ERRORED
        assert resource.error() is not None
        assert "Fetch failed" in str(resource.error())
    
    @pytest.mark.asyncio
    async def test_resource_error_recovery(self):
        """Resource can recover from errors."""
        should_fail = True
        
        async def flaky_fetcher():
            nonlocal should_fail
            if should_fail:
                raise ValueError("Failed")
            return "success"
        
        resource = Resource(flaky_fetcher)
        
        # First fetch fails
        with pytest.raises(ValueError):
            await resource.fetch()
        
        assert resource.state() == ResourceState.ERRORED
        
        # Second fetch succeeds
        should_fail = False
        result = await resource.refetch()
        
        assert result == "success"
        assert resource.state() == ResourceState.READY
        assert resource.error() is None


class TestResourceMutation:
    """Tests for Resource mutation and invalidation."""
    
    @pytest.mark.asyncio
    async def test_resource_mutate(self):
        """Resource can be mutated optimistically."""
        async def fetcher():
            return {"count": 0}
        
        resource = Resource(fetcher)
        await resource.fetch()
        
        assert resource()["count"] == 0
        
        # Optimistic update
        await resource.mutate({"count": 5})
        
        assert resource()["count"] == 5
        assert resource.state() == ResourceState.READY
    
    @pytest.mark.asyncio
    async def test_resource_invalidate(self):
        """Resource can be invalidated."""
        fetch_count = 0
        
        async def counting_fetcher():
            nonlocal fetch_count
            fetch_count += 1
            return {"count": fetch_count}
        
        resource = Resource(counting_fetcher)
        
        await resource.fetch()
        assert resource()["count"] == 1
        
        # Fetch again (should use cache)
        await resource.fetch()
        assert fetch_count == 1  # No new fetch
        
        # Invalidate and refetch
        resource.invalidate()
        assert resource.state() == ResourceState.UNRESOLVED
        
        await resource.fetch()
        assert fetch_count == 2  # New fetch occurred


class TestResourceCaching:
    """Tests for Resource caching with TTL."""
    
    @pytest.mark.asyncio
    async def test_resource_cache_hit(self):
        """Resource uses cached data."""
        fetch_count = 0
        
        async def fetcher():
            nonlocal fetch_count
            fetch_count += 1
            return "data"
        
        resource = Resource(fetcher)
        
        await resource.fetch()
        await resource.fetch()
        await resource.fetch()
        
        assert fetch_count == 1  # Only one actual fetch
    
    @pytest.mark.asyncio
    async def test_resource_refetch_bypasses_cache(self):
        """Resource.refetch() bypasses cache."""
        fetch_count = 0
        
        async def fetcher():
            nonlocal fetch_count
            fetch_count += 1
            return f"data_{fetch_count}"
        
        resource = Resource(fetcher)
        
        await resource.fetch()
        await resource.refetch()
        await resource.refetch()
        
        assert fetch_count == 3
        assert resource() == "data_3"


class TestResourceLatest:
    """Tests for Resource.latest property."""
    
    @pytest.mark.asyncio
    async def test_latest_during_refresh(self):
        """latest returns stale data during refresh."""
        current_value = "first"
        
        async def fetcher():
            await asyncio.sleep(0.01)
            return current_value
        
        resource = Resource(fetcher)
        
        # First fetch
        await resource.fetch()
        assert resource.latest == "first"
        
        # Start refresh (don't await)
        current_value = "second"
        task = asyncio.create_task(resource.refetch())
        
        # During refresh, latest still has old value
        await asyncio.sleep(0.001)
        assert resource.loading()
        assert resource.latest == "first"
        
        # After refresh, latest is updated
        await task
        assert resource.latest == "second"


class TestResourceSerialization:
    """Tests for Resource hydration serialization."""
    
    @pytest.mark.asyncio
    async def test_resource_get_info(self):
        """Resource provides info for serialization."""
        async def fetcher():
            return {"key": "value"}
        
        resource = Resource(fetcher, name="test_resource")
        await resource.fetch()
        
        info = resource.get_info()
        
        assert info.state == ResourceState.READY
        assert info.data == {"key": "value"}
        assert info.error is None
    
    @pytest.mark.asyncio
    async def test_resource_js_init(self):
        """Resource generates JS initialization code."""
        async def fetcher():
            return {"count": 42}
        
        resource = Resource(fetcher, name="counter")
        await resource.fetch()
        
        js = resource.get_js_init()
        
        assert "__pynext__.createResource" in js
        assert '"ready"' in js
        assert "42" in js
    
    @pytest.mark.asyncio
    async def test_resource_error_serialization(self):
        """Resource serializes error state."""
        async def failing():
            raise ValueError("Test error")
        
        resource = Resource(failing)
        
        try:
            await resource.fetch()
        except:
            pass
        
        info = resource.get_info()
        
        assert info.state == ResourceState.ERRORED
        assert "Test error" in info.error


class TestResourceRegistry:
    """Tests for ResourceRegistry."""
    
    def test_registry_singleton(self):
        """Registry is a singleton."""
        r1 = get_resource_registry()
        r2 = get_resource_registry()
        
        assert r1 is r2
    
    @pytest.mark.asyncio
    async def test_registry_wait_all(self):
        """Registry can wait for all pending resources."""
        registry = ResourceRegistry()
        registry.clear()
        
        async def slow_fetch():
            await asyncio.sleep(0.01)
            return "done"
        
        r1 = Resource(slow_fetch)
        r2 = Resource(slow_fetch)
        
        registry.register(r1)
        registry.register(r2)
        registry.mark_pending(r1._id)
        registry.mark_pending(r2._id)
        
        assert registry.has_pending()
        
        await registry.wait_all()
        
        assert r1.state() == ResourceState.READY
        assert r2.state() == ResourceState.READY
    
    @pytest.mark.asyncio
    async def test_registry_hydration_data(self):
        """Registry provides hydration data."""
        registry = ResourceRegistry()
        registry.clear()
        
        async def fetcher():
            return "data"
        
        resource = Resource(fetcher)
        registry.register(resource)
        
        # Run fetch
        await resource.fetch()
        
        data = registry.get_hydration_data()
        
        assert resource._id in data
        assert data[resource._id]["state"] == ResourceState.READY


class TestResourceHelpers:
    """Tests for Resource helper functions."""
    
    @pytest.mark.asyncio
    async def test_is_pending(self):
        """is_pending checks resource states."""
        async def fetcher():
            return "data"
        
        r1 = Resource(fetcher)
        r2 = Resource(fetcher)
        
        assert is_pending(r1, r2)  # Both unresolved
        
        await r1.fetch()
        
        assert is_pending(r1, r2)  # r2 still pending
        
        await r2.fetch()
        
        assert not is_pending(r1, r2)  # Both ready
    
    @pytest.mark.asyncio
    async def test_suspend_until_ready(self):
        """suspend_until_ready waits for resources."""
        async def slow_fetch():
            await asyncio.sleep(0.01)
            return "done"
        
        r1 = Resource(slow_fetch)
        r2 = Resource(slow_fetch)
        
        await suspend_until_ready(r1, r2)
        
        assert r1.state() == ResourceState.READY
        assert r2.state() == ResourceState.READY


class TestCreateResourceFactory:
    """Tests for create_resource factory function."""
    
    @pytest.mark.asyncio
    async def test_create_resource_function(self):
        """create_resource factory works."""
        async def fetcher():
            return "data"
        
        resource = create_resource(fetcher, name="my_resource")
        
        assert isinstance(resource, Resource)
        
        await resource.fetch()
        assert resource() == "data"
    
    @pytest.mark.asyncio
    async def test_create_resource_with_source(self):
        """create_resource works with source."""
        source = Signal(1)
        
        async def fetcher(val):
            return val * 2
        
        resource = create_resource(fetcher, source=source)
        
        await resource.fetch()
        assert resource() == 2
        
        source.set(5)
        await resource.fetch()
        assert resource() == 10


class TestResourceConcurrency:
    """Tests for Resource concurrency handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_fetches_dedupe(self):
        """Concurrent fetches are handled correctly."""
        fetch_count = 0
        
        async def slow_fetch():
            nonlocal fetch_count
            fetch_count += 1
            await asyncio.sleep(0.05)
            return fetch_count
        
        resource = Resource(slow_fetch)
        
        # Start multiple concurrent fetches
        tasks = [
            asyncio.create_task(resource.fetch()),
            asyncio.create_task(resource.fetch()),
            asyncio.create_task(resource.fetch()),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return the same result
        assert all(r == results[0] for r in results)
    
    @pytest.mark.asyncio
    async def test_latest_fetch_wins(self):
        """Only the latest fetch result is used."""
        call_order = []
        
        async def varying_speed_fetch(id):
            call_order.append(f"start_{id}")
            # Second call is faster
            delay = 0.05 if id == 1 else 0.01
            await asyncio.sleep(delay)
            call_order.append(f"end_{id}")
            return id
        
        resource = Resource(varying_speed_fetch, source=Signal(1))
        
        # Start first fetch
        task1 = asyncio.create_task(resource.fetch())
        await asyncio.sleep(0.001)
        
        # Start second fetch before first completes
        resource._source.set(2)
        task2 = asyncio.create_task(resource.fetch())
        
        await asyncio.gather(task1, task2)
        
        # Second (faster) result should be the final value
        assert resource() == 2

