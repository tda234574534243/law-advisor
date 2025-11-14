from backend.bot import compose_answer, check_definition_exists_in_db, retrieve, detect_intent

# First check if definition exists
exists, defn = check_definition_exists_in_db('quyền sử dụng đất')
print(f"Definition exists: {exists}")
print(f"Definition: {defn[:100] if defn else 'None'}\n")

# Get hits
hits = retrieve('Quyền sử dụng đất là gì?', k=5, mode='keyword')
print(f"Number of hits: {len(hits)}")
if hits:
    print(f"First hit score: {hits[0].get('score', 'N/A')}")
    print(f"First hit title: {hits[0].get('title', 'N/A')}\n")

# Check intent
intent = detect_intent('Quyền sử dụng đất là gì?')
print(f"Detected intent: {intent}\n")

# Test compose_answer
answer, updated_confidence = compose_answer(
    intent, hits, 'Quyền sử dụng đất là gì?', 'very_high'
)
print(f"Updated confidence: {updated_confidence}")
print(f"Answer preview: {answer[:200]}")
