from backend.bot import detect_intent

intent = detect_intent('Quyền sử dụng đất là gì?')
print(f"Detected intent: {intent}")
