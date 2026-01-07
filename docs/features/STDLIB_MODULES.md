# PyNext Standard Library Modules

## Overview

PyNext provides JavaScript implementations of Python's standard library modules, allowing you to use familiar Python APIs in client-side code.

## Who Should Use This

- **Python developers** writing client-side code
- **Teams migrating Python code** to the client
- **Anyone needing Python stdlib functionality** in JavaScript

## What It Provides

### Available Modules

1. **datetime** - Date and time operations
2. **collections** - Advanced data structures (Counter, defaultdict, deque, etc.)
3. **itertools** - Iterator tools
4. **functools** - Function utilities
5. **operator** - Operator functions
6. **copy** - Copy operations

## When to Use

- **Date/Time**: Use `datetime` module
- **Counting**: Use `Counter` from `collections`
- **Iteration**: Use `itertools` functions
- **Function composition**: Use `functools`
- **Object copying**: Use `copy` module

## How It Works

### Import Pattern

```python
# In Python code:
from pynext.client.datetime import datetime, timedelta
from pynext.client.collections import Counter, defaultdict
from pynext.client.itertools import chain, groupby

# Transpiles to:
# import { datetime, timedelta } from 'pynext/runtime/stdlib/datetime.js'
# import { Counter, defaultdict } from 'pynext/runtime/stdlib/collections.js'
```

### Usage Examples

```python
# datetime
from pynext.client.datetime import datetime, timedelta

now = datetime.now()
tomorrow = now + timedelta(days=1)

# collections
from pynext.client.collections import Counter, defaultdict

counter = Counter(["a", "b", "a"])
assert counter["a"] == 2

dd = defaultdict(list)
dd["key"].append("value")  # No KeyError

# itertools
from pynext.client.itertools import chain, groupby

result = list(chain([1, 2], [3, 4]))  # [1, 2, 3, 4]
```

## Where to Find More

- `pynext/runtime/stdlib/datetime.js` - datetime implementation
- `pynext/runtime/stdlib/collections.js` - collections implementation
- `pynext/runtime/stdlib/itertools.js` - itertools implementation
- `pynext/runtime/stdlib/functools.js` - functools implementation
- `pynext/runtime/stdlib/operator.js` - operator implementation
- `pynext/runtime/stdlib/copy.js` - copy implementation

