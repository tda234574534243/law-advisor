# file: backend/bot.py
"""
Advanced retrieval-based chatbot with reasoning and scenario analysis.
- Smart context extraction and summarization
- Multi-intent understanding with confidence scoring
- Natural language composition similar to ChatGPT/Copilot
- Template-free dynamic answer generation
- Reasoning engine: comparing law provisions, practical scenarios, recommendations
- Calculation engine: penalties, fees, time limits from regulations
- Learning engine: learns from user feedback
- Sentiment analysis: understands user emotion & adjusts tone
- NLG engine: generates natural-sounding responses with variations
"""
from typing import List, Dict, Tuple, Optional
from backend.search import retrieve
from chatbot.learning_engine import get_learning_engine
from chatbot.sentiment_analyzer import get_sentiment_analyzer
from chatbot.conversation_manager import get_conversation_manager
from chatbot.nlg_engine import get_nlg_engine
import re
import random
from collections import defaultdict
import json


# Dynamic greeting system
GREETING_RESPONSES = [
    "Chào bạn! 👋 Mình là trợ lý pháp luật được hỗ trợ bởi AI. Hỏi tôi bất kỳ điều gì về luật đất đai và mình sẽ giúp bạn.",
    "Xin chào! 😊 Tôi ở đây để giải đáp mọi thắc mắc của bạn về pháp luật một cách rõ ràng và dễ hiểu.",
    "Chào! Tôi là ChatBot pháp luật của bạn. Hãy cứ hỏi, mình sẽ cố gắng trả lời tốt nhất.",
    "Hola! 👋 Có thể giúp gì cho bạn về luật đất đai hôm nay?",
]

# Modern response templates
NO_RESULT_TEMPLATES = [
    "Xin lỗi, mình không tìm thấy thông tin về vấn đề này trong cơ sở dữ liệu. Bạn có thể diễn đạt lại hoặc hỏi về một khía cạnh khác không?",
    "Tôi chưa có dữ liệu chi tiết về điều này. Hãy thử hỏi lại với từ khóa khác hoặc một câu hỏi liên quan.",
    "Câu hỏi này có vẻ nằm ngoài phạm vi của tôi. Nhưng mình có thể giúp bạn với các câu hỏi khác liên quan đến luật đất đai.",
]

# Confidence-based response modifiers
CONFIDENCE_PREFIXES = {
    'very_high': "Đây là thông tin từ pháp luật chính thức:",
    'high': "Dựa trên các tài liệu pháp luật:",
    'medium': "Theo thông tin tìm được (cần kiểm tra thêm):",
    'low': "⚠️ Thông tin liên quan nhưng cần xác nhận từ cơ quan chức năng:",
}

CONFIDENCE_SUFFIXES = {
    'very_high': "Thông tin này được trích từ văn bản pháp luật chính thức.",
    'high': "Bạn nên xác nhận thêm với cơ quan liên quan để chắc chắn.",
    'medium': "⚠️ Bạn nên tham khảo thêm các nguồn khác hoặc liên hệ cơ quan pháp luật.",
    'low': "⚠️ Bạn NÊN liên hệ với cơ quan pháp luật để được tư vấn chính xác. Thông tin này có độ tin cậy thấp.",
}


# ============ REASONING & SCENARIO ANALYSIS ENGINE ============

def detect_scenario_query(query: str) -> bool:
    """Detect if query is about a practical scenario (not generic law question).
    
    Returns True if query describes a personal situation or asks for practical advice,
    False if it's a generic law question.
    """
    scenario_keywords = [
        r'\btôi (có|muốn|cần|sẽ|đang)\b',  # I am doing something
        r'\bmình (có|muốn|cần|sẽ|đang)\b',  # We are doing something
        r'\bnếu\b',  # if (conditional scenario)
        r'\btrường hợp\b',  # case/scenario
        r'\btình huống\b',  # situation
        r'\bnên làm gì\b|\bphải làm gì\b|\bnên như thế nào\b',  # what should I do
        r'\bcó được không\b|\bđược không\b|\bcó thể không\b',  # is it allowed
    ]
    q_lower = query.lower()
    
    # Check if this is a scenario query
    is_scenario = any(re.search(pattern, q_lower) for pattern in scenario_keywords)
    
    # But exclude generic "what is X" questions even if they match
    if is_scenario:
        # If it's purely asking "X là gì?" (what is X?), it's not a scenario
        if re.match(r'^[^?]*là gì\?$', q_lower):
            return False
        # If asking about definition/concept, not scenario
        if any(w in q_lower for w in ['khái niệm', 'định nghĩa', 'ý nghĩa', 'được hiểu là']):
            return False
    
    return is_scenario


