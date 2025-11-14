"""Backend package exports.

Important: avoid importing modules that have side effects (like `ingest.py`) at
package import time. `ingest.py` performs file I/O and DB writes when imported,
which caused the application to run ingestion automatically when any
`backend` submodule was imported. Keep `ingest` out of top-level imports and
import it explicitly where needed.
"""

from . import search, db, bot, indexer

__all__ = ["search", "db", "bot", "indexer"]
