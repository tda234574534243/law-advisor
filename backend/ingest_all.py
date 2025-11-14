# -*- coding: utf-8 -*-
"""
Ingest all JSON law files found in `scraper/data` and `data` into the DB (Mongo if available, else TinyDB).
After ingesting all files, rebuild TF-IDF (and embeddings if configured).
"""
import sys
from pathlib import Path
import json
import os

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
from config import DATA_DIR, DB_NAME, COLLECTION, MONGO_URI, TINYDB_PATH

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    MONGO_AVAILABLE = True
except Exception:
    MONGO_AVAILABLE = False

from tinydb import TinyDB
from tinydb.storages import JSONStorage

class UTF8Storage(JSONStorage):
    def __init__(self, path, **kwargs):
        kwargs['encoding'] = 'utf-8'
        super().__init__(path, **kwargs)


def load_json(path: Path):
    try:
        txt = path.read_text(encoding='utf-8')
        return json.loads(txt)
    except Exception as e:
        print(f"Skipping {path} (error reading JSON): {e}")
        return None


def ingest_doc(doc: dict, collection=None, tiny_table=None):
    # Normalize document fields
    doc_out = {
        "tieu_de_luat": doc.get('tieu_de_luat') or doc.get('tieu_de') or doc.get('title') or 'Unnamed Law',
        "nguon": doc.get('nguon') or doc.get('url') or '',
        "tong_so_dieu": doc.get('tong_so_dieu') or len(doc.get('noi_dung', [])),
        "thoi_gian_ingest": doc.get('thoi_gian_ingest') or '',
        "noi_dung": doc.get('noi_dung', [])
    }

    if collection is not None:
        try:
            collection.delete_many({"tieu_de_luat": doc_out['tieu_de_luat']})
            collection.insert_one(doc_out)
            return True
        except Exception as e:
            print("Mongo insert error:", e)
            return False
    else:
        try:
            tiny_table.remove(lambda r: r.get('tieu_de_luat') == doc_out['tieu_de_luat'])
            tiny_table.insert(doc_out)
            return True
        except Exception as e:
            print("TinyDB insert error:", e)
            return False


def main():
    scraper_dir = Path(__file__).parent.parent / 'scraper' / 'data'
    data_dir = Path(DATA_DIR)
    files = []
    if scraper_dir.exists():
        files += list(scraper_dir.glob('*.json'))
    if data_dir.exists():
        files += list(data_dir.glob('*.json'))

    # dedupe
    files = sorted(set(files), key=lambda p: str(p))
    if not files:
        print("No JSON files found to ingest.")
        return

    # prepare DB
    collection = None
    tiny_table = None
    if MONGO_AVAILABLE and MONGO_URI:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
            client.server_info()
            db = client[DB_NAME]
            collection = db[COLLECTION]
            print("Using MongoDB for ingest.")
        except Exception as e:
            print("MongoDB not available (will use TinyDB):", e)
            collection = None

    if collection is None:
        tiny_path = TINYDB_PATH or (Path(DATA_DIR) / 'tinydb.json')
        os.makedirs(Path(tiny_path).parent, exist_ok=True)
        tiny_db = TinyDB(tiny_path, storage=UTF8Storage)
        tiny_table = tiny_db.table('laws')
        print(f"Using TinyDB for ingest: {tiny_path}")

    processed = 0
    for f in files:
        d = load_json(f)
        if not d:
            continue
        # If file contains a list of documents, ingest each
        if isinstance(d, list):
            any_ok = False
            for item in d:
                if isinstance(item, dict):
                    ok = ingest_doc(item, collection=collection, tiny_table=tiny_table)
                    any_ok = any_ok or ok
            if any_ok:
                print(f"Ingested list file: {f}")
                processed += 1
            else:
                print(f"No suitable docs found in list file: {f}")
        elif isinstance(d, dict):
            ok = ingest_doc(d, collection=collection, tiny_table=tiny_table)
            if ok:
                print(f"Ingested: {f}")
                processed += 1
        else:
            print(f"Skipping {f}: unexpected JSON root type: {type(d)}")

    print(f"Ingested {processed}/{len(files)} files.")

    # Rebuild index once
    print("Rebuilding TF-IDF index...")
    try:
        from backend.indexer import build_tfidf, build_embeddings
        build_tfidf()
        print("TF-IDF rebuild done.")
        if os.getenv('USE_EMBEDDINGS', 'False').lower() in ('true', '1', 'yes'):
            try:
                build_embeddings()
                print('Embeddings rebuild done.')
            except Exception as e:
                print('Embeddings rebuild failed:', e)
    except Exception as e:
        print('Error rebuilding index:', e)

    print('All done.')

if __name__ == '__main__':
    main()
