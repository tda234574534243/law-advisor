#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'c:\Users\admin\Desktop\PhapLuatProject')

from backend.bot import answer_question, detect_intent, retrieve, compose_answer, calculate_confidence

q = 'Quyền sử dụng đất là gì?'

# Step 1: Check intent
intent = detect_intent(q)
print(f"1. Intent: {intent}")

# Step 2: Get hits
hits = retrieve(q, k=5, mode='keyword')
print(f"2. Retrieved {len(hits)} hits")
if hits:
    print(f"   Top hit score: {hits[0].get('score', 'N/A')}")

# Step 3: Calculate confidence
scores = [h.get('score', 0) for h in hits]
conf_level, conf_score = calculate_confidence(scores, q, hits)
print(f"3. Initial confidence: {conf_level} ({conf_score})")

# Step 4: Compose answer
if hits:
    answer, updated_conf = compose_answer(intent, hits, q, conf_level)
    print(f"4. Updated confidence after compose: {updated_conf}")
    print(f"   Answer has warning: {'⚠️' in answer}")
    print(f"\nAnswer start:")
    print(answer[:300])
