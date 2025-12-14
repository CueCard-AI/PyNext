# PyNext Reactive System Test Specifications

> **Version:** 1.0.0  
> **Total Tests:** 5,000  
> **Last Updated:** December 2024

---

## Overview

This document defines **5,000 test specifications** for the PyNext Unified Reactive System. Each test is designed to verify specific behavior and catch potential bugs.

### Test Distribution

| Category | Tests | Purpose |
|----------|-------|---------|
| Signal | 800 | Core reactive primitive |
| Effect | 800 | Side effects and cleanup |
| Memo | 600 | Cached computations |
| Store | 800 | Deep reactive objects |
| Control Flow | 800 | Show, For, Switch, Portal, ErrorBoundary |
| Hydration | 600 | Server/client handoff |
| Compilation | 600 | Python to JS |
| **Total** | **5,000** | |

---

## 1. SIGNAL TESTS (800 tests)

### 1.1 Basic Operations (100 tests)

#### 1.1.1 Creation (25 tests)

```
TEST_SIGNAL_001: Create signal with integer initial value
  Given: signal(0)
  Expect: signal() returns 0

TEST_SIGNAL_002: Create signal with negative integer
  Given: signal(-100)
  Expect: signal() returns -100

TEST_SIGNAL_003: Create signal with large integer
  Given: signal(2**53 - 1)
  Expect: signal() returns 9007199254740991

TEST_SIGNAL_004: Create signal with float
  Given: signal(3.14159)
  Expect: signal() returns 3.14159

TEST_SIGNAL_005: Create signal with negative float
  Given: signal(-0.001)
  Expect: signal() returns -0.001

TEST_SIGNAL_006: Create signal with zero
  Given: signal(0)
  Expect: signal() returns 0, type is int

TEST_SIGNAL_007: Create signal with empty string
  Given: signal("")
  Expect: signal() returns ""

TEST_SIGNAL_008: Create signal with string
  Given: signal("hello")
  Expect: signal() returns "hello"

TEST_SIGNAL_009: Create signal with unicode string
  Given: signal("日本語 🎉")
  Expect: signal() returns "日本語 🎉"

TEST_SIGNAL_010: Create signal with multiline string
  Given: signal("line1\nline2\nline3")
  Expect: signal() returns string with newlines

TEST_SIGNAL_011: Create signal with True
  Given: signal(True)
  Expect: signal() returns True

TEST_SIGNAL_012: Create signal with False
  Given: signal(False)
  Expect: signal() returns False

TEST_SIGNAL_013: Create signal with None
  Given: signal(None)
  Expect: signal() returns None

TEST_SIGNAL_014: Create signal with empty list
  Given: signal([])
  Expect: signal() returns []

TEST_SIGNAL_015: Create signal with populated list
  Given: signal([1, 2, 3])
  Expect: signal() returns [1, 2, 3]

TEST_SIGNAL_016: Create signal with nested list
  Given: signal([[1, 2], [3, 4]])
  Expect: signal() returns [[1, 2], [3, 4]]

TEST_SIGNAL_017: Create signal with empty dict
  Given: signal({})
  Expect: signal() returns {}

TEST_SIGNAL_018: Create signal with populated dict
  Given: signal({"a": 1, "b": 2})
  Expect: signal() returns {"a": 1, "b": 2}

TEST_SIGNAL_019: Create signal with nested dict
  Given: signal({"outer": {"inner": 1}})
  Expect: signal() returns nested structure

TEST_SIGNAL_020: Create signal with tuple
  Given: signal((1, 2, 3))
  Expect: signal() returns (1, 2, 3)

TEST_SIGNAL_021: Create signal with set
  Given: signal({1, 2, 3})
  Expect: signal() returns set with 3 elements

TEST_SIGNAL_022: Create signal with frozenset
  Given: signal(frozenset([1, 2, 3]))
  Expect: signal() returns frozenset

TEST_SIGNAL_023: Create signal with bytes
  Given: signal(b"hello")
  Expect: signal() returns b"hello"

TEST_SIGNAL_024: Create signal with bytearray
  Given: signal(bytearray(b"hello"))
  Expect: signal() returns bytearray

TEST_SIGNAL_025: Create multiple independent signals
  Given: a = signal(1), b = signal(2)
  Expect: a() returns 1, b() returns 2, independent
```

#### 1.1.2 Reading (25 tests)

