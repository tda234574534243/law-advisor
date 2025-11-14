import sys, os, json
sys.path.insert(0, '.')

from config import DATA_DIR, TINYDB_PATH
from backend import indexer

print('Running index checks...')

passages = indexer.fetch_all_passages()
print('Passages fetched:', len(passages))
for i, p in enumerate(passages[:8], 1):
    print(f'--#{i} doc_id={p.get("doc_id")} section={p.get("section")}')
    t = p.get('text') or ''
    print('   text preview:', (t[:200] + '...') if len(str(t))>200 else t)

tfidf_path = os.path.join(DATA_DIR, 'tfidf.joblib')
if os.path.exists(tfidf_path):
    try:
        import joblib
        import numpy as np
        vec, X, docs = joblib.load(tfidf_path)
        print('Loaded TF-IDF: docs=', len(docs), 'matrix shape=', X.shape)

        queries = [
            'Quyền sử dụng đất là gì?',
            'Thủ tục mua đất cần gì?',
            'Điều 3 định nghĩa gì'
        ]
        for q in queries:
            qv = vec.transform([q])
            scores = (X @ qv.T).toarray().ravel()
            if scores.max() > 0:
                idxs = (-scores).argsort()[:5]
            else:
                idxs = (-scores).argsort()[:5]
            print('\nQuery:', q)
            for rank,i in enumerate(idxs,1):
                print(f' {rank}. score={float(scores[i]):.4f} title={docs[i].get("title")[:60]} section={docs[i].get("section")}')
    except Exception as e:
        print('Error loading TF-IDF:', e)
else:
    print('TF-IDF file not found at', tfidf_path)

# Show tinydb sample
try:
    tiny_path = TINYDB_PATH or os.path.join('data','tinydb.json')
    if os.path.exists(tiny_path):
        with open(tiny_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print('\nTinyDB entries (sample):', len(data) if isinstance(data, list) else 'unknown')
        if isinstance(data, list):
            for d in data[:3]:
                print(' - title:', d.get('tieu_de_luat') or d.get('title'))
                print('   keys:', list(d.keys()))
    else:
        print('TinyDB file not found:', tiny_path)
except Exception as e:
    print('Error reading tinydb:', e)

print('\nCheck complete')
