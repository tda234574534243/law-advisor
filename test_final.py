#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'c:\Users\admin\Desktop\PhapLuatProject')

from backend.bot import answer_question

try:
    result = answer_question('Quyền sử dụng đất là gì?')
    print(f"✓ Query executed successfully")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    print(f"Has warning: {'⚠️' in result.get('answer', '')}")
    print(f"\nAnswer preview:")
    print(result.get('answer', '')[:400])
except Exception as e:
    import traceback
    print(f"✗ Error: {e}")
    traceback.print_exc()