```
TEST_SIGNAL_026: Read signal value via call
  Given: count = signal(5)
  When: value = count()
  Expect: value == 5

TEST_SIGNAL_027: Read signal multiple times returns same value
  Given: count = signal(10)
  When: a = count(), b = count(), c = count()
  Expect: a == b == c == 10

TEST_SIGNAL_028: Read signal in expression
  Given: count = signal(5)
  When: result = count() * 2
  Expect: result == 10

TEST_SIGNAL_029: Read signal in string interpolation
  Given: name = signal("Alice")
  When: result = f"Hello, {name()}!"
  Expect: result == "Hello, Alice!"

TEST_SIGNAL_030: Read signal in conditional
  Given: flag = signal(True)
  When: result = "yes" if flag() else "no"
  Expect: result == "yes"

TEST_SIGNAL_031: Read signal in list comprehension
  Given: items = signal([1, 2, 3])
  When: result = [x * 2 for x in items()]
  Expect: result == [2, 4, 6]

TEST_SIGNAL_032: Read signal in dict comprehension
  Given: items = signal([1, 2, 3])
  When: result = {x: x**2 for x in items()}
  Expect: result == {1: 1, 2: 4, 3: 9}

TEST_SIGNAL_033: Read signal in function argument
  Given: value = signal(5)
  When: result = max(0, value())
  Expect: result == 5

TEST_SIGNAL_034: Read signal in lambda
  Given: x = signal(3)
  When: fn = lambda: x() * 2; result = fn()
  Expect: result == 6

TEST_SIGNAL_035: Read signal inside effect tracks dependency
  Given: count = signal(0)
  When: @effect def track(): log.append(count())
  Expect: log contains 0, effect subscribed to count

TEST_SIGNAL_036: Read signal inside memo tracks dependency
  Given: count = signal(2)
  When: doubled = memo(lambda: count() * 2)
  Expect: doubled() == 4, memo subscribed to count

TEST_SIGNAL_037: Read signal with peek() does not track
  Given: count = signal(0)
  When: @effect def no_track(): log.append(count.peek())
  Then: count.set(1)
  Expect: effect ran once (initial), not on update

TEST_SIGNAL_038: Read signal after disposal raises error
  Given: count = signal(0); dispose = effect(lambda: count())
  When: dispose(); del count; count()
  Expect: raises SignalDisposedError

TEST_SIGNAL_039: Read signal in nested function
  Given: count = signal(5)
  When: def outer(): def inner(): return count(); return inner()
  Expect: outer() == 5

TEST_SIGNAL_040: Read signal in recursive function
  Given: depth = signal(3)
  When: def recurse(n): return n if n <= 0 else recurse(n-1) + depth()
  Expect: recurse(2) includes signal reads

TEST_SIGNAL_041: Read signal in async context
  Given: value = signal(10)
  When: async def get(): return value()
  Expect: await get() == 10

TEST_SIGNAL_042: Read signal in try block
  Given: value = signal("safe")
  When: try: result = value() except: result = "error"
  Expect: result == "safe"

TEST_SIGNAL_043: Read signal in finally block
  Given: cleanup = signal(None)
  When: try: pass finally: cleanup_val = cleanup()
  Expect: cleanup_val is None

TEST_SIGNAL_044: Read signal with truthy check
  Given: items = signal([1, 2, 3])
  When: result = bool(items())
  Expect: result == True

TEST_SIGNAL_045: Read signal with falsy value truthy check
  Given: items = signal([])
  When: result = bool(items())
  Expect: result == False

TEST_SIGNAL_046: Read signal in and expression (short circuit)
  Given: a = signal(True), b = signal(False)
  When: result = a() and b()
  Expect: result == False, both signals read

TEST_SIGNAL_047: Read signal in or expression (short circuit)
  Given: a = signal(False), b = signal(True)
  When: result = a() or b()
  Expect: result == True, both signals read

TEST_SIGNAL_048: Read signal in ternary operator
  Given: cond = signal(True), a = signal(1), b = signal(2)
  When: result = a() if cond() else b()
  Expect: result == 1

TEST_SIGNAL_049: Read signal in slice
  Given: items = signal([0, 1, 2, 3, 4])
  When: result = items()[1:3]
  Expect: result == [1, 2]

TEST_SIGNAL_050: Read signal in unpacking
  Given: pair = signal((1, 2))
  When: a, b = pair()
  Expect: a == 1, b == 2
```

#### 1.1.3 Writing (25 tests)

```
TEST_SIGNAL_051: Set signal to new value
  Given: count = signal(0)
  When: count.set(5)
  Expect: count() == 5

TEST_SIGNAL_052: Set signal to same value does not notify
  Given: count = signal(5); notifications = []
  When: count.set(5)
  Expect: no notification triggered

TEST_SIGNAL_053: Set signal to different value notifies
  Given: count = signal(5); @effect def track(): log.append(count())
  When: count.set(6)
  Expect: log == [5, 6]

TEST_SIGNAL_054: Set signal multiple times in sequence
  Given: count = signal(0)
  When: count.set(1); count.set(2); count.set(3)
  Expect: count() == 3

TEST_SIGNAL_055: Set signal to None
  Given: value = signal("hello")
  When: value.set(None)
  Expect: value() is None

TEST_SIGNAL_056: Set signal from None to value
  Given: value = signal(None)
  When: value.set("hello")
  Expect: value() == "hello"

TEST_SIGNAL_057: Set signal with type change (int to str)
  Given: value = signal(42)
  When: value.set("forty-two")
  Expect: value() == "forty-two"

TEST_SIGNAL_058: Update signal with function
  Given: count = signal(5)
  When: count.update(lambda x: x + 1)
  Expect: count() == 6

TEST_SIGNAL_059: Update signal with negative function
  Given: count = signal(10)
  When: count.update(lambda x: x - 5)
  Expect: count() == 5

TEST_SIGNAL_060: Update signal with multiplication
  Given: count = signal(3)
  When: count.update(lambda x: x * 2)
  Expect: count() == 6

TEST_SIGNAL_061: Update signal with division
  Given: count = signal(10)
  When: count.update(lambda x: x // 2)
  Expect: count() == 5

TEST_SIGNAL_062: Update signal to same value via function
  Given: count = signal(5)
  When: count.update(lambda x: x)
  Expect: no notification (value unchanged)

TEST_SIGNAL_063: Update signal with conditional function
  Given: count = signal(5)
  When: count.update(lambda x: x + 1 if x < 10 else x)
  Expect: count() == 6

TEST_SIGNAL_064: Update signal multiple times in batch
  Given: count = signal(0)
  When: batch(lambda: [count.update(lambda x: x+1) for _ in range(5)])
  Expect: count() == 5, single notification

TEST_SIGNAL_065: Set signal in effect does not cause infinite loop
  Given: count = signal(0); runs = 0
  When: @effect def increment(): nonlocal runs; runs += 1; if count() < 5: count.set(count() + 1)
  Expect: runs == 6 (0,1,2,3,4,5), no infinite loop

TEST_SIGNAL_066: Set signal in memo raises warning
  Given: count = signal(0)
  When: doubled = memo(lambda: (count.set(1), count() * 2)[1])
  Expect: warning raised about mutation in memo

TEST_SIGNAL_067: Set signal with custom equality
  Given: obj = signal({"a": 1}, equals=lambda x, y: x["a"] == y["a"])
  When: obj.set({"a": 1, "b": 2})
  Expect: no notification (a unchanged)

TEST_SIGNAL_068: Set signal with always-notify equality
  Given: count = signal(5, equals=lambda x, y: False)
  When: count.set(5)
  Expect: notification triggered

TEST_SIGNAL_069: Set signal with never-notify equality
  Given: count = signal(5, equals=lambda x, y: True)
  When: count.set(10)
  Expect: no notification, but value is 10

TEST_SIGNAL_070: Set signal in nested effect
  Given: a = signal(0), b = signal(0)
  When: @effect def outer(): if a() > 0: @effect def inner(): b.set(a() * 2)
  Expect: nested effect created when a > 0

TEST_SIGNAL_071: Set signal from async function
  Given: count = signal(0)
  When: async def set_async(): count.set(await get_value())
  Expect: signal updated after await

TEST_SIGNAL_072: Set signal with reference type
  Given: items = signal([1, 2])
  When: new_list = [3, 4]; items.set(new_list)
  Expect: items() == [3, 4], items() is new_list

TEST_SIGNAL_073: Set signal triggers all subscribers
  Given: count = signal(0); logs = []
  When: @effect def e1(): logs.append(f"e1:{count()}"); @effect def e2(): logs.append(f"e2:{count()}")
  Then: count.set(1)
  Expect: logs contains both e1:0, e2:0, e1:1, e2:1

TEST_SIGNAL_074: Set signal during batch defers notification
  Given: count = signal(0); logs = []
  When: batch(lambda: [count.set(1), logs.append(count())])
  Expect: logs == [1], notification after batch

TEST_SIGNAL_075: Set signal to complex object
  Given: data = signal(None)
  When: data.set({"users": [{"name": "Alice"}, {"name": "Bob"}], "count": 2})
  Expect: data() equals complex object
```

