# 1. Writing to a file cleanly
with open("chunk.txt", "w", encoding="utf-8") as f:
    f.write("Section 1: Data retention and privacy guidelines.")
# 2\. Reading it back safely
with open("chunk.txt", "r", encoding="utf-8") as f:
    text = f.read()
print(f"Read from file: {text}")
