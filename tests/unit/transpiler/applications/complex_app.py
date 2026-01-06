"""
Complex Application

Complex application combining multiple features.
"""

COMPLEX_APP_CODE = """
class Product:
    def __init__(self, name, price, category):
        self.name = name
        self.price = price
        self.category = category
    
    def __str__(self):
        return f"{self.name} (${self.price:.2f})"

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, product, quantity=1):
        for _ in range(quantity):
            self.items.append(product)
    
    def total(self):
        return sum(item.price for item in self.items)
    
    def by_category(self, category):
        return [item for item in self.items if item.category == category]
    
    def apply_discount(self, discount_func):
        return discount_func(self.total())

# Create products
products = [
    Product("Laptop", 999.99, "Electronics"),
    Product("Mouse", 29.99, "Electronics"),
    Product("Desk", 199.99, "Furniture"),
    Product("Chair", 149.99, "Furniture")
]

# Create cart
cart = ShoppingCart()
cart.add_item(products[0], 1)
cart.add_item(products[1], 2)
cart.add_item(products[2], 1)

# Calculate totals
total = cart.total()
electronics = cart.by_category("Electronics")
electronics_total = sum(p.price for p in electronics)

# Discount function
discount_10 = lambda total: total * 0.9
discounted = cart.apply_discount(discount_10)

print(f"Total: ${total:.2f}")
print(f"Electronics: ${electronics_total:.2f}")
print(f"After 10% discount: ${discounted:.2f}")
"""

