#file: backend/ingest.py
"""
ingest.py - Đọc dữ liệu Luật vào cơ sở dữ liệu (MongoDB hoặc TinyDB)
Tự động load cấu hình từ file .env
"""

import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from tinydb import TinyDB, Query

# ===== LOAD CONFIG =====
load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "data")
LAW_FILE = os.getenv("LAW_FILE")
TINYDB_PATH = os.getenv("TINYDB_PATH", os.path.join(DATA_DIR, "laws_tinydb.json"))

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "phapluat")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "laws")

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except ImportError:
    MongoClient = None


def ingest_raw_file():
    """Đọc file JSON luật và lưu vào MongoDB hoặc TinyDB"""
    json_path = os.path.join(DATA_DIR, LAW_FILE)
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Không tìm thấy file: {json_path}")

    print(f"[+] Đọc dữ liệu từ: {json_path}")
    text = Path(json_path).read_text(encoding="utf-8")
    data = json.loads(text)

    # Thử dùng MongoDB
    if MongoClient and MONGO_URI:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
            db = client[MONGO_DB]
            col = db[MONGO_COLLECTION]

            # Index text (không dùng ngôn ngữ tiếng Việt)
            col.create_index(
                [("tieu_de_luat", "text"),
                 ("noi_dung.tieu_de", "text"),
                 ("noi_dung.noi_dung", "text")],
                name="law_text_index",
                default_language="none"
            )

            # Xóa bản cũ cùng tên
            col.delete_many({"tieu_de_luat": data["tieu_de_luat"]})

            # Insert mới
            col.insert_one({
                "tieu_de_luat": data["tieu_de_luat"],
                "nguon": data["nguon"],
                "tong_so_dieu": data["tong_so_dieu"],
                "thoi_gian_ingest": datetime.now().isoformat(),
                "noi_dung": data["noi_dung"]
            })

            print(f"[✓] Đã import {data['tieu_de_luat']} vào MongoDB ({MONGO_DB}.{MONGO_COLLECTION})")
            return
        except PyMongoError as e:
            print(f"⚠️ Lỗi MongoDB: {e} — fallback sang TinyDB.")
        except Exception as e:
            print(f"⚠️ Không kết nối được MongoDB: {e}")

    # Fallback sang TinyDB
    os.makedirs(DATA_DIR, exist_ok=True)
    db = TinyDB(TINYDB_PATH, encoding="utf-8")
    table = db.table("laws")

    table.remove(Query().tieu_de_luat == data["tieu_de_luat"])
    table.insert({
        "tieu_de_luat": data["tieu_de_luat"],
        "nguon": data["nguon"],
        "tong_so_dieu": data["tong_so_dieu"],
        "thoi_gian_ingest": datetime.now().isoformat(),
        "noi_dung": data["noi_dung"]
    })

    print(f"[✓] Đã lưu dữ liệu vào TinyDB: {TINYDB_PATH}")


if __name__ == "__main__":
    print("=" * 60)
    print("INGEST LAW DATABASE (from .env config)")
    print("=" * 60)
    try:
        ingest_raw_file()
        print("\n[✔] Hoàn tất ingest dữ liệu.")
    except Exception as e:
        print(f"\n❌ Lỗi ingest: {e}")
    print("=" * 60)
