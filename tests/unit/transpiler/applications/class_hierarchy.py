"""
Class Hierarchy Application

Class inheritance and polymorphism.
"""

CLASS_HIERARCHY_CODE = """
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        return f"{self.name} makes a sound"
    
    def move(self):
        return f"{self.name} moves"

class Dog(Animal):
    def speak(self):
        return f"{self.name} barks"
    
    def fetch(self):
        return f"{self.name} fetches the ball"

class Cat(Animal):
    def speak(self):
        return f"{self.name} meows"
    
    def climb(self):
        return f"{self.name} climbs a tree"

# Polymorphism
animals = [Dog("Buddy"), Cat("Whiskers"), Animal("Generic")]

for animal in animals:
    print(animal.speak())
    print(animal.move())

# Type-specific methods
dog = Dog("Rex")
cat = Cat("Fluffy")
print(dog.fetch())
print(cat.climb())
"""

