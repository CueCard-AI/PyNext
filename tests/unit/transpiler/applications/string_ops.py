"""
String Operations Application

String manipulation and formatting.
"""

STRING_OPS_CODE = """
def process_text(text):
    # String methods
    words = text.split()
    upper_words = [w.upper() for w in words]
    joined = " ".join(upper_words)
    
    # String formatting
    formatted = f"Processed: {joined} ({len(words)} words)"
    return formatted

text = "hello world from python"
result = process_text(text)
print(result)
print(f"Original length: {len(text)}")
print(f"Word count: {len(text.split())}")
"""

