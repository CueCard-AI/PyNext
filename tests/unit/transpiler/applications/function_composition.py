"""
Function Composition Application

Function composition and higher-order functions.
"""

FUNCTION_COMPOSITION_CODE = """
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

