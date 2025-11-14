# 🔍 Search Module

Multi-tier search pipeline for law documents.

## Overview

The search system uses a three-tier approach:

1. **Semantic Search** (Embeddings) - If enabled
   - Uses sentence-transformers
   - Best for meaning-based queries

2. **TF-IDF Ranking** (Default)
   - Fast and efficient
   - Good quality results
   - With keyword matching boost

3. **Keyword Fallback**
   - Simple string matching
   - Fast
   - Works without indexes

## Configuration

Enable/disable in `config.py`:

```python
USE_EMBEDDINGS = True/False
TOP_K = 5  # Number of results

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

## Usage

### Basic Search

```python
from backend.search import retrieve

# Auto-mode (embeddings -> TF-IDF -> keyword)
results = retrieve("chuyển nhượng quyền sử dụng đất", k=5)

# Specific mode
results = retrieve(query, k=5, mode="keyword")
results = retrieve(query, k=5, mode="article")
```

### Response Format

```python
results = [{
    "title": "Điều 69 - Bồi thường",
    "section": "Chương V",
    "text": "...",
    "score": 0.85,
    "url": "http://...",
    "noi_dung": [...]  # Raw content
}]
```

## Query Types

### Article Query
```python
retrieve("Điều 69", mode="article")
# Direct article lookup
# Finds documents with "Điều 69"
```

### Keyword Query
```python
retrieve("phạt tiền vi phạm", mode="keyword")
# Search by keywords
# Good for general questions
```

### Semantic Query
```python
retrieve("Những quy định về quyền sử dụng đất", mode="semantic")
# Meaning-based search
# Best for complex questions
```

## Building Indexes

### TF-IDF Index

```bash
python backend/indexer.py
```

Creates `data/tfidf.joblib` containing:
- Vectorizer
- TF-IDF matrix
- Document list

### Semantic Embeddings

```bash
# Enable in config.py
USE_EMBEDDINGS = True

# Build index
python backend/indexer.py
```

Creates `data/embeddings.joblib` containing:
- Pre-computed embeddings
- Document list

## Search Pipeline

### TF-IDF + Keyword Matching

```python
# In retrieve() function:

1. Normalize query
2. Transform with TF-IDF vectorizer
3. Compute cosine similarity
4. Normalize TF-IDF scores
5. Compute keyword match fraction
6. Combine scores: 70% TF-IDF + 30% keyword match
7. Sort and return top K
```

### Semantic Search

```python
1. Encode query with sentence-transformers
2. Compute cosine similarity with embeddings
3. Filter by threshold (0.1)
4. Return top K
```

## Advanced Features

### Article-Specific Search

For queries mentioning specific article numbers:

```python
retrieve("Điều 69", mode="article")
# Automatically extracts article number
# Searches section/title fields
# Returns exact matches first
```

### Keyword Normalization

Vietnamese text normalization:

```python
# Using pyvi if available:
text = "chuyển nhượng quyền sử dụng đất"
normalized = normalize_text(text)
# Returns: "chuyến nhượng quyền sử dụng đất" (tokenized)
```

### Query Expansion

Using learned synonyms:

```python
# From learning_engine
synonyms = learning_engine.get_synonyms("đất")
# ["mảnh đất", "thửa đất", "bất động sản"]
# Query is expanded with synonyms
```

## Performance Optimization

### Caching

```python
# Frequently used queries are cached
# Cache invalidation on index rebuild
```

### Batch Search

```python
# Search multiple queries efficiently
queries = ["quyền sử dụng", "phạt tiền", "bồi thường"]
for q in queries:
    results = retrieve(q, k=3)
```

### Index Preloading

```python
# Load indexes once on startup
# Subsequent searches are faster
# Handled automatically by search.py
```

## Troubleshooting

### No Results

```python
# 1. Check if index exists
# 2. Try keyword mode: retrieve(q, mode="keyword")
# 3. Check data is ingested: backend/ingest.py
# 4. Rebuild index: python backend/indexer.py
```

### Low Scores

```python
# 1. Try semantic search if enabled
# 2. Use simpler keywords
# 3. Check article number format (Điều 69 vs Diều 69)
# 4. Add learned synonyms
```

### Slow Queries

```python
# 1. Reduce TOP_K in config.py
# 2. Use keyword mode (faster)
# 3. Rebuild TF-IDF index
# 4. Enable embeddings caching
```

## File Structure

```
data/
├── tinydb.json           # Local database
├── tfidf.joblib          # TF-IDF model & matrix
├── embeddings.joblib     # Embeddings (if enabled)
└── tinydb_index/         # Optional TinyDB indexes
```

## API Integration

### Flask Endpoint

```python
# app.py
@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    q = data.get("q", "")
    k = data.get("k", TOP_K)
    mode = data.get("mode", None)
    
    hits = retrieve(q, k=int(k), mode=mode)
    # Format and return results
```

### Request

```bash
POST /api/search
{
  "q": "quyền sử dụng đất",
  "k": 5,
  "mode": "auto"  # or "keyword", "article", "semantic"
}
```

### Response

```json
{
  "query": "quyền sử dụng đất",
  "results": [
    {
      "title": "Điều 69",
      "section": "Chương V",
      "text": "...",
      "score": 0.85,
      "url": "http://..."
    }
  ]
}
```

## Configuration

### config.py

```python
# Search parameters
TOP_K = 5                  # Default results
USE_EMBEDDINGS = False     # Enable semantic search
EMBEDDING_MODEL = "..."    # Model name
DEFAULT_LANGUAGE = "english"

# Database
MONGO_URI = "..."
DB_NAME = "phapluat"
TINYDB_PATH = "data/tinydb.json"
```

### .env

```
USE_EMBEDDINGS=false
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
TOP_K=5
```

## Performance Metrics

| Metric | Value |
|--------|-------|
| Query time (TF-IDF) | ~50ms |
| Query time (Semantic) | ~100ms |
| Index size (TF-IDF) | ~5MB |
| Index size (Embeddings) | ~50MB |
| Memory (loaded) | ~100MB |

## Future Improvements

- [ ] Query expansion with thesaurus
- [ ] Faceted search by document type
- [ ] Spell correction for queries
- [ ] Recent query caching
- [ ] A/B testing for ranking algorithms
- [ ] User feedback integration for ranking

---

**Version 2.0 | Search Module**
