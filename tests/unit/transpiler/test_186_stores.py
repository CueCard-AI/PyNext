"""
Phase 18.6 Store Transform Tests

=============================================================================
TEST COVERAGE: 60 tests for Store transforms
=============================================================================

Tests verify that store operations are correctly transformed to use the
__pynext__.getStore() API.

Transformations tested:
- store.prop → __pynext__.getStore('id').prop
- store["key"] → __pynext__.getStore('id')["key"]
- store.items.append(x) → __pynext__.getStore('id').items.append(x)
- Nested property access
- Array mutations
"""

import pytest
from pynext.transpiler.reactive import create_context
from pynext.transpiler.pynext import transpile_handler_source


def transpile_with_context(code: str, ctx):
    """Helper to transpile code with a given reactive context."""
    return transpile_handler_source(code, ctx)


# =============================================================================
# BASIC STORE PROPERTY ACCESS (15 tests)
# =============================================================================

class TestStorePropertyAccess:
    """Test store.prop → __pynext__.getStore('id').prop"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(stores={"todos": "store_1"})
    
    def test_simple_property_read(self, ctx):
        """todos.items → __pynext__.getStore('store_1').items"""
        code = "x = todos.items"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert "store_1" in result  # May be single or double quotes
        assert ".items" in result
    
    def test_property_in_expression(self, ctx):
        """len(todos.items) → .items.length"""
        code = "x = len(todos.items)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert ".items" in result
    
    def test_property_in_condition(self, ctx):
        """if todos.items: → if (getStore().items)"""
        code = """
if todos.items:
    x = 1
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_multiple_properties(self, ctx):
        """todos.items + todos.filter → both transformed"""
        code = "x = len(todos.items) + len(todos.filter)"
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_property_assignment(self, ctx):
        """todos.filter = "all" → getStore().filter = "all\""""
        code = 'todos.filter = "all"'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_nested_property_read(self, ctx):
        """todos.user.name → getStore().user.name"""
        code = "x = todos.user.name"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_nested_property_write(self, ctx):
        """todos.user.name = "Alice" """
        code = 'todos.user.name = "Alice"'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_property_in_loop(self, ctx):
        """for item in todos.items: → for (item of getStore().items)"""
        code = """
for item in todos.items:
    print(item)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_property_in_comprehension(self, ctx):
        """[x for x in todos.items] → getStore().items.map(...)"""
        code = "[x for x in todos.items]"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_property_length(self, ctx):
        """len(todos.items) → getStore().items.length"""
        code = "x = len(todos.items)"
        result = transpile_with_context(code, ctx)
        assert ".items" in result
    
    def test_property_boolean_check(self, ctx):
        """bool(todos.items) → !!getStore().items"""
        code = "x = bool(todos.items)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_property_in_ternary(self, ctx):
        """todos.items if cond else [] → cond ? getStore().items : []"""
        code = "x = todos.items if cond else []"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_property_comparison(self, ctx):
        """todos.filter == "all" → getStore().filter === "all\""""
        code = 'x = todos.filter == "all"'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_property_in_function_call(self, ctx):
        """process(todos.items) → process(getStore().items)"""
        code = "process(todos.items)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_property_chained(self, ctx):
        """todos.items.length → getStore().items.length"""
        code = "x = len(todos.items)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result


# =============================================================================
# STORE SUBSCRIPT ACCESS (10 tests)
# =============================================================================

