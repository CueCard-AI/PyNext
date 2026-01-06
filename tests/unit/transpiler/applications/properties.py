"""
Properties Application

Property decorators and getters/setters.
"""

PROPERTIES_CODE = """
class Circle:
    def __init__(self, radius):
        self._radius = radius
    
    @property
    def radius(self):
        return self._radius
    
    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("Radius cannot be negative")
        self._radius = value
    
    @property
    def area(self):
        return 3.14159 * self._radius ** 2
    
    @property
    def diameter(self):
        return 2 * self._radius

circle = Circle(5)
print(f"Radius: {circle.radius}")
print(f"Area: {circle.area:.2f}")
print(f"Diameter: {circle.diameter}")

circle.radius = 10
print(f"New radius: {circle.radius}")
print(f"New area: {circle.area:.2f}")
"""

