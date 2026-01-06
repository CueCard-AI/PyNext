"""
Todo Application

A simple todo list application.
"""

TODO_CODE = """
class Todo:
    def __init__(self, title):
        self.title = title
        self.done = False
    
    def toggle(self):
        self.done = not self.done
    
    def __str__(self):
        status = "✓" if self.done else " "
        return f"[{status}] {self.title}"

class TodoList:
    def __init__(self):
        self.todos = []
    
    def add(self, title):
        self.todos.append(Todo(title))
    
    def toggle(self, index):
        if 0 <= index < len(self.todos):
            self.todos[index].toggle()
    
    def list_all(self):
        for i, todo in enumerate(self.todos):
            print(f"{i}: {todo}")

todos = TodoList()
todos.add("Buy milk")
todos.add("Walk dog")
todos.toggle(0)
todos.list_all()
"""