class TestStoreSubscriptAccess:
    """Test store["key"] → __pynext__.getStore('id')["key"]"""
    
    @pytest.fixture
    def ctx(self):
        return create_context(stores={"data": "store_1"})
    
    def test_string_subscript(self, ctx):
        """data["key"] → __py.getitem(getStore(), "key")"""
        code = 'x = data["key"]'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        # The transpiler uses __py.getitem() for subscript access (correct behavior)
        assert "__py.getitem" in result
        assert '"key"' in result
    
    def test_variable_subscript(self, ctx):
        """data[key] → getStore()[key]"""
        code = "x = data[key]"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_integer_subscript(self, ctx):
        """data[0] → getStore()[0]"""
        code = "x = data[0]"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_subscript_write(self, ctx):
        """data["key"] = value → getStore()["key"] = value"""
        code = 'data["key"] = "value"'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_nested_subscript(self, ctx):
        """data["users"][0] → getStore()["users"][0]"""
        code = 'x = data["users"][0]'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_computed_subscript(self, ctx):
        """data[f"user_{i}"] → getStore()[`user_${i}`]"""
        code = 'x = data[f"user_{i}"]'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_subscript_in_condition(self, ctx):
        """if data["enabled"]: → if (getStore()["enabled"])"""
        code = """
if data["enabled"]:
    x = 1
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_subscript_delete(self, ctx):
        """del data["key"] → delete getStore()["key"]"""
        code = 'del data["key"]'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_subscript_in_loop(self, ctx):
        """for key in data["keys"]: → for (key of getStore()["keys"])"""
        code = """
for key in data["keys"]:
    print(key)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_subscript_with_method(self, ctx):
        """data["text"].upper() → getStore()["text"].toUpperCase()"""
        code = 'x = data["text"].upper()'
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result


# =============================================================================
# STORE ARRAY MUTATIONS (15 tests)
# =============================================================================

class TestStoreArrayMutations:
    """Test store.items.append(x), etc."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(stores={"todos": "store_1"})
    
    def test_append(self, ctx):
        """todos.items.append(item) → getStore().items.push(item)"""
        code = "todos.items.append(item)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert ".items" in result
    
    def test_pop(self, ctx):
        """todos.items.pop() → getStore().items.pop()"""
        code = "x = todos.items.pop()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert ".items" in result
    
    def test_insert(self, ctx):
        """todos.items.insert(0, item) → getStore().items.splice(0, 0, item)"""
        code = "todos.items.insert(0, item)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_remove(self, ctx):
        """todos.items.remove(item) → getStore().items.splice(...)"""
        code = "todos.items.remove(item)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_extend(self, ctx):
        """todos.items.extend(more) → getStore().items.push(...more)"""
        code = "todos.items.extend(more)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_clear(self, ctx):
        """todos.items.clear() → getStore().items.length = 0"""
        code = "todos.items.clear()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_sort(self, ctx):
        """todos.items.sort() → getStore().items.sort()"""
        code = "todos.items.sort()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_reverse(self, ctx):
        """todos.items.reverse() → getStore().items.reverse()"""
        code = "todos.items.reverse()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_index_assignment(self, ctx):
        """todos.items[0] = item → getStore().items[0] = item"""
        code = "todos.items[0] = item"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_index_delete(self, ctx):
        """del todos.items[0] → getStore().items.splice(0, 1)"""
        code = "del todos.items[0]"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_append_in_condition(self, ctx):
        """if cond: todos.items.append(item)"""
        code = """
if cond:
    todos.items.append(item)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_multiple_mutations(self, ctx):
        """todos.items.append(a); todos.items.append(b)"""
        code = """
todos.items.append(a)
todos.items.append(b)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_mutation_in_loop(self, ctx):
        """for x in items: todos.items.append(x)"""
        code = """
for x in items:
    todos.items.append(x)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_slice_assignment(self, ctx):
        """todos.items[1:3] = [a, b] → splice"""
        code = "todos.items[1:3] = [a, b]"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
    
    def test_length_check_after_mutation(self, ctx):
        """todos.items.append(item); return len(todos.items)"""
        code = """
todos.items.append(item)
return len(todos.items)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2


# =============================================================================
# MULTIPLE STORES (10 tests)
# =============================================================================

class TestMultipleStores:
    """Test handlers with multiple stores."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(stores={
            "todos": "store_1",
            "users": "store_2",
            "settings": "store_3",
        })
    
    def test_two_stores_read(self, ctx):
        """Access two stores"""
        code = "x = len(todos.items) + len(users.list)"
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_two_stores_write(self, ctx):
        """Write to two stores"""
        code = """
todos.filter = "all"
users.active = True
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_cross_store_copy(self, ctx):
        """Copy from one store to another"""
        code = "todos.items = users.tasks"
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_conditional_store_access(self, ctx):
        """if todos.items: users.count = len(todos.items)"""
        code = """
