# file: backend/indexer.py
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from config import DATA_DIR, EMBEDDING_MODEL, USE_EMBEDDINGS
import numpy as np
import json
os.makedirs(DATA_DIR, exist_ok=True)


def fetch_all_passages():
    """Return a list of normalized passages for indexing.

    Handles both MongoDB and TinyDB backends. Supports documents where
    `noi_dung` is a list of strings or a list of dicts (with keys like
    'noi_dung', 'dieu_so_phu', 'dieu_so', 'tieu_de'). Skips empty texts.
    """
    passages = []
    # Lazy import backend.db to ensure connection logic runs
    try:
        from backend import db as backend_db
        backend_db.ensure_connection()
        USE_MONGO = getattr(backend_db, 'USE_MONGO', False)
        coll = getattr(backend_db, 'coll', None)
    except Exception:
        USE_MONGO = False
        coll = None

    raw_docs = []
    if USE_MONGO and coll is not None:
        try:
            raw_docs = list(coll.find({}))
        except Exception:
            raw_docs = []
    if not raw_docs:
        # Fallback to TinyDB with UTF-8 storage
        from tinydb import TinyDB
        from tinydb.storages import JSONStorage

        class UTF8Storage(JSONStorage):
            def __init__(self, path, **kwargs):
                kwargs['encoding'] = 'utf-8'
                super().__init__(path, **kwargs)

        dbt = TinyDB('data/tinydb.json', storage=UTF8Storage)
        raw_docs = dbt.all()

    # Normalize raw_docs into a list of passages (one per article/section)
    for doc in raw_docs:
        if not isinstance(doc, dict):
            continue

        # If document already looks like a passage
        if 'text' in doc and isinstance(doc.get('text'), str):
            if doc['text'].strip():
                passages.append(doc)
            continue

        title_luat = doc.get('tieu_de_luat') or doc.get('title') or doc.get('tieu_de') or ''
        nguon = doc.get('nguon') or doc.get('url') or ''
        noi_dung = doc.get('noi_dung') or []

        if isinstance(noi_dung, list):
            for i, art in enumerate(noi_dung, start=1):
                # art can be a dict (with 'noi_dung') or a plain string
                if isinstance(art, dict):
                    text = art.get('noi_dung') or art.get('text') or ''
                    # Build a human-friendly section label
                    sec_parts = []
                    if doc.get('dieu_so'):
                        sec_parts.append(f"Điều {doc.get('dieu_so')}")
                    if art.get('dieu_so_phu'):
                        sec_parts.append(str(art.get('dieu_so_phu')))
                    section = art.get('tieu_de') or ' '.join(sec_parts) or f'Doạn {i}'
                else:
                    text = str(art)
                    section = f'Doạn {i}'

                if not text or not str(text).strip():
                    continue

                passages.append({
                    'doc_id': f"{title_luat}#{doc.get('dieu_so', i)}#{i}",
                    'title': title_luat,
                    'section': section,
                    'text': str(text),
                    'url': nguon
                })
        else:
            # fallback: store doc as a single passage
            text = json.dumps(doc, ensure_ascii=False)
            passages.append({
                'doc_id': doc.get('doc_id') or doc.get('_id') or title_luat,
                'title': title_luat,
                'section': '',
                'text': text,
                'url': nguon
            })

    return passages


def build_tfidf():
    docs = fetch_all_passages()
    texts = [d.get('text', '') for d in docs if d.get('text') and len(str(d.get('text')).strip()) > 3]
    if not texts:
        raise ValueError("No text documents available for TF-IDF indexing.")

    # Use a token pattern that includes unicode word characters to handle Vietnamese
    vec = TfidfVectorizer(max_df=0.85, min_df=1, ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b")
    X = vec.fit_transform(texts)
    joblib.dump((vec, X, docs), os.path.join(DATA_DIR, "tfidf.joblib"))
    print("TF-IDF index built.")


def build_embeddings():
    if not USE_EMBEDDINGS:
        print("Embeddings disabled in config.")
        return
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print("SentenceTransformer not available:", e)
        return
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
