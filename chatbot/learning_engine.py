"""
learning_engine.py - Hệ thống tự học từ feedback người dùng

Tính năng:
- Lưu trữ các câu hỏi/câu trả lời được người dùng đánh giá tốt
- Ghi nhận feedback (tốt/xấu) và từ khóa tương tự
- Tổng hợp patterns để cải thiện câu trả lời tương lai
- Pattern matching để detect câu hỏi tương tự
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import re


class LearningEngine:
    """Quản lý học tập từ feedback người dùng"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.learning_file = os.path.join(data_dir, "learned_interactions.json")
        self.patterns_file = os.path.join(data_dir, "learned_patterns.json")
        self.synonyms_file = os.path.join(data_dir, "learned_synonyms.json")
        self.feedback_file = os.path.join(data_dir, "feedback_stats.json")
        
        os.makedirs(data_dir, exist_ok=True)
        
        # Tải dữ liệu hiện có
        self.interactions = self._load_json(self.learning_file, [])
        self.patterns = self._load_json(self.patterns_file, {})
        self.synonyms = self._load_json(self.synonyms_file, {})
        self.feedback_stats = self._load_json(self.feedback_file, {
            "total_interactions": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "avg_rating": 0.0,
            "most_asked": []
        })
    
    def _load_json(self, filepath: str, default=None):
        """Load JSON file or return default"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {filepath}: {e}")
        return default if default is not None else {}
    
    def _save_json(self, filepath: str, data):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving {filepath}: {e}")
    
    def record_interaction(self, query: str, answer: str, sources: List[str], 
                          user_id: str = "anonymous", metadata: Dict = None) -> str:
        """Ghi nhận một tương tác (câu hỏi + câu trả lời)"""
        interaction = {
            "id": self._generate_id(),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer,
            "sources": sources,
            "user_id": user_id,
            "rating": 0,
            "feedback": None,
            "metadata": metadata or {},
            "query_normalized": self._normalize_query(query),
            "query_tokens": self._tokenize(query)
        }
        
        self.interactions.append(interaction)
        self._save_json(self.learning_file, self.interactions)
        
        # Update stats
        self.feedback_stats["total_interactions"] += 1
        self._save_json(self.feedback_file, self.feedback_stats)
        
        return interaction["id"]
    
    def submit_feedback(self, interaction_id: str, rating: int, feedback_text: str = "", 
                       is_helpful: bool = None):
        """Người dùng feedback câu trả lời (rating 1-5, true/false)"""
        for inter in self.interactions:
            if inter["id"] == interaction_id:
                inter["rating"] = rating
                inter["feedback"] = feedback_text
                inter["feedback_timestamp"] = datetime.now().isoformat()
                
                # Update stats
                if rating >= 4:
                    self.feedback_stats["positive_feedback"] += 1
                elif rating <= 2:
                    self.feedback_stats["negative_feedback"] += 1
                
                # Update average rating
                ratings = [i.get("rating", 0) for i in self.interactions if i.get("rating", 0) > 0]
                if ratings:
                    self.feedback_stats["avg_rating"] = sum(ratings) / len(ratings)
                
                # Extract learned patterns from positive feedback
                if rating >= 4:
                    self._learn_from_positive(inter)
                
                self._save_json(self.learning_file, self.interactions)
                self._save_json(self.feedback_file, self.feedback_stats)
                break
    
    def _learn_from_positive(self, interaction: Dict):
        """Học từ những feedback tích cực"""
        query = interaction["query"]
        answer = interaction["answer"]
        tokens = interaction["query_tokens"]
        
        # Tăng tần suất của các từ khóa
        for token in tokens:
            if token not in self.patterns:
                self.patterns[token] = {
                    "frequency": 0,
                    "answers": [],
                    "success_rate": 0.0
                }
            self.patterns[token]["frequency"] += 1
            
            # Lưu trữ pattern của câu trả lời
            if answer not in self.patterns[token]["answers"]:
                self.patterns[token]["answers"].append(answer[:500])  # Limit answer length
        
        self._save_json(self.patterns_file, self.patterns)
    
    def find_similar_learned_answers(self, query: str, top_k: int = 3) -> List[Dict]:
        """Tìm các câu trả lời tương tự từ những câu hỏi đã được học"""
        query_tokens = set(self._tokenize(query))
        
        similar = []
        for inter in self.interactions:
            if inter.get("rating", 0) >= 4:  # Chỉ lấy những câu trả lời được đánh giá tốt
                inter_tokens = set(inter.get("query_tokens", []))
                
                # Tính độ tương tự Jaccard
                if query_tokens and inter_tokens:
                    intersection = len(query_tokens & inter_tokens)
                    union = len(query_tokens | inter_tokens)
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.3:  # Threshold
                        similar.append({
                            "similarity": similarity,
                            "query": inter["query"],
                            "answer": inter["answer"],
                            "rating": inter.get("rating", 0)
                        })
        
        # Sort by similarity
        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:top_k]
    
    def get_synonyms(self, word: str) -> List[str]:
        """Lấy từ đồng nghĩa đã học hoặc mặc định"""
        vietnamese_synonyms = {
            "đất": ["mảnh đất", "thửa đất", "bất động sản", "tài sản đất đai"],
            "luật": ["pháp luật", "quy định", "điều luật", "bộ luật"],
            "quyền": ["chủ quyền", "quyền hạn", "tài quyền", "yêu cầu"],
            "nghĩa vụ": ["bổn phận", "trách nhiệm", "dụng vụ"],
            "vi phạm": ["phạm pháp", "infringement", "lỗi phạm", "vi pháp"],
            "xử phạt": ["phạt tiền", "hình phạt", "xử lý", "có hậu quả"],
            "mua": ["sở hữu", "sở lĩnh", "chiếm hữu", "chuyên hữu"],
            "bán": ["chuyển nhượng", "phát hành", "tiêu thụ"],
            "cho thuê": ["khoán", "thuê bao", "cho sử dụng"],
            "xây dựng": ["khai thác", "phát triển", "công trình"],
        }
        
        if word in vietnamese_synonyms:
            return vietnamese_synonyms[word]
        
        # Tìm từ đồng nghĩa đã học
        if word in self.synonyms:
            return self.synonyms[word]
        
        return []
    
    def record_synonym_pair(self, word1: str, word2: str):
        """Ghi nhận cặp từ đồng nghĩa"""
        if word1 not in self.synonyms:
            self.synonyms[word1] = []
        if word2 not in self.synonyms[word1]:
            self.synonyms[word1].append(word2)
        
        if word2 not in self.synonyms:
            self.synonyms[word2] = []
        if word1 not in self.synonyms[word2]:
            self.synonyms[word2].append(word1)
        
        self._save_json(self.synonyms_file, self.synonyms)
    
    def get_learning_stats(self) -> Dict:
        """Lấy thống kê học tập"""
        return {
            **self.feedback_stats,
            "total_patterns_learned": len(self.patterns),
            "total_synonym_pairs": len(self.synonyms),
            "interactions_with_feedback": sum(1 for i in self.interactions if i.get("rating", 0) > 0)
        }
    
    def suggest_improvements(self, query: str, current_answer: str) -> List[str]:
        """Gợi ý cách cải thiện câu trả lời dựa trên những tương tác tương tự"""
        suggestions = []
        
        # Tìm câu hỏi tương tự
        similar = self.find_similar_learned_answers(query, top_k=5)
        
        if similar:
            suggestions.append(f"💡 Tìm thấy {len(similar)} câu hỏi tương tự")
            for idx, sim in enumerate(similar[:2], 1):
                if sim["similarity"] > 0.5:
                    suggestions.append(f"  {idx}. Câu hỏi tương tự: '{sim['query']}' "
                                     f"(được đánh giá {sim['rating']}/5)")
        
        # Gợi ý dựa trên patterns
        query_tokens = self._tokenize(query)
        related_patterns = []
        
        for token in query_tokens:
            if token in self.patterns:
                freq = self.patterns[token]["frequency"]
                if freq > 2:
                    related_patterns.append((token, freq))
        
        if related_patterns:
            related_patterns.sort(key=lambda x: x[1], reverse=True)
            suggestions.append(f"🔑 Các từ khóa chính: {', '.join([p[0] for p in related_patterns[:3]])}")
        
        return suggestions
    
    def _normalize_query(self, query: str) -> str:
        """Chuẩn hóa query: viết thường, bỏ dấu"""
        query = query.lower()
        # Bỏ các ký tự đặc biệt nhưng giữ từ
        query = re.sub(r'[^\w\sàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', '', query)
        return query.strip()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tách từ từ text"""
        text = self._normalize_query(text)
        # Bỏ các stop words phổ biến
        stop_words = {'các', 'và', 'hay', 'là', 'được', 'để', 'trong', 'ở', 'về', 'từ', 'với', 
                     'như', 'cái', 'cái gì', 'gì', 'ai', 'không', 'có', 'bạn', 'tôi', 'mình'}
        
        tokens = text.split()
        return [t for t in tokens if t not in stop_words and len(t) > 2]
    
    def _generate_id(self) -> str:
        """Tạo ID unique cho interaction"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_top_questions(self, limit: int = 10) -> List[Dict]:
        """Lấy những câu hỏi được hỏi nhiều nhất"""
        question_counts = Counter()
        for inter in self.interactions:
            normalized = inter.get("query_normalized", "")
            if normalized:
                question_counts[normalized] += 1
        
        top = question_counts.most_common(limit)
        
        result = []
        for normalized_q, count in top:
            # Tìm câu hỏi gốc tương ứng
            for inter in self.interactions:
                if inter.get("query_normalized") == normalized_q:
                    result.append({
                        "question": inter["query"],
                        "count": count,
                        "avg_rating": inter.get("rating", 0)
                    })
                    break
        
        return result
    
    def export_learned_data(self, output_dir: str = "data/learned_exports"):
        """Export dữ liệu học được để phân tích"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export all interactions with high rating
        high_quality = [i for i in self.interactions if i.get("rating", 0) >= 4]
        with open(os.path.join(output_dir, "high_quality_qa.json"), 'w', encoding='utf-8') as f:
            json.dump(high_quality, f, ensure_ascii=False, indent=2)
        
        # Export patterns
        with open(os.path.join(output_dir, "patterns.json"), 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)
        
        # Export stats
        stats = self.get_learning_stats()
        with open(os.path.join(output_dir, "stats.json"), 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported learned data to {output_dir}")


# Global instance
_learning_engine = None

def get_learning_engine() -> LearningEngine:
    """Get hoặc tạo global learning engine instance"""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine
