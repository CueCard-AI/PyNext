"""
Control Flow Application

Complex control flow patterns.
"""

CONTROL_FLOW_CODE = """
# Complex control flow
numbers = list(range(1, 21))

# Find first prime
primes = []
for num in numbers:
    if num < 2:
        continue
    is_prime = True
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            is_prime = False
            break
    if is_prime:
        primes.append(num)
    if len(primes) >= 5:
        break

print(f"First 5 primes: {primes}")

# While loop with else
count = 0
while count < 3:
    print(f"Count: {count}")
    count += 1
else:
    print("Loop completed normally")
"""

