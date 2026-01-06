"""
Phase 33.1: Additional Mini Application Tests

More comprehensive mini applications testing various transpiler features.
"""

import pytest
import sys
from pathlib import Path
from pynext.transpiler import transpile

# Import harness
sys.path.insert(0, str(Path(__file__).parent))
from test_mini_applications import MiniAppHarness


@pytest.fixture
def harness():
    """Create a mini app harness."""
    h = MiniAppHarness()
    yield h
    import shutil
    shutil.rmtree(h.temp_dir, ignore_errors=True)


class TestStringManipulationApp:
    """String manipulation and formatting."""
    
    def test_string_operations(self, harness):
        """String operations, formatting, and methods."""
        app_code = """
def process_text(text):
    # String methods
    words = text.split()
    upper_words = [w.upper() for w in words]
    joined = " ".join(upper_words)
    
    # String formatting
    formatted = f"Processed: {joined} ({len(words)} words)"
    return formatted

text = "hello world from python"
result = process_text(text)
print(result)
print(f"Original length: {len(text)}")
print(f"Word count: {len(text.split())}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestListOperationsApp:
    """List operations and comprehensions."""
    
    def test_list_manipulation(self, harness):
        """List operations, slicing, and comprehensions."""
        app_code = """
# List creation and manipulation
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Filtering and mapping
evens = [x for x in numbers if x % 2 == 0]
squares = [x*x for x in numbers]
even_squares = [x*x for x in numbers if x % 2 == 0]

# Slicing
first_half = numbers[:5]
second_half = numbers[5:]
reversed_list = numbers[::-1]

