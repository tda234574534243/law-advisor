# 🏛️ Hệ Thống Tra Cứu Pháp Luật Thông Minh v2.0

**AI-Powered Vietnamese Law Query System with Self-Learning Chatbot**

---

## 🚀 Quick Start (5 phút)

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Test các modules
python tests/test_new_features.py

# 3. Chạy ứng dụng
python app.py

# 4. Mở trình duyệt
# http://localhost:8000
```

---

## 📁 Cấu Trúc Project

```
PhapLuatProject/
├── README.md                    # Main documentation
├── requirements.txt
├── config.py
├── app.py                       # Flask server
│
├── backend/
│   ├── README.md               # Backend documentation (search, db, indexing)
│   ├── bot.py                  # Chatbot engine orchestrator
│   ├── search.py               # Search engine
│   ├── db.py                   # Database layer
│   ├── indexer.py              # TF-IDF indexing
│   └── ingest.py               # Data ingestion
│
├── chatbot/                    # 🆕 Core AI conversation module
│   ├── README.md               # Chatbot documentation
│   ├── learning_engine.py      # Self-learning from user feedback
│   ├── sentiment_analyzer.py   # Emotion & urgency detection
│   ├── conversation_manager.py # Conversation history & context
│   └── nlg_engine.py           # Natural language generation
│
├── scraper/
│   ├── README.md               # Scraper documentation
│   ├── scraper.py              # Web scraper
│   ├── fix_titles.py
│   └── data/                   # Law data files
│
├── search/
│   └── README.md               # Search documentation
│
├── frontend/
│   ├── README.md               # Frontend documentation
│   ├── templates/
│   │   └── index.html          # Web UI
│   └── static/
│       ├── app.js              # Frontend logic
│       └── styles.css          # Styling
│
├── data/
│   ├── tinydb.json             # Local database
│   ├── learned_interactions.json # Bot learning data
│   ├── learned_patterns.json
│   ├── learned_synonyms.json
│   └── conversations/          # Conversation history
│
└── tests/
    └── test_new_features.py
```

---

## 🎯 Modules

### 🤖 Backend (`backend/README.md`)
- **bot.py** - Chatbot engine với NLG + sentiment analysis
- **search.py** - Search pipeline (TF-IDF, embeddings, keyword)
- **learning_engine.py** - Tự học từ feedback người dùng
- **sentiment_analyzer.py** - Phân tích cảm xúc & urgency
- **conversation_manager.py** - Quản lý ngữ cảnh cuộc trò chuyện
- **nlg_engine.py** - Tạo response tự nhiên

### 🔍 Search (`search/README.md`)
- TF-IDF ranking
- Semantic search (embeddings)
- Keyword matching
- Article-specific queries

### 🕷️ Scraper (`scraper/README.md`)
- Web scraping
- Data normalization
- JSON export
- Data ingestion

### 💬 Chatbot
- Retrieval-based QA
- Natural language generation
- Self-learning from feedback
- Sentiment-based tone adjustment

---

## 💡 Tính Năng Chính

### 1. **Tự Học Từ Feedback** 🧠
- User đánh giá (1-5 sao)
- Bot học từ feedback tích cực
- Tái sử dụng câu trả lời tốt
- Quản lý từ đồng nghĩa

### 2. **Trả Lời Tự Nhiên** 🎨
- Paraphrasing (nhiều phiên bản)
- Synonyms replacement
- Emoji & formatting
- Style adjustment (formal/informal)

### 3. **Hiểu Cảm Xúc** 😊
- Sentiment detection (positive/negative/frustrated/urgent)
- Urgency level detection
- Tone adjustment
- Context-aware responses

### 4. **Nhớ Context** 💬
- Conversation history
- Follow-up question understanding
- Topic extraction
- Multi-turn support

---

## 🔌 API Endpoints

```bash
# Chat (with learning)
POST /api/chat
{
  "q": "Quyền sử dụng đất là gì?",
  "session_id": "optional",
  "user_id": "optional"
}

# Submit feedback
POST /api/feedback
{
  "interaction_id": "xxx",
  "rating": 5,
  "feedback": "text"
}

# Get learning stats
GET /api/learning-stats

# Session management
POST /api/session/create
GET /api/session/{id}/stats
GET /api/session/{id}/context
POST /api/export-learned
```

---

## 📊 Learning Flow

```
User Question
    ↓
Bot Search & Answer
    ↓
User Rating (1-5 ⭐)
    ↓
Rating >= 4? → Learn Pattern
    ↓
Similar Question
    ↓
Bot Finds Learned Answer
    ↓
Paraphrase & Respond
```

---

## 🧪 Testing

```bash
# Test all modules
python tests/test_new_features.py

# Expected output:
# ✅ Learning Engine test passed!
# ✅ Sentiment Analyzer test passed!
# ✅ Conversation Manager test passed!
# ✅ NLG Engine test passed!
# ✅ ALL TESTS PASSED!
```

---

## ⚙️ Configuration

Edit `config.py`:

```python
# Server
HOST = "127.0.0.1"
PORT = 8000
DEBUG = True

# Database
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "phapluat"

# Search
TOP_K = 5
USE_EMBEDDINGS = False
```

---

## 📦 Dependencies

```
Flask>=2.2
pymongo>=4.0
scikit-learn
sentence-transformers
tinydb
joblib
pyvi
numpy
```

---

## 📖 Module-Specific Docs

- See `backend/README.md` for backend details
- See `search/README.md` for search configuration
- See `scraper/README.md` for data collection

---

## 🚀 Deployment

```bash
# Production build
export FLASK_ENV=production
python app.py

# Or use gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## 📝 License

MIT License

---

## 👨‍💻 Development

Contributions welcome! Please:
1. Test your changes: `python tests/test_new_features.py`
2. Update module READMEs
3. Submit PR

---

**Version 2.0 | 2025 | AI-Powered Learning Chatbot**
