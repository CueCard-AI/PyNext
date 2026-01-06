"""
Multiple Inheritance Application

Multiple inheritance with mixins.
"""

MULTIPLE_INHERITANCE_CODE = """
class Flyable:
    def fly(self):
        return f"{self.name} is flying"

class Swimmable:
    def swim(self):
        return f"{self.name} is swimming"

class Duck(Flyable, Swimmable):
    def __init__(self, name):
        self.name = name
    
    def quack(self):
        return f"{self.name} quacks"

duck = Duck("Donald")
print(duck.quack())
print(duck.fly())
print(duck.swim())
"""

