# file: backend/indexer.py
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.db import coll, USE_MONGO
from config import DATA_DIR, EMBEDDING_MODEL, USE_EMBEDDINGS
import numpy as np
import json
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_all_passages():
    passages = []
    if USE_MONGO:
        from backend.db import coll
        raw_docs = list(coll.find({}))
    else:
        from tinydb import TinyDB
        dbt = TinyDB('data/tinydb.json')
        raw_docs = dbt.all()

    # Normalize raw_docs into a list of passages (one per article/section)
    for doc in raw_docs:
        # if doc already looks like a passage (has 'text'), keep it
        if isinstance(doc, dict) and 'text' in doc:
            passages.append(doc)
            continue

        # if doc looks like a law document with 'noi_dung' list, expand
        title_luat = doc.get('tieu_de_luat') or doc.get('title') or ''
        nguon = doc.get('nguon') or doc.get('url') or ''
        noi_dung = doc.get('noi_dung') or []
        if isinstance(noi_dung, list):
            for i, art in enumerate(noi_dung, start=1):
                text = art.get('noi_dung') if isinstance(art, dict) else str(art)
                section = art.get('tieu_de') if isinstance(art, dict) else f'Doạn {i}'
                passages.append({
                    'doc_id': f"{title_luat}#{i}",
                    'title': title_luat,
                    'section': section,
                    'text': text,
                    'url': nguon
                })
        else:
            # fallback: store doc as a single passage
            passages.append({
                'doc_id': doc.get('doc_id') or doc.get('_id') or title_luat,
                'title': title_luat,
                'section': '',
                'text': json.dumps(doc, ensure_ascii=False),
                'url': nguon
            })

    return passages

def build_tfidf():
    docs = fetch_all_passages()
    texts = [d['text'] for d in docs]
    vec = TfidfVectorizer(max_df=0.85, min_df=1, ngram_range=(1,2))
    X = vec.fit_transform(texts)
    joblib.dump((vec, X, docs), os.path.join(DATA_DIR, "tfidf.joblib"))
    print("TF-IDF index built.")

def build_embeddings():
    if not USE_EMBEDDINGS:
        print("Embeddings disabled in config.")
        return
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    docs = fetch_all_passages()
    texts = [d['text'] for d in docs]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    joblib.dump((embeddings, docs), os.path.join(DATA_DIR, "embeddings.joblib"))
    # optional: build faiss index (if faiss installed)
    try:
        import faiss
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        faiss.write_index(index, os.path.join(DATA_DIR, "faiss.index"))
        print("Faiss index built.")
    except Exception as e:
        print("Faiss not available:", e)
    print("Embeddings built.")

if __name__ == "__main__":
    build_tfidf()
    if USE_EMBEDDINGS:
        build_embeddings()
