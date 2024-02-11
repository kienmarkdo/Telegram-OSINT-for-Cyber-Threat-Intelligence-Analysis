keys = []

for i in range(97, 123, 1):  # ASCII values of a-z inclusive
    keys.append(chr(i))

for i in range(48, 58, 1):  # ASCII values of 0-9 inclusive
    keys.append(chr(i))

print(len(keys))