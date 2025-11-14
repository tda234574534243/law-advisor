from backend.bot import answer_question

result = answer_question('Quyền sử dụng đất là gì?')
print(f"Confidence from answer_question: {result['confidence']}")
print(f"Answer preview: {result['answer'][:300]}")

# Check if warning is in the answer
if "⚠️" in result['answer']:
    print("\n✓ WARNING PRESENT IN ANSWER")
else:
    print("\n✗ WARNING NOT PRESENT IN ANSWER")