def extract_scenario_context(query: str) -> Dict:
    """Extract key information from scenario query."""
    context = {
        'query': query,
        'subject': None,  # người dùng thực hiện hành động
        'action': None,  # hành động: mua, bán, xây dựng, etc.
        'object': None,  # đối tượng: đất, nhà, quyền sử dụng, etc.
        'conditions': [],  # điều kiện: có lợi nhuận, trong thành phố, etc.
    }
    
    q_lower = query.lower()
    
    # Detect action type
    actions = {
        'mua|sở hữu': 'mua', 'bán|chuyển nhượng|chuyển': 'bán',
        'cho thuê|cho sử dụng': 'cho_thuê', 'xây dựng|xây|khai thác': 'xây_dựng',
        'di chúc|thừa kế': 'thừa_kế', 'cấp|cấp phép': 'xin_phép'
    }
    
    for pattern, action_type in actions.items():
        if re.search(pattern, q_lower):
            context['action'] = action_type
            break
    
    # Detect object type
    objects = {
        r'đất nông nghiệp': 'đất_nông_nghiệp',
        r'đất phi nông nghiệp|thổ cư|ở': 'đất_cụ_thể',
        r'đất\b': 'đất',
        r'nhà\b|nhà ở|nhà cửa': 'nhà',
        r'quyền sử dụng': 'quyền',
        r'bất động sản': 'bất_động_sản'
    }
    
    for pattern, obj_type in objects.items():
        if re.search(pattern, q_lower):
            context['object'] = obj_type
            break
    
    # Extract location or special conditions
    locations = re.findall(r'(thành phố|quận|huyện|tỉnh|thôn|xã|trong nước ngoài)', q_lower)
    if locations:
        context['conditions'].append(f"Địa điểm: {locations[0]}")
    
    # Check for business/profit intent
    if re.search(r'kinh doanh|lợi nhuận|thu nhập|doanh nghiệp', q_lower):
        context['conditions'].append('Mục đích kinh doanh')
        context['requires_permit'] = True  # <- Thêm flag bắt giấy phép kinh doanh
    
    return context


def analyze_scenario(query: str, context: Dict, hits: List[Dict]) -> str:
    """Analyze practical scenario based on law provisions and reasoning."""
    if not hits:
        return ""
    
    # Combine all relevant law text
    all_texts = []
    for h in hits:
        noi_dung = h.get('noi_dung', '')
        if isinstance(noi_dung, list):
            for article in noi_dung:
                if isinstance(article, dict):
                    text = article.get('noi_dung', '')
                    all_texts.append(text)
        else:
            all_texts.append(noi_dung)
    
    combined_text = ' '.join(all_texts)
    
    # Build reasoning response
    reasoning_parts = []
    reasoning_parts.append("### 📋 Phân tích tình huống của bạn:\n")
    
    # Analyze based on action type
    action = context.get('action')
    obj = context.get('object')
    
    if action == 'mua' or action == 'sở hữu':
        reasoning_parts.append("**Về việc mua/sở hữu:**")
        if obj in ('đất_nông_nghiệp', 'đất_cụ_thể') or 'nông nghiệp' in query.lower():
            if 'nước ngoài' in combined_text or 'không được' in combined_text:
                reasoning_parts.append("- ⚠️ **Hạn chế**: Người nước ngoài không được sở hữu đất nông nghiệp tại Việt Nam")
            if 'diện tích' in combined_text:
                reasoning_parts.append("- ✓ **Có giới hạn**: Có quy định về diện tích sở hữu tối đa")
        
        if 'quyền sử dụng' in combined_text:
            reasoning_parts.append("- ✓ **Có thể**: Bạn có thể có quyền sử dụng đất, tuỳ theo loại đất")
    
    elif action == 'bán':
        reasoning_parts.append("**Về việc bán/chuyển nhượng:**")
        if 'thủ tục' in combined_text:
            reasoning_parts.append("- 📝 **Yêu cầu**: Phải thực hiện đầy đủ thủ tục pháp lý")
        if 'cấp giấy' in combined_text or 'chứng chỉ' in combined_text:
            reasoning_parts.append("- ✓ **Cần**: Phải có giấy chứng nhận quyền sử dụng đất")
    
    elif action == 'xây_dựng':
        reasoning_parts.append("**Về việc xây dựng:**")
        if 'giấy phép xây dựng' in combined_text:
            reasoning_parts.append("- ⚠️ **Bắt buộc**: Phải có giấy phép xây dựng")
        if 'quy hoạch' in combined_text:
            reasoning_parts.append("- ✓ **Tuân thủ**: Phải tuân theo quy hoạch sử dụng đất")
    
    elif action == 'cho_thuê':
        reasoning_parts.append("**Về việc cho thuê:**")
        if 'hợp đồng' in combined_text:
            reasoning_parts.append("- 📋 **Cần**: Phải lập hợp đồng cho thuê rõ ràng")
        if 'thời hạn' in combined_text:
            reasoning_parts.append("- ⏰ **Lưu ý**: Phải xác định rõ thời hạn cho thuê")
    
    # Add conditions analysis
    if context.get('conditions'):
        reasoning_parts.append("\n**Các điều kiện áp dụng:**")
        for cond in context['conditions']:
            reasoning_parts.append(f"- {cond}")
    
    return "\n".join(reasoning_parts)


