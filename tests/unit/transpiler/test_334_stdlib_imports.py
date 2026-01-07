"""
Phase 33.4: Stdlib Import Transpilation Tests

Tests that verify importing stdlib modules transpiles correctly
to appropriate JavaScript imports/runtime calls.
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# DATETIME IMPORTS
# =============================================================================

class TestDatetimeImports:
    """Test datetime module import transpilation."""
    
    def test_from_datetime_import_datetime(self):
        """from datetime import datetime"""
        code = "from datetime import datetime"
        js = transpile(code)
        # Should reference runtime datetime
        assert "datetime" in js.lower() or "__py" in js
    
    def test_from_datetime_import_multiple(self):
        """from datetime import datetime, date, time"""
        code = "from datetime import datetime, date, time"
        js = transpile(code)
        # Should handle multiple imports
        assert js is not None
    
    def test_from_datetime_import_timedelta(self):
        """from datetime import timedelta"""
        code = "from datetime import timedelta"
        js = transpile(code)
        assert "timedelta" in js.lower() or "__py" in js
    
    def test_import_datetime_module(self):
        """import datetime"""
        code = "import datetime"
        js = transpile(code)
        assert js is not None
    
    def test_datetime_usage(self):
        """Test datetime usage transpiles."""
        code = '''
from datetime import datetime
now = datetime.now()
'''
        js = transpile(code)
        assert "now" in js


# =============================================================================
# COLLECTIONS IMPORTS
# =============================================================================

class TestCollectionsImports:
    """Test collections module import transpilation."""
    
    def test_from_collections_import_counter(self):
        """from collections import Counter"""
        code = "from collections import Counter"
        js = transpile(code)
        assert js is not None
    
    def test_from_collections_import_defaultdict(self):
        """from collections import defaultdict"""
        code = "from collections import defaultdict"
        js = transpile(code)
        assert js is not None
    
    def test_from_collections_import_deque(self):
        """from collections import deque"""
        code = "from collections import deque"
        js = transpile(code)
        assert js is not None
    
    def test_from_collections_import_namedtuple(self):
        """from collections import namedtuple"""
        code = "from collections import namedtuple"
        js = transpile(code)
        assert js is not None
    
    def test_from_collections_import_ordereddict(self):
        """from collections import OrderedDict"""
        code = "from collections import OrderedDict"
        js = transpile(code)
        assert js is not None
    
    def test_collections_usage(self):
        """Test collections usage transpiles."""
        code = '''
from collections import Counter
c = Counter(["a", "b", "a"])
'''
        js = transpile(code)
        assert "Counter" in js or "__py" in js


# =============================================================================
# ITERTOOLS IMPORTS
# =============================================================================

class TestItertoolsImports:
    """Test itertools module import transpilation."""
    
    def test_from_itertools_import_chain(self):
        """from itertools import chain"""
        code = "from itertools import chain"
        js = transpile(code)
        assert js is not None
    
    def test_from_itertools_import_count(self):
        """from itertools import count"""
        code = "from itertools import count"
        js = transpile(code)
        assert js is not None
    
    def test_from_itertools_import_cycle(self):
        """from itertools import cycle"""
        code = "from itertools import cycle"
        js = transpile(code)
        assert js is not None
    
    def test_from_itertools_import_groupby(self):
        """from itertools import groupby"""
        code = "from itertools import groupby"
        js = transpile(code)
        assert js is not None
    
    def test_from_itertools_import_permutations(self):
        """from itertools import permutations"""
        code = "from itertools import permutations"
        js = transpile(code)
        assert js is not None
    
    def test_from_itertools_import_combinations(self):
        """from itertools import combinations"""
        code = "from itertools import combinations"
        js = transpile(code)
        assert js is not None
    
    def test_from_itertools_import_islice(self):
        """from itertools import islice"""
        code = "from itertools import islice"
        js = transpile(code)
        assert js is not None
    
    def test_from_itertools_import_multiple(self):
        """from itertools import chain, count, islice"""
        code = "from itertools import chain, count, islice"
        js = transpile(code)
        assert js is not None


# =============================================================================
# FUNCTOOLS IMPORTS
# =============================================================================

class TestFunctoolsImports:
    """Test functools module import transpilation."""
    
    def test_from_functools_import_partial(self):
        """from functools import partial"""
        code = "from functools import partial"
        js = transpile(code)
        assert js is not None
    
    def test_from_functools_import_reduce(self):
        """from functools import reduce"""
        code = "from functools import reduce"
        js = transpile(code)
        assert js is not None
    
    def test_from_functools_import_lru_cache(self):
        """from functools import lru_cache"""
        code = "from functools import lru_cache"
        js = transpile(code)
        assert js is not None
    
    def test_from_functools_import_cache(self):
        """from functools import cache"""
        code = "from functools import cache"
        js = transpile(code)
        assert js is not None
    
    def test_from_functools_import_wraps(self):
        """from functools import wraps"""
        code = "from functools import wraps"
        js = transpile(code)
        assert js is not None
    
    def test_functools_usage(self):
        """Test functools usage transpiles."""
        code = '''
from functools import reduce
result = reduce(lambda a, b: a + b, [1, 2, 3])
'''
        js = transpile(code)
        assert "reduce" in js or "__py" in js


# =============================================================================
# OPERATOR IMPORTS
# =============================================================================

class TestOperatorImports:
    """Test operator module import transpilation."""
    
    def test_from_operator_import_itemgetter(self):
        """from operator import itemgetter"""
        code = "from operator import itemgetter"
        js = transpile(code)
        assert js is not None
    
    def test_from_operator_import_attrgetter(self):
        """from operator import attrgetter"""
        code = "from operator import attrgetter"
        js = transpile(code)
        assert js is not None
    
    def test_from_operator_import_methodcaller(self):
        """from operator import methodcaller"""
        code = "from operator import methodcaller"
        js = transpile(code)
        assert js is not None
    
    def test_from_operator_import_arithmetic(self):
        """from operator import add, sub, mul, truediv"""
        code = "from operator import add, sub, mul, truediv"
        js = transpile(code)
        assert js is not None
    
    def test_operator_usage(self):
        """Test operator usage transpiles."""
        code = '''
from operator import itemgetter
get_name = itemgetter("name")
'''
        js = transpile(code)
        assert "itemgetter" in js or "__py" in js


# =============================================================================
# COPY IMPORTS
# =============================================================================

class TestCopyImports:
    """Test copy module import transpilation."""
    
    def test_from_copy_import_copy(self):
        """from copy import copy"""
        code = "from copy import copy"
        js = transpile(code)
        assert js is not None
    
    def test_from_copy_import_deepcopy(self):
        """from copy import deepcopy"""
        code = "from copy import deepcopy"
        js = transpile(code)
        assert js is not None
    
    def test_from_copy_import_both(self):
        """from copy import copy, deepcopy"""
        code = "from copy import copy, deepcopy"
        js = transpile(code)
        assert js is not None
    
    def test_copy_usage(self):
        """Test copy usage transpiles."""
        code = '''
from copy import deepcopy
result = deepcopy([1, 2, 3])
'''
        js = transpile(code)
        assert "deepcopy" in js or "__py" in js


# =============================================================================
# MIXED IMPORTS
# =============================================================================

class TestMixedStdlibImports:
    """Test multiple stdlib imports together."""
    
    def test_multiple_stdlib_imports(self):
        """Multiple stdlib imports in one file."""
        code = '''
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from itertools import chain, groupby
from functools import reduce, partial
from operator import itemgetter
from copy import deepcopy
'''
        js = transpile(code)
        assert js is not None
    
    def test_stdlib_with_user_code(self):
        """Stdlib imports with user code."""
        code = '''
from collections import Counter

def count_words(text):
    words = text.split()
    return Counter(words)

result = count_words("hello world hello")
'''
        js = transpile(code)
        assert "count_words" in js
        assert "Counter" in js or "__py" in js
    
    def test_stdlib_in_class(self):
        """Stdlib usage in class methods."""
        code = '''
from collections import defaultdict

class WordCounter:
    def __init__(self):
        self.counts = defaultdict(int)
    
    def add_word(self, word):
        self.counts[word] += 1
'''
        js = transpile(code)
        assert "WordCounter" in js
        assert "add_word" in js


# =============================================================================
# ALIASED IMPORTS
# =============================================================================

class TestAliasedImports:
    """Test aliased stdlib imports."""
    
    def test_import_datetime_as_dt(self):
        """import datetime as dt"""
        code = '''
import datetime as dt
now = dt.datetime.now()
'''
        js = transpile(code)
        assert js is not None
    
    def test_from_collections_import_counter_as_c(self):
        """from collections import Counter as C"""
        code = '''
from collections import Counter as C
c = C(["a", "b", "a"])
'''
        js = transpile(code)
        # The alias should be used
        assert "C" in js or "Counter" in js
    
    def test_multiple_aliases(self):
        """Multiple aliased imports."""
        code = '''
from itertools import chain as ch, count as cnt
'''
        js = transpile(code)
        assert js is not None

