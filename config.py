# file: config.py
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "phapluat")
COLLECTION = os.getenv("MONGO_COLLECTION", "laws")

# Fallback TinyDB
# Default to the actual tinydb file present in the workspace
TINYDB_PATH = os.getenv("TINYDB_PATH", "data/tinydb.json")

# Data paths
DATA_DIR = os.getenv("DATA_DIR", "data")
LAW_FILE = os.getenv("LAW_FILE", "luật_đất_đai_2024_số_31_2024_qh15_áp_dụng_năm_2025_mới_nhất.json")

# Server
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Search / AI
USE_EMBEDDINGS = os.getenv("USE_EMBEDDINGS", "False").lower() in ("true", "1", "yes")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K", 5))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "english")
