import json

# Load tinydb.json để tìm định nghĩa "Quyền sử dụng đất"
with open('data/tinydb.json', 'r', encoding='utf-8') as f:
    content = f.read()
    
print("=== SEARCHING FOR 'Quyền sử dụng đất' ===")
if "Quyền sử dụng đất" in content:
    idx = content.find("Quyền sử dụng đất")
    snippet = content[max(0, idx-100):idx+300]
    print("Found at position:", idx)
    print(snippet)
else:
    print("Not found")
