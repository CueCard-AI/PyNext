"""
Exception Handling Application

Exception handling and error management.
"""

EXCEPTION_HANDLING_CODE = """
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

