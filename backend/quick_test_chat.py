# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Ensure project root is on sys.path so `backend` package can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from backend.bot import answer_question

if __name__ == '__main__':
    tests = [
        'Quyền sử dụng đất là gì?',
        'Điều 3 nói gì về định nghĩa?',
        'Những đối tượng được sử dụng đất là ai?',
        'Tôi muốn mua đất, cần những thủ tục gì?'
    ]

    for q in tests:
        print('=' * 60)
        print('Query:', q)
        res = answer_question(q, k=5, session_id=None, user_id='test_user')
        print('Answer (truncated):')
        ans = res.get('answer', '')
        print(ans[:1500])
        print('\nConfidence:', res.get('confidence'))
        print('Sources:', res.get('sources'))
        print('\n')
