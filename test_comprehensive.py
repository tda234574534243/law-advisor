#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'c:\Users\admin\Desktop\PhapLuatProject')

from backend.bot import answer_question

# Test 1: Definition query (missing definition)
print("=== TEST 1: Definition Query (Missing) ===")
result = answer_question('Quyền sử dụng đất là gì?')
print(f"Confidence: {result.get('confidence')}")
print(f"Has warning: {'⚠️' in result.get('answer', '')}")
print(f"Answer preview: {result.get('answer', '')[:200]}\n")

# Test 2: Article query
print("=== TEST 2: Article Query ===")
result = answer_question('Điều 1 nói về cái gì?')
print(f"Confidence: {result.get('confidence')}")
print(f"Has warning: {'⚠️' in result.get('answer', '')}")
print(f"Answer preview: {result.get('answer', '')[:200]}\n")

# Test 3: Procedure query
print("=== TEST 3: Procedure Query ===")
result = answer_question('Thủ tục cấp giấy phép xây dựng như thế nào?')
print(f"Confidence: {result.get('confidence')}")
print(f"Has warning: {'⚠️' in result.get('answer', '')}")
print(f"Answer preview: {result.get('answer', '')[:200]}\n")

# Test 4: General question
print("=== TEST 4: General Question ===")
result = answer_question('Luật đất đai năm 2024 có gì mới?')
print(f"Confidence: {result.get('confidence')}")
print(f"Has warning: {'⚠️' in result.get('answer', '')}")
print(f"Answer preview: {result.get('answer', '')[:200]}\n")