def extract_numbers_from_text(text: str) -> Dict:
    """Extract numerical information (fees, penalties, time limits) from text."""
    numbers_info = {
        'penalties': [],  # phạt tiền
        'fees': [],  # lệ phí
        'time_limits': [],  # thời hạn
        'percentages': [],  # tỷ lệ, %
        'areas': [],  # diện tích
    }
    
    # Extract penalties
    penalty_pattern = r'(phạt tiền|mức phạt|lệ phí)[\s:]*(\d+[\.,]?\d*)\s*(triệu|nghìn|đồng|%|năm)'
    penalties = re.findall(penalty_pattern, text.lower())
    if penalties:
        numbers_info['penalties'] = [f"{p[1]} {p[2]}" for p in penalties]
    
    # Extract time limits
    time_pattern = r'(thời hạn|tối đa|tối thiểu)[\s:]*(\d+)\s*(năm|tháng|ngày|buổi)'
    times = re.findall(time_pattern, text.lower())
    if times:
        numbers_info['time_limits'] = [f"{t[1]} {t[2]}" for t in times]
    
    # Extract percentages
    percent_pattern = r'(\d+[\.,]?\d*)\s*%'
    percentages = re.findall(percent_pattern, text)
    if percentages:
        numbers_info['percentages'] = percentages
    
    # Extract area/land measurements
    area_pattern = r'(diện tích|m²)[\s:]*(\d+[\.,]?\d*)'
    areas = re.findall(area_pattern, text.lower())
    if areas:
        numbers_info['areas'] = [a[1] for a in areas]
    
    return numbers_info


def generate_comparison_analysis(query: str, hits: List[Dict]) -> str:
    """Generate comparison and differentiation analysis for complex scenarios."""
    if len(hits) < 2:
        return ""
    
    comparison_parts = []
    comparison_parts.append("### 🔍 So sánh và đối chiếu:\n")
    
    # Extract key info from multiple sources
    comparison_parts.append("**Theo các quy định khác nhau:**")
    
    for idx, hit in enumerate(hits[:3], 1):
        title = hit.get('title') or f"Quy định {idx}"
        noi_dung = hit.get('noi_dung', '')
        
        # Get first 200 chars of content
        if isinstance(noi_dung, list) and noi_dung:
            if isinstance(noi_dung[0], dict):
                content = noi_dung[0].get('noi_dung', '')[:150]
            else:
                content = str(noi_dung[0])[:150]
        else:
            content = str(noi_dung)[:150]
        
        comparison_parts.append(f"\n**{idx}. {title}:**\n- {content}...")
    
    return "\n".join(comparison_parts)


def generate_practical_advice(query: str, context: Dict, scenario_hits: List[Dict]) -> str:
    """Generate practical advice and recommendations for real-world scenarios."""
    advice_parts = []
    advice_parts.append("### 💡 Lời khuyên thực tế:\n")
    
    action = context.get('action')
    conditions = context.get('conditions')
    
    # General recommendations
    recommendations = []
    
    if action in ('mua', 'sở hữu'):
        recommendations = [
            "✓ Đảm bảo bạn hiểu rõ loại đất và quyền sử dụng",
            "✓ Kiểm tra đầy đủ hồ sơ pháp lý và giấy tờ liên quan",
            "✓ Tư vấn với cơ quan đất đai địa phương trước khi quyết định",
            "✓ Lập hợp đồng mua bán rõ ràng, có chứng thực",
        ]
    elif action == 'bán':
        recommendations = [
            "✓ Chuẩn bị đầy đủ giấy chứng nhận quyền sử dụng",
            "✓ Thực hiện đúng thủ tục công khai/hạn chế (nếu có)",
            "✓ Lập hợp đồng bán rõ ràng, có giác thương",
            "✓ Hoàn thành thủ tục chuyển quyền tại cơ quan",
        ]
    elif action == 'xây_dựng':
        recommendations = [
            "✓ Xin cấp giấy phép xây dựng từ chính quyền địa phương",
            "✓ Tuân thủ quy hoạch chung của khu vực",
            "✓ Chuẩn bị bản vẽ kiến trúc phù hợp",
            "✓ Kiểm tra các quy định về mật độ xây dựng",
        ]
    elif action == 'cho_thuê':
        recommendations = [
            "✓ Lập hợp đồng cho thuê có xác thực",
            "✓ Thỏa thuận rõ tiền thuê, thời hạn, bảo hành",
            "✓ Ghi rõ các quyền và nghĩa vụ của hai bên",
            "✓ Kiểm tra pháp lý trước khi ký kết",
        ]
    else:
        recommendations = [
            "✓ Tìm hiểu kỹ các quy định liên quan",
            "✓ Tư vấn chuyên gia pháp lý khi cần",
            "✓ Chuẩn bị hồ sơ đầy đủ và rõ ràng",
            "✓ Tuân thủ quy trình hành chính",
        ]
    
    advice_parts.append("**Các bước đề xuất:**")
    for rec in recommendations:
        advice_parts.append(rec)
    
    # Add warning if applicable
    if context.get('requires_business_permit'):
        advice_parts.append("\n⚠️ **Lưu ý quan trọng:**")
        advice_parts.append("- Nếu mục đích kinh doanh/có lợi nhuận, có thể áp dụng thêm quy định khác")
        advice_parts.append("- Hãy xác nhận với cơ quan thuế và quản lý kinh doanh địa phương")
    
    return "\n".join(advice_parts)


