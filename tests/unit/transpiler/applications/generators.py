"""
Generators Application

Generator expressions and functions.
"""

GENERATORS_CODE = """
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

