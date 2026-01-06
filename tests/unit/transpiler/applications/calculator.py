"""
Calculator Application

A simple calculator with history tracking.
"""

CALCULATOR_CODE = """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self):
        return self.history

calc = Calculator()
print(calc.add(2, 3))
print(calc.multiply(4, 5))
print(len(calc.get_history()))
"""