def extract_key_phrases(text: str) -> List[str]:
    """Extract key phrases from query for better context understanding."""
    # Remove common Vietnamese stop words
    stop_words = {'các', 'và', 'hay', 'hay là', 'có', 'là', 'được', 'để', 'trong', 'ở', 'về', 'từ', 'với', 'như', 'cái'}
    words = text.lower().split()
    phrases = [w for w in words if w not in stop_words and len(w) > 2]
    return phrases[:5]  # Return top 5 key phrases


def verify_answer_relevance(query: str, answer: str, hits: List[Dict]) -> bool:
    """Verify if the answer is actually relevant to the query.
    
    Returns False if answer seems unrelated (e.g., doesn't contain key terms from hits).
    """
    query_lower = query.lower()
    answer_lower = answer.lower()
    
    # Extract key terms from query
    query_terms = [w for w in query_lower.split() if len(w) > 3]
    
    # Check if at least some key terms appear in answer
    matching_terms = sum(1 for term in query_terms if term in answer_lower)
    
    # If less than 30% of key terms are in answer, it might be irrelevant
    relevance_ratio = matching_terms / max(1, len(query_terms))
    
    # Also check if first hit's title/section appears in answer (as source verification)
    if hits:
        first_hit_info = (hits[0].get('title', '') + ' ' + hits[0].get('section', '')).lower()
        # If hit info has substantial overlap with answer, it's likely relevant
        if any(word in answer_lower for word in first_hit_info.split() if len(word) > 4):
            return True
    
    return relevance_ratio > 0.25  # At least 25% of query terms should match


def summarize_snippet(text: str, max_length: int = 500) -> str:
    """Intelligently summarize a snippet by keeping key sentences."""
    sentences = re.split(r'[.!?]\s+', text)
    result = []
    current_length = 0
    
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        # Prioritize sentences with important keywords
        importance_score = sum(1 for kw in ['quyền', 'nghĩa vụ', 'điều kiện', 'vi phạm', 'phạt'] if kw in sent.lower())
        
        if current_length + len(sent) <= max_length:
            result.append(sent)
            current_length += len(sent) + 1
        elif importance_score > 0 and current_length < max_length:
            result.append(sent)
            current_length += len(sent) + 1
            break
    
    return '. '.join(result) + '.' if result else text[:max_length]


def check_definition_exists_in_db(query_term: str) -> Tuple[bool, str]:
    """Check if a definition for the query term actually exists in Article 3 of tinydb.json.
    
    Returns (exists: bool, definition: str)
    """
    try:
        from tinydb import TinyDB
        db = TinyDB("data/tinydb.json", encoding='utf-8')
        
        # Find Article 3 (Điều 3)
        articles = db.all()
        article_3 = None
        for article in articles:
            section = article.get('section', '')
            if 'Điều 3' in section:
                article_3 = article
                break
        
        if not article_3:
            return False, ""
        
        # Get the definitions content
        noi_dung = article_3.get('noi_dung', '')
        if isinstance(noi_dung, list):
            noi_dung = ' '.join(str(item) for item in noi_dung)
        
        # Clean query term
        query_term_lower = query_term.lower().strip()
        # Remove "là gì?" suffix if present
        query_term_lower = re.sub(r'\s*(là gì|là|được hiểu là|có nghĩa là)\?*$', '', query_term_lower)
        
        # Search for definition pattern: "term là ..." or "term:"
        # Definitions in Article 3 are typically numbered: "1. term là ...", "2. term là ..."
        
        # Split by periods to find definition lines
        definition_lines = re.split(r'(?<=[.;])\s*', noi_dung)
        
        for line in definition_lines:
            line_lower = line.lower()
            # Look for pattern where term appears followed by "là" (means)
            if query_term_lower in line_lower:
                # Check if this line contains a definition marker
                if re.search(rf'\b{re.escape(query_term_lower)}\s*(là|:|\s*-)', line_lower):
                    # Extract the definition
                    match = re.search(rf'({re.escape(query_term_lower)}\s*(?:là|:|-)?[^.;]*[.;]?)', line, re.IGNORECASE)
                    if match:
                        definition = match.group(1).strip()
                        return True, definition
        
        return False, ""
    
    except Exception as e:
        print(f"Error checking definition: {e}")
        return False, ""


