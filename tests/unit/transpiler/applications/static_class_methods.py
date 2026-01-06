"""
Static and Class Methods Application

Static methods and class methods.
"""

STATIC_CLASS_METHODS_CODE = """
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

