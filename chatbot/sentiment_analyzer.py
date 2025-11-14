"""
sentiment_analyzer.py - Phân tích cảm xúc & context từ query của người dùng

Tính năng:
- Detect tâm trạng (tích cực, tiêu cực, trung lập)
- Nhận diện độ khẩn cấp (urgent, normal, general)
- Detect satisfaction level
- Điều chỉnh tone của bot response
"""

import re
from typing import Dict, Tuple
from enum import Enum


class Sentiment(Enum):
    """Cảm xúc của người dùng"""
    POSITIVE = "positive"      # Hài lòng, tích cực
    NEGATIVE = "negative"      # Không hài lòng, tức giận
    NEUTRAL = "neutral"        # Bình thường, đơn thuần hỏi
    FRUSTRATED = "frustrated"  # Bực bã, khó chịu
    URGENT = "urgent"          # Cần gấp, vội vã


class Urgency(Enum):
    """Mức độ khẩn cấp"""
    LOW = "low"              # Thông thường
    MEDIUM = "medium"        # Cần hỏi nhưng không cấp bách
    HIGH = "high"            # Cần gấp
    CRITICAL = "critical"    # Rất cấp bách


class SentimentAnalyzer:
    """Phân tích cảm xúc và ngữ cảnh"""
    
    def __init__(self):
        # Từ khóa tích cực
        self.positive_keywords = {
            'cảm ơn': 2, 'thanks': 2, 'thank you': 2,
            'tuyệt': 3, 'excellent': 3, 'great': 3,
            'tốt': 1, 'good': 1,
            'hiểu': 1, 'clarify': 1,
            'rõ': 1, 'clear': 1,
        }
        
        # Từ khóa tiêu cực
        self.negative_keywords = {
            'không hiểu': 3, 'confused': 3, 'confusing': 3,
            'sai': 2, 'wrong': 2, 'incorrect': 2,
            'không đúng': 2, 'inaccurate': 2,
            'phức tạp': 1, 'complicated': 1, 'complex': 1,
            'khó': 1, 'difficult': 1, 'hard': 1,
            'tệ': 2, 'bad': 2, 'terrible': 2,
            'vô dụng': 3, 'useless': 3,
        }
        
        # Từ khóa bực bã/khó chịu
        self.frustration_keywords = {
            'sao': 1, 'why': 1,
            'tại sao': 1, 'why not': 1,
            'không biết': 1, "don't know": 1,
            'bối rối': 2, 'confused': 2, 'bewildered': 2,
            'mơ hồ': 2, 'vague': 2, 'unclear': 2,
        }
        
        # Từ khóa khẩn cấp
        self.urgent_keywords = {
            'gấp': 2, 'urgent': 2, 'ngay': 2,
            'ngay bây giờ': 3, 'immediately': 3, 'asap': 3,
            'cấp bách': 3, 'critical': 3, 'emergency': 3,
            'sắp': 1, 'sắp tới': 2, 'soon': 1,
            'deadline': 2,
            'hôm nay': 1, 'today': 1,
            'cần gấp': 3,
        }
        
        # Từ khóa yêu cầu làm lại/cải thiện
        self.retry_keywords = {
            'lại': 1, 'again': 1,
            'khác': 1, 'other': 1,
            'hỏi lại': 1, 'ask again': 1,
            'hiểu sai': 2, 'misunderstood': 2,
            'không phải': 1, "isn't": 1,
        }
    
    def analyze_sentiment(self, query: str) -> Tuple[Sentiment, float]:
        """
        Phân tích cảm xúc của query
        Returns: (Sentiment, confidence_score 0-1)
        """
        query_lower = query.lower()
        
        # Score từng loại cảm xúc
        positive_score = self._calculate_keyword_score(query_lower, self.positive_keywords)
        negative_score = self._calculate_keyword_score(query_lower, self.negative_keywords)
        frustration_score = self._calculate_keyword_score(query_lower, self.frustration_keywords)
        urgent_score = self._calculate_keyword_score(query_lower, self.urgent_keywords)
        
        # Determine sentiment based on scores
        total_score = positive_score - negative_score
        
        if urgent_score > 2:
            return Sentiment.URGENT, min(1.0, urgent_score / 5)
        
        if frustration_score > 1.5:
            return Sentiment.FRUSTRATED, min(1.0, frustration_score / 5)
        
        if positive_score > negative_score:
            return Sentiment.POSITIVE, min(1.0, positive_score / 5)
        elif negative_score > 0:
            return Sentiment.NEGATIVE, min(1.0, negative_score / 5)
        else:
            return Sentiment.NEUTRAL, 0.5
    
    def analyze_urgency(self, query: str) -> Tuple[Urgency, float]:
        """
        Phân tích mức độ khẩn cấp
        Returns: (Urgency, confidence_score 0-1)
        """
        query_lower = query.lower()
        urgent_score = self._calculate_keyword_score(query_lower, self.urgent_keywords)
        
        # Kiểm tra pattern về deadline (Điều X trước ngày Y)
        deadline_pattern = r"(trước|by|deadline).*(ngày|date|tháng|month|năm|year)\s+(\d+)"
        has_deadline = bool(re.search(deadline_pattern, query_lower))
        
        if has_deadline or urgent_score >= 3:
            return Urgency.CRITICAL, min(1.0, urgent_score / 5)
        elif urgent_score >= 2:
            return Urgency.HIGH, min(1.0, urgent_score / 5)
        elif urgent_score >= 1:
            return Urgency.MEDIUM, min(1.0, urgent_score / 5)
        else:
            return Urgency.LOW, 0.3
    
    def is_follow_up_question(self, query: str) -> bool:
        """Detect if this is a follow-up question (hỏi lại, hỏi thêm)"""
        retry_score = self._calculate_keyword_score(query.lower(), self.retry_keywords)
        
        # Hoặc check pattern như "Vậy nếu...", "Nếu vậy..."
        followup_patterns = [
            r"vậy (nếu|khi|thì|mà)",
            r"nếu vậy",
            r"nghe đâu",
            r"còn",
            r"thêm về",
            r"chi tiết hơn",
            r"more details",
            r"what if"
        ]
        
        has_followup_pattern = any(re.search(p, query.lower()) for p in followup_patterns)
        
        return retry_score > 0.5 or has_followup_pattern
    
    def get_response_tone(self, sentiment: Sentiment, urgency: Urgency) -> Dict[str, str]:
        """
        Xác định tone của response dựa trên sentiment & urgency
        """
        tones = {
            # (Sentiment, Urgency) -> tone configuration
            (Sentiment.POSITIVE, Urgency.LOW): {
                "greeting": "Cảm ơn bạn! 😊",
                "prefix": "Vui mừng là có thể giúp bạn:",
                "suffix": "Hy vọng câu trả lời này hữu ích! 👍",
                "formality": "informal"
            },
            (Sentiment.POSITIVE, Urgency.HIGH): {
                "greeting": "Hiểu rồi! Tôi sẽ giúp ngay:",
                "prefix": "Để giải quyết vấn đề của bạn ngay:",
                "suffix": "Hy vọng điều này giúp bạn kịp thời! ✓",
                "formality": "semi-formal"
            },
            (Sentiment.NEUTRAL, Urgency.LOW): {
                "greeting": "Tôi có thể giúp bạn:",
                "prefix": "Dưới đây là thông tin:",
                "suffix": "Hãy cho tôi biết nếu cần thêm thông tin.",
                "formality": "formal"
            },
            (Sentiment.NEUTRAL, Urgency.HIGH): {
                "greeting": "Hiểu rồi, bạn cần thông tin gấp:",
                "prefix": "Thông tin cần thiết:",
                "suffix": "Hy vọng điều này giải quyết được vấn đề của bạn.",
                "formality": "semi-formal"
            },
            (Sentiment.FRUSTRATED, Urgency.LOW): {
                "greeting": "Xin lỗi nếu câu hỏi trước không rõ. Để tôi giải thích lại:",
                "prefix": "Để làm cho vấn đề này rõ ràng hơn:",
                "suffix": "Nếu vẫn còn vấn đề đề, hãy báo cho tôi biết.",
                "formality": "semi-formal"
            },
            (Sentiment.FRUSTRATED, Urgency.HIGH): {
                "greeting": "Tôi hiểu bạn bức xúc. Để giải quyết ngay:",
                "prefix": "Thông tin quan trọng nhất mà bạn cần:",
                "suffix": "Xin lỗi vì sự khó chịu này. Bạn có cần tôi giải thích thêm không?",
                "formality": "semi-formal"
            },
            (Sentiment.NEGATIVE, Urgency.LOW): {
                "greeting": "Xin lỗi nếu câu trả lời trước không chính xác.",
                "prefix": "Để sửa lại:",
                "suffix": "Cảm ơn bạn vì phản hồi. Tôi sẽ cải thiện.",
                "formality": "formal"
            },
            (Sentiment.NEGATIVE, Urgency.HIGH): {
                "greeting": "Xin lỗi! Để sửa ngay:",
                "prefix": "Thông tin chính xác:",
                "suffix": "Xin lỗi vì sự nhầm lẫn. Bạn có cần thêm hỗ trợ không?",
                "formality": "semi-formal"
            },
            (Sentiment.URGENT, Urgency.CRITICAL): {
                "greeting": "⚠️ Vấn đề cấp bách! Tôi sẽ giải quyết ngay:",
                "prefix": "Thông tin TÌM KIẾM:",
                "suffix": "Đây là thông tin cấp bách. Liên hệ cơ quan hữu quan nếu cần thêm hỗ trợ.",
                "formality": "urgent"
            }
        }
        
        # Tìm tone phù hợp
        tone = tones.get((sentiment, urgency))
        
        if not tone:
            # Fallback to neutral tone
            tone = tones[(Sentiment.NEUTRAL, Urgency.LOW)]
        
        return tone
    
    def suggest_question_improvements(self, query: str) -> list:
        """Gợi ý cách hỏi tốt hơn"""
        suggestions = []
        
        if len(query) < 10:
            suggestions.append("💡 Câu hỏi có vẻ quá ngắn. Hãy thêm chi tiết để tôi hiểu tốt hơn.")
        
        if query.endswith("?") is False and query.endswith("。") is False:
            suggestions.append("💡 Câu hỏi nên kết thúc bằng dấu '?' để rõ ràng hơn.")
        
        if "Điều" not in query and "điều" not in query.lower():
            # Không nhắc đến Điều luật cụ thể
            if any(word in query.lower() for word in ["quyền", "nghĩa vụ", "vi phạm"]):
                suggestions.append("💡 Nếu muốn hỏi về Điều cụ thể, hãy nêu số Điều (ví dụ: 'Điều 69')")
        
        return suggestions
    
    def _calculate_keyword_score(self, text: str, keywords: dict) -> float:
        """Calculate score based on keywords found in text"""
        score = 0.0
        for keyword, weight in keywords.items():
            if keyword in text:
                score += weight
        return score
    
    def detect_context_type(self, query: str) -> str:
        """Detect loại context của query"""
        query_lower = query.lower()
        
        # Business context
        if any(w in query_lower for w in ['kinh doanh', 'doanh nghiệp', 'lợi nhuận', 'thu nhập', 'business']):
            return 'business'
        
        # Personal context
        if any(w in query_lower for w in ['cá nhân', 'gia đình', 'personal', 'family', 'tôi', 'mình']):
            return 'personal'
        
        # Legal consultation
        if any(w in query_lower for w in ['tư vấn', 'sư', 'lawyer', 'hỏi', 'advice']):
            return 'legal_consultation'
        
        # General information seeking
        return 'information'


# Global instance
_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get hoặc tạo global sentiment analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