#### 1.1.4 Comparison (25 tests)

```
TEST_SIGNAL_076: Default equality uses ==
  Given: count = signal(5)
  When: count.set(5)
  Expect: no notification

TEST_SIGNAL_077: Default equality for strings
  Given: name = signal("hello")
  When: name.set("hello")
  Expect: no notification

TEST_SIGNAL_078: Default equality for lists (reference)
  Given: items = signal([1, 2, 3])
  When: items.set([1, 2, 3])
  Expect: notification (different list object)

TEST_SIGNAL_079: Default equality for dicts (reference)
  Given: data = signal({"a": 1})
  When: data.set({"a": 1})
  Expect: notification (different dict object)

TEST_SIGNAL_080: Default equality for None
  Given: value = signal(None)
  When: value.set(None)
  Expect: no notification

TEST_SIGNAL_081: Custom equality function - object id
  Given: obj = signal(obj1, equals=lambda a, b: a.id == b.id)
  When: obj.set(obj2_same_id)
  Expect: no notification

TEST_SIGNAL_082: Custom equality function - always different
  Given: count = signal(0, equals=lambda a, b: False)
  When: count.set(0)
  Expect: notification triggered

TEST_SIGNAL_083: Custom equality function - always same
  Given: count = signal(0, equals=lambda a, b: True)
  When: count.set(100)
  Expect: no notification, value is 100

TEST_SIGNAL_084: Custom equality with deep comparison
  Given: data = signal({"a": 1}, equals=deep_equal)
  When: data.set({"a": 1})
  Expect: no notification (deep equal)

TEST_SIGNAL_085: Custom equality with array deep comparison
  Given: items = signal([1, 2], equals=lambda a, b: a == b)
  When: items.set([1, 2])
  Expect: no notification (== works for lists)

TEST_SIGNAL_086: Equality check receives old and new values
  Given: comparisons = []; eq = lambda a, b: (comparisons.append((a, b)), a == b)[1]
  When: s = signal(1, equals=eq); s.set(2)
  Expect: comparisons == [(1, 2)]

TEST_SIGNAL_087: Equality error is propagated
  Given: def bad_eq(a, b): raise ValueError()
  When: s = signal(0, equals=bad_eq); s.set(1)
  Expect: ValueError raised

TEST_SIGNAL_088: NaN equality (special case)
  Given: val = signal(float('nan'))
  When: val.set(float('nan'))
  Expect: notification (NaN != NaN)

TEST_SIGNAL_089: Infinity equality
  Given: val = signal(float('inf'))
  When: val.set(float('inf'))
  Expect: no notification

TEST_SIGNAL_090: Negative infinity equality
  Given: val = signal(float('-inf'))
  When: val.set(float('-inf'))
  Expect: no notification

TEST_SIGNAL_091: Zero and negative zero equality
  Given: val = signal(0.0)
  When: val.set(-0.0)
  Expect: no notification (0.0 == -0.0 in Python)

TEST_SIGNAL_092: Empty string vs whitespace
  Given: val = signal("")
  When: val.set(" ")
  Expect: notification

TEST_SIGNAL_093: Empty list vs empty tuple
  Given: val = signal([])
  When: val.set(())
  Expect: notification (different types)

TEST_SIGNAL_094: 0 vs False equality
  Given: val = signal(0)
  When: val.set(False)
  Expect: depends on strict mode setting

TEST_SIGNAL_095: 1 vs True equality
  Given: val = signal(1)
  When: val.set(True)
  Expect: depends on strict mode setting

TEST_SIGNAL_096: Equality with memo subscriber
  Given: count = signal(0); doubled = memo(lambda: count() * 2)
  When: count.set(0)
  Expect: memo not recomputed

TEST_SIGNAL_097: Equality check before notification
  Given: count = signal(5); notified = False
  When: @effect def track(): nonlocal notified; notified = True
  Then: count.set(5)
  Expect: notified stays True only from init

TEST_SIGNAL_098: Multiple sets with equality checks
  Given: count = signal(0)
  When: count.set(0); count.set(1); count.set(1); count.set(2)
  Expect: 2 notifications (0→1, 1→2)

TEST_SIGNAL_099: Equality with immutable update pattern
  Given: items = signal((1, 2, 3))
  When: items.set(items() + (4,))
  Expect: notification, value is (1,2,3,4)

TEST_SIGNAL_100: Equality preserves referential transparency
  Given: a = signal([1, 2])
  When: ref1 = a(); a.set([1, 2]); ref2 = a()
  Expect: ref1 is not ref2
```

### 1.2 Type Support (150 tests)

#### 1.2.1 Primitives (30 tests)

