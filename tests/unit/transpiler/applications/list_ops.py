"""
List Operations Application

List operations, slicing, and comprehensions.
"""

LIST_OPS_CODE = """
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

