# file: backend/search_engine.py
"""
search_engine.py - Tìm kiếm văn bản pháp luật theo từ khóa, TF-IDF hoặc ngữ nghĩa
Tự động đồng bộ với cấu hình trong .env và ingest.py
"""

import os
import re
import json
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from config import TINYDB_PATH, DATA_DIR, MONGO_URI, DB_NAME, COLLECTION, DEFAULT_LANGUAGE

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    USE_MONGO = True
except ImportError:
    USE_MONGO = False

# ===== LOAD CONFIG =====
load_dotenv()

# Ensure path defaults
DATA_DIR = DATA_DIR or os.getenv("DATA_DIR", "data")
TINYDB_PATH = TINYDB_PATH or os.path.join(DATA_DIR, "tinydb.json")
MONGO_URI = MONGO_URI or os.getenv("MONGO_URI")
DB_NAME = DB_NAME or os.getenv("MONGO_DB", "phapluat")
COLLECTION = COLLECTION or os.getenv("MONGO_COLLECTION", "laws")
DEFAULT_LANGUAGE = DEFAULT_LANGUAGE or os.getenv("DEFAULT_LANGUAGE", "english")


# ===================== HELPER =====================
def normalize_text(text: str):
    """Chuẩn hóa text để tìm kiếm: bỏ dấu câu, viết thường"""
    if not text:
        return ""
    # Try to use pyvi ViTokenizer for better Vietnamese tokenization if available
    try:
        from pyvi import ViTokenizer
        tokenized = ViTokenizer.tokenize(text)
        # remove punctuation and lower
        return re.sub(r"[^\w\s]", "", tokenized.lower())
    except Exception:
        # fallback: remove punctuation and lowercase
        return re.sub(r"[^\w\s]", "", text.lower())


def connect_mongo():
    """Kết nối MongoDB"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # Use the configured DB_NAME and COLLECTION variables
        db = client[DB_NAME]
        col = db[COLLECTION]
        client.admin.command("ping")
        return col
    except Exception as e:
        print(f"⚠️ MongoDB không khả dụng ({e}), fallback TinyDB.")
        return None


# ===================== SEARCH CORE =====================
def search_keyword(query, limit=10):
    """Tìm kiếm theo từ khóa trong Mongo hoặc TinyDB"""
    q_norm = normalize_text(query)
    mongo_col = connect_mongo()

    # --- MongoDB search ---
    if mongo_col is not None:   # <-- sửa ở đây
        try:
            results = mongo_col.find(
                {"$text": {"$search": q_norm}},
                {"score": {"$meta": "textScore"}, "_id": 0}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            return list(results)
        except PyMongoError as e:
            print("⚠️ Mongo search error:", e)

    # --- Fallback TinyDB search (use unified TINYDB_PATH with UTF-8) ---
    from tinydb.storages import JSONStorage

    class UTF8Storage(JSONStorage):
        def __init__(self, path, **kwargs):
            kwargs['encoding'] = 'utf-8'
            super().__init__(path, **kwargs)

    db = TinyDB(TINYDB_PATH, storage=UTF8Storage)
    table = db.table("laws")
    q = Query()
    data = table.all()
    results = []

    for item in data:
        text = " ".join(
            [item.get("tieu_de_luat", ""), json.dumps(item.get("noi_dung", ""), ensure_ascii=False)]
        )
        if q_norm in normalize_text(text):
            results.append(item)
            if len(results) >= limit:
                break

    return results
# ===================== ADVANCED RETRIEVAL (TF-IDF / Embeddings) =====================
def retrieve(query, k=10, mode=None):
    """
    Hàm trung tâm: thử tìm theo embeddings (nếu có),
    rồi TF-IDF, cuối cùng fallback về keyword.
    """
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        import joblib
        import numpy as np
    except ImportError:
        return search_keyword(query, k)

    # Đường dẫn model
    TFIDF_PATH = os.path.join(DATA_DIR, "tfidf.joblib")
    EMB_PATH = os.path.join(DATA_DIR, "embeddings.joblib")

    # If mode requests article search, try fast article lookup
    if mode and str(mode).lower() in ("article", "by_article", "dieu"):
        # try to extract article number
        m = re.search(r"\b[Đd]i[eê]u\s*\.?\s*(\d+)\b", query)
        if m:
            article_no = m.group(1)
            # scan passages/docs for 'Điều {n}'
            passages = fetch_all_passages() if 'fetch_all_passages' in globals() else []
            res = []
            for p in passages:
                sec = (p.get('section') or '') + ' ' + (p.get('title') or '')
                if f"Điều {article_no}" in sec or f"Điều{article_no}" in sec:
                    p['score'] = 1.0
                    res.append(p)
            if res:
                return res[:k]
    # Ưu tiên semantic search
    if os.path.exists(EMB_PATH):
        try:
            from sentence_transformers import SentenceTransformer
            emb_vecs, docs = joblib.load(EMB_PATH)
            model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            q_emb = model.encode([query], convert_to_numpy=True)
            sims = cosine_similarity(q_emb, emb_vecs)[0]
            idxs = np.argsort(-sims)[:k]
            return [{"score": float(sims[i]), **docs[i]} for i in idxs if sims[i] > 0.1]
        except Exception as e:
            print("⚠️ Semantic retrieval error:", e)

    # TF-IDF search (improved ranking with keyword matching)
    if os.path.exists(TFIDF_PATH):
        try:
            vec, X, docs = joblib.load(TFIDF_PATH)
            qv = vec.transform([query])
            scores = (X @ qv.T).toarray().ravel()
            # Normalize TF-IDF scores
            if scores.max() > 0:
                norm_scores = scores / (scores.max() + 1e-12)
            else:
                norm_scores = scores

            # compute keyword-match score to boost exact matches
            q_norm = normalize_text(query)
            q_tokens = set(q_norm.split())

            ranked = []
            for i, s in enumerate(norm_scores):
                if s <= 0:
                    continue
                doc = docs[i].copy()
                text = (doc.get('text') or '')
                text_norm = normalize_text(text)
                text_tokens = set(text_norm.split())
                # fraction of query tokens present in doc
                if q_tokens:
                    match_frac = sum(1 for t in q_tokens if t in text_tokens) / len(q_tokens)
                else:
                    match_frac = 0.0
                # final score: weighted sum (70% tfidf + 30% match)
                final_score = 0.7 * float(s) + 0.3 * float(match_frac)
                doc['score'] = float(final_score)
                ranked.append((final_score, doc))

            ranked.sort(key=lambda x: x[0], reverse=True)
            res = [d for _, d in ranked[:k]]
            if res:
                return res
        except Exception as e:
            print("⚠️ TF-IDF retrieval error:", e)

    # Fallback: support mode-specific fallback
    if mode and str(mode).lower() in ("keyword", "by_keyword"):
        return search_keyword(query, k)
    # default fallback
    return search_keyword(query, k)


# ===================== TEST =====================
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 KIỂM TRA SEARCH ENGINE (theo .env)")
    print("=" * 60)
    q = "chuyển nhượng quyền sử dụng đất"
    results = retrieve(q, k=5)
    print(f"Tìm thấy {len(results)} kết quả cho truy vấn: '{q}'")
    for r in results[:3]:
        print("-", r.get("tieu_de_luat", r.get("title", "")))