```
TEST_SIGNAL_101: Integer zero
TEST_SIGNAL_102: Positive integer
TEST_SIGNAL_103: Negative integer
TEST_SIGNAL_104: Large positive integer (> 2^31)
TEST_SIGNAL_105: Large negative integer (< -2^31)
TEST_SIGNAL_106: Float zero
TEST_SIGNAL_107: Positive float
TEST_SIGNAL_108: Negative float
TEST_SIGNAL_109: Float with many decimals
TEST_SIGNAL_110: Float infinity
TEST_SIGNAL_111: Float negative infinity
TEST_SIGNAL_112: Float NaN
TEST_SIGNAL_113: Empty string
TEST_SIGNAL_114: Short string
TEST_SIGNAL_115: Long string (>1000 chars)
TEST_SIGNAL_116: Unicode string
TEST_SIGNAL_117: String with special chars
TEST_SIGNAL_118: String with null char
TEST_SIGNAL_119: Boolean True
TEST_SIGNAL_120: Boolean False
TEST_SIGNAL_121: None value
TEST_SIGNAL_122: Complex number
TEST_SIGNAL_123: Decimal
TEST_SIGNAL_124: Fraction
TEST_SIGNAL_125: Range object
TEST_SIGNAL_126: Bytes literal
TEST_SIGNAL_127: Bytearray
TEST_SIGNAL_128: Memoryview
TEST_SIGNAL_129: Enum value
TEST_SIGNAL_130: UUID
```

#### 1.2.2 Collections (40 tests)

```
TEST_SIGNAL_131: Empty list
TEST_SIGNAL_132: List with integers
TEST_SIGNAL_133: List with mixed types
TEST_SIGNAL_134: List with nested lists
TEST_SIGNAL_135: List with 1000 items
TEST_SIGNAL_136: Empty dict
TEST_SIGNAL_137: Dict with string keys
TEST_SIGNAL_138: Dict with int keys
TEST_SIGNAL_139: Dict with tuple keys
TEST_SIGNAL_140: Dict with mixed values
TEST_SIGNAL_141: Nested dict
TEST_SIGNAL_142: Dict with 100 keys
TEST_SIGNAL_143: Empty set
TEST_SIGNAL_144: Set with integers
TEST_SIGNAL_145: Set with strings
TEST_SIGNAL_146: Set with 100 items
TEST_SIGNAL_147: Frozenset
TEST_SIGNAL_148: Empty tuple
TEST_SIGNAL_149: Tuple with items
TEST_SIGNAL_150: Nested tuple
TEST_SIGNAL_151: Named tuple
TEST_SIGNAL_152: Deque
TEST_SIGNAL_153: OrderedDict
TEST_SIGNAL_154: DefaultDict
TEST_SIGNAL_155: Counter
TEST_SIGNAL_156: ChainMap
TEST_SIGNAL_157: List of dicts
TEST_SIGNAL_158: Dict of lists
TEST_SIGNAL_159: Set of tuples
TEST_SIGNAL_160: Tuple of sets (via frozenset)
TEST_SIGNAL_161: Deeply nested structure (5 levels)
TEST_SIGNAL_162: Wide structure (100 keys per level)
TEST_SIGNAL_163: Mixed nesting types
TEST_SIGNAL_164: List with None values
TEST_SIGNAL_165: Dict with None values
TEST_SIGNAL_166: Sparse list (many None)
TEST_SIGNAL_167: Circular reference detection
TEST_SIGNAL_168: Self-referential dict
TEST_SIGNAL_169: Immutable nested structure
TEST_SIGNAL_170: Mutable nested structure
```

#### 1.2.3 Nested (30 tests)

```
TEST_SIGNAL_171: Dict in list
TEST_SIGNAL_172: List in dict
TEST_SIGNAL_173: Dict in dict
TEST_SIGNAL_174: List in list
TEST_SIGNAL_175: 3-level nesting
TEST_SIGNAL_176: 5-level nesting
TEST_SIGNAL_177: 10-level nesting
TEST_SIGNAL_178: Mixed types at each level
TEST_SIGNAL_179: Access nested value
TEST_SIGNAL_180: Modify nested value
TEST_SIGNAL_181: Delete nested value
TEST_SIGNAL_182: Add to nested list
TEST_SIGNAL_183: Add to nested dict
TEST_SIGNAL_184: Replace nested structure
TEST_SIGNAL_185: Nested with None values
TEST_SIGNAL_186: Nested with empty collections
TEST_SIGNAL_187: Deeply nested array access
TEST_SIGNAL_188: Deeply nested dict access
TEST_SIGNAL_189: Path-based access
TEST_SIGNAL_190: Nested structure equality
TEST_SIGNAL_191: Nested structure copy behavior
TEST_SIGNAL_192: Nested with circular prevention
TEST_SIGNAL_193: Nested tuple in dict
TEST_SIGNAL_194: Nested frozenset in list
TEST_SIGNAL_195: JSON-serializable nested
TEST_SIGNAL_196: Non-JSON-serializable nested
TEST_SIGNAL_197: Nested with date objects
TEST_SIGNAL_198: Nested with custom objects
TEST_SIGNAL_199: Nested structure memory usage
TEST_SIGNAL_200: Nested structure iteration
```

#### 1.2.4 Custom Objects (25 tests)

```
TEST_SIGNAL_201: Dataclass instance
TEST_SIGNAL_202: Named tuple instance
TEST_SIGNAL_203: Custom class instance
TEST_SIGNAL_204: Class with __eq__
TEST_SIGNAL_205: Class with __hash__
TEST_SIGNAL_206: Class with slots
TEST_SIGNAL_207: Class with property
TEST_SIGNAL_208: Class with method
TEST_SIGNAL_209: Subclass instance
TEST_SIGNAL_210: Abstract class instance
TEST_SIGNAL_211: Protocol implementation
TEST_SIGNAL_212: Generic class instance
TEST_SIGNAL_213: Frozen dataclass
TEST_SIGNAL_214: Mutable dataclass
TEST_SIGNAL_215: Pydantic model
TEST_SIGNAL_216: Attrs class
TEST_SIGNAL_217: NamedTuple subclass
TEST_SIGNAL_218: TypedDict
TEST_SIGNAL_219: Object with to_dict
TEST_SIGNAL_220: Object with __dict__
TEST_SIGNAL_221: Object equality comparison
TEST_SIGNAL_222: Object identity comparison
TEST_SIGNAL_223: Object with __repr__
TEST_SIGNAL_224: Object serialization
TEST_SIGNAL_225: Object deserialization
```

#### 1.2.5 Special Values (25 tests)

