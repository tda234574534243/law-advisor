# file: backend/run_api_test.py
"""Run quick API tests using Flask test client (no network sockets needed).
This imports `app` from the top-level `app.py` and calls endpoints directly.
"""
import json
from app import app

client = app.test_client()

def test_search(q):
    r = client.post('/api/search', json={'q': q, 'k': 4})
    print('SEARCH status:', r.status_code)
    print(json.dumps(r.get_json(), ensure_ascii=False)[:2000])

def test_chat(q):
    r = client.post('/api/chat', json={'q': q})
    print('\nCHAT status:', r.status_code)
    print(json.dumps(r.get_json(), ensure_ascii=False)[:2000])

if __name__ == '__main__':
    print('Running API tests (Flask test client)')
    test_search('quyền sử dụng đất là gì')
    test_chat('Điều 1')
