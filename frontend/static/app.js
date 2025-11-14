// file: static/app.js

let currentSessionId = null;
let lastInteractionId = null;
let userId = localStorage.getItem('userId') || 'user_' + Math.random().toString(36).substr(2, 9);

// Save userId to localStorage
localStorage.setItem('userId', userId);

async function postJSON(url, body) {
  const r = await fetch(url, { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' }, 
    body: JSON.stringify(body) 
  });
  return r.json();
}

function addMessage(text, who, metadata = {}) {
  const chatBox = document.getElementById('chatBox');
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${who === 'user' ? 'user-message' : 'bot-message'}`;
  
  // Format markdown-like content
  let formattedText = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/###\s+(.*?)(<br>)/g, '<h4>$1</h4>');
  
  msgDiv.innerHTML = formattedText;
  msgDiv.dataset.interactionId = metadata.interaction_id || '';
  msgDiv.dataset.role = who;
  
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function showFeedbackArea(interactionId) {
  lastInteractionId = interactionId;
  const feedbackArea = document.getElementById('feedbackArea');
  feedbackArea.classList.add('active');
  
  // Create rating stars
  const ratingDiv = document.getElementById('ratingStars');
  ratingDiv.innerHTML = '';
  for (let i = 1; i <= 5; i++) {
    const star = document.createElement('span');
    star.className = 'star';
    star.textContent = '⭐';
    star.dataset.rating = i;
    star.onclick = () => selectRating(i);
    ratingDiv.appendChild(star);
  }
}

function selectRating(rating) {
  const stars = document.querySelectorAll('.star');
  stars.forEach((s, idx) => {
    if (idx < rating) {
      s.classList.add('active');
    } else {
      s.classList.remove('active');
    }
  });
}

function closeFeedback() {
  document.getElementById('feedbackArea').classList.remove('active');
  document.getElementById('feedbackText').value = '';
  lastInteractionId = null;
}

async function submitFeedback() {
  if (!lastInteractionId) return;
  
  const rating = document.querySelectorAll('.star.active').length || 3;
  const feedback = document.getElementById('feedbackText').value;
  
  try {
    const resp = await postJSON('/api/feedback', {
      interaction_id: lastInteractionId,
      rating: rating,
      feedback: feedback
    });
    
    alert(resp.message || 'Cảm ơn phản hồi của bạn!');
    closeFeedback();
    loadStats();
  } catch (e) {
    alert('Lỗi: ' + e);
  }
}

async function doSearch() {
  const q = document.getElementById('q').value;
  if (!q) return;
  
  const modeEl = document.getElementById('mode');
  const mode = modeEl ? modeEl.value : undefined;
  
  addMessage(`<strong>Tìm kiếm:</strong> ${q}`, 'user');
  addMessage('⏳ Đang tìm...', 'bot');
  
  try {
    const r = await postJSON('/api/search', { q: q, k: 6, mode: mode });
    
    // Remove loading message
    const chatBox = document.getElementById('chatBox');
    const loadingMsg = chatBox.querySelector('.bot-message');
    if (loadingMsg && loadingMsg.textContent.includes('Đang tìm')) {
      loadingMsg.remove();
    }
    
    if (!r.results || r.results.length === 0) {
      addMessage('<i>❌ Không tìm thấy kết quả</i>', 'bot');
      return;
    }
    
    let html = '<div class="results">';
    r.results.forEach(it => {
      html += `<div class="res">
        <strong>${it.section || 'Kết quả'}</strong>
        <div>${it.text}</div>
        <div class="small">
          <span>Score: ${Number(it.score).toFixed(3)}</span>
          ${it.url ? `<a href="${it.url}" target="_blank" class="sources">📄 Xem thêm</a>` : ''}
        </div>
      </div>`;
    });
    html += '</div>';
    addMessage(html, 'bot');
  } catch (e) {
    addMessage('❌ Lỗi: ' + e, 'bot');
  }
}

async function doChat() {
  const q = document.getElementById('q').value;
  if (!q) return;
  
  // Create session if not exists
  if (!currentSessionId) {
    const sessionResp = await postJSON('/api/session/create', {
      user_id: userId,
      session_name: 'Chat Session'
    });
    currentSessionId = sessionResp.session_id;
  }
  
  addMessage(`<strong>${q}</strong>`, 'user');
  addMessage('⏳ Chatbot đang trả lời...', 'bot');
  
  try {
    const r = await postJSON('/api/chat', {
      q: q,
      session_id: currentSessionId,
      user_id: userId
    });
    
    // Remove loading message
    const chatBox = document.getElementById('chatBox');
    const loadingMsg = chatBox.querySelector('.bot-message:last-child');
    if (loadingMsg && loadingMsg.textContent.includes('Chatbot đang')) {
      loadingMsg.remove();
    }
    
    let response = r.answer || 'Không có câu trả lời';
    
    // Add metadata
    const metadata = {
      interaction_id: r.interaction_id
    };
    
    addMessage(response, 'bot', metadata);
    
    // Add info
    let infoHtml = '<div class="stats" style="margin-top: 10px; font-size: 12px;">';
    if (r.confidence) {
      infoHtml += `📊 Độ tin cậy: ${(r.confidence * 100).toFixed(0)}% | `;
    }
    if (r.sentiment) {
      infoHtml += `😊 Tâm trạng: ${r.sentiment} | `;
    }
    if (r.urgency) {
      infoHtml += `⏰ Mức độ: ${r.urgency}`;
    }
    infoHtml += '</div>';
    
    // Add feedback button
    let feedbackHtml = `<div style="margin-top: 10px;">
      <button class="secondary" style="padding: 6px 12px; font-size: 12px;" 
              onclick="showFeedbackArea('${r.interaction_id}')">👍 Đánh giá câu trả lời</button>
    </div>`;
    
    const lastMsg = chatBox.lastChild;
    if (lastMsg) {
      lastMsg.innerHTML += infoHtml + feedbackHtml;
    }
    
    document.getElementById('q').value = '';
  } catch (e) {
    addMessage('❌ Lỗi: ' + e, 'bot');
  }
}

async function rebuildIndex() {
  if (!confirm('Rebuild index sẽ mất một chút thời gian. Tiếp tục?')) return;
  
  try {
    const r = await postJSON('/api/build_index', {});
    alert('✅ ' + (r.message || 'Index đã rebuild thành công'));
  } catch (e) {
    alert('❌ Lỗi: ' + e);
  }
}

async function loadStats() {
  try {
    const r = await postJSON('/api/learning-stats', {});
    
    let statsHtml = `
      <strong>📈 Thống kê học tập:</strong><br>
      • Tổng interactions: ${r.total_interactions}<br>
      • Feedback tích cực: ${r.positive_feedback}<br>
      • Feedback tiêu cực: ${r.negative_feedback}<br>
      • Trung bình rating: ${r.avg_rating.toFixed(2)}/5<br>
      • Patterns đã học: ${r.total_patterns_learned}<br>
      • Cặp từ đồng nghĩa: ${r.total_synonym_pairs}
    `;
    
    document.getElementById('stats').innerHTML = statsHtml;
  } catch (e) {
    console.error('Error loading stats:', e);
  }
}

window.onload = () => {
  document.getElementById('btnSearch').onclick = doSearch;
  document.getElementById('btnChat').onclick = doChat;
  document.getElementById('btnReindex').onclick = rebuildIndex;
  
  if (document.getElementById('btnStats')) {
    document.getElementById('btnStats').onclick = loadStats;
  }
  
  // Allow Enter key in textarea
  document.getElementById('q').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doChat();
    }
  });
  
  // Load initial stats
  loadStats();
};
