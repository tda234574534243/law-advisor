"""
conversation_manager.py - Quản lý cuộc trò chuyện & context memory

Tính năng:
- Lưu trữ lịch sử cuộc trò chuyện
- Nhận diện context từ những câu hỏi trước đó
- Multi-turn conversation support
- Context window management
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class ConversationManager:
    """Quản lý lịch sử và context của cuộc trò chuyện"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.conversations_dir = os.path.join(data_dir, "conversations")
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        # Conversation sessions in memory (session_id -> conversation_data)
        self.active_sessions = {}
    
    def create_session(self, user_id: str, session_name: str = "") -> str:
        """Tạo session trò chuyện mới"""
        import uuid
        session_id = str(uuid.uuid4())
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "name": session_name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "messages": [],
            "context": {},
            "tags": [],
            "summary": ""
        }
        
        self.active_sessions[session_id] = session
        self._save_session(session)
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, 
                   metadata: Dict = None) -> Dict:
        """Thêm message vào conversation"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,  # "user" hoặc "bot"
            "content": content,
            "metadata": metadata or {},
            "message_id": len(session["messages"]) + 1
        }
        
        session["messages"].append(message)
        self._save_session(session)
        
        return message
    
    def get_context_window(self, session_id: str, window_size: int = 5) -> Dict:
        """Lấy context từ những messages trước đó"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        messages = session["messages"]
        
        # Lấy last N messages
        recent_messages = messages[-window_size:]
        
        context = {
            "session_id": session_id,
            "messages": recent_messages,
            "user_questions": [],
            "bot_answers": [],
            "topics": self._extract_topics(recent_messages),
            "continuity": self._detect_continuity(recent_messages)
        }
        
        # Extract user questions and bot answers
        for msg in recent_messages:
            if msg["role"] == "user":
                context["user_questions"].append(msg["content"])
            elif msg["role"] == "bot":
                context["bot_answers"].append(msg["content"])
        
        return context
    
    def update_session_context(self, session_id: str, context_key: str, context_value):
        """Update context key trong session"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session["context"][context_key] = context_value
        self._save_session(session)
    
    def is_follow_up(self, session_id: str) -> bool:
        """Check if current query là follow-up question"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        return len(session["messages"]) > 2  # Có ít nhất 1 pair Q&A trước đó
    
    def get_last_bot_answer(self, session_id: str) -> Optional[str]:
        """Lấy câu trả lời cuối cùng của bot"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        for msg in reversed(session["messages"]):
            if msg["role"] == "bot":
                return msg["content"]
        
        return None
    
    def get_previous_queries(self, session_id: str, limit: int = 5) -> List[str]:
        """Lấy các query trước đó"""
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        queries = [msg["content"] for msg in session["messages"] if msg["role"] == "user"]
        return queries[-limit:]
    
    def generate_session_summary(self, session_id: str) -> str:
        """Tạo tóm tắt session"""
        if session_id not in self.active_sessions:
            return ""
        
        session = self.active_sessions[session_id]
        messages = session["messages"]
        
        # Tạo tóm tắt dựa trên user questions
        questions = [msg["content"][:100] for msg in messages if msg["role"] == "user"]
        
        if not questions:
            return ""
        
        summary = "Cuộc trò chuyện về: " + ", ".join(questions[:3])
        if len(questions) > 3:
            summary += f" (và {len(questions) - 3} câu hỏi khác)"
        
        session["summary"] = summary
        self._save_session(session)
        
        return summary
    
    def tag_session(self, session_id: str, tag: str):
        """Thêm tag cho session (để phân loại)"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        if tag not in session["tags"]:
            session["tags"].append(tag)
            self._save_session(session)
    
    def search_conversations(self, user_id: str, keyword: str = "", 
                            tag: str = "", limit: int = 10) -> List[Dict]:
        """Tìm kiếm conversations"""
        results = []
        
        for session in self.active_sessions.values():
            if session["user_id"] != user_id:
                continue
            
            # Filter by keyword
            if keyword:
                keyword_lower = keyword.lower()
                found = False
                for msg in session["messages"]:
                    if keyword_lower in msg["content"].lower():
                        found = True
                        break
                if not found:
                    continue
            
            # Filter by tag
            if tag and tag not in session["tags"]:
                continue
            
            results.append({
                "session_id": session["session_id"],
                "name": session["name"],
                "created_at": session["created_at"],
                "summary": session["summary"],
                "tags": session["tags"],
                "message_count": len(session["messages"])
            })
        
        return results[:limit]
    
    def get_conversation_stats(self, session_id: str) -> Dict:
        """Lấy thống kê của session"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        messages = session["messages"]
        
        user_msgs = [m for m in messages if m["role"] == "user"]
        bot_msgs = [m for m in messages if m["role"] == "bot"]
        
        # Tính average message length
        avg_user_len = sum(len(m["content"]) for m in user_msgs) / max(1, len(user_msgs))
        avg_bot_len = sum(len(m["content"]) for m in bot_msgs) / max(1, len(bot_msgs))
        
        return {
            "total_messages": len(messages),
            "user_messages": len(user_msgs),
            "bot_messages": len(bot_msgs),
            "avg_user_message_length": round(avg_user_len, 2),
            "avg_bot_message_length": round(avg_bot_len, 2),
            "session_duration": self._calculate_session_duration(session),
            "topics": self._extract_topics(messages),
            "tags": session["tags"]
        }
    
    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """Extract topics từ messages"""
        topics = set()
        
        for msg in messages:
            content_lower = msg["content"].lower()
            
            # Detect topics based on keywords
            topic_keywords = {
                "đất": ["đất", "land", "thửa", "mảnh"],
                "quyền": ["quyền", "rights", "chủ quyền"],
                "luật": ["luật", "pháp luật", "law", "legal"],
                "mua bán": ["mua", "bán", "chuyển nhượng", "buy", "sell"],
                "cho thuê": ["thuê", "khoán", "rent", "lease"],
                "xây dựng": ["xây", "dựng", "construct", "building"],
                "bồi thường": ["bồi", "thường", "compensation"],
                "vi phạm": ["vi phạm", "violation", "infringement"]
            }
            
            for topic, keywords in topic_keywords.items():
                if any(kw in content_lower for kw in keywords):
                    topics.add(topic)
        
        return list(topics)
    
    def _detect_continuity(self, messages: List[Dict]) -> bool:
        """Detect if messages are continuous (related)"""
        if len(messages) < 2:
            return False
        
        # Check if there's semantic continuity between consecutive user messages
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        
        if len(user_messages) < 2:
            return True
        
        # Nếu có từ khóa "vậy", "còn", "tiếp", etc -> là follow-up
        last_query = user_messages[-1].lower()
        followup_words = ["vậy", "còn", "tiếp", "nữa", "khác", "lại", "if", "what if", "and what about"]
        
        return any(word in last_query for word in followup_words)
    
    def _calculate_session_duration(self, session: Dict) -> str:
        """Calculate session duration"""
        if not session["messages"]:
            return "0 phút"
        
        first_msg_time = datetime.fromisoformat(session["messages"][0]["timestamp"])
        last_msg_time = datetime.fromisoformat(session["messages"][-1]["timestamp"])
        
        duration = (last_msg_time - first_msg_time).total_seconds()
        
        if duration < 60:
            return f"{int(duration)} giây"
        elif duration < 3600:
            return f"{int(duration / 60)} phút"
        else:
            return f"{int(duration / 3600)} giờ"
    
    def _save_session(self, session: Dict):
        """Lưu session vào file"""
        try:
            session_file = os.path.join(self.conversations_dir, f"{session['session_id']}.json")
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving session: {e}")
    
    def _load_session(self, session_id: str) -> Optional[Dict]:
        """Load session từ file"""
        try:
            session_file = os.path.join(self.conversations_dir, f"{session_id}.json")
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading session: {e}")
        return None
    
    def cleanup_old_sessions(self, days: int = 7):
        """Xóa old sessions (mặc định > 7 ngày)"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for session_id, session in list(self.active_sessions.items()):
            created_at = datetime.fromisoformat(session["created_at"])
            if created_at < cutoff_date:
                del self.active_sessions[session_id]


# Global instance
_conversation_manager = None

def get_conversation_manager() -> ConversationManager:
    """Get hoặc tạo global conversation manager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
