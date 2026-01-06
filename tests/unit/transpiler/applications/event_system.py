"""
Event System Application

An event system with callbacks and closures.
"""

EVENT_SYSTEM_CODE = """
class EventEmitter:
    def __init__(self):
        self.listeners = {}
    
    def on(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
    
    def emit(self, event, *args):
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*args)

emitter = EventEmitter()

# Register listeners
emitter.on("greet", lambda name: print(f"Hello, {name}!"))
emitter.on("greet", lambda name: print(f"Welcome, {name}!"))

# Emit events
emitter.emit("greet", "Alice")
emitter.emit("greet", "Bob")
"""

