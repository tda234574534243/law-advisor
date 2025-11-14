# Data

Persistent data used by the system.

Files of interest
- `tinydb.json` (or `laws_tinydb.json`) — TinyDB fallback storage. Configurable via `TINYDB_PATH` in `.env` / `config.py`.
- `tfidf.joblib` — serialized TF‑IDF vectorizer & matrix created by `backend/indexer.py`.
- `embeddings.joblib` (optional) — serialized embedding vectors if embeddings are enabled.
- `law_database.txt` — human-readable export of processed law passages (optional).

Notes
- TinyDB files are read/written using UTF‑8 storage wrappers to support Vietnamese characters.
- Do not print large JSON blobs to the console during production runs — long prints can crash consoles or flood logs.