if todos.items:
    users.count = len(todos.items)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_stores_in_loop(self, ctx):
        """for u in users.list: todos.items.append(u.task)"""
        code = """
for u in users.list:
    todos.items.append(u.task)
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_three_stores(self, ctx):
        """Access all three stores"""
        code = """
todos.filter = settings.default_filter
users.active = settings.show_all
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 3
    
    def test_store_comparison(self, ctx):
        """if todos.count == users.count: → getStore().count === getStore().count"""
        code = """
if todos.count == users.count:
    pass
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_store_in_function_call(self, ctx):
        """process(todos.items, users.list) → both transformed"""
        code = "process(todos.items, users.list)"
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 2
    
    def test_store_reset_multiple(self, ctx):
        """Reset all stores"""
        code = """
todos.items = []
users.list = []
settings.theme = "default"
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 3
    
    def test_store_batch_update(self, ctx):
        """Update multiple stores together"""
        code = """
count = len(todos.items)
users.task_count = count
settings.last_count = count
"""
        result = transpile_with_context(code, ctx)
        assert result.count("__pynext__.getStore") >= 3


# =============================================================================
# STORE ID PRESERVATION (5 tests)
# =============================================================================

class TestStoreIdPreservation:
    """Test that store IDs are correctly preserved."""
    
    def test_single_store_id(self):
        """Store ID should appear in output"""
        ctx = create_context(stores={"todos": "my_store_id_123"})
        code = "x = todos.items"
        result = transpile_with_context(code, ctx)
        assert "my_store_id_123" in result
    
    def test_multiple_store_ids(self):
        """Multiple store IDs should all appear"""
        ctx = create_context(stores={
            "a": "id_a",
            "b": "id_b",
        })
        code = "x = a.items + b.items"
        result = transpile_with_context(code, ctx)
        assert "id_a" in result
        assert "id_b" in result
    
    def test_store_id_in_mutation(self):
        """ID should be in mutation call"""
        ctx = create_context(stores={"todos": "unique_store"})
        code = "todos.items.append(item)"
        result = transpile_with_context(code, ctx)
        assert "unique_store" in result
    
    def test_store_id_in_write(self):
        """ID should be in property write"""
        ctx = create_context(stores={"todos": "write_store"})
        code = 'todos.filter = "all"'
        result = transpile_with_context(code, ctx)
        assert "write_store" in result
    
    def test_store_id_with_underscore(self):
        """IDs with underscores should work"""
        ctx = create_context(stores={"my_store": "store_my_store_1"})
        code = "x = my_store.items"
        result = transpile_with_context(code, ctx)
        assert "store_my_store_1" in result


# =============================================================================
# STORE AND SIGNAL TOGETHER (5 tests)
# =============================================================================

class TestStoreAndSignal:
    """Test handlers with both stores and signals."""
    
    @pytest.fixture
    def ctx(self):
        return create_context(
            stores={"todos": "store_1"},
            signals={"count": "sig_1"}
        )
    
    def test_store_read_signal_write(self, ctx):
        """count.set(len(todos.items)) → .set(getStore().items.length)"""
        code = "count.set(len(todos.items))"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert "__pynext__.getSignal" in result
    
    def test_signal_read_store_write(self, ctx):
        """todos.count = count() → getStore().count = .read()"""
        code = "todos.count = count()"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert "__pynext__.getSignal" in result
    
    def test_conditional_both(self, ctx):
        """if count() > 0: todos.items.append(item)"""
        code = """
if count() > 0:
    todos.items.append(item)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert "__pynext__.getSignal" in result
    
    def test_loop_both(self, ctx):
        """for x in todos.items: count.update(lambda n: n + 1)"""
        code = """
for x in todos.items:
    count.update(lambda n: n + 1)
"""
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert "__pynext__.getSignal" in result
    
    def test_expression_both(self, ctx):
        """count() + len(todos.items) → .read() + getStore().items.length"""
        code = "x = count() + len(todos.items)"
        result = transpile_with_context(code, ctx)
        assert "__pynext__.getStore" in result
        assert "__pynext__.getSignal" in result
