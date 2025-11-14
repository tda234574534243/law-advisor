# Chatbot Helpers

Small helper modules used by the chatbot pipeline (learning, sentiment, NLG, conversation state). These modules are not a full LLM but provide lightweight functionality used by `backend.bot`.

Key modules
- `learning_engine.py` — learning storage and simple retrieval of learned answers.
- `sentiment_analyzer.py` — crude sentiment & urgency detection used to adjust tone.
- `nlg_engine.py` — small paraphrasing/emoji utilities.

Usage
- These modules are imported by `backend.bot.answer_question()` and generally require no direct invocation.
# 🤖 Chatbot Module

**Core AI conversation engine with self-learning capabilities**

---

## 📋 Overview

Chatbot module contains the 4 core components that make the bot **intelligent, adaptive, and natural**:

1. **Learning Engine** - Bot learns from user feedback & reuses high-quality answers
2. **Sentiment Analyzer** - Detects emotion & urgency, adjusts tone accordingly
3. **Conversation Manager** - Tracks conversation history & extracts context
4. **NLG Engine** - Generates natural, varied responses (paraphrasing + emoji)

---

## 🧠 Components

### 1. Learning Engine (`learning_engine.py`)

Enables the bot to **improve over time** from user interactions.

**Key Features:**
- Records Q&A pairs with metadata (sources, timestamps, user_id)
- Processes user feedback (1-5 star ratings)
- Finds similar learned questions using Jaccard similarity (threshold: 0.3)
- Extracts patterns from high-quality answers (rating ≥ 4)
- Stores learned synonyms for better matching

**Main Methods:**

```python
from chatbot.learning_engine import get_learning_engine

engine = get_learning_engine()

# Record interaction
interaction_id = engine.record_interaction(
    question="Quyền sử dụng đất là gì?",
    answer="Quyền sử dụng đất là...",
    sources=["http://example.com/law"],
    user_id="user123"
)

# Submit feedback (1-5 stars)
engine.submit_feedback(interaction_id, rating=5)

# Find similar learned answers
learned_answers = engine.find_similar_learned_answers("quyền đất")

# Get learning statistics
stats = engine.get_learning_stats()
# Returns: {'total_interactions': 10, 'avg_rating': 4.2, 'learned_patterns': 5}
```

**Data Storage:**
- `data/learned_interactions.json` - All recorded Q&A pairs
- `data/learned_patterns.json` - Extracted patterns from high-quality answers
- `data/learned_synonyms.json` - Word synonyms learned from interactions

---

### 2. Sentiment Analyzer (`sentiment_analyzer.py`)

Detects **5 sentiment types** and **4 urgency levels** to adjust response tone.

**Key Features:**
- Analyzes text for 5 sentiment types:
  - ✅ POSITIVE (positive keywords: "cảm ơn", "tuyệt vời")
  - ❌ NEGATIVE (negative keywords: "xấu", "tồi tệ")
  - 😐 NEUTRAL (balanced, factual)
  - 😤 FRUSTRATED (confused/annoyed: "tại sao", "không hiểu")
  - 🚨 URGENT (critical needs: "gấp", "khẩn cấp")

- Analyzes urgency levels:
  - LOW (non-urgent)
  - MEDIUM (normal)
  - HIGH (time-sensitive)
  - CRITICAL (emergency)

- Detects follow-up questions & context type (general/specific)

**Main Methods:**

```python
from chatbot.sentiment_analyzer import get_sentiment_analyzer

analyzer = get_sentiment_analyzer()

# Analyze sentiment & urgency
sentiment, confidence = analyzer.analyze_sentiment("Tại sao luật này lại như vậy?")
# Returns: ("FRUSTRATED", 0.85)

urgency, confidence = analyzer.analyze_urgency("Tôi cần giải quyết việc này gấp!")
# Returns: ("CRITICAL", 0.9)

# Get response tone configuration
tone = analyzer.get_response_tone("FRUSTRATED", "HIGH")
# Returns: {
#     'greeting': "Mình hiểu bạn đang lo lắng. ",
#     'prefix': "Mình sẽ cố gắng giải thích rõ ràng: ",
#     'suffix': "\nNếu còn thắc mắc, hãy hỏi thêm nhé!",
#     'formality': 'warm'
# }

# Check if follow-up
is_followup = analyzer.is_follow_up_question("Vậy làm sao để xin giấy phép?")
# Returns: True
```