```
TEST_SIGNAL_226: NaN behavior on read
TEST_SIGNAL_227: NaN behavior on write
TEST_SIGNAL_228: NaN comparison
TEST_SIGNAL_229: Infinity behavior
TEST_SIGNAL_230: Negative infinity
TEST_SIGNAL_231: Empty collections - list
TEST_SIGNAL_232: Empty collections - dict
TEST_SIGNAL_233: Empty collections - set
TEST_SIGNAL_234: Empty collections - string
TEST_SIGNAL_235: Unicode - Basic multilingual plane
TEST_SIGNAL_236: Unicode - Supplementary planes
TEST_SIGNAL_237: Unicode - Combining characters
TEST_SIGNAL_238: Unicode - Zero-width chars
TEST_SIGNAL_239: Unicode - Emoji
TEST_SIGNAL_240: Unicode - RTL text
TEST_SIGNAL_241: Max safe integer
TEST_SIGNAL_242: Min safe integer
TEST_SIGNAL_243: Very small float
TEST_SIGNAL_244: Very large float
TEST_SIGNAL_245: Float precision limits
TEST_SIGNAL_246: String with newlines
TEST_SIGNAL_247: String with tabs
TEST_SIGNAL_248: String with backslashes
TEST_SIGNAL_249: String with quotes
TEST_SIGNAL_250: Binary data in string
```

### 1.3 Reactivity (200 tests)

#### 1.3.1 Subscription (40 tests)

```
TEST_SIGNAL_251: Effect subscribes on read
TEST_SIGNAL_252: Memo subscribes on read
TEST_SIGNAL_253: Multiple effects subscribe
TEST_SIGNAL_254: Same effect reads multiple times
TEST_SIGNAL_255: Effect unsubscribes on dispose
TEST_SIGNAL_256: Weak reference cleanup
TEST_SIGNAL_257: Subscription count tracking
TEST_SIGNAL_258: Subscription order preserved
TEST_SIGNAL_259: Subscription after disposal
TEST_SIGNAL_260: Conditional subscription
TEST_SIGNAL_261: Dynamic subscription
TEST_SIGNAL_262: Subscription in nested scope
TEST_SIGNAL_263: Subscription inheritance
TEST_SIGNAL_264: Subscription with peek
TEST_SIGNAL_265: Subscription with untrack
TEST_SIGNAL_266: Multiple signals single effect
TEST_SIGNAL_267: Single signal multiple effects
TEST_SIGNAL_268: Cross-effect subscription
TEST_SIGNAL_269: Subscription during notification
TEST_SIGNAL_270: Unsubscription during notification
TEST_SIGNAL_271: Resubscription after unsubscribe
TEST_SIGNAL_272: Subscription memory footprint
TEST_SIGNAL_273: Subscription with closure
TEST_SIGNAL_274: Subscription scope isolation
TEST_SIGNAL_275: Subscription cleanup order
TEST_SIGNAL_276: Subscription leak detection
TEST_SIGNAL_277: Subscription with WeakRef
TEST_SIGNAL_278: Subscription persistence
TEST_SIGNAL_279: Subscription state consistency
TEST_SIGNAL_280: Concurrent subscriptions
TEST_SIGNAL_281-290: Additional subscription edge cases
```

#### 1.3.2 Notification (40 tests)

```
TEST_SIGNAL_291: Notification on value change
TEST_SIGNAL_292: No notification on same value
TEST_SIGNAL_293: Notification order
TEST_SIGNAL_294: Notification batching
TEST_SIGNAL_295: Notification coalescing
TEST_SIGNAL_296: Notification during effect
TEST_SIGNAL_297: Notification cascade
TEST_SIGNAL_298: Notification depth limit
TEST_SIGNAL_299: Notification error handling
TEST_SIGNAL_300: Notification timing
TEST_SIGNAL_301: Synchronous notification
TEST_SIGNAL_302: Deferred notification
TEST_SIGNAL_303: Priority notification
TEST_SIGNAL_304: Notification with cleanup
TEST_SIGNAL_305: Notification context
TEST_SIGNAL_306: Notification payload
TEST_SIGNAL_307: Notification filtering
TEST_SIGNAL_308: Notification throttling
TEST_SIGNAL_309: Notification debouncing
TEST_SIGNAL_310: Notification once
TEST_SIGNAL_311-330: Additional notification patterns
```

#### 1.3.3 Batching (50 tests)

```
TEST_SIGNAL_331: Basic batch
TEST_SIGNAL_332: Nested batch
TEST_SIGNAL_333: Batch with multiple signals
TEST_SIGNAL_334: Batch with errors
TEST_SIGNAL_335: Batch completion callback
TEST_SIGNAL_336: Batch isolation
TEST_SIGNAL_337: Async batch
TEST_SIGNAL_338: Batch timing
TEST_SIGNAL_339: Batch coalescing
TEST_SIGNAL_340: Batch ordering
TEST_SIGNAL_341: Batch with effects
TEST_SIGNAL_342: Batch with memos
TEST_SIGNAL_343: Batch with stores
TEST_SIGNAL_344: Batch scope
TEST_SIGNAL_345: Batch cleanup
TEST_SIGNAL_346: Batch memory
TEST_SIGNAL_347: Batch performance
TEST_SIGNAL_348: Batch cancellation
TEST_SIGNAL_349: Batch retry
TEST_SIGNAL_350: Batch transaction
TEST_SIGNAL_351-380: Additional batching scenarios
```

#### 1.3.4 Dependency Tracking (40 tests)

```
TEST_SIGNAL_381: Auto-track in effect
TEST_SIGNAL_382: Auto-track in memo
TEST_SIGNAL_383: Track conditional read
TEST_SIGNAL_384: Track in loop
TEST_SIGNAL_385: Track in nested function
TEST_SIGNAL_386: Track in callback
TEST_SIGNAL_387: Track dynamic access
TEST_SIGNAL_388: Untrack explicit
TEST_SIGNAL_389: Untrack scope
TEST_SIGNAL_390: Explicit deps with on()
TEST_SIGNAL_391: Mixed tracking
TEST_SIGNAL_392: Track cleanup
TEST_SIGNAL_393: Track recompute
TEST_SIGNAL_394: Track invalidation
TEST_SIGNAL_395: Track optimization
TEST_SIGNAL_396: Track debugging
TEST_SIGNAL_397: Track visualization
TEST_SIGNAL_398: Track graph
TEST_SIGNAL_399: Track cycle detection
TEST_SIGNAL_400: Track depth
TEST_SIGNAL_401-420: Additional tracking patterns
```

