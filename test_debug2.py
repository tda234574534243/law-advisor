from backend.bot import retrieve, verify_answer_relevance
import re

# Get hits
hits = retrieve('Quyền sử dụng đất là gì?', k=5, mode='keyword')

# Helper function from bot.py
def get_text(h):
    """Extract text from hit"""
    text = h.get('text') or h.get('noi_dung') or ''
    
    # Convert list items to strings
    if isinstance(text, list):
        text_parts = []
        for item in text:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                dict_text = item.get('noi_dung') or item.get('text') or item.get('content') or str(item)
                text_parts.append(str(dict_text)[:200])  # Limit each dict to 200 chars
            else:
                text_parts.append(str(item)[:200])
        text = ' '.join(text_parts)
    return str(text)

# Check first hit
h = hits[0]
text = get_text(h)
sentences = re.split(r'[.!?]\s+', text)

print(f"Total sentences in first hit: {len(sentences)}")
print(f"\nFirst 10 sentences:")
for i, sent in enumerate(sentences[:10]):
    print(f"{i}: {sent[:80]}...")
    if any(kw in sent.lower() for kw in ['là', 'được hiểu', 'được gọi', 'có nghĩa']):
        print(f"   ^ Has definition keyword!")
        # Check relevance
        is_relevant = verify_answer_relevance('Quyền sử dụng đất là gì?', sent, hits)
        print(f"   Relevant: {is_relevant}")
        if is_relevant:
            print(f"   ** WOULD RETURN THIS **")
            break