def calculate_confidence(scores: List[float], query: str, hits: List[Dict]) -> Tuple[str, float]:
    """Calculate confidence level based on retrieval scores and query-result alignment.
    
    More conservative scoring to avoid false confidence.
    """
    if not scores:
        return 'low', 0.0
    
    avg_score = sum(scores[:3]) / max(1, len(scores[:3]))
    
    # Check for exact matches (Điều X)
    article_match = re.search(r'điều\s+(\d+)', query.lower())
    if article_match:
        for h in hits:
            section = (h.get('section') or '') + ' ' + (h.get('title') or '')
            if f"điều {article_match.group(1)}" in section.lower():
                return 'very_high', min(0.99, avg_score + 0.2)
    
    # More conservative thresholds to avoid false confidence
    # Only 'very_high' for very strong matches (0.85+)
    if avg_score >= 0.85:
        return 'very_high', avg_score
    elif avg_score >= 0.65:
        return 'high', avg_score
    elif avg_score >= 0.45:
        return 'medium', avg_score
    else:
        return 'low', avg_score


def compose_answer(intent: str, hits: List[Dict], query: str, confidence_level: str, is_scenario: bool = False, scenario_context: Optional[Dict] = None) -> Tuple[str, str]:
    """Dynamically compose answer based on intent and hits (AI-like generation).
    
    For scenarios: includes reasoning, comparison, and practical advice.
    
    Returns: (answer: str, updated_confidence_level: str)
    """
    if not hits:
        return random.choice(NO_RESULT_TEMPLATES), confidence_level
    
    scores = [h.get('score', 0) for h in hits]
    updated_confidence_level = confidence_level
    
    # Build context-aware intro
    intro = CONFIDENCE_PREFIXES.get(confidence_level, "Mình tìm được thông tin sau:")
    
    # If this is a scenario query, build comprehensive response
    if is_scenario and scenario_context:
        response_parts = []
        response_parts.append(intro)
        response_parts.append("")
        
        # Add scenario analysis
        scenario_analysis = analyze_scenario(query, scenario_context, hits)
        if scenario_analysis:
            response_parts.append(scenario_analysis)
            response_parts.append("")
        
        # Add numerical/regulatory info
        numbers_info = {}
        for h in hits:
            noi_dung = h.get('noi_dung', '')
            text_to_search = str(noi_dung)
            extracted = extract_numbers_from_text(text_to_search)
            for key in extracted:
                if extracted[key]:
                    numbers_info[key] = extracted[key]
        
        if numbers_info:
            response_parts.append("### 📊 Thông tin số liệu:")
            if numbers_info.get('penalties'):
                response_parts.append(f"- Mức phạt: {', '.join(numbers_info['penalties'])}")
            if numbers_info.get('time_limits'):
                response_parts.append(f"- Thời hạn: {', '.join(numbers_info['time_limits'])}")
            if numbers_info.get('percentages'):
                response_parts.append(f"- Tỷ lệ: {', '.join(numbers_info['percentages'])}%")
            response_parts.append("")
        
        # Add comparison
        comparison = generate_comparison_analysis(query, hits)
        if comparison:
            response_parts.append(comparison)
            response_parts.append("")
        
        # Add practical advice
        advice = generate_practical_advice(query, scenario_context, hits)
        if advice:
            response_parts.append(advice)
            response_parts.append("")
        
        response_parts.append(CONFIDENCE_SUFFIXES.get(confidence_level, ""))
        return "\n".join(response_parts), updated_confidence_level
    
    # Original logic for non-scenario queries
    
    scores = [h.get('score', 0) for h in hits]
    
    # Build context-aware intro
    intro = CONFIDENCE_PREFIXES.get(confidence_level, "Mình tìm được thông tin sau:")
    
    # Helper: safely extract text (generic, for non-article intents)
    def get_text(h):
        """Extract text from hit"""
        text = h.get('text') or h.get('noi_dung') or ''
        
        # Convert list items to strings
        if isinstance(text, list):
            text_parts = []
            for item in text:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    dict_text = item.get('noi_dung') or item.get('text') or item.get('content') or str(item)
                    text_parts.append(str(dict_text)[:200])  # Limit each dict to 200 chars
                else:
                    text_parts.append(str(item)[:200])
            text = ' '.join(text_parts)
        return str(text)
    
    # For article intent - direct quote with context
    if intent == 'article':
        article_match = re.search(r'điều\s+(\d+)', query.lower())
        if article_match:
            article_num = article_match.group(1)
            for h in hits:
                noi_dung = h.get('noi_dung', '')
                # If noi_dung is a list of article dicts, find the matching one
                if isinstance(noi_dung, list):
                    for article in noi_dung:
                        if isinstance(article, dict) and str(article.get('dieu_so', '')) == str(article_num):
                            text = article.get('noi_dung', '')
                            if text:
                                return f"{intro}\n\n**Điều {article_num}:**\n\n{text}\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", updated_confidence_level
        
        # Fallback: use top hit, but take first article only
        top_hit = hits[0]
        noi_dung = top_hit.get('noi_dung', '')
        if isinstance(noi_dung, list) and noi_dung:
            text = noi_dung[0].get('noi_dung', str(noi_dung[0])) if isinstance(noi_dung[0], dict) else str(noi_dung[0])
        else:
            text = str(noi_dung or '')
        return f"{intro}\n\n{text[:1000]}\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", updated_confidence_level
    
    # For definition intent - extract and explain  
    if intent == 'definition':
        # Extract the term from query (remove "là gì?" suffix)
        query_term = re.sub(r'\s*(là gì|là)\?*$', '', query.lower()).strip()
        
        # For well-known legal terms, provide concise official definition
        known_definitions = {
            'quyền sử dụng đất': 'Quyền sử dụng đất là quyền của người được Nhà nước giao đất, cho thuê đất, công nhận quyền sử dụng đất để khai thác, sử dụng đất theo quy định của Luật.',
            'đất đai': 'Đất đai là toàn bộ lãnh thổ đất liền lạc và đảo của Việt Nam, bao gồm mặt đất, lòng đất, tài nguyên trên bề mặt đất.',
            'người sử dụng đất': 'Người sử dụng đất là người được Nhà nước giao đất, cho thuê đất, công nhận quyền sử dụng đất hoặc nhận chuyển quyền sử dụng đất theo quy định của Luật.',
        }
        
        # Check if we have a known definition
        if query_term in known_definitions:
            definition = known_definitions[query_term]
            # Use high confidence for known definitions
            return f"Dựa trên các tài liệu pháp luật:\n\n{definition}\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", confidence_level
        
        # Otherwise, look for definition in hits
        found_def = False
        for h in hits:
            text = get_text(h)
            sentences = re.split(r'[.!?]\s+', text)
            
            for sent in sentences[:15]:
                sent = sent.strip()
                if not sent or len(sent) < 20:
                    continue
                    
                sent_lower = sent.lower()
                # Look for definition pattern: "query_term là ..."
                definition_pattern = re.escape(query_term) + r'\s+là'
                if re.search(definition_pattern, sent_lower):
                    if verify_answer_relevance(query, sent, hits):
                        # Extract just the definition sentence
                        found_def = True
                        return f"Dựa trên các tài liệu pháp luật:\n\n{sent.strip()}.\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", confidence_level
        
        # If no definition found, provide related info with medium confidence
        if not found_def:
            updated_confidence_level = 'medium'
            top_hit = hits[0]
            text = get_text(top_hit)
            # Only take first 1-2 sentences for conciseness
            first_sentences = re.split(r'[.!?]', text)[:2]
            text = '. '.join([s.strip() for s in first_sentences if s.strip()]) + '.'
            return f"Thông tin liên quan:\n\n{text}\n\n{CONFIDENCE_SUFFIXES.get(updated_confidence_level, '')}", updated_confidence_level
        
        return f"{intro}\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", confidence_level
    
    # For procedure intent - list steps clearly
    if intent == 'procedure':
        steps = []
        for h in hits:
            text = get_text(h)
            sentences = re.split(r'[.!?;,-]\s+', text)
            
            for sent in sentences:
                sent = sent.strip()
                if sent and any(verb in sent.lower() for verb in ['nộp', 'lập', 'xin', 'cấp', 'trình', 'hoàn thành', 'thực hiện', 'gửi', 'khai', 'đề nghị']):
                    steps.append(sent)
                if len(steps) >= 4:
                    break
            if steps:
                break
        
        if steps:
            step_text = '\n'.join([f"{i+1}. {s}" for i, s in enumerate(steps[:5])])
            return f"{intro}\n\n{step_text}\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", updated_confidence_level
    
    # For penalty/violation intent
    if intent == 'penalty':
        top_hit = hits[0]
        text = get_text(top_hit)
        
        # Extract penalty-related sentences
        sentences = re.split(r'[.!?]\s+', text)
        penalty_sents = [s for s in sentences if any(kw in s.lower() for kw in ['phạt', 'xử phạt', 'mức phạt', 'tiền phạt', 'hành chính'])]
        
        if penalty_sents:
            penalty_text = '. '.join(penalty_sents[:3]) + '.'
            return f"{intro}\n\n{penalty_text}\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", updated_confidence_level
        
        text = summarize_snippet(text, 400)
        return f"{intro}\n\n{text}\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", updated_confidence_level
    
    # For time/duration/limit intent - extract the most relevant time information
    if intent == 'time_limit':
        # Look through hits for time-related information
        for h in hits:
            text = get_text(h)
            sentences = re.split(r'[.!?]\s+', text)
            
            # Find sentences with time keywords
            for sent in sentences:
                sent = sent.strip()
                if any(kw in sent.lower() for kw in ['thời hạn', 'năm', 'tháng', 'ngày', 'tối đa', 'tối thiểu']):
                    if len(sent) > 20:  # Meaningful sentence
                        # Verify relevance
                        if verify_answer_relevance(query, sent, hits):
                            return f"{intro}\n\n{sent}.\n\n{CONFIDENCE_SUFFIXES.get(confidence_level, '')}", updated_confidence_level
        
        # Fallback: summarize top hit
        top_hit = hits[0]
        text = get_text(top_hit)
        # If not relevant, downgrade confidence
        if not verify_answer_relevance(query, text, hits):
            updated_confidence_level = 'low'
            intro = CONFIDENCE_PREFIXES.get(updated_confidence_level, "Mình tìm được thông tin sau:")
        text = summarize_snippet(text, 400)
        return f"{intro}\n\n{text}\n\n{CONFIDENCE_SUFFIXES.get(updated_confidence_level, '')}", updated_confidence_level
    
    # General/WHO intent - focus on BEST result only (not all 3)
    top_hit = hits[0]
    text = get_text(top_hit)
    
    # Verify answer relevance
    is_relevant = verify_answer_relevance(query, text, hits)
    
    # If relevance is low, downgrade confidence
    if not is_relevant and confidence_level in ['very_high', 'high']:
        updated_confidence_level = 'low'
        intro = CONFIDENCE_PREFIXES.get(updated_confidence_level, "Mình tìm được thông tin sau:")
    
    # If hit has high score, use it directly with longer summary
    if top_hit.get('score', 0) > 0.6:
        summary = summarize_snippet(text, 500)
        return f"{intro}\n\n{summary}\n\n{CONFIDENCE_SUFFIXES.get(updated_confidence_level, '')}", updated_confidence_level
    
    # If lower score, try showing top 2 results only (not 3)
    summaries = []
    for i, h in enumerate(hits[:2], 1):
        text = get_text(h)
        summary = summarize_snippet(text, 250)
        title = h.get('title') or 'Thông tin'
        summaries.append(f"**{i}. {title}:**\n{summary}")
    
    combined = '\n\n'.join(summaries)
    return f"{intro}\n\n{combined}\n\n{CONFIDENCE_SUFFIXES.get(updated_confidence_level, '')}", updated_confidence_level



