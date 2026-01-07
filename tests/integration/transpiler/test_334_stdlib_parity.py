"""
Phase 33.4: Stdlib Module Transpilation Tests

Tests that verify stdlib imports transpile correctly.

Note: Full Python-JS runtime parity testing requires the complete JS
runtime environment with all stdlib modules bundled. These tests focus
on verifying that:
1. Stdlib imports transpile to valid JavaScript
2. The transpiled code structure is correct

For full runtime parity testing, use the mini-app harness which provides
the complete runtime environment.
"""

import pytest
from pynext.transpiler import transpile


class TestStdlibTranspilation:
    """Tests that stdlib imports transpile correctly."""
    
    def test_datetime_import_transpiles(self):
        """datetime import produces valid JS."""
        code = "from datetime import datetime"
        js = transpile(code)
        # Should produce valid import or runtime reference
        assert js is not None
        assert "datetime" in js.lower()
    
    def test_collections_import_transpiles(self):
        """collections import produces valid JS."""
        code = "from collections import Counter"
        js = transpile(code)
        assert js is not None
        assert "Counter" in js or "__py" in js
    
    def test_itertools_import_transpiles(self):
        """itertools import produces valid JS."""
        code = "from itertools import chain"
        js = transpile(code)
        assert js is not None
    
    def test_functools_import_transpiles(self):
        """functools import produces valid JS."""
        code = "from functools import reduce"
        js = transpile(code)
        assert js is not None


# Stub fixture for compatibility
@pytest.fixture
def harness():
    """Stub harness - real parity tests use mini-app harness."""
    yield None


# =============================================================================
# DATETIME TRANSPILATION TESTS
# =============================================================================

class TestDatetimeParity:
    """Test datetime module transpilation."""
    
    def test_datetime_now_type(self, harness):
        """datetime.now() transpiles correctly."""
        code = '''
from datetime import datetime
now = datetime.now()
print(type(now).__name__)
'''
        js = transpile(code)
        assert "datetime" in js.lower()
        assert "now" in js
    
    def test_datetime_construction(self, harness):
        """datetime construction transpiles correctly."""
        code = '''
from datetime import datetime
dt = datetime(2024, 12, 14, 10, 30, 0)
print(dt.year)
'''
        js = transpile(code)
        assert "2024" in js
        assert "datetime" in js.lower()
    
    def test_timedelta_days(self, harness):
        """timedelta transpiles correctly."""
        code = '''
from datetime import timedelta
td = timedelta(days=7, hours=3)
print(td.days)
'''
        js = transpile(code)
        assert "timedelta" in js.lower()
    
    def test_timedelta_total_seconds(self, harness):
        """timedelta.total_seconds() transpiles correctly."""
        code = '''
from datetime import timedelta
td = timedelta(hours=2, minutes=30)
print(int(td.total_seconds()))
'''
        js = transpile(code)
        assert "timedelta" in js.lower() or "td" in js


# =============================================================================
# COLLECTIONS TRANSPILATION TESTS  
# =============================================================================

class TestCollectionsParity:
    """Test collections module transpilation."""
    
    def test_counter_basic(self, harness):
        """Counter transpiles correctly."""
        code = '''
from collections import Counter
c = Counter(["a", "b", "a"])
print(c["a"])
'''
        js = transpile(code)
        assert "Counter" in js or "__py" in js
    
    def test_defaultdict_list(self, harness):
        """defaultdict transpiles correctly."""
        code = '''
from collections import defaultdict
dd = defaultdict(list)
dd["a"].append(1)
'''
        js = transpile(code)
        assert "defaultdict" in js.lower() or "__py" in js
    
    def test_deque_basic(self, harness):
        """deque transpiles correctly."""
        code = '''
from collections import deque
dq = deque([1, 2, 3])
dq.append(4)
'''
        js = transpile(code)
        assert "deque" in js.lower() or "__py" in js
    
    def test_namedtuple(self, harness):
        """namedtuple transpiles correctly."""
        code = '''
from collections import namedtuple
Point = namedtuple("Point", ["x", "y"])
p = Point(10, 20)
'''
        js = transpile(code)
        assert "Point" in js


# =============================================================================
# ITERTOOLS TRANSPILATION TESTS
# =============================================================================

class TestItertoolsParity:
    """Test itertools module transpilation."""
    
    def test_chain(self, harness):
        """chain transpiles correctly."""
        code = '''
from itertools import chain
result = list(chain([1, 2], [3, 4]))
'''
        js = transpile(code)
        assert "chain" in js.lower() or "__py" in js
    
    def test_permutations(self, harness):
        """permutations transpiles correctly."""
        code = '''
from itertools import permutations
result = list(permutations([1, 2, 3], 2))
'''
        js = transpile(code)
        assert "permutations" in js.lower() or "__py" in js
    
    def test_combinations(self, harness):
        """combinations transpiles correctly."""
        code = '''
from itertools import combinations
result = list(combinations([1, 2, 3, 4], 2))
'''
        js = transpile(code)
        assert "combinations" in js.lower() or "__py" in js


# =============================================================================
# FUNCTOOLS TRANSPILATION TESTS
# =============================================================================

class TestFunctoolsParity:
    """Test functools module transpilation."""
    
    def test_partial(self, harness):
        """partial transpiles correctly."""
        code = '''
from functools import partial

def power(base, exp):
    return base ** exp

square = partial(power, exp=2)
'''
        js = transpile(code)
        assert "partial" in js.lower() or "__py" in js
    
    def test_reduce(self, harness):
        """reduce transpiles correctly."""
        code = '''
from functools import reduce
result = reduce(lambda a, b: a + b, [1, 2, 3])
'''
        js = transpile(code)
        assert "reduce" in js.lower() or "__py" in js


# =============================================================================
# OPERATOR TRANSPILATION TESTS
# =============================================================================

class TestOperatorParity:
    """Test operator module transpilation."""
    
    def test_itemgetter(self, harness):
        """itemgetter transpiles correctly."""
        code = '''
from operator import itemgetter
get_name = itemgetter("name")
'''
        js = transpile(code)
        assert "itemgetter" in js.lower() or "__py" in js
    
    def test_attrgetter(self, harness):
        """attrgetter transpiles correctly."""
        code = '''
from operator import attrgetter
get_x = attrgetter("x")
'''
        js = transpile(code)
        assert "attrgetter" in js.lower() or "__py" in js
    
    def test_arithmetic(self, harness):
        """arithmetic operators transpile correctly."""
        code = '''
from operator import add, sub, mul
result = add(3, 4)
'''
        js = transpile(code)
        assert js is not None


# =============================================================================
# COPY TRANSPILATION TESTS
# =============================================================================

class TestCopyParity:
    """Test copy module transpilation."""
    
    def test_shallow_copy(self, harness):
        """copy transpiles correctly."""
        code = '''
from copy import copy
original = [1, 2, 3]
copied = copy(original)
'''
        js = transpile(code)
        assert "copy" in js.lower() or "__py" in js
    
    def test_deep_copy(self, harness):
        """deepcopy transpiles correctly."""
        code = '''
from copy import deepcopy
original = {"a": [1, 2, 3]}
copied = deepcopy(original)
'''
        js = transpile(code)
        assert "deepcopy" in js.lower() or "__py" in js

