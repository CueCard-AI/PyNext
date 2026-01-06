# Python to JavaScript Transpilation: Fundamentals

## Overview

This document provides comprehensive documentation for PyNext's core transpilation features, covering the essential building blocks needed to transpile Python code to JavaScript. It includes complete support for functions, classes, control flow, and comprehensions—the fundamental constructs that enable Python code to run in the browser.

**Status**: ✅ **COMPLETE** (46/46 features implemented, 427+ tests)

**Phase**: 33.1 - Core Transpilation Fundamentals

This guide is essential reading for:
- **Developers** writing Python code that needs to run in the browser
- **Framework contributors** extending or debugging the transpiler
- **AI assistants** generating PyNext-compatible Python code
- **Anyone** wanting to understand how Python constructs map to JavaScript

---

## Table of Contents

1. [Functions](#functions) (10 features)
2. [Classes](#classes) (15 features)
3. [Control Flow](#control-flow) (13 features)
4. [Comprehensions](#comprehensions) (8 features)
5. [Recent Fixes](#recent-fixes)
6. [Best Practices](#best-practices)
7. [Known Limitations](#known-limitations)

---

## Functions

Functions are the building blocks of Python programs. PyNext transpiles Python function definitions, including all parameter types, decorators, and closures, to equivalent JavaScript functions that preserve Python's semantics.

### ✅ Basic Function Definitions

Python `def` statements are transpiled to JavaScript `function` declarations. The function name, parameters, and body are preserved, with Python-specific constructs (like `self`, `f-strings`) converted to their JavaScript equivalents:

```python
# Python
def greet(name):
    return f"Hello, {name}!"
```

```javascript
// JavaScript Output
function greet(name) {
    return `Hello, ${name}!`;
}
```

### ✅ Default Argument Values

Default arguments allow functions to be called with fewer arguments than defined. PyNext handles both immutable defaults (numbers, strings, None) and mutable defaults (lists, dicts). **Important**: Mutable defaults are shared across function calls, matching Python's behavior—this is a common Python gotcha that PyNext correctly preserves:

```python
# Python
def append_item(item, lst=[]):
    lst.append(item)
    return lst
```

```javascript
// JavaScript Output
const _default_lst = [];
function append_item(item, lst = _default_lst) {
    lst.push(item);
    return lst;
}
```

**Note**: Mutable defaults (lists, dicts) are shared across calls, matching Python's behavior.

### ✅ *args (Variadic Positional)

Python's `*args` allows functions to accept any number of positional arguments. This is transpiled to JavaScript's rest parameters (`...args`), which collects all remaining arguments into an array. This enables flexible function signatures that work with varying numbers of arguments:

```python
# Python
def sum_all(*args):
    return sum(args)
```

```javascript
// JavaScript Output
function sum_all(...args) {
    return __py.sum(args);
}
```

### ✅ **kwargs (Variadic Keyword)

Python's `**kwargs` allows functions to accept any number of keyword arguments. PyNext transpiles this using JavaScript object destructuring and a runtime helper (`__py.kwargs()`) to properly handle keyword argument semantics. This enables functions to accept flexible keyword arguments:

```python
# Python
def create_user(name, **kwargs):
    return {"name": name, **kwargs}
```

```javascript
// JavaScript Output
function create_user(name, ..._kwargs) {
    const kwargs = __py.kwargs(_kwargs);
    return {name: name, ...kwargs};
}
```

### ✅ Keyword-Only Arguments (*, kw_only)

Functions with `*` separator support keyword-only arguments:

```python
# Python
def process(data, *, validate=True):
    if validate:
        check(data)
    return data
```

```javascript
// JavaScript Output
function process(data, {validate = true} = {}) {
    if (validate) {
        check(data);
    }
    return data;
}
```

### ✅ Positional-Only Arguments (/, pos_only)

Functions with `/` separator support positional-only arguments:

```python
# Python
def pow(x, y, /, z=None):
    result = x ** y
    if z is not None:
        result = result ** z
    return result
```

```javascript
// JavaScript Output
function pow(x, y, {z = null} = {}) {
    let result = Math.pow(x, y);
    if (z !== null) {
        result = Math.pow(result, z);
    }
    return result;
}
```

### ✅ Nested Functions (Closures)

Python supports nested function definitions, where inner functions can access variables from their enclosing scope. This creates closures—functions that "remember" their environment. PyNext transpiles nested functions to JavaScript functions, preserving closure semantics. The `nonlocal` keyword is handled automatically through JavaScript's lexical scoping:

```python
# Python
def make_counter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment
```

```javascript
// JavaScript Output
function make_counter() {
    let count = 0;
    function increment() {
        count++;
        return count;
    }
    return increment;
}
```

### ✅ Lambda Expressions

Lambda expressions are anonymous functions defined inline. PyNext transpiles Python lambdas to JavaScript arrow functions, preserving their concise syntax and lexical scoping. Lambdas are commonly used with comprehensions, `map()`, `filter()`, and other higher-order functions:

```python
# Python
square = lambda x: x ** 2
numbers = [1, 2, 3, 4]
squared = [square(x) for x in numbers]
```

```javascript
// JavaScript Output
const square = (x) => Math.pow(x, 2);
const numbers = [1, 2, 3, 4];
const squared = [...numbers.map(x => square(x))];
```

### ✅ Simple Decorators (@decorator)

Decorators are a powerful Python feature that allows functions to be wrapped or modified without changing their definition. PyNext supports both simple decorators (that take a function) and parameterized decorators (that return a decorator). Decorators are commonly used for logging, caching, validation, and cross-cutting concerns:

```python
# Python
def log_calls(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a, b):
    return a + b
```

```javascript
// JavaScript Output
function log_calls(func) {
    function wrapper(...args) {
        const kwargs = __py.kwargs(args.slice(func.length));
        console.log(`Calling ${func.name}`);
        return func(...args.slice(0, func.length), kwargs);
    }
    return wrapper;
}

const add = log_calls(function add(a, b) {
    return a + b;
});
```

### ✅ Parameterized Decorators (@decorator(args))

Decorators can accept parameters:

```python
# Python
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(name):
    print(f"Hello, {name}!")
```

```javascript
// JavaScript Output
function repeat(n) {
    function decorator(func) {
        function wrapper(...args) {
            const kwargs = __py.kwargs(args.slice(func.length));
            for (let _ = 0; _ < n; _++) {
                const result = func(...args.slice(0, func.length), kwargs);
            }
            return result;
        }
        return wrapper;
    }
    return decorator;
}

const greet = repeat(3)(function greet(name) {
    console.log(`Hello, ${name}!`);
});
```

---

## Classes

Python's object-oriented programming features are fully supported, including inheritance, properties, static methods, and multiple inheritance via mixins. PyNext transpiles Python classes to JavaScript ES6 classes while preserving Python's semantics like `self`, `super()`, and method resolution order.

### ✅ Basic Class Definition

Python classes are transpiled to JavaScript ES6 classes. Empty classes, classes with constructors, and classes with methods all work seamlessly:

```python
# Python
class Point:
    pass
```

```javascript
// JavaScript Output
class Point {
}
```

### ✅ __init__ → constructor

The `__init__` method becomes the `constructor`:

```python
# Python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

```javascript
// JavaScript Output
class Point {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
}
```

### ✅ Instance Methods (self → this)

Instance methods automatically convert `self` to `this`:

```python
# Python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx**2 + dy**2)**0.5
```

```javascript
// JavaScript Output
class Point {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
    
    distance(other) {
        const dx = this.x - other.x;
        const dy = this.y - other.y;
        return Math.pow(Math.pow(dx, 2) + Math.pow(dy, 2), 0.5);
    }
}
```

### ✅ Single Inheritance (extends)

Python supports single inheritance, where a class can inherit from one parent class. PyNext transpiles this to JavaScript's `extends` keyword. The `super()` function is properly handled to call parent class methods and constructors:

```python
# Python
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed
```

```javascript
// JavaScript Output
class Animal {
    constructor(name) {
        this.name = name;
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name);
        this.breed = breed;
    }
}
```

### ✅ super() Calls

`super()` calls are properly transpiled:

```python
# Python
class Parent:
    def greet(self):
        return "Hello"

class Child(Parent):
    def greet(self):
        return super().greet() + " World"
```

```javascript
// JavaScript Output
class Parent {
    greet() {
        return "Hello";
    }
}

class Child extends Parent {
    greet() {
        return super.greet() + " World";
    }
}
```

### ✅ Multiple Inheritance (Mixin Pattern)

Python supports multiple inheritance, where a class can inherit from multiple parent classes. Since JavaScript only supports single inheritance, PyNext implements multiple inheritance using a mixin pattern. The first parent class uses `extends`, and additional parents are applied as mixins using the `__py_classes.applyMixins()` runtime helper. This preserves Python's method resolution order (MRO):

```python
# Python
class Flyable:
    def fly(self):
        return "Flying!"

class Swimmable:
    def swim(self):
        return "Swimming!"

class Duck(Flyable, Swimmable):
    def __init__(self, name):
        self.name = name
```

```javascript
// JavaScript Output
class Flyable {
    fly() {
        return "Flying!";
    }
}

class Swimmable {
    swim() {
        return "Swimming!";
    }
}

class Duck extends Flyable {
    constructor(name) {
        super();
        this.name = name;
    }
}

__py_classes.applyMixins(Duck, [Swimmable]);
```

### ✅ @staticmethod

Static methods are transpiled to JavaScript static methods:

```python
# Python
class MathUtils:
    @staticmethod
    def add(a, b):
        return a + b
```

```javascript
// JavaScript Output
class MathUtils {
    static add(a, b) {
        return a + b;
    }
}
```

### ✅ @classmethod

Class methods are supported:

```python
# Python
class Person:
    population = 0
    
    def __init__(self, name):
        self.name = name
        Person.population += 1
    
    @classmethod
    def get_population(cls):
        return cls.population
```

```javascript
// JavaScript Output
class Person {
    static population = 0;
    
    constructor(name) {
        this.name = name;
        Person.population++;
    }
    
    static get_population() {
        return Person.population;
    }
}
```

### ✅ @property Getter

The `@property` decorator allows methods to be accessed like attributes. PyNext transpiles properties to JavaScript getters, creating a clean API where computed values can be accessed without method call syntax. Properties are useful for computed attributes, validation, and encapsulation:

```python
# Python
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    @property
    def area(self):
        return self.width * self.height
```

```javascript
// JavaScript Output
class Rectangle {
    constructor(width, height) {
        this.width = width;
        this.height = height;
    }
    
    get area() {
        return this.width * this.height;
    }
}
```

### ✅ @property Setter

Property setters allow controlled assignment to properties. When combined with getters, they create a complete property interface. PyNext transpiles property setters to JavaScript setters, enabling validation, transformation, or side effects when setting values:

```python
# Python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius
    
    @property
    def celsius(self):
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("Temperature too low")
        self._celsius = value
```

```javascript
// JavaScript Output
class Temperature {
    constructor(celsius) {
        this._celsius = celsius;
    }
    
    get celsius() {
        return this._celsius;
    }
    
    set celsius(value) {
        if (value < -273.15) {
            throw new Error("Temperature too low");
        }
        this._celsius = value;
    }
}
```

### ✅ @property Deleter

Property deleters are supported:

```python
# Python
class Resource:
    def __init__(self):
        self._data = {}
    
    @property
    def data(self):
        return self._data
    
    @data.deleter
    def data(self):
        self._data = {}
```

```javascript
// JavaScript Output
class Resource {
    constructor() {
        this._data = {};
    }
    
    get data() {
        return this._data;
    }
    
    set data(value) {
        if (value === undefined) {
            this._data = {};
        } else {
            this._data = value;
        }
    }
}
```

### ✅ Private Methods (_ prefix)

Methods with `_` prefix are treated as private (convention only):

```python
# Python
class BankAccount:
    def __init__(self, balance):
        self._balance = balance
    
    def _validate_amount(self, amount):
        return amount > 0
    
    def deposit(self, amount):
        if self._validate_amount(amount):
            self._balance += amount
```

```javascript
// JavaScript Output
class BankAccount {
    constructor(balance) {
        this._balance = balance;
    }
    
    _validate_amount(amount) {
        return amount > 0;
    }
    
    deposit(amount) {
        if (this._validate_amount(amount)) {
            this._balance += amount;
        }
    }
}
```

### ✅ Name Mangling (__ prefix → #private)

Methods with `__` prefix use JavaScript private methods (`#`):

```python
# Python
class Secure:
    def __init__(self):
        self.__secret = "hidden"
    
    def __secret_method(self):
        return self.__secret
```

```javascript
// JavaScript Output
class Secure {
    constructor() {
        this.#secret = "hidden";
    }
    
    #secret_method() {
        return this.#secret;
    }
}
```

### ✅ @dataclass

Dataclasses are supported with auto-generated methods:

```python
# Python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
```

```javascript
// JavaScript Output
class Point {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
    
    __eq__(other) {
        return this.x === other.x && this.y === other.y;
    }
    
    __repr__() {
        return `Point(x=${this.x}, y=${this.y})`;
    }
}
```

### ✅ Abstract Base Classes (ABC, @abstractmethod)

Abstract base classes are supported:

```python
# Python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass
```

```javascript
// JavaScript Output
class Shape {
    constructor() {
        __py_classes.checkAbstract(this, Shape);
    }
    
    area() {
        throw new Error("Abstract method must be implemented");
    }
}
```

---

## Control Flow

Control flow statements determine the execution path of your program. PyNext supports all Python control structures, including conditionals, loops (with `else` clauses), exception handling, and assertions. These are transpiled to equivalent JavaScript control structures while preserving Python's unique semantics like `for...else` and `while...else`.

### ✅ if / elif / else

Conditional statements (`if`, `elif`, `else`) work exactly as in Python, with proper boolean evaluation using Python's truthiness rules:

```python
# Python
def classify(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    else:
        return "C"
```

```javascript
// JavaScript Output
function classify(score) {
    if (score >= 90) {
        return "A";
    } else if (score >= 80) {
        return "B";
    } else {
        return "C";
    }
}
```

### ✅ for loops (for x in iterable → for...of)

For loops are transpiled to `for...of`:

```python
# Python
def sum_list(items):
    total = 0
    for item in items:
        total += item
    return total
```

```javascript
// JavaScript Output
function sum_list(items) {
    let total = 0;
    for (const item of items) {
        total += item;
    }
    return total;
}
```

### ✅ for...else (Loop Completion Flag)

For loops with `else` clauses track completion:

```python
# Python
def find_item(items, target):
    for item in items:
        if item == target:
            return item
    else:
        return None
```

```javascript
// JavaScript Output
function find_item(items, target) {
    let _loop_complete = true;
    for (const item of items) {
        if (item === target) {
            _loop_complete = false;
            break;
        }
    }
    if (_loop_complete) {
        return null;
    }
}
```

### ✅ while loops

While loops work as expected:

```python
# Python
def countdown(n):
    while n > 0:
        print(n)
        n -= 1
```

```javascript
// JavaScript Output
function countdown(n) {
    while (n > 0) {
        console.log(n);
        n--;
    }
}
```

### ✅ while...else

While loops with `else` clauses:

```python
# Python
def search(items, target):
    i = 0
    while i < len(items):
        if items[i] == target:
            return i
        i += 1
    else:
        return -1
```

```javascript
// JavaScript Output
function search(items, target) {
    let i = 0;
    let _loop_complete = true;
    while (i < items.length) {
        if (items[i] === target) {
            _loop_complete = false;
            break;
        }
        i++;
    }
    if (_loop_complete) {
        return -1;
    }
}
```

### ✅ break / continue

Break and continue statements work:

```python
# Python
def process_items(items):
    for item in items:
        if item is None:
            continue
        if item == "stop":
            break
        process(item)
```

```javascript
// JavaScript Output
function process_items(items) {
    for (const item of items) {
        if (item === null) {
            continue;
        }
        if (item === "stop") {
            break;
        }
        process(item);
    }
}
```

### ✅ try / except (→ try/catch)

Exception handling allows code to gracefully handle errors. PyNext transpiles Python's `try/except` blocks to JavaScript's `try/catch`, preserving exception semantics. Multiple exception handlers, exception binding (`except as e`), and `finally` blocks are all supported:

```python
# Python
def safe_divide(a, b):
    try:
        return a / b
    except:
        return None
```

```javascript
// JavaScript Output
function safe_divide(a, b) {
    try {
        return a / b;
    } catch (_e) {
        return null;
    }
}
```

### ✅ except with Type Checking

Exception types can be checked:

```python
# Python
def safe_get(data, key):
    try:
        return data[key]
    except KeyError:
        return None
    except TypeError:
        return "Invalid type"
```

```javascript
// JavaScript Output
function safe_get(data, key) {
    try {
        return data[key];
    } catch (_e) {
        if (_e instanceof KeyError) {
            return null;
        } else if (_e instanceof TypeError) {
            return "Invalid type";
        } else {
            throw _e;
        }
    }
}
```

### ✅ except as Binding

Exceptions can be bound to variables:

```python
# Python
def process(data):
    try:
        result = data.process()
    except ValueError as e:
        print(f"Error: {e}")
        return None
```

```javascript
// JavaScript Output
function process(data) {
    try {
        const result = data.process();
    } catch (_e) {
        if (_e instanceof ValueError) {
            const e = _e;
            console.log(`Error: ${e}`);
            return null;
        } else {
            throw _e;
        }
    }
}
```

### ✅ Multiple except Clauses

Multiple exception handlers are supported:

```python
# Python
def handle(data):
    try:
        return process(data)
    except ValueError:
        return "Value error"
    except TypeError:
        return "Type error"
    except:
        return "Unknown error"
```

```javascript
// JavaScript Output
function handle(data) {
    try {
        return process(data);
    } catch (_e) {
        if (_e instanceof ValueError) {
            return "Value error";
        } else if (_e instanceof TypeError) {
            return "Type error";
        } else {
            return "Unknown error";
        }
    }
}
```

### ✅ finally Block

Finally blocks are supported:

```python
# Python
def process_file(filename):
    f = open(filename)
    try:
        return f.read()
    finally:
        f.close()
```

```javascript
// JavaScript Output
function process_file(filename) {
    const f = open(filename);
    try {
        return f.read();
    } finally {
        f.close();
    }
}
```

### ✅ raise Exceptions (→ throw)

Raising exceptions is supported:

```python
# Python
def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative")
    return age
```

```javascript
// JavaScript Output
function validate_age(age) {
    if (age < 0) {
        throw new ValueError("Age cannot be negative");
    }
    return age;
}
```

### ✅ assert Statements (→ conditional throw)

Assert statements are transpiled:

```python
# Python
def divide(a, b):
    assert b != 0, "Division by zero"
    return a / b
```

```javascript
// JavaScript Output
function divide(a, b) {
    if (!(b !== 0)) {
        throw new AssertionError("Division by zero");
    }
    return a / b;
}
```

---

## Comprehensions

Comprehensions are Python's concise syntax for creating lists, dictionaries, and sets from iterables. PyNext transpiles comprehensions to optimized JavaScript array methods (`map`, `filter`, `reduce`) and native JavaScript constructs (`Set`, `Object.fromEntries`). This provides both readability and performance.

### ✅ List Comprehension: [x for x in items]

List comprehensions are transpiled to JavaScript array methods. Simple comprehensions use `map()`, filtered comprehensions use `filter().map()`, and the spread operator (`...`) ensures the result is a proper array:

```python
# Python
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
```

```javascript
// JavaScript Output
const numbers = [1, 2, 3, 4, 5];
const squared = [...numbers.map(x => Math.pow(x, 2))];
```

### ✅ Filtered: [x for x in items if cond]

Filtered comprehensions use `filter`:

```python
# Python
numbers = [1, 2, 3, 4, 5]
evens = [x for x in numbers if x % 2 == 0]
```

```javascript
// JavaScript Output
const numbers = [1, 2, 3, 4, 5];
const evens = [...numbers.filter(x => x % 2 === 0)];
```

### ✅ Mapped + Filtered: [f(x) for x in items if cond]

Combined map and filter:

```python
# Python
numbers = [1, 2, 3, 4, 5]
squared_evens = [x**2 for x in numbers if x % 2 == 0]
```

```javascript
// JavaScript Output
const numbers = [1, 2, 3, 4, 5];
const squared_evens = [...numbers.filter(x => x % 2 === 0).map(x => Math.pow(x, 2))];
```

### ✅ Nested: [[y for y in row] for row in matrix]

Nested comprehensions:

```python
# Python
matrix = [[1, 2], [3, 4]]
doubled = [[y*2 for y in row] for row in matrix]
```

```javascript
// JavaScript Output
const matrix = [[1, 2], [3, 4]];
const doubled = [...matrix.map(row => [...row.map(y => y * 2)])];
```

### ✅ Dict Comprehension: {k: v for k, v in pairs}

Dict comprehensions create dictionaries from iterables. PyNext uses a custom runtime helper (`__py.dict.fromEntries()`) to preserve key types—this is crucial because JavaScript's `Object.fromEntries()` converts all keys to strings, but Python dictionaries can have numeric or other non-string keys. This ensures Pythonic behavior is maintained:

```python
# Python
items = [("a", 1), ("b", 2), (3, "three")]
mapping = {k: v for k, v in items}
```

```javascript
// JavaScript Output
const items = [["a", 1], ["b", 2], [3, "three"]];
const mapping = __py.dict.fromEntries(items);
```

**Note**: Numeric keys are preserved (not converted to strings), matching Python's behavior.

### ✅ Set Comprehension: {x for x in items}

Set comprehensions:

```python
# Python
numbers = [1, 2, 2, 3, 3, 3]
unique = {x for x in numbers}
```

```javascript
// JavaScript Output
const numbers = [1, 2, 2, 3, 3, 3];
const unique = new Set(numbers);
```

### ✅ Generator Expression: (x for x in items)

Generator expressions create lazy iterators that compute values on-demand. PyNext transpiles generator expressions to JavaScript iterators using the `__py.iter()` runtime helper. This enables memory-efficient processing of large datasets. **Note**: Generator functions (with `yield`) are not yet supported, but generator expressions work fully:

```python
# Python
numbers = [1, 2, 3, 4, 5]
squares = (x**2 for x in numbers)
total = sum(squares)
```

```javascript
// JavaScript Output
const numbers = [1, 2, 3, 4, 5];
const squares = __py.iter(numbers).map(x => Math.pow(x, 2));
const total = __py.iter(squares).reduce((__acc__, x) => __acc__ + x, 0);
```

**Note**: Generator functions (with `yield`) are not yet supported.

### ✅ Multiple for Clauses

Multiple generators in comprehensions:

```python
# Python
pairs = [(x, y) for x in range(3) for y in range(2)]
```

```javascript
// JavaScript Output
const pairs = [];
for (let x = 0; x < 3; x++) {
    for (let y = 0; y < 2; y++) {
        pairs.push([x, y]);
    }
}
```

---

## Recent Fixes

### Mutable Default Arguments

**Issue**: Mutable defaults (lists, dicts) were creating new instances on each call instead of sharing.

**Fix**: Default mutable values are now created as constants outside the function and shared:

```python
def append(item, lst=[]):  # lst is now shared across calls
    lst.append(item)
    return lst
```

### Class Instantiation

**Issue**: Class instantiations were missing the `new` keyword.

**Fix**: The transpiler now tracks class names in scope and automatically prepends `new`:

```python
point = Point(1, 2)  # → new Point(1, 2)
```

### Property Getters/Setters

**Issue**: Property setters were not working correctly.

**Fix**: Property descriptors are now properly created using runtime helpers.

### Multiple Inheritance

**Issue**: Multiple inheritance was marked as unsupported.

**Fix**: Multiple inheritance is now supported via mixin pattern using `__py_classes.applyMixins()`.

### super() Detection

**Issue**: Auto-inserted `super()` calls conflicted with explicit `super().__init__()` calls.

**Fix**: The transpiler now properly detects existing `super()` calls in the IR and avoids duplicates.

### Dict Items Key Preservation

**Issue**: `dict.items()` was converting numeric keys to strings via `Object.entries()`.

**Fix**: Custom `__py.dict.items()` runtime helper preserves key types:

```python
d = {1: "one", 2: "two"}
for k, v in d.items():  # k is int, not string
    print(k, v)
```

---

## Best Practices

### 1. Use Type Hints

Type hints help the transpiler optimize:

```python
def process(items: list[int]) -> int:
    return sum(items)
```

### 2. Keep Functions Focused

Small, focused functions transpile better:

```python
# Good
def validate_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[1]

# Avoid
def do_everything():
    # 200 lines of code
    pass
```

### 3. Use Comprehensions for Data Transformation

Comprehensions are optimized:

```python
# Good
squared = [x**2 for x in numbers if x > 0]

# Less optimal
squared = []
for x in numbers:
    if x > 0:
        squared.append(x**2)
```

### 4. Prefer Composition Over Multiple Inheritance

While multiple inheritance works, composition is often clearer:

```python
# Good
class Duck:
    def __init__(self):
        self.flyer = Flyable()
        self.swimmer = Swimmable()
    
    def fly(self):
        return self.flyer.fly()
```

### 5. Use @property for Computed Attributes

Properties create clean APIs:

```python
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    @property
    def area(self):
        return self.width * self.height
```

---

## Known Limitations

### Generator Functions

**Status**: Not yet supported

Generator functions with `yield` are not supported:

```python
# NOT SUPPORTED
def count():
    yield 1
    yield 2
    yield 3
```

**Workaround**: Use generator expressions or list comprehensions:

```python
# Supported
numbers = (x for x in range(10))
squares = [x**2 for x in numbers]
```

### Context Managers

**Status**: Not yet supported (Phase 33.2)

The `with` statement is not yet supported:

```python
# NOT SUPPORTED
with open("file.txt") as f:
    content = f.read()
```

**Workaround**: Use try/finally:

```python
# Supported
f = open("file.txt")
try:
    content = f.read()
finally:
    f.close()
```

### Pattern Matching

**Status**: Not yet supported (Phase 33.2)

The `match/case` statement is not yet supported:

```python
# NOT SUPPORTED
match value:
    case 1:
        return "one"
    case 2:
        return "two"
```

**Workaround**: Use if/elif:

```python
# Supported
if value == 1:
    return "one"
elif value == 2:
    return "two"
```

---

## Runtime Helpers

The transpiler uses runtime helpers for Python semantics:

### Core Helpers (`__py.*`)

- `__py.bool(x)` - Python truthiness
- `__py.at(arr, index)` - Negative indexing
- `__py.slice(arr, start, stop, step)` - Slicing
- `__py.isinstance(obj, type)` - Type checking
- `__py.iter(iterable)` - Iterator protocol

### Dict Helpers (`__py.dict.*`)

- `__py.dict.items(d)` - Preserves key types
- `__py.dict.fromEntries(pairs)` - Creates dict from pairs

### Class Helpers (`__py_classes.*`)

- `__py_classes.applyMixins(Class, mixins)` - Multiple inheritance
- `__py_classes.createProperty(getter, setter, deleter)` - Property descriptors
- `__py_classes.checkAbstract(instance, cls)` - Abstract class validation

---

## Testing

Phase 33.1 has comprehensive test coverage:

- **427+ unit tests** in Phase 33.1 specific test files
- **22,659+ total passing tests** across the entire test suite
- **52 integration tests** verifying Python/JavaScript equivalence

### Running Tests

```bash
# Run Phase 33.1 specific tests
pytest tests/unit/transpiler/test_331_functions.py
pytest tests/unit/transpiler/test_331_classes.py
pytest tests/unit/transpiler/test_list_comprehensions.py
pytest tests/unit/transpiler/test_dict_comprehensions.py
pytest tests/unit/transpiler/test_set_comprehensions.py

# Run integration tests
pytest tests/integration/transpiler/
```

---

## See Also

- [ROADMAP.md](../ROADMAP.md) - Phase 33.1 checklist and milestones
- [CLASSES.md](CLASSES.md) - Detailed class transpilation guide
- [CORE_STATEMENTS.md](CORE_STATEMENTS.md) - Control flow and statement details
- [EXPRESSIONS.md](EXPRESSIONS.md) - Expression and operator transpilation
- [ADVANCED.md](ADVANCED.md) - Advanced transpilation features

---

## Version History

### Phase 33.1 (Current) ✅

- **Status**: Complete (46/46 features)
- **Tests**: 427+ unit tests, 22,659+ total passing
- **Recent Fixes**: Mutable defaults, class instantiation, properties, multiple inheritance, super() detection, dict key preservation

### Future Phases

- **Phase 33.2**: Advanced constructs (generators, context managers, pattern matching)
- **Phase 33.3**: Infrastructure improvements
- **Phase 33.4**: Developer tools

---

**Last Updated**: Phase 33.1 Complete
**Maintainer**: PyNext Team

