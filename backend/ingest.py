# -*- coding: utf-8 -*-
"""
Ingest a specific JSON law file (scraper/data/văn_bản_pháp_luật_2024.json)
into MongoDB if available, otherwise into TinyDB.
Also rebuilds TF-IDF index after ingest.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ensure project root on sys.path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
from config import DATA_DIR, LAW_FILE, TINYDB_PATH, MONGO_URI, DB_NAME, COLLECTION

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    MONGO_AVAILABLE = True
except Exception:
    MONGO_AVAILABLE = False

# target file
LAW_FILE = LAW_FILE or "văn_bản_pháp_luật_2024.json"
scraper_dir = Path(__file__).parent.parent / 'scraper' / 'data'
src = scraper_dir / LAW_FILE
if not src.exists():
    # fallback: pick first JSON in scraper/data
    candidates = list(scraper_dir.glob('*.json'))
    if candidates:
        # Prefer filenames that look like laws
        preferred = [c for c in candidates if any(x in c.name.lower() for x in ('luat', 'phap', 'văn', 'van'))]
        if preferred:
            src = preferred[0]
        else:
            src = candidates[0]
        print(f"LAW_FILE not found; using scraper JSON: {src}")
    else:
        print(f"Source not found: {src}")
        raise SystemExit(1)

print(f"Reading law file: {src}")
text = src.read_text(encoding='utf-8')
data = json.loads(text)

# Prepare document
doc = {
    "tieu_de_luat": data.get('tieu_de_luat') or data.get('tieu_de') or data.get('title') or 'Unnamed Law',
    "nguon": data.get('nguon') or data.get('url') or '',
    "tong_so_dieu": data.get('tong_so_dieu') or len(data.get('noi_dung', [])),
    "thoi_gian_ingest": datetime.now().isoformat(),
    "noi_dung": data.get('noi_dung', [])
}

# Try MongoDB
if MONGO_AVAILABLE and MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client[DB_NAME]
        col = db[COLLECTION]
        # Remove old versions
        col.delete_many({"tieu_de_luat": doc['tieu_de_luat']})
        col.insert_one(doc)
        print(f"Inserted into MongoDB: {DB_NAME}.{COLLECTION}")
    except Exception as e:
        print("MongoDB not available or error:", e)
        MONGO_AVAILABLE = False

if not MONGO_AVAILABLE:
    # Write to TinyDB fallback
    from tinydb import TinyDB
    from tinydb.storages import JSONStorage

    class UTF8Storage(JSONStorage):
        def __init__(self, path, **kwargs):
            kwargs['encoding'] = 'utf-8'
            super().__init__(path, **kwargs)

    os.makedirs(DATA_DIR, exist_ok=True)
    tiny_path = TINYDB_PATH or os.path.join(DATA_DIR, "tinydb.json")
    dbt = TinyDB(tiny_path, storage=UTF8Storage)
    table = dbt.table('laws')
    # Remove similar title
    table.remove(lambda r: r.get('tieu_de_luat') == doc['tieu_de_luat'])
    table.insert(doc)
    print(f"Inserted into TinyDB: {tiny_path}")

# Rebuild TF-IDF index
print('Rebuilding TF-IDF index...')
try:
    from backend.indexer import build_tfidf, build_embeddings
    build_tfidf()
    print('TF-IDF rebuild done.')
    if os.getenv('USE_EMBEDDINGS', 'False').lower() in ('true', '1', 'yes'):
        try:
            build_embeddings()
        except Exception as e:
            print('Embeddings rebuild failed:', e)
except Exception as e:
    print('Error rebuilding index:', e)

print('Ingest complete.')