#### 1.3.5 Glitch-Free (30 tests)

```
TEST_SIGNAL_421: Diamond dependency
TEST_SIGNAL_422: Multiple paths to same value
TEST_SIGNAL_423: Cascading updates
TEST_SIGNAL_424: Update ordering
TEST_SIGNAL_425: Consistent reads
TEST_SIGNAL_426: No intermediate states
TEST_SIGNAL_427: Atomic updates
TEST_SIGNAL_428: Transaction semantics
TEST_SIGNAL_429: Rollback on error
TEST_SIGNAL_430: Multi-signal consistency
TEST_SIGNAL_431-450: Additional glitch-free scenarios
```

### 1.4 Memory Management (150 tests)

```
TEST_SIGNAL_451-490: Weak reference tests (40)
TEST_SIGNAL_491-530: Leak prevention tests (40)
TEST_SIGNAL_531-570: Disposal tests (40)
TEST_SIGNAL_571-600: Stress tests (30)
```

### 1.5 Concurrency (100 tests)

```
TEST_SIGNAL_601-630: Thread safety (30)
TEST_SIGNAL_631-670: Async integration (40)
TEST_SIGNAL_671-700: Race conditions (30)
```

### 1.6 Edge Cases (100 tests)

```
TEST_SIGNAL_701-725: Recursive updates (25)
TEST_SIGNAL_726-750: Circular dependencies (25)
TEST_SIGNAL_751-775: Error handling (25)
TEST_SIGNAL_776-800: Boundary values (25)
```

---

## 2. EFFECT TESTS (800 tests)

### 2.1 Basic Operations (150 tests)

```
TEST_EFFECT_001: Create effect with decorator
TEST_EFFECT_002: Create effect with function call
TEST_EFFECT_003: Effect runs immediately
TEST_EFFECT_004: Effect receives dispose function
TEST_EFFECT_005: Effect tracks signal reads
TEST_EFFECT_006: Effect re-runs on signal change
TEST_EFFECT_007: Effect with no dependencies
TEST_EFFECT_008: Effect with multiple dependencies
TEST_EFFECT_009: Effect with nested signal reads
TEST_EFFECT_010: Effect with conditional signal read
...
TEST_EFFECT_150: Effect stress test scenarios
```

### 2.2 Dependency Tracking (200 tests)

```
TEST_EFFECT_151: Auto-track single signal
TEST_EFFECT_152: Auto-track multiple signals
TEST_EFFECT_153: Track in if branch
TEST_EFFECT_154: Track in else branch
TEST_EFFECT_155: Track in both branches
TEST_EFFECT_156: Track in loop
TEST_EFFECT_157: Track in nested function
TEST_EFFECT_158: Untrack with peek()
TEST_EFFECT_159: Untrack with untrack()
TEST_EFFECT_160: Dynamic dependencies
...
TEST_EFFECT_350: Dependency edge cases
```

### 2.3 Cleanup (150 tests)

```
TEST_EFFECT_351: Return cleanup function
TEST_EFFECT_352: Cleanup runs before re-execution
TEST_EFFECT_353: Cleanup runs on dispose
TEST_EFFECT_354: Cleanup with error
TEST_EFFECT_355: Multiple cleanups
TEST_EFFECT_356: Nested cleanup
TEST_EFFECT_357: Timer cleanup
TEST_EFFECT_358: Event listener cleanup
TEST_EFFECT_359: Subscription cleanup
TEST_EFFECT_360: Abort controller cleanup
...
TEST_EFFECT_500: Cleanup integration
```

### 2.4 Ordering (150 tests)

```
TEST_EFFECT_501: Parent before child
TEST_EFFECT_502: Sibling order
TEST_EFFECT_503: Creation order
TEST_EFFECT_504: Dependency order
TEST_EFFECT_505: Priority effects
TEST_EFFECT_506: Render effects
TEST_EFFECT_507: Batched order
TEST_EFFECT_508: Async order
...
TEST_EFFECT_650: Ordering edge cases
```

### 2.5 Edge Cases (150 tests)

```
TEST_EFFECT_651: Nested effect creation
TEST_EFFECT_652: Effect creates effect
TEST_EFFECT_653: Recursive effect trigger
TEST_EFFECT_654: Effect depth limit
TEST_EFFECT_655: Effect error recovery
TEST_EFFECT_656: Effect retry
TEST_EFFECT_657: Performance - 1000 effects
TEST_EFFECT_658: Performance - rapid re-execution
...
TEST_EFFECT_800: Effect edge case scenarios
```

---

## 3. MEMO TESTS (600 tests)

### 3.1 Basic Operations (120 tests)

```
TEST_MEMO_001: Create memo with lambda
TEST_MEMO_002: Create memo with function
TEST_MEMO_003: Memo lazy evaluation
TEST_MEMO_004: Memo returns cached value
TEST_MEMO_005: Memo recomputes on dependency change
TEST_MEMO_006: Memo with single dependency
TEST_MEMO_007: Memo with multiple dependencies
TEST_MEMO_008: Memo with no dependencies
TEST_MEMO_009: Chained memos
TEST_MEMO_010: Memo used in effect
...
TEST_MEMO_120: Memo basic edge cases
```

### 3.2 Caching (150 tests)

```
TEST_MEMO_121: Cache hit on same deps
TEST_MEMO_122: Cache hit on multiple reads
TEST_MEMO_123: Cache miss on dep change
TEST_MEMO_124: Cache invalidation
TEST_MEMO_125: Cache with equality check
TEST_MEMO_126: Cache memory usage
TEST_MEMO_127: Cache eviction
TEST_MEMO_128: Cache stats
...
TEST_MEMO_270: Caching edge cases
```

### 3.3 Dependency Tracking (150 tests)

```
TEST_MEMO_271: Auto-track signal reads
TEST_MEMO_272: Nested memo dependencies
TEST_MEMO_273: Dynamic dependencies
TEST_MEMO_274: Conditional dependencies
TEST_MEMO_275: Diamond dependency
...
TEST_MEMO_420: Dependency tracking edge cases
```

### 3.4 Edge Cases (180 tests)