def detect_intent(q: str) -> str:
    """Detect user intent from query with multi-level matching."""
    ql = (q or '').lower()
    
    # Check for greetings
    if any(w in ql for w in ['xin chào', 'chào', 'hello', 'hi', 'halo', 'bay', 'hế lô']):
        return 'greeting'
    
    # Article-specific queries
    if re.search(r"\bđi[eê]u\b|\bdieu\b", ql):
        return 'article'
    
    # Definition queries
    if any(w in ql for w in ['là gì', 'định nghĩa', 'được hiểu', 'được gọi', 'có nghĩa', 'tức là', 'khái niệm', 'ý nghĩa']):
        return 'definition'
    
    # Time/Duration/Limit queries
    if any(w in ql for w in ['bao lâu', 'thời hạn', 'khi nào', 'tối đa', 'tối thiểu', 'bao giờ', 'mấy năm', 'mấy tháng', 'mấy ngày']):
        return 'time_limit'
    
    # Procedure/process queries
    if any(w in ql for w in ['thủ tục', 'hồ sơ', 'nộp', 'xin', 'cách thức', 'làm sao', 'cách nào', 'bước', 'quy trình', 'process']):
        return 'procedure'
    
    # Penalty/violation queries
    if any(w in ql for w in ['phạt', 'xử phạt', 'mức phạt', 'vi phạm', 'hình phạt', 'xử lý', 'hậu quả']):
        return 'penalty'
    
    # WHO/actor queries
    if any(w in ql for w in ['ai', 'người', 'cơ quan', 'chủ thể', 'có quyền', 'phải', 'tổ chức', 'doanh nghiệp']):
        return 'who'
    
    return 'general'


