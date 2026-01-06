"""
Phase 33.1: Additional Mini Application Tests

More comprehensive mini applications testing various patterns.
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


class TestShoppingCartApp:
    """Shopping cart with items, quantities, and totals."""
    
    def test_shopping_cart(self, harness):
        """Shopping cart application"""
        app_code = """
class Item:
    def __init__(self, name, price):
        self.name = name
        self.price = price

class Cart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item, quantity=1):
        for _ in range(quantity):
            self.items.append(item)
    
    def total(self):
        return sum(item.price for item in self.items)
    
    def item_count(self):
        return len(self.items)

cart = Cart()
cart.add_item(Item("Apple", 1.50), 3)
cart.add_item(Item("Banana", 0.75), 2)
print(f"Total: ${cart.total():.2f}")
print(f"Items: {cart.item_count()}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestBankAccountApp:
    """Bank account with deposits, withdrawals, and balance."""
    
    def test_bank_account(self, harness):
        """Bank account application"""
        app_code = """
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self._balance = balance
    
    def deposit(self, amount):
        if amount > 0:
            self._balance += amount
            return True
        return False
    
    def withdraw(self, amount):
        if 0 < amount <= self._balance:
            self._balance -= amount
            return True
        return False
    
    @property
    def balance(self):
        return self._balance

account = BankAccount("Alice", 100)
account.deposit(50)
account.withdraw(30)
print(f"{account.owner}: ${account.balance}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestLibrarySystemApp:
    """Library system with books and borrowing."""
    
    def test_library_system(self, harness):
        """Library system application"""
        app_code = """
class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.borrowed = False

class Library:
    def __init__(self):
        self.books = []
    
    def add_book(self, book):
        self.books.append(book)
    
    def borrow_book(self, title):
        for book in self.books:
            if book.title == title and not book.borrowed:
                book.borrowed = True
                return book
        return None
    
    def return_book(self, title):
        for book in self.books:
            if book.title == title and book.borrowed:
                book.borrowed = False
                return True
        return False
    
    def available_books(self):
        return [book.title for book in self.books if not book.borrowed]

library = Library()
library.add_book(Book("1984", "Orwell"))
library.add_book(Book("Brave New World", "Huxley"))
library.borrow_book("1984")
available = library.available_books()
print(f"Available: {len(available)}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestSortingApp:
    """Various sorting algorithms."""
    
    def test_sorting_app(self, harness):
        """Sorting application"""
        app_code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

numbers = [64, 34, 25, 12, 22, 11, 90]
sorted1 = bubble_sort(numbers.copy())
sorted2 = quick_sort(numbers.copy())
print(f"Bubble: {sorted1[:3]}")
print(f"Quick: {sorted2[:3]}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestCacheApp:
    """Simple caching system."""
    
    def test_cache_app(self, harness):
        """Cache application"""
        app_code = """
class Cache:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
    
    def get(self, key):
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        if key in self.cache:
            self.cache[key] = value
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                lru = self.access_order.pop(0)
                del self.cache[lru]
            self.cache[key] = value
            self.access_order.append(key)

cache = Cache(3)
cache.set("a", 1)
cache.set("b", 2)
cache.set("c", 3)
cache.get("a")  # Make 'a' most recently used
cache.set("d", 4)  # Should evict 'b'
print(f"Size: {len(cache.cache)}")
print(f"Has 'a': {'a' in cache.cache}")
print(f"Has 'b': {'b' in cache.cache}")
"""
        result = harness.run_mini_app(app_code)
        
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0

