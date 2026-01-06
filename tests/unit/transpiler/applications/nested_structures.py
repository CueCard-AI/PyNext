"""
Nested Structures Application

Nested data structures.
"""

NESTED_STRUCTURES_CODE = """
# Nested structures
students = [
    {"name": "Alice", "scores": [85, 90, 88]},
    {"name": "Bob", "scores": [92, 87, 91]},
    {"name": "Charlie", "scores": [78, 82, 80]}
]

# Calculate averages
averages = {s["name"]: sum(s["scores"]) / len(s["scores"]) for s in students}

# Find top student
top_student = max(averages.items(), key=lambda x: x[1])

print(f"Averages: {averages}")
print(f"Top student: {top_student[0]} with {top_student[1]:.1f}")
"""

