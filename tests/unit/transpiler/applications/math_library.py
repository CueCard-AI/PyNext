"""
Math Library Application

A math library with various functions.
"""

MATH_LIBRARY_CODE = """
class MathUtils:
    @staticmethod
    def factorial(n):
        if n <= 1:
            return 1
        return n * MathUtils.factorial(n - 1)
    
    @staticmethod
    def fibonacci(n):
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    @staticmethod
    def primes_up_to(n):
        return [x for x in range(2, n + 1) 
                if all(x % i != 0 for i in range(2, int(x**0.5) + 1))]

print(f"Factorial(5): {MathUtils.factorial(5)}")
print(f"Fibonacci(10): {MathUtils.fibonacci(10)}")
print(f"Primes up to 20: {MathUtils.primes_up_to(20)}")
"""

