# PyNext Class Transpilation

This document describes how Python classes are transpiled to JavaScript in PyNext.

## Overview

PyNext supports transpiling Python classes to JavaScript classes for client-side code. This enables you to write object-oriented UI components using familiar Python syntax.

## Supported Features

### Basic Classes

```python
# Python
class Todo:
    def __init__(self, title):
        self.title = title
        self.done = False
```

```javascript
// JavaScript Output
class Todo {
    constructor(title) {
        this.title = title;
        this.done = false;
    }
}
```

### Instance Methods

Instance methods are transpiled with `self` automatically converted to `this`:

```python
# Python
class Counter:
    def __init__(self):
        self.count = 0
    
    def increment(self):
        self.count = self.count + 1
    
    def decrement(self):
        self.count = self.count - 1
```

```javascript
// JavaScript Output
class Counter {
    constructor() {
        this.count = 0;
    }
    
    increment() {
        this.count = this.count + 1;
    }
    
    decrement() {
        this.count = this.count - 1;
    }
}
```

### Default Parameter Values

```python
# Python
class Todo:
    def __init__(self, title, done=False, priority=0):
        self.title = title
        self.done = done
        self.priority = priority
```

```javascript
// JavaScript Output
class Todo {
    constructor(title, done = false, priority = 0) {
        this.title = title;
        this.done = done;
        this.priority = priority;
    }
}
```

### Property Getters

The `@property` decorator creates a JavaScript getter:

```python
# Python
class Todo:
    def __init__(self, title):
        self.title = title
        self.done = False
    
    @property
    def status(self):
        if self.done:
            return "Done"
        return "Pending"
```

```javascript
// JavaScript Output
class Todo {
    constructor(title) {
        this.title = title;
        this.done = false;
    }
    
    get status() {
        if (this.done) {
            return "Done";
        }
        return "Pending";
    }
}
```

### Static Methods

```python
# Python
class Utils:
    @staticmethod
    def validate(title):
        return len(title) > 0
    
    @staticmethod
    def clamp(value, min_val, max_val):
        return max(min_val, min(max_val, value))
```

```javascript
// JavaScript Output
class Utils {
    static validate(title) {
        return title.length > 0;
    }
    
    static clamp(value, min_val, max_val) {
        return Math.max(min_val, Math.min(max_val, value));
    }
}
```

### Single Inheritance

PyNext supports single inheritance with `super()`:

```python
# Python
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        return "Some sound"

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed
    
    def speak(self):
        return "Woof!"
```

```javascript
// JavaScript Output
class Animal {
    constructor(name) {
        this.name = name;
    }
    
    speak() {
        return "Some sound";
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name);
        this.breed = breed;
    }
    
    speak() {
        return "Woof!";
    }
}
```

### Async Methods

```python
# Python
class DataFetcher:
    async def fetch(self, url):
        data = await fetch(url)
        return await data.json()
```

```javascript
// JavaScript Output
class DataFetcher {
    async fetch(url) {
        const data = await fetch(url);
        return await data.json();
    }
}
```

### Multiple Inheritance

Multiple inheritance is supported via the mixin pattern:

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
class Duck extends Flyable {
    constructor(name) {
        super();
        this.name = name;
    }
}

__py_classes.applyMixins(Duck, [Swimmable]);
```

The first parent class uses `extends`, and additional parents are applied as mixins.

### @classmethod

Class methods are fully supported:

```python
# Python
class Counter:
    count = 0
    
    @classmethod
    def increment(cls):
        cls.count += 1
        return cls.count
```

```javascript
// JavaScript Output
class Counter {
    static count = 0;
    
    static increment() {
        Counter.count++;
        return Counter.count;
    }
}
```

### Property Setters

Property setters are fully supported:

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
            throw new ValueError("Temperature too low");
        }
        this._celsius = value;
    }
}
```

## Unsupported Features

The following Python class features are **not supported** for client-side transpilation:

### Metaclasses

```python
# NOT SUPPORTED
class Singleton(metaclass=Meta):  # Error: Metaclass not supported
    pass
```

**Suggestion:** Use `@server_action` for complex class patterns.

### __slots__

```python
# NOT SUPPORTED
class Fast:
    __slots__ = ['x', 'y']  # Error: __slots__ not supported
```

**Suggestion:** Just remove `__slots__`. JavaScript classes don't have this optimization.

## Best Practices

### 1. Keep Classes Simple

Client-side classes should focus on UI state and behavior:

```python
class TodoItem:
    def __init__(self, title):
        self.title = title
        self.done = False
    
    def toggle(self):
        self.done = not self.done
```

### 2. Use @server_action for Complex Logic

Heavy computation or database access should stay on the server:

```python
class TodoItem:
    def __init__(self, title):
        self.title = title
    
    @server_action
    async def save_to_database(self):
        # This runs on the server
        await db.insert(self)
```

### 3. Combine with Signals for Reactivity

Classes work great with PyNext's reactive primitives:

```python
class TodoList:
    def __init__(self):
        self.items = signal([])
    
    def add(self, title):
        current = self.items()
        self.items.set([*current, TodoItem(title)])
```

### 4. Validate in Constructor

Use assert for constructor validation:

```python
class Todo:
    def __init__(self, title):
        assert title, "Title is required"
        assert len(title) <= 100, "Title too long"
        self.title = title
```

## Complete Example

Here's a complete example of a Todo app using classes:

```python
class Todo:
    def __init__(self, title, done=False):
        assert title, "Title required"
        self.title = title
        self.done = done
    
    def toggle(self):
        self.done = not self.done
    
    @property
    def status(self):
        return "✓" if self.done else "○"
    
    @staticmethod
    def from_dict(data):
        return Todo(data["title"], data.get("done", False))


class TodoList:
    def __init__(self):
        self.items = []
    
    def add(self, title):
        todo = Todo(title)
        self.items.append(todo)
        return todo
    
    def remove(self, index):
        del self.items[index]
    
    @property
    def pending_count(self):
        return len([t for t in self.items if not t.done])
    
    @property
    def completed_count(self):
        return len([t for t in self.items if t.done])
```

This transpiles to clean, idiomatic JavaScript that works in any modern browser.

## See Also

- [ADVANCED.md](ADVANCED.md) - Advanced transpilation features
- [OPTIMIZER.md](OPTIMIZER.md) - Optimization passes
- [DEBUG.md](DEBUG.md) - Debugging transpilation

