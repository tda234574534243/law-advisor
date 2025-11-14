# 💻 Frontend Module

Web interface for the law query system.

## 📂 Structure

```
frontend/
├── templates/
│   └── index.html      # Main web UI
├── static/
│   ├── app.js          # Frontend logic
│   └── styles.css      # Styling
└── README.md
```

## 🖥️ Main Page (`templates/index.html`)

Responsive web interface with:
- Modern design (gradient, smooth animations)
- Chat interface
- Feedback system (1-5 star rating)
- Search modes
- Real-time statistics

### Features

**Chat Section**
- Message history display
- User & bot messages
- Auto-scroll to latest

**Feedback Panel**
- Rate response (1-5 stars)
- Optional feedback text
- Send & close buttons

**Controls**
- Textarea for input (Shift+Enter for newline, Enter to send)
- Chat mode button
- Search button
- Rebuild index button
- Statistics button

**Display Elements**
- Chat history
- Confidence score
- Sentiment indicator
- Urgency level
- Learning statistics

## 🎨 Styling (`static/styles.css`)

Features:
- Responsive design (mobile & desktop)
- Gradient backgrounds
- Smooth animations
- Modern UI components
- Dark/light theme support

## 🔧 Frontend Logic (`static/app.js`)

### Key Functions

```javascript
// Chat operations
doChat()              // Send question to bot
doSearch()            // Search documents
rebuildIndex()        // Rebuild TF-IDF index
loadStats()           // Load learning statistics

// Feedback operations
showFeedbackArea()    // Show feedback panel
selectRating()        // Select star rating
submitFeedback()      // Submit feedback
closeFeedback()       // Close feedback panel

// Utility functions
addMessage()          // Add message to chat
postJSON()            // POST JSON request
```

### API Integration

**Chat with Learning**
```javascript
const response = await postJSON('/api/chat', {
  q: "Quyền sử dụng đất là gì?",
  session_id: "optional",
  user_id: "optional"
});

// response contains:
{
  "answer": "...",
  "sentiment": "positive|negative|neutral|frustrated|urgent",
  "urgency": "low|medium|high|critical",
  "confidence": 0.85,
  "interaction_id": "xxx",
  "is_followup": false
}
```

**Submit Feedback**
```javascript
await postJSON('/api/feedback', {
  "interaction_id": response.interaction_id,
  "rating": 5,
  "feedback": "Very helpful!"
});
```

**Get Statistics**
```javascript
const stats = await fetch('/api/learning-stats').then(r => r.json());

// stats contains:
{
  "total_interactions": 42,
  "positive_feedback": 30,
  "avg_rating": 4.2,
  "total_patterns_learned": 125
}
```

## 🎯 UI Workflows

### Query Workflow

1. User types question
2. Click "💬 Hỏi Chatbot" or press Enter
3. Loading indicator shows
4. Bot returns answer with metadata
5. Display answer, confidence, sentiment
6. Show "👍 Đánh Giá" button

### Feedback Workflow

1. User clicks "👍 Đánh Giá"
2. Feedback panel opens
3. User selects rating (1-5 stars)
4. (Optional) Write feedback text
5. Click "Gửi"
6. Confirmation message
7. Panel closes
8. Statistics update

### Search Workflow

1. User enters query
2. Select search mode (Auto/Keyword/Article)
3. Click "🔍 Tìm"
4. Display search results as cards
5. Each result shows score, section, source link

## 🎨 UI Components

### Message Display
- User messages: Blue background, right-aligned
- Bot messages: Light background, left-aligned
- Markdown formatting support
- Emoji support

### Feedback Stars
- Clickable star rating (1-5)
- Visual feedback on hover
- Selected stars highlighted in gold

### Statistics Box
- Grid layout
- Key metrics display
- Auto-update on feedback

### Search Results
- Card-based layout
- Score display
- Document section
- Content preview (truncated)
- Source link

## 📱 Responsive Design

**Desktop** (> 1024px)
- Wide layout
- Full-width chat
- Side panels

**Tablet** (768px - 1024px)
- Medium layout
- Adjusted spacing
- Stacked panels

**Mobile** (< 768px)
- Compact layout
- Full-width elements
- Touch-friendly buttons
- Vertical stacking

## 🎨 Color Scheme

```css
Primary: #667eea (purple)
Secondary: #764ba2 (darker purple)
Success: #28a745 (green)
Danger: #dc3545 (red)
Warning: #ffc107 (yellow)
Text: #333 (dark gray)
Background: #f8f9fa (light gray)
```

## 🔌 Integration Points

### Connection to Backend

**Flask Templates**
```python
# app.py
@app.route("/")
def index():
    return render_template("index.html")
```

**API Endpoints Used**
- `POST /api/chat`
- `POST /api/search`
- `POST /api/feedback`
- `GET /api/learning-stats`
- `POST /api/session/create`
- `GET /api/session/{id}/stats`
- `POST /api/build_index`

### Session Management

```javascript
// Generate user ID on first load
let userId = localStorage.getItem('userId') || 
             'user_' + Math.random().toString(36).substr(2, 9);
localStorage.setItem('userId', userId);

// Create session
const sessionResp = await postJSON('/api/session/create', {
  user_id: userId,
  session_name: 'Chat Session'
});
currentSessionId = sessionResp.session_id;

// Use in chat
await postJSON('/api/chat', {
  q: query,
  session_id: currentSessionId,
  user_id: userId
});
```

## 🐛 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Optimization

### Frontend
- Minimize reflows/repaints
- Lazy load statistics
- Cache API responses
- Debounce input
- Async operations

### Network
- Compress responses
- Cache static assets
- Use CDN for libraries
- Minimize requests

## Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus indicators
- Color contrast compliance
- Alt text for images

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Voice input/output
- [ ] Export chat to PDF
- [ ] Multi-language support
- [ ] Advanced search filters
- [ ] Conversation sharing
- [ ] Syntax highlighting for code
- [ ] Mobile app version

---

**Version 2.0 | Frontend Module**
