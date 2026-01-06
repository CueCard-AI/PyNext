"""
Game Application

A simple game with classes and control flow.
"""

GAME_CODE = """
class Player:
    def __init__(self, name, health=100):
        self.name = name
        self.health = health
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
    
    def is_alive(self):
        return self.health > 0

class Enemy:
    def __init__(self, name, damage=10):
        self.name = name
        self.damage = damage
    
    def attack(self, player):
        player.take_damage(self.damage)
        return f"{self.name} attacks {player.name} for {self.damage} damage"

player = Player("Hero")
enemy = Enemy("Goblin")

rounds = 0
while player.is_alive() and rounds < 5:
    rounds += 1
    message = enemy.attack(player)
    print(f"Round {rounds}: {message}, Health: {player.health}")

if player.is_alive():
    print(f"{player.name} survived!")
else:
    print(f"{player.name} was defeated!")
"""

