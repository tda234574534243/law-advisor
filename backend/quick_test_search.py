# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Ensure project root is on sys.path so `backend` package can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from backend import search


if __name__ == '__main__':
    q = 'quyền sử dụng đất'
    res = search.retrieve(q, k=5)
    print('Results:', len(res))
    for r in res[:5]:
        print('---')
        print('score:', r.get('score'))
        print('title:', r.get('title'))
        print('section:', r.get('section'))
        txt = r.get('text')
        print('text sample:', str(txt)[:300])