**Sentiment Configuration:**
Each sentiment×urgency combination has a custom tone configuration (greeting, prefix, suffix, formality level).

---

### 3. Conversation Manager (`conversation_manager.py`)

Manages **conversation sessions** with history tracking and context extraction.

**Key Features:**
- Creates unique sessions with UUID
- Stores message history (user → bot exchanges)
- Extracts last N messages for context
- Detects conversation topics (extracted from message keywords)
- Tracks conversation statistics (duration, message count, topics)
- Handles session persistence in JSON

**Main Methods:**

```python
from chatbot.conversation_manager import get_conversation_manager

manager = get_conversation_manager()

# Create new session
session_id = manager.create_session()
# Returns: UUID string like "6287d994-683c-4724-aa9b-5b926fba8812"

# Add messages to session
manager.add_message(session_id, "user", "Quyền sử dụng đất là gì?")
manager.add_message(session_id, "bot", "Quyền sử dụng đất là...")

# Get context from session
context = manager.get_context_window(session_id, window_size=5)
# Returns: {
#     'recent_messages': [...],
#     'topics': ['đất', 'quyền', 'luật'],
#     'continuity_score': 0.85
# }

# Get session statistics
stats = manager.get_conversation_stats(session_id)
# Returns: {
#     'message_count': 10,
#     'duration_minutes': 5,
#     'topics': ['đất', 'quyền'],
#     'tags': ['technical', 'follow-up']
# }
```

**Topic Detection:**
Automatically extracts topics from conversation based on keywords:
- 📍 Location: "đất", "thửa", "lô"
- 📋 Documents: "giấy chứng thực", "hợp đồng"
- ⚖️ Rights: "quyền", "căn cứ", "điều"
- 💼 Procedures: "thủ tục", "đăng ký", "xin phép"

**Data Storage:**
- `data/conversations/{session_id}.json` - Each session stored separately

---

### 4. NLG Engine (`nlg_engine.py`)

Generates **natural, diverse responses** avoiding repetition.

**Key Features:**
- Paraphrases answers using synonym replacement
- Generates 3-4 variations per answer (different styles)
- Supports 8 template categories (intro, transition, conclusion, warning, etc.)
- Adjusts formality level (professional ↔ casual)
- Adds contextual emoji for visual appeal
- Composes rich responses with multiple sections

**Main Methods:**

```python
from chatbot.nlg_engine import get_nlg_engine

engine = get_nlg_engine()

# Paraphrase with style
response1 = engine.paraphrase(
    "Quyền sử dụng đất là quyền được sử dụng đất.",
    formality='formal'
)
# Returns: "Quyền sử dụng đất được định nghĩa là quyền pháp lý..."

response2 = engine.paraphrase(
    "Quyền sử dụng đất là quyền được sử dụng đất.",
    formality='casual'
)
# Returns: "Quyền sử dụng đất chính là quyền mà bạn có để..."

# Generate intro/transition/conclusion
intro = engine.generate_intro()
# Returns: "Được rồi, mình sẽ giải thích chi tiết cho bạn."

transition = engine.generate_transition()
# Returns: "Ngoài ra, bạn cần biết rằng..."

conclusion = engine.generate_conclusion()
# Returns: "Hy vọng giải thích trên đã giúp bạn hiểu rõ hơn!"

# Compose full response
full_response = engine.compose_rich_answer(
    intro="Đây là câu trả lời của mình:",
    main_answer="Quyền sử dụng đất là...",
    details="Chi tiết thêm: ...",
    warning="Lưu ý: ...",
    conclusion="Bạn có thêm câu hỏi không?"
)

# Add emoji
emojis = engine.add_emojis("Quyền sử dụng đất")
# Returns: "📍 Quyền sử dụng đất"
```

