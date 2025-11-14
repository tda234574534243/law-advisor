# file: backend/db.py
from pymongo import MongoClient, TEXT
from tinydb import TinyDB
from config import MONGO_URI, DB_NAME, COLLECTION
import os
import atexit

USE_MONGO = True
client = None
coll = None
db_tiny = None


def ensure_connection():
    """Lazily initialize MongoDB client and collection or fallback to TinyDB."""
    global client, coll, db_tiny, USE_MONGO
    if client is not None or db_tiny is not None:
        return

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.server_info()  # Kiểm tra kết nối
        db = client[DB_NAME]
        coll = db[COLLECTION]

        # --- Xử lý index MongoDB text ---
        try:
            for idx in coll.list_indexes():
                if idx.get("name") in ["text_text_title_text", "law_text_index"]:
                    coll.drop_index(idx["name"]) if idx.get("name") else None
            coll.create_index(
                [("tieu_de_luat", TEXT),
                 ("noi_dung.tieu_de", TEXT),
                 ("noi_dung.noi_dung", TEXT)],
                name="text_text_title_text",
                default_language='english'
            )
            print("✅ Text index created.")
        except Exception as e:
            print("⚠️ MongoDB index error:", e)

        print("✅ Connected to MongoDB:", DB_NAME, "/", COLLECTION)

    except Exception as e:
        print("⚠️ MongoDB not available, falling back to TinyDB:", e)
        USE_MONGO = False
        os.makedirs("data", exist_ok=True)
        db_tiny = TinyDB("data/tinydb.json")


def close_client():
    """Close the MongoClient if it was created."""
    global client
    try:
        if client is not None:
            client.close()
    except Exception:
        pass
    finally:
        client = None


# Ensure client is closed on process exit
atexit.register(close_client)


def insert_passage(p):
    """Insert một đoạn luật."""
    ensure_connection()
    if USE_MONGO and coll is not None:
        coll.insert_one(p)
    else:
        db_tiny.insert(p)


def find_by_id(_id):
    ensure_connection()
    if USE_MONGO and coll is not None:
        return coll.find_one({"_id": _id})
    else:
        from tinydb import where
        return db_tiny.search(where("doc_id") == _id)


def text_search(query, limit=10):
    """Search theo keyword."""
    ensure_connection()
    if USE_MONGO and coll is not None:
        cursor = coll.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        return list(cursor)
    else:
        from tinydb import where
        results = db_tiny.search(where("text").test(lambda t: query.lower() in t.lower()))
        return results[:limit]