```
TEST_MEMO_421: Circular memo detection
TEST_MEMO_422: Circular memo error
TEST_MEMO_423: Error in computation
TEST_MEMO_424: Error recovery
TEST_MEMO_425: Async memo
TEST_MEMO_426: Expensive computation
TEST_MEMO_427: Many memos performance
...
TEST_MEMO_600: Memo edge case scenarios
```

---

## 4. STORE TESTS (800 tests)

### 4.1 Basic Operations (150 tests)

```
TEST_STORE_001: Create store with object
TEST_STORE_002: Create store with array
TEST_STORE_003: Create store with nested data
TEST_STORE_004: Read property
TEST_STORE_005: Read nested property
TEST_STORE_006: Read array index
TEST_STORE_007: Write property
TEST_STORE_008: Write nested property
TEST_STORE_009: Write array index
TEST_STORE_010: Delete property
...
TEST_STORE_150: Basic operation edge cases
```

### 4.2 Deep Reactivity (200 tests)

```
TEST_STORE_151: Nested object change triggers
TEST_STORE_152: Deep nested change
TEST_STORE_153: Array in object change
TEST_STORE_154: Object in array change
TEST_STORE_155: Path tracking accuracy
TEST_STORE_156: Partial path subscription
TEST_STORE_157: Proxy behavior
TEST_STORE_158: Proxy trap handling
...
TEST_STORE_350: Deep reactivity edge cases
```

### 4.3 Array Operations (200 tests)

```
TEST_STORE_351: push()
TEST_STORE_352: pop()
TEST_STORE_353: shift()
TEST_STORE_354: unshift()
TEST_STORE_355: splice() add
TEST_STORE_356: splice() remove
TEST_STORE_357: splice() replace
TEST_STORE_358: sort()
TEST_STORE_359: reverse()
TEST_STORE_360: fill()
TEST_STORE_361: copyWithin()
TEST_STORE_362: map() (non-mutating)
TEST_STORE_363: filter() (non-mutating)
TEST_STORE_364: reduce() (non-mutating)
TEST_STORE_365: slice() (non-mutating)
TEST_STORE_366: concat() (non-mutating)
TEST_STORE_367: indexOf()
TEST_STORE_368: includes()
TEST_STORE_369: find()
TEST_STORE_370: findIndex()
...
TEST_STORE_550: Array operation edge cases
```

### 4.4 Immutable Updates (100 tests)

```
TEST_STORE_551: produce() basic
TEST_STORE_552: produce() nested
TEST_STORE_553: produce() array
TEST_STORE_554: reconcile() basic
TEST_STORE_555: reconcile() with key
TEST_STORE_556: reconcile() merge
...
TEST_STORE_650: Immutable update edge cases
```

### 4.5 Edge Cases (150 tests)

```
TEST_STORE_651: Circular reference
TEST_STORE_652: Prototype chain access
TEST_STORE_653: Symbol properties
TEST_STORE_654: Getters and setters
TEST_STORE_655: Large store (10k items)
TEST_STORE_656: Deep nesting (20 levels)
TEST_STORE_657: Wide object (1000 keys)
TEST_STORE_658: Store disposal
...
TEST_STORE_800: Store edge case scenarios
```

---

## 5. CONTROL FLOW TESTS (800 tests)

### 5.1 Show (200 tests)

```
TEST_SHOW_001: Show with true condition
TEST_SHOW_002: Show with false condition
TEST_SHOW_003: Show with truthy value
TEST_SHOW_004: Show with falsy value
TEST_SHOW_005: Show with signal condition
TEST_SHOW_006: Show reactive toggle
TEST_SHOW_007: Show with fallback
TEST_SHOW_008: Show without fallback
TEST_SHOW_009: Show keyed
TEST_SHOW_010: Show non-keyed
TEST_SHOW_011: Show with cleanup
TEST_SHOW_012: Show nested
TEST_SHOW_013: Show in For
TEST_SHOW_014: Show with effect
TEST_SHOW_015: Show with memo
...
TEST_SHOW_200: Show edge cases
```

### 5.2 For (250 tests)

```
TEST_FOR_001: Basic array iteration
TEST_FOR_002: Empty array
TEST_FOR_003: Single item array
TEST_FOR_004: Large array (1000 items)
TEST_FOR_005: Key function
TEST_FOR_006: Key uniqueness validation
TEST_FOR_007: Add item to end
TEST_FOR_008: Add item to start
TEST_FOR_009: Add item in middle
TEST_FOR_010: Remove item from end
TEST_FOR_011: Remove item from start
TEST_FOR_012: Remove item from middle
TEST_FOR_013: Reorder items
TEST_FOR_014: Swap two items
TEST_FOR_015: Reverse order
TEST_FOR_016: Sort items
TEST_FOR_017: Filter items
TEST_FOR_018: Replace all items
TEST_FOR_019: Clear all items
TEST_FOR_020: Item property change
TEST_FOR_021: LIS reconciliation
TEST_FOR_022: Keyed reconciliation performance
TEST_FOR_023: Non-keyed fallback
...
TEST_FOR_250: For edge cases
```

### 5.3 Index (100 tests)

```
TEST_INDEX_001: Basic index access
TEST_INDEX_002: Index in map function
TEST_INDEX_003: Index reactive update
TEST_INDEX_004: Index with empty array
TEST_INDEX_005: Index with single item
...
TEST_INDEX_100: Index edge cases
```

### 5.4 Switch/Match (150 tests)

```
TEST_SWITCH_001: Single match
TEST_SWITCH_002: Multiple matches
TEST_SWITCH_003: Default case
TEST_SWITCH_004: Reactive switch
TEST_SWITCH_005: Switch with signals
TEST_SWITCH_006: Match with condition
TEST_SWITCH_007: Fallthrough behavior
...
TEST_SWITCH_150: Switch/Match edge cases
```

### 5.5 Portal (50 tests)

```
TEST_PORTAL_001: Render to body
TEST_PORTAL_002: Render to selector
TEST_PORTAL_003: Render to element
TEST_PORTAL_004: Portal cleanup
TEST_PORTAL_005: Nested portals
TEST_PORTAL_006: Portal with events
...
TEST_PORTAL_050: Portal edge cases
```

### 5.6 ErrorBoundary (50 tests)

