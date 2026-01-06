"""
Dictionary Operations Application

Dictionary creation, manipulation, and comprehensions.
"""

DICT_OPS_CODE = """
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

