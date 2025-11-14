"""
nlg_engine.py - Natural Language Generation Engine

Tính năng:
- Tạo các phiên bản khác nhau của cùng một câu trả lời (paraphrasing)
- Sử dụng từ đồng nghĩa
- Tạo sentence structures đa dạng
- Template-free generation
"""

import random
from typing import List, Dict
import re


class NLGEngine:
    """Natural Language Generation Engine"""
    
    def __init__(self):
        # Paraphrase templates
        self.paraphrase_templates = {
            # Giới thiệu câu trả lời
            "intro": [
                "Theo luật định:",
                "Dựa trên quy định pháp luật:",
                "Theo đó:",
                "Điểm quan trọng là:",
                "Cần lưu ý rằng:",
                "Theo các tài liệu pháp luật:",
                "Quy định này nói rằng:",
                "Cụ thể:",
                "Chi tiết hơn:",
                "Để trả lời bạn:",
            ],
            
            # Kết luận/dùng kết
            "conclusion": [
                "Tóm lại:",
                "Do đó:",
                "Vì vậy:",
                "Kết luận:",
                "Như vậy:",
                "Như bạn thấy:",
                "Điều này có nghĩa là:",
                "Nói cách khác:",
                "Hay nói cách khác:",
                "Bản chất là:",
            ],
            
            # Giáo dục/giải thích
            "explanation": [
                "Để giải thích chi tiết hơn:",
                "Nói rõ hơn:",
                "Để dễ hiểu hơn:",
                "Nói một cách khác:",
                "Hiểu đơn giản là:",
                "Về mặt thực tế:",
                "Ý nghĩa của điều đó là:",
                "Nói cách khác:",
            ],
            
            # Cảnh báo
            "warning": [
                "⚠️ Lưu ý:",
                "❗ Chú ý:",
                "‼️ Quan trọng:",
                "🚨 Cần biết:",
                "📌 Lưu ý quan trọng:",
                "💡 Cần chú ý:",
                "⚠️ Hãy lưu ý:",
                "Nếu không tuân thủ:",
            ],
            
            # Khuyến nghị
            "recommendation": [
                "💡 Tôi đề xuất:",
                "✓ Bạn nên:",
                "👉 Khuyến nghị:",
                "💬 Gợi ý:",
                "📝 Nên:",
                "🔔 Đề nghị:",
            ],
            
            # Xác nhận/Phê duyệt
            "confirmation": [
                "✓ Đúng, bạn có thể:",
                "✓ Có, bạn được phép:",
                "✓ Vâng, điều đó được cho phép:",
                "✓ Hoàn toàn có thể:",
                "✓ Được rồi:",
                "✓ Chắc chắn:",
            ],
            
            # Phủ định
            "negation": [
                "✗ Không, bạn không thể:",
                "✗ Không, điều đó không được phép:",
                "✗ Không thể:",
                "✗ Bị cấm:",
                "✗ Không được:",
            ],
        }
        
        # Transition words
        self.transition_words = {
            "addition": ["hơn nữa", "ngoài ra", "thêm vào đó", "cùng với", "bên cạnh đó"],
            "contrast": ["tuy nhiên", "nhưng", "mặc dù", "dù sao", "nhưng mà"],
            "example": ["ví dụ", "chẳng hạn", "để minh họa", "như"],
            "result": ["do đó", "vì thế", "kết quả là", "từ đó"],
            "time": ["sau đó", "rồi", "khi", "lúc", "trong khi"],
        }
        
        # Vietnamese synonyms for common words
        self.synonyms = {
            "đất": ["mảnh đất", "thửa đất", "tài sản đất đai", "bất động sản"],
            "quyền": ["chủ quyền", "quyền hạn", "tài quyền"],
            "bán": ["chuyển nhượng", "phát hành", "tiêu thụ"],
            "mua": ["sở hữu", "chiếm hữu"],
            "cho thuê": ["khoán", "cho sử dụng"],
            "xây dựng": ["khai thác", "phát triển"],
            "vi phạm": ["phạm pháp", "infringement"],
            "xử phạt": ["phạt tiền", "hình phạt"],
            "thủ tục": ["quy trình", "cách thức"],
            "giấy phép": ["chứng chỉ", "license"],
            "cơ quan": ["ban", "sở", "agency"],
            "người": ["cá nhân", "chủ thể", "bên"],
            "ngân sách": ["quỹ", "tài chính"],
            "thuế": ["phí", "lệ phí"],
        }
    
    def paraphrase(self, text: str, style: str = "formal") -> str:
        """
        Tạo phiên bản khác của text (paraphrase)
        style: "formal", "informal", "technical"
        """
        paraphrased = text
        
        # Replace synonyms
        for word, syns in self.synonyms.items():
            if word in paraphrased.lower():
                synonym = random.choice(syns)
                paraphrased = re.sub(rf'\b{word}\b', synonym, paraphrased, flags=re.IGNORECASE)
        
        # Adjust formality
        if style == "informal":
            paraphrased = self._make_informal(paraphrased)
        elif style == "technical":
            paraphrased = self._make_technical(paraphrased)
        elif style == "formal":
            paraphrased = self._make_formal(paraphrased)
        
        return paraphrased
    
    def generate_intro(self, intro_type: str = "intro") -> str:
        """Generate random intro phrase"""
        if intro_type in self.paraphrase_templates:
            return random.choice(self.paraphrase_templates[intro_type])
        return "Theo đó:"
    
    def generate_transition(self, trans_type: str = "addition") -> str:
        """Generate transition word"""
        if trans_type in self.transition_words:
            return random.choice(self.transition_words[trans_type])
        return ""
    
    def generate_conclusion(self) -> str:
        """Generate random conclusion"""
        return random.choice(self.paraphrase_templates["conclusion"])
    
    def generate_varied_response(self, core_answer: str, variations: int = 3) -> List[str]:
        """
        Tạo nhiều biến thể của cùng một câu trả lời
        Trả về danh sách các phiên bản khác nhau
        """
        variations_list = [core_answer]
        
        # Variation 1: Formal style
        if variations >= 1:
            formal = self.paraphrase(core_answer, style="formal")
            variations_list.append(formal)
        
        # Variation 2: Informal style
        if variations >= 2:
            informal = self.paraphrase(core_answer, style="informal")
            variations_list.append(informal)
        
        # Variation 3: Reordered sentences
        if variations >= 3:
            reordered = self._reorder_sentences(core_answer)
            variations_list.append(reordered)
        
        # Variation 4: With explanation
        if variations >= 4:
            with_explanation = self._add_explanation(core_answer)
            variations_list.append(with_explanation)
        
        return variations_list[:variations]
    
    def compose_rich_answer(self, parts: Dict[str, str]) -> str:
        """
        Compose rich answer từ các phần:
        {
            "intro": "...",
            "main": "...",
            "details": "...",
            "conclusion": "...",
            "warning": "..." (optional)
        }
        """
        answer_parts = []
        
        if parts.get("intro"):
            answer_parts.append(parts["intro"])
        
        if parts.get("main"):
            answer_parts.append("\n" + parts["main"])
        
        if parts.get("details"):
            answer_parts.append("\n" + self.generate_transition("addition") + " " + parts["details"])
        
        if parts.get("warning"):
            answer_parts.append("\n\n" + self.generate_intro("warning") + " " + parts["warning"])
        
        if parts.get("conclusion"):
            answer_parts.append("\n\n" + self.generate_conclusion() + " " + parts["conclusion"])
        
        return "".join(answer_parts)
    
    def generate_bullet_points(self, text: str) -> str:
        """Chuyển đoạn text thành bullet points"""
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        bullet_points = []
        for sent in sentences:
            if sent:
                bullet_points.append(f"• {sent.strip()}")
        
        return "\n".join(bullet_points)
    
    def generate_numbered_list(self, items: List[str]) -> str:
        """Tạo numbered list"""
        return "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
    
    def add_emojis(self, text: str) -> str:
        """Thêm emoji để làm cho text thêm sinh động - NHƯNG CHỈ ở tiêu đề, không inline"""
        # Only add emojis to heading lines, not inline text to avoid clutter
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            # Only process lines that are clearly headings (start with #)
            if line.strip().startswith('##') or line.strip().startswith('###'):
                # It's a heading - safe to add emoji
                if 'cảnh báo' in line.lower() or 'lưu ý' in line.lower():
                    line = re.sub(r'(cảnh báo|lưu ý)', r'⚠️ \1', line, flags=re.IGNORECASE)
                elif 'ghi chú' in line.lower():
                    line = re.sub(r'ghi chú', '📝 ghi chú', line, flags=re.IGNORECASE)
            # For non-heading lines, don't add emojis to avoid text pollution
            result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _make_informal(self, text: str) -> str:
        """Chuyển text sang informal style"""
        replacements = {
            "được cho phép": "có thể",
            "bị cấm": "không được",
            "điều khoản": "điểm",
            "theo đó": "vậy thì",
        }
        
        result = text
        for formal, informal in replacements.items():
            result = re.sub(rf'\b{formal}\b', informal, result, flags=re.IGNORECASE)
        
        return result
    
    def _make_formal(self, text: str) -> str:
        """Chuyển text sang formal style"""
        replacements = {
            "vậy thì": "theo đó",
            "không được": "bị cấm",
            "có thể": "được cho phép",
        }
        
        result = text
        for informal, formal in replacements.items():
            result = re.sub(rf'\b{informal}\b', formal, result, flags=re.IGNORECASE)
        
        return result
    
    def _make_technical(self, text: str) -> str:
        """Chuyển text sang technical style"""
        # Thêm công thức, số liệu, v.v.
        return text  # Simplification
    
    def _reorder_sentences(self, text: str) -> str:
        """Sắp xếp lại thứ tự các câu"""
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 1:
            # Giữ first sentence, shuffle the rest
            first = sentences[0]
            rest = sentences[1:]
            random.shuffle(rest)
            return ". ".join([first] + rest) + "."
        
        return text
    
    def _add_explanation(self, text: str) -> str:
        """Thêm giải thích vào text"""
        return f"{self.generate_intro('explanation')} {text}"


# Global instance
_nlg_engine = None

def get_nlg_engine() -> NLGEngine:
    """Get hoặc tạo global NLG engine instance"""
    global _nlg_engine
    if _nlg_engine is None:
        _nlg_engine = NLGEngine()
    return _nlg_engine