**Paraphrasing Dictionary (40+ pairs):**
- Quyền ↔ Phát hành, Lợi ích
- Đất ↔ Lô, Thửa
- Luật ↔ Quy định, Pháp lệnh
- Hợp pháp ↔ Hợp lệ, Được phép
- Thủ tục ↔ Quá trình, Các bước

---

## 🔄 Integration Flow

When a user asks a question, the chatbot orchestrates all 4 modules:

```
User Question
    ↓
[Sentiment Analyzer] → Detect emotion & urgency
    ↓
[Learning Engine] → Check for similar learned answers
    ↓ (if no learned answer)
[Bot Engine] → Retrieve from database
    ↓
[NLG Engine] → Generate natural, varied response
    ↓
[Conversation Manager] → Log interaction & context
    ↓
Return Response with Metadata
    ↓
User Submits Feedback (1-5 stars)
    ↓
[Learning Engine] → Record feedback, extract patterns
    ↓
System Improves
```

---

## 📊 API Endpoints (via `app.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Send question, get response with sentiment/urgency |
| `/api/feedback` | POST | Submit feedback (rating) for learning |
| `/api/learning-stats` | GET | Get overall learning statistics |
| `/api/session/create` | POST | Create new conversation session |
| `/api/session/{id}/context` | GET | Get session context & history |
| `/api/session/{id}/stats` | GET | Get session statistics |

---

## 🚀 Quick Start

### 1. Test Chatbot Modules

```bash
# Run comprehensive tests
python tests/test_new_features.py
```

Expected output:
```
✅ Learning Engine test passed
✅ Sentiment Analyzer test passed
✅ Conversation Manager test passed
✅ NLG Engine test passed
✅ ALL TESTS PASSED ✓
```

### 2. Use in Code

```python
from chatbot import LearningEngine, SentimentAnalyzer, ConversationManager, NLGEngine

# Initialize
learning = LearningEngine()
sentiment = SentimentAnalyzer()
manager = ConversationManager()
nlg = NLGEngine()

# Create session
session_id = manager.create_session()

# Analyze user question
question = "Tôi cần xin giấy phép đất gấp!"
sent, conf = sentiment.analyze_sentiment(question)
urgency, _ = sentiment.analyze_urgency(question)

# Get response (from learned data or database)
# ... bot retrieves answer ...

# Generate natural response
response = nlg.paraphrase(answer, formality='warm')
response = nlg.add_emojis(response)

# Log conversation
manager.add_message(session_id, "user", question)
manager.add_message(session_id, "bot", response)

# User can submit feedback later
learning.submit_feedback(interaction_id, rating=5)
```

### 3. Deploy

The chatbot module is already integrated into `app.py`. Just run:

```bash
python app.py
# Open http://localhost:8000
```

---

## 📈 Performance Tips

1. **Faster Learning:** High-quality answers (rating ≥ 4) are extracted as patterns for future reuse (~80% reuse rate)
2. **Better Context:** Conversation manager tracks last 10 messages by default (configurable)
3. **Natural Responses:** NLG engine generates 3-4 variations to avoid repetition
4. **Emotion Awareness:** Sentiment analysis adjusts tone based on user's emotional state

---

## 🔧 Configuration

Edit these files to customize:

- `chatbot/learning_engine.py` - Jaccard similarity threshold (default: 0.3)
- `chatbot/sentiment_analyzer.py` - Sentiment keyword dictionaries
- `chatbot/conversation_manager.py` - Context window size (default: 10)
- `chatbot/nlg_engine.py` - Template phrases & synonym dictionary

---

## 📚 Related Files

- `backend/bot.py` - Main orchestrator that calls all 4 modules
- `app.py` - Flask API endpoints
- `tests/test_new_features.py` - Comprehensive test suite
- `frontend/` - UI for feedback system

---

## ✅ Feature Checklist

- ✅ Self-learning from user feedback
- ✅ Emotion & urgency detection
- ✅ Conversation history tracking
- ✅ Natural language response generation
- ✅ Session management
- ✅ Pattern extraction & reuse
- ✅ Paraphrasing & synonym replacement
- ✅ Emoji insertion
- ✅ 5-star feedback system
- ✅ Full integration with bot engine

---

**Last Updated:** Nov 14, 2025
