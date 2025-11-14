from backend.bot import answer_question

result = answer_question('Quyền sử dụng đất là gì?')
print(f"Confidence: {result['confidence']}")
print(f"Answer: {result['answer']}")
