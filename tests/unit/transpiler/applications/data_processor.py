"""
Data Processor Application

A data processing application with comprehensions.
"""

DATA_PROCESSOR_CODE = """
# Process a list of numbers
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Filter evens and square them
evens_squared = [x*x for x in numbers if x % 2 == 0]
print(f"Evens squared: {evens_squared}")

# Create a mapping
number_map = {x: x*2 for x in numbers if x > 5}
print(f"Number map: {sorted(number_map.items())}")

# Process with functions
def process_data(data):
    return [x*2 for x in data if x > 3]

result = process_data(numbers)
print(f"Processed: {result}")
"""

