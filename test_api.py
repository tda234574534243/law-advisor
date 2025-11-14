#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

url = "http://127.0.0.1:8000/api/chat"
payload = {
    "q": "Quyền sử dụng đất là gì?",
    "user_id": "test_user"
}

response = requests.post(url, json=payload)
result = response.json()

print("=" * 60)
print("RESPONSE FROM API:")
print("=" * 60)
print(f"Confidence: {result.get('confidence', 'N/A')}")
print(f"\nAnswer:")
print(result.get('answer', 'N/A'))
print("\n" + "=" * 60)