print(f"Evens: {evens}")
print(f"Squares: {squares[:5]}")
print(f"Even squares: {even_squares}")
print(f"First half: {first_half}")
print(f"Reversed: {reversed_list[:5]}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestDictionaryApp:
    """Dictionary operations and comprehensions."""
    
    def test_dictionary_operations(self, harness):
        """Dictionary creation, manipulation, and comprehensions."""
        app_code = """
# Dictionary creation
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

# Dictionary operations
person["email"] = "alice@example.com"
person["age"] = 31

# Dictionary comprehension
squares_dict = {x: x*x for x in range(1, 6)}
filtered_dict = {k: v for k, v in person.items() if isinstance(v, int)}

print(f"Person: {person}")
print(f"Squares: {squares_dict}")
print(f"Filtered: {filtered_dict}")
print(f"Keys: {list(person.keys())}")
print(f"Values: {list(person.values())}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestNestedStructuresApp:
    """Nested data structures."""
    
    def test_nested_structures(self, harness):
        """Nested lists, dicts, and comprehensions."""
        app_code = """
# Nested structures
students = [
    {"name": "Alice", "scores": [85, 90, 88]},
    {"name": "Bob", "scores": [92, 87, 91]},
    {"name": "Charlie", "scores": [78, 82, 80]}
]

# Calculate averages
averages = {s["name"]: sum(s["scores"]) / len(s["scores"]) for s in students}

# Find top student
top_student = max(averages.items(), key=lambda x: x[1])

print(f"Averages: {averages}")
print(f"Top student: {top_student[0]} with {top_student[1]:.1f}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestControlFlowApp:
    """Complex control flow patterns."""
    
    def test_control_flow(self, harness):
        """If/else, loops, break/continue."""
        app_code = """
# Complex control flow
numbers = list(range(1, 21))

# Find first prime
primes = []
for num in numbers:
    if num < 2:
        continue
    is_prime = True
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            is_prime = False
            break
    if is_prime:
        primes.append(num)
    if len(primes) >= 5:
        break

print(f"First 5 primes: {primes}")

# While loop with else
count = 0
while count < 3:
    print(f"Count: {count}")
    count += 1
else:
    print("Loop completed normally")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestFunctionCompositionApp:
    """Function composition and higher-order functions."""
    
    def test_function_composition(self, harness):
        """Nested functions, closures, and function composition."""
        app_code = """
def make_multiplier(n):
    def multiply(x):
        return x * n
    return multiply

def compose(f, g):
    def composed(x):
        return f(g(x))
    return composed

# Create multipliers
double = make_multiplier(2)
triple = make_multiplier(3)

# Compose functions
square = lambda x: x * x
add_one = lambda x: x + 1
square_then_add = compose(add_one, square)

print(f"Double 5: {double(5)}")
print(f"Triple 5: {triple(5)}")
print(f"Square then add 1 to 4: {square_then_add(4)}")

# List of functions
functions = [double, triple, square]
results = [f(3) for f in functions]
print(f"Results: {results}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestClassHierarchyApp:
    """Class inheritance and polymorphism."""
    
    def test_class_hierarchy(self, harness):
        """Inheritance, method overriding, and polymorphism."""
        app_code = """
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        return f"{self.name} makes a sound"
    
    def move(self):
        return f"{self.name} moves"

class Dog(Animal):
    def speak(self):
        return f"{self.name} barks"
    
    def fetch(self):
        return f"{self.name} fetches the ball"

class Cat(Animal):
    def speak(self):
        return f"{self.name} meows"
    
    def climb(self):
        return f"{self.name} climbs a tree"

# Polymorphism
animals = [Dog("Buddy"), Cat("Whiskers"), Animal("Generic")]

for animal in animals:
    print(animal.speak())
    print(animal.move())

# Type-specific methods
dog = Dog("Rex")
cat = Cat("Fluffy")
print(dog.fetch())
print(cat.climb())
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestMultipleInheritanceApp:
    """Multiple inheritance with mixins."""
    
    def test_multiple_inheritance(self, harness):
        """Multiple inheritance and mixin pattern."""
        app_code = """
class Flyable:
    def fly(self):
        return f"{self.name} is flying"

class Swimmable:
    def swim(self):
        return f"{self.name} is swimming"

class Duck(Flyable, Swimmable):
    def __init__(self, name):
        self.name = name
    
    def quack(self):
        return f"{self.name} quacks"

duck = Duck("Donald")
print(duck.quack())
print(duck.fly())
print(duck.swim())
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestPropertyApp:
    """Property decorators and getters/setters."""
    
    def test_properties(self, harness):
        """Property decorators with getters and setters."""
        app_code = """
class Circle:
    def __init__(self, radius):
        self._radius = radius
    
    @property
    def radius(self):
        return self._radius
    
    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("Radius cannot be negative")
        self._radius = value
    
    @property
    def area(self):
        return 3.14159 * self._radius ** 2
    
    @property
    def diameter(self):
        return 2 * self._radius

circle = Circle(5)
print(f"Radius: {circle.radius}")
print(f"Area: {circle.area:.2f}")
print(f"Diameter: {circle.diameter}")

circle.radius = 10
print(f"New radius: {circle.radius}")
print(f"New area: {circle.area:.2f}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestStaticClassMethodsApp:
    """Static and class methods."""
    
    def test_static_class_methods(self, harness):
        """Static methods and class methods."""
        app_code = """
class MathUtils:
    PI = 3.14159
    
    @staticmethod
    def add(a, b):
        return a + b
    
    @staticmethod
    def multiply(a, b):
        return a * b
    
    @classmethod
    def get_pi(cls):
        return cls.PI
    
    @classmethod
    def circle_area(cls, radius):
        return cls.PI * radius ** 2

# Static methods
print(f"Add: {MathUtils.add(3, 4)}")
print(f"Multiply: {MathUtils.multiply(3, 4)}")

# Class methods
print(f"PI: {MathUtils.get_pi()}")
print(f"Circle area (r=5): {MathUtils.circle_area(5):.2f}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestExceptionHandlingApp:
    """Exception handling and error management."""
    
    def test_exception_handling(self, harness):
        """Try/except/finally blocks."""
        app_code = """
def divide(a, b):
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        return "Cannot divide by zero"
    except TypeError:
        return "Invalid types"
    finally:
        print("Division attempted")

def safe_get(data, key):
    try:
        return data[key]
    except KeyError:
        return None
    except TypeError:
        return "Invalid data type"

# Test division
print(f"10 / 2 = {divide(10, 2)}")
print(f"10 / 0 = {divide(10, 0)}")

# Test dictionary access
data = {"name": "Alice", "age": 30}
print(f"Name: {safe_get(data, 'name')}")
print(f"Email: {safe_get(data, 'email')}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestGeneratorApp:
    """Generator expressions and functions."""
    
    def test_generators(self, harness):
        """Generator expressions and functions."""
        app_code = """
# Generator expression
squares_gen = (x*x for x in range(10))
first_five = [next(squares_gen) for _ in range(5)]

# Generator function
def fibonacci(n):
    a, b = 0, 1
    count = 0
    while count < n:
        yield a
        a, b = b, a + b
        count += 1

fib_gen = fibonacci(10)
fib_list = list(fib_gen)

print(f"First 5 squares: {first_five}")
print(f"First 10 Fibonacci: {fib_list[:10]}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestComplexApp:
    """Complex application combining multiple features."""
    
    def test_complex_app(self, harness):
        """Complex application with classes, functions, and comprehensions."""
        app_code = """
class Product:
    def __init__(self, name, price, category):
        self.name = name
        self.price = price
        self.category = category
    
    def __str__(self):
        return f"{self.name} (${self.price:.2f})"

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, product, quantity=1):
        for _ in range(quantity):
            self.items.append(product)
    
    def total(self):
        return sum(item.price for item in self.items)
    
    def by_category(self, category):
        return [item for item in self.items if item.category == category]
    
    def apply_discount(self, discount_func):
        return discount_func(self.total())

# Create products
products = [
    Product("Laptop", 999.99, "Electronics"),
    Product("Mouse", 29.99, "Electronics"),
    Product("Desk", 199.99, "Furniture"),
    Product("Chair", 149.99, "Furniture")
]

# Create cart
cart = ShoppingCart()
cart.add_item(products[0], 1)
cart.add_item(products[1], 2)
cart.add_item(products[2], 1)

# Calculate totals
total = cart.total()
electronics = cart.by_category("Electronics")
electronics_total = sum(p.price for p in electronics)

# Discount function
discount_10 = lambda total: total * 0.9
discounted = cart.apply_discount(discount_10)

print(f"Total: ${total:.2f}")
print(f"Electronics: ${electronics_total:.2f}")
print(f"After 10% discount: ${discounted:.2f}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0