```
TEST_ERRORBOUNDARY_001: Catch render error
TEST_ERRORBOUNDARY_002: Fallback rendering
TEST_ERRORBOUNDARY_003: Error info passed
TEST_ERRORBOUNDARY_004: Reset functionality
TEST_ERRORBOUNDARY_005: Nested boundaries
TEST_ERRORBOUNDARY_006: Retry functionality
...
TEST_ERRORBOUNDARY_050: ErrorBoundary edge cases
```

---

## 6. HYDRATION TESTS (600 tests)

### 6.1 Server Rendering (150 tests)

```
TEST_HYDRATION_001: Render signal to HTML
TEST_HYDRATION_002: Render effect markers
TEST_HYDRATION_003: Data attributes correct
TEST_HYDRATION_004: Event handler markers
TEST_HYDRATION_005: Nested component markers
TEST_HYDRATION_006: List rendering markers
TEST_HYDRATION_007: Conditional markers
...
TEST_HYDRATION_150: Server rendering edge cases
```

### 6.2 Client Hydration (200 tests)

```
TEST_HYDRATION_151: Signal binding
TEST_HYDRATION_152: Effect binding
TEST_HYDRATION_153: Event handler binding
TEST_HYDRATION_154: List reconciliation
TEST_HYDRATION_155: Conditional hydration
TEST_HYDRATION_156: Nested component hydration
TEST_HYDRATION_157: State restoration
TEST_HYDRATION_158: Error recovery
TEST_HYDRATION_159: Mismatch detection
TEST_HYDRATION_160: Mismatch recovery
...
TEST_HYDRATION_350: Client hydration edge cases
```

### 6.3 Islands Mode (150 tests)

```
TEST_HYDRATION_351: Island detection
TEST_HYDRATION_352: Selective hydration
TEST_HYDRATION_353: Bundle splitting
TEST_HYDRATION_354: Island communication
TEST_HYDRATION_355: Lazy hydration
TEST_HYDRATION_356: Visible hydration
TEST_HYDRATION_357: Idle hydration
TEST_HYDRATION_358: Interaction hydration
...
TEST_HYDRATION_500: Islands edge cases
```

### 6.4 Full Hydration (100 tests)

```
TEST_HYDRATION_501: Full page hydration
TEST_HYDRATION_502: Nested components
TEST_HYDRATION_503: Large page performance
TEST_HYDRATION_504: Memory usage
TEST_HYDRATION_505: Error boundaries
...
TEST_HYDRATION_600: Full hydration edge cases
```

---

## 7. COMPILATION TESTS (600 tests)

### 7.1 Valid Constructs (200 tests)

```
TEST_COMPILE_001: signal() creation
TEST_COMPILE_002: signal.set()
TEST_COMPILE_003: signal.update()
TEST_COMPILE_004: signal.peek()
TEST_COMPILE_005: effect()
TEST_COMPILE_006: memo()
TEST_COMPILE_007: store()
TEST_COMPILE_008: if statement
TEST_COMPILE_009: for loop
TEST_COMPILE_010: while loop
TEST_COMPILE_011: match statement
TEST_COMPILE_012: arithmetic operators
TEST_COMPILE_013: comparison operators
TEST_COMPILE_014: logical operators
TEST_COMPILE_015: string operations
TEST_COMPILE_016: list operations
TEST_COMPILE_017: dict operations
TEST_COMPILE_018: lambda functions
TEST_COMPILE_019: function definitions
TEST_COMPILE_020: closures
...
TEST_COMPILE_200: Valid construct edge cases
```

### 7.2 Invalid Constructs (150 tests)

```
TEST_COMPILE_201: import os fails
TEST_COMPILE_202: import sys fails
TEST_COMPILE_203: class definition fails
TEST_COMPILE_204: generator fails
TEST_COMPILE_205: file open fails
TEST_COMPILE_206: network request fails
TEST_COMPILE_207: global mutation fails
TEST_COMPILE_208: exec/eval fails
...
TEST_COMPILE_350: Invalid construct detection
```

### 7.3 Source Maps (100 tests)

```
TEST_COMPILE_351: Line mapping accuracy
TEST_COMPILE_352: Column mapping
TEST_COMPILE_353: Multi-file mapping
TEST_COMPILE_354: Breakpoint setting
TEST_COMPILE_355: Stack trace mapping
TEST_COMPILE_356: Error message mapping
...
TEST_COMPILE_450: Source map edge cases
```

### 7.4 Optimization (150 tests)

```
TEST_COMPILE_451: Dead code elimination
TEST_COMPILE_452: Constant folding
TEST_COMPILE_453: Signal access optimization
TEST_COMPILE_454: Inline event handlers
TEST_COMPILE_455: Tree shaking
TEST_COMPILE_456: Bundle size target
TEST_COMPILE_457: Minification
TEST_COMPILE_458: Compression
...
TEST_COMPILE_600: Optimization edge cases
```

---

## Test Implementation Template

Each test should follow this pattern:

```python
def test_signal_001_create_with_integer():
    """
    TEST_SIGNAL_001: Create signal with integer initial value
    
    Given: signal(0)
    Expect: signal() returns 0
    
    Category: Signal > Basic Operations > Creation
    Priority: P0 (Critical)
    """
    # Arrange
    initial_value = 0
    
    # Act
    s = signal(initial_value)
    
    # Assert
    assert s() == 0
    assert type(s()) == int
```

---

## Running Tests

```bash
# Run all 5000 tests
pytest tests/unit/reactive/ -v

# Run by category
pytest tests/unit/reactive/test_signal.py -v  # 800 tests
pytest tests/unit/reactive/test_effect.py -v  # 800 tests
pytest tests/unit/reactive/test_memo.py -v    # 600 tests
pytest tests/unit/reactive/test_store.py -v   # 800 tests
pytest tests/unit/reactive/test_control_flow.py -v  # 800 tests
pytest tests/unit/reactive/test_hydration.py -v  # 600 tests
pytest tests/unit/reactive/test_compilation.py -v  # 600 tests

# Run by priority
pytest tests/unit/reactive/ -v -m "p0"  # Critical tests only
pytest tests/unit/reactive/ -v -m "p1"  # Important tests
pytest tests/unit/reactive/ -v -m "p2"  # Nice-to-have tests

# Performance tests
pytest tests/unit/reactive/ -v -m "performance"
```

---

*End of Test Specifications*

