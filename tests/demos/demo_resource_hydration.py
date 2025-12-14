"""
Demonstration: Resource Impact on Hydration

This script shows how createResource affects the hydration payload
that gets sent from server to client.

Run with: python tests/demos/demo_resource_hydration.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pynext.core.resource import (
    Resource,
    ResourceState,
    ResourceRegistry,
    get_resource_registry,
    create_resource,
)
from pynext.reactive import Signal, Store


def format_size(bytes_count: int) -> str:
    """Format bytes as human-readable size."""
    if bytes_count < 1024:
        return f"{bytes_count} bytes"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.2f} KB"
    else:
        return f"{bytes_count / (1024 * 1024):.2f} MB"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def demo_basic_resource():
    """Demo: Basic resource hydration."""
    print_section("1. Basic Resource Hydration")
    
    # Simulate a data fetcher (no source needed)
    async def fetch_user():
        # Simulate API call
        return {
            "id": 1,
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "avatar": "https://example.com/avatar.jpg",
        }
    
    # Create and fetch resource
    user = Resource(fetch_user, name="user_profile")
    await user.fetch()
    
    # Get hydration info
    info = user.get_info()
    js_init = user.get_js_init()
    
    print("Resource Info (Python):")
    print(f"  State: {info.state.value}")
    print(f"  Data: {info.data}")
    print(f"  Error: {info.error}")
    print()
    
    print("JavaScript Initialization Code:")
    print("-" * 40)
    print(js_init)
    print("-" * 40)
    print()
    
    print(f"JS Init Size: {format_size(len(js_init))}")
    
    return len(js_init)


async def demo_resource_with_source():
    """Demo: Resource with reactive source."""
    print_section("2. Resource with Reactive Source")
    
    user_id = Signal(42, name="user_id")
    
    async def fetch_user_by_id(id: int):
        return {"id": id, "name": f"User #{id}"}
    
    user = Resource(fetch_user_by_id, source=user_id, name="user_by_id")
    await user.fetch()
    
    info = user.get_info()
    js_init = user.get_js_init()
    
    print("Resource tracks source signal changes:")
    print(f"  Source Value: {info.source}")
    print(f"  Data: {info.data}")
    print()
    print("JavaScript Code:")
    print(js_init)
    
    return len(js_init)


async def demo_resource_error_state():
    """Demo: Resource error handling in hydration."""
    print_section("3. Resource Error State")
    
    async def failing_fetcher():
        raise ValueError("Network error: Connection refused")
    
    resource = Resource(failing_fetcher, name="failing_resource")
    
    try:
        await resource.fetch()
    except:
        pass  # Expected to fail
    
    info = resource.get_info()
    js_init = resource.get_js_init()
    
    print("Error State Serialization:")
    print(f"  State: {info.state.value}")
    print(f"  Error: {info.error}")
    print()
    print("JavaScript Code (error state is preserved):")
    print(js_init)
    
    return len(js_init)


async def demo_multiple_resources():
    """Demo: Multiple resources in a page."""
    print_section("4. Multiple Resources (Typical Page)")
    
    registry = ResourceRegistry()
    registry.clear()
    
    # Simulate a typical page with multiple data sources
    async def fetch_users():
        return [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
    
    async def fetch_posts():
        return [
            {"id": 1, "title": "Hello World", "author_id": 1},
            {"id": 2, "title": "Getting Started", "author_id": 2},
        ]
    
    async def fetch_comments():
        return [
            {"id": 1, "text": "Great post!", "post_id": 1},
            {"id": 2, "text": "Thanks!", "post_id": 1},
        ]
    
    # Create resources
    users = Resource(fetch_users, name="users")
    posts = Resource(fetch_posts, name="posts")
    comments = Resource(fetch_comments, name="comments")
    
    registry.register(users)
    registry.register(posts)
    registry.register(comments)
    
    # Fetch all
    await asyncio.gather(
        users.fetch(),
        posts.fetch(),
        comments.fetch(),
    )
    
    # Get combined hydration
    js_init = registry.get_js_init()
    hydration_data = registry.get_hydration_data()
    
    print("Multiple Resources Hydration:")
    print(f"  Resources: {len(hydration_data)}")
    print(f"  States: {[d['state'].value for d in hydration_data.values()]}")
    print()
    print("Combined JavaScript Initialization:")
    print("-" * 40)
    print(js_init)
    print("-" * 40)
    print()
    print(f"Total JS Init Size: {format_size(len(js_init))}")
    
    return len(js_init)


async def demo_large_dataset():
    """Demo: Resource with large dataset."""
    print_section("5. Large Dataset Impact")
    
    async def fetch_large_data():
        # Simulate a large API response
        return [
            {
                "id": i,
                "name": f"Item {i}",
                "description": f"This is item number {i} with some description text.",
                "price": 19.99 + i,
                "category": f"Category {i % 10}",
                "tags": [f"tag{j}" for j in range(5)],
            }
            for i in range(100)  # 100 items
        ]
    
    resource = Resource(fetch_large_data, name="products")
    await resource.fetch()
    
    js_init = resource.get_js_init()
    
    print("Large Dataset Hydration:")
    print(f"  Items: 100 products with nested data")
    print(f"  JS Init Size: {format_size(len(js_init))}")
    print()
    
    # Compare with gzip
    import gzip
    compressed = gzip.compress(js_init.encode())
    print(f"Compressed (gzip): {format_size(len(compressed))}")
    print(f"Compression ratio: {len(compressed) / len(js_init) * 100:.1f}%")
    
    return len(js_init), len(compressed)


async def demo_comparison_signal_vs_resource():
    """Demo: Compare Signal vs Resource hydration."""
    print_section("6. Signal vs Resource Comparison")
    
    # Same data, different approaches
    data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
    
    # Approach 1: Using Signal directly
    signal = Signal(data, name="users_signal")
    signal_init = signal.get_js_init()
    
    # Approach 2: Using Resource
    async def fetch_data():
        return data
    
    resource = Resource(fetch_data, name="users_resource")
    await resource.fetch()
    resource_init = resource.get_js_init()
    
    print("Signal-based Hydration:")
    print(f"  Size: {format_size(len(signal_init))}")
    print(f"  Code: {signal_init[:100]}...")
    print()
    
    print("Resource-based Hydration:")
    print(f"  Size: {format_size(len(resource_init))}")
    print(f"  Code: {resource_init[:100]}...")
    print()
    
    print("Comparison:")
    overhead = len(resource_init) - len(signal_init)
    print(f"  Resource adds ~{overhead} bytes overhead")
    print(f"  This includes: state tracking, error handling, refetch capability")
    
    return len(signal_init), len(resource_init)


async def demo_hydration_timeline():
    """Demo: Simulated hydration timeline."""
    print_section("7. Hydration Timeline Visualization")
    
    print("Server-Side Rendering Flow:")
    print("┌─────────────────────────────────────────────────────┐")
    print("│ 1. Request arrives                                  │")
    print("│    └─> Route matched via trie (O(1))               │")
    print("│                                                     │")
    print("│ 2. Page component renders                           │")
    print("│    └─> Resources created (UNRESOLVED state)        │")
    print("│                                                     │")
    print("│ 3. Suspense boundary detects pending resources      │")
    print("│    └─> Triggers parallel fetches                   │")
    print("│                                                     │")
    print("│ 4. Resources resolve                                │")
    print("│    └─> State changes to READY                      │")
    print("│    └─> Data cached for hydration                   │")
    print("│                                                     │")
    print("│ 5. HTML generated with embedded hydration data      │")
    print("│    └─> __pynext__.createResource(...) calls        │")
    print("│    └─> Signals + Resources serialized              │")
    print("└─────────────────────────────────────────────────────┘")
    print()
    print("Client-Side Hydration Flow:")
    print("┌─────────────────────────────────────────────────────┐")
    print("│ 1. HTML received (includes hydration script)        │")
    print("│                                                     │")
    print("│ 2. signals.js loads                                 │")
    print("│    └─> Creates reactive runtime                    │")
    print("│                                                     │")
    print("│ 3. resource.js loads                                │")
    print("│    └─> Resource primitives available               │")
    print("│                                                     │")
    print("│ 4. Hydration data executes                          │")
    print("│    └─> __pynext__.createResource() calls           │")
    print("│    └─> Resources hydrated with server data         │")
    print("│    └─> State = READY (no refetch needed!)          │")
    print("│                                                     │")
    print("│ 5. Interactive!                                     │")
    print("│    └─> resource.refetch() available                │")
    print("│    └─> resource.mutate() for optimistic updates    │")
    print("└─────────────────────────────────────────────────────┘")


async def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("   PyNext Resource Hydration Impact Demo")
    print("="*60)
    
    sizes = {}
    
    # Run demos
    sizes['basic'] = await demo_basic_resource()
    sizes['with_source'] = await demo_resource_with_source()
    sizes['error'] = await demo_resource_error_state()
    sizes['multiple'] = await demo_multiple_resources()
    raw, compressed = await demo_large_dataset()
    sizes['large_raw'] = raw
    sizes['large_compressed'] = compressed
    signal_size, resource_size = await demo_comparison_signal_vs_resource()
    sizes['signal'] = signal_size
    sizes['resource'] = resource_size
    await demo_hydration_timeline()
    
    # Summary
    print_section("Summary: Hydration Payload Sizes")
    
    print("Scenario                    | Size")
    print("-" * 50)
    print(f"Basic resource              | {format_size(sizes['basic'])}")
    print(f"Resource with source        | {format_size(sizes['with_source'])}")
    print(f"Error state                 | {format_size(sizes['error'])}")
    print(f"Multiple resources (3)      | {format_size(sizes['multiple'])}")
    print(f"Large dataset (100 items)   | {format_size(sizes['large_raw'])}")
    print(f"  └─ With gzip              | {format_size(sizes['large_compressed'])}")
    print()
    print("Signal vs Resource:")
    print(f"  Signal only               | {format_size(sizes['signal'])}")
    print(f"  Resource (with states)    | {format_size(sizes['resource'])}")
    print(f"  Overhead                  | +{sizes['resource'] - sizes['signal']} bytes")
    print()
    print("Key Insights:")
    print("  ✓ Resource adds ~50-100 bytes overhead for state tracking")
    print("  ✓ This enables: loading states, error handling, refetch, mutation")
    print("  ✓ Gzip compression reduces payload by ~70-80%")
    print("  ✓ Server-resolved data means NO client refetch on hydration")


if __name__ == "__main__":
    asyncio.run(main())