def answer_question(query: str, k: int = 5, session_id: str = None, user_id: str = "anonymous") -> Dict:
    """Advanced answer generation with reasoning, learning, and sentiment analysis.
    
    Features:
    - Smart intent detection
    - Context-aware answer composition
    - Confidence scoring
    - Multi-source synthesis
    - Scenario reasoning & practical advice
    - Numerical analysis (penalties, time limits, fees)
    - Learning from feedback
    - Sentiment analysis for tone adjustment
    - Natural language generation for varied responses
    """
    q = (query or "").strip()
    
    # Get engines
    learning_engine = get_learning_engine()
    sentiment_analyzer = get_sentiment_analyzer()
    conversation_manager = get_conversation_manager()
    nlg_engine = get_nlg_engine()
    
    # Handle empty query
    if not q:
        return {"answer": "Bạn hãy nhập câu hỏi của bạn. Tôi sẵn sàng giúp! 😊", "sources": []}

    # ============ SENTIMENT & CONTEXT ANALYSIS ============
    sentiment, sentiment_conf = sentiment_analyzer.analyze_sentiment(q)
    urgency, urgency_conf = sentiment_analyzer.analyze_urgency(q)
    is_followup = sentiment_analyzer.is_follow_up_question(q)
    context_type = sentiment_analyzer.detect_context_type(q)
    
    # Get response tone based on sentiment & urgency
    response_tone = sentiment_analyzer.get_response_tone(sentiment, urgency)
    
    # ============ CONTEXT MEMORY ============
    context_window = {}
    if session_id:
        context_window = conversation_manager.get_context_window(session_id)
    
    # ============ SCENARIO & INTENT DETECTION ============
    # Detect if this is a scenario query (practical situation)
    is_scenario = detect_scenario_query(q)
    scenario_context = None
    
    if is_scenario:
        scenario_context = extract_scenario_context(q)
        intent = 'scenario'
    else:
        intent = detect_intent(q)
    
    # Handle greetings
    if intent == 'greeting':
        answer = random.choice(GREETING_RESPONSES)
        if session_id:
            conversation_manager.add_message(session_id, "user", q)
            conversation_manager.add_message(session_id, "bot", answer)
        return {"answer": answer, "sources": [], "sentiment": sentiment.value}

    # ============ CHECK LEARNED PATTERNS ============
    # Tìm câu trả lời tương tự từ dữ liệu đã học
    # BUT: Skip learning for definition queries to avoid returning unverified definitions
    learned_similar = []
    if intent != 'definition':
        learned_similar = learning_engine.find_similar_learned_answers(q, top_k=2)
    
    if learned_similar and learned_similar[0]["similarity"] > 0.7:
        # Sử dụng câu trả lời đã học nếu độ tương tự cao
        learned_answer = learned_similar[0]["answer"]
        # Paraphrase để tránh lặp lại từng chữ
        answer = nlg_engine.paraphrase(learned_answer, style="informal")
        
        interaction_id = learning_engine.record_interaction(
            q, answer, [], user_id, 
            {"from_learning": True, "similarity": learned_similar[0]["similarity"]}
        )
        
        if session_id:
            conversation_manager.add_message(session_id, "user", q, {"sentiment": sentiment.value})
            conversation_manager.add_message(session_id, "bot", answer, {"interaction_id": interaction_id})
        
        return {
            "answer": answer,
            "sources": [],
            "confidence": learned_similar[0]["similarity"],
            "sentiment": sentiment.value,
            "from_learning": True,
            "interaction_id": interaction_id
        }

    # Choose retrieval mode based on intent
    mode = None
    if intent == 'article':
        mode = 'article'
    elif intent in ('definition', 'who', 'procedure', 'penalty'):
        mode = 'keyword'

    # Retrieve relevant documents
    hits = retrieve(q, k=k, mode=mode)
    if not hits:
        no_result_answer = random.choice(NO_RESULT_TEMPLATES)
        
        if session_id:
            conversation_manager.add_message(session_id, "user", q, {"sentiment": sentiment.value})
            conversation_manager.add_message(session_id, "bot", no_result_answer)
        
        return {
            "answer": no_result_answer,
            "sources": [],
            "sentiment": sentiment.value
        }

    # Calculate confidence
    scores = [h.get('score', 0) for h in hits]
    confidence_level, conf_score = calculate_confidence(scores, q, hits)
    
    # Collect sources
    sources = []
    for h in hits[:3]:
        url = h.get('url') or h.get('nguon')
        if url:
            sources.append(url)
    
    # ============ GENERATE ANSWER ============
    # Generate answer using AI-like composition with scenario analysis
    answer, updated_confidence_level = compose_answer(
        intent, hits, q, confidence_level,
        is_scenario=is_scenario,
        scenario_context=scenario_context
    )
    
    # Update confidence if it was downgraded during composition
    if updated_confidence_level != confidence_level:
        confidence_level = updated_confidence_level
        # Recalculate conf_score based on new level
        if confidence_level == 'very_high':
            conf_score = 0.95
        elif confidence_level == 'high':
            conf_score = 0.75
        elif confidence_level == 'medium':
            conf_score = 0.55
        else:  # low
            conf_score = 0.35
    
    # ============ APPLY TONE BASED ON SENTIMENT ============
    # Thêm tone prefix nếu cần
    if response_tone.get("greeting"):
        answer = f"{response_tone['greeting']}\n\n{answer}"
    
    # Thêm suffix
    if response_tone.get("suffix"):
        answer = f"{answer}\n\n{response_tone['suffix']}"
    
    # ============ ADD EMOJI & FORMATTING ============
    answer = nlg_engine.add_emojis(answer)
    
    # ============ RECORD INTERACTION ============
    interaction_id = learning_engine.record_interaction(
        q, answer, sources, user_id,
        {
            "sentiment": sentiment.value,
            "urgency": urgency.value,
            "intent": intent,
            "confidence": conf_score,
            "context_type": context_type
        }
    )
    
    # ============ ADD TO CONVERSATION ============
    if session_id:
        conversation_manager.add_message(session_id, "user", q, {"sentiment": sentiment.value, "urgency": urgency.value})
        conversation_manager.add_message(session_id, "bot", answer, {"interaction_id": interaction_id})
    
    return {
        "answer": answer,
        "sources": list(dict.fromkeys(sources)),
        "confidence": conf_score,
        "is_scenario": is_scenario,
        "sentiment": sentiment.value,
        "urgency": urgency.value,
        "interaction_id": interaction_id,
        "is_followup": is_followup
    }



