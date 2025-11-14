import json
import re

with open('data/tinydb.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Search for "Quyền sử dụng đất là" or definition pattern
patterns = [
    r"Quyền sử dụng đất\s+là\s+[^.]+\.",
    r"quyền sử dụng đất\s+của\s+[^.]+\.",
    r"\"quyền sử dụng đất\"\s+là\s+[^.]+\.",
]

for pattern in patterns:
    matches = re.finditer(pattern, content, re.IGNORECASE)
    for match in matches:
        print(f"Pattern: {pattern}")
        print(f"Match: {match.group()}\n")
