# file: app.py
from flask import Flask, render_template, request, jsonify
from backend.search import retrieve
from backend.db import insert_passage
from backend.bot import answer_question
from chatbot.learning_engine import get_learning_engine
from chatbot.sentiment_analyzer import get_sentiment_analyzer
from chatbot.conversation_manager import get_conversation_manager
import json, uuid, os
from config import TOP_K, HOST, PORT, DEBUG

app = Flask(__name__, static_folder="frontend/static", template_folder="frontend/templates")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    q = data.get("q", "")
    k = data.get("k", TOP_K)
    mode = data.get("mode", None)
    hits = retrieve(q, k=int(k), mode=mode)
    # format response
    out = []
    for h in hits:
        out.append({
            "title": h.get("title"),
            "section": h.get("section"),
            "text": (h.get("text")[:800] + "...") if len(h.get("text",""))>800 else h.get("text",""),
            "score": h.get("score", 0),
            "url": h.get("url")
        })
    return jsonify({"query": q, "results": out})

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    q = data.get("q","")
    session_id = data.get("session_id", None)
    user_id = data.get("user_id", "anonymous")
    
    # Use bot helper to compose answer from retrieval
    bot_resp = answer_question(q, k=5, session_id=session_id, user_id=user_id)
    
    # Return answer and confidence if present
    resp = {
        "answer": bot_resp.get("answer"),
        "sources": bot_resp.get("sources", []),
        "interaction_id": bot_resp.get("interaction_id"),
        "sentiment": bot_resp.get("sentiment"),
        "urgency": bot_resp.get("urgency"),
        "is_followup": bot_resp.get("is_followup", False)
    }
    if bot_resp.get("confidence") is not None:
        resp["confidence"] = bot_resp.get("confidence")
    return jsonify(resp)


@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    """Record user feedback on bot response"""
    data = request.get_json()
    interaction_id = data.get("interaction_id", "")
    rating = data.get("rating", 0)  # 1-5
    feedback_text = data.get("feedback", "")
    
    learning_engine = get_learning_engine()
    learning_engine.submit_feedback(interaction_id, rating, feedback_text)
    
    return jsonify({
        "status": "ok",
        "message": "Cảm ơn bạn vì phản hồi! Tôi sẽ cải thiện.",
        "interaction_id": interaction_id
    })


@app.route("/api/learning-stats", methods=["GET"])
def api_learning_stats():
    """Get learning engine statistics"""
    learning_engine = get_learning_engine()
    stats = learning_engine.get_learning_stats()
    return jsonify(stats)


@app.route("/api/session/create", methods=["POST"])
def api_create_session():
    """Create new conversation session"""
    data = request.get_json()
    user_id = data.get("user_id", "anonymous")
    session_name = data.get("session_name", "")
    
    conversation_manager = get_conversation_manager()
    session_id = conversation_manager.create_session(user_id, session_name)
    
    return jsonify({
        "status": "ok",
        "session_id": session_id
    })


@app.route("/api/session/<session_id>/stats", methods=["GET"])
def api_session_stats(session_id):
    """Get statistics for a session"""
    conversation_manager = get_conversation_manager()
    stats = conversation_manager.get_conversation_stats(session_id)
    return jsonify(stats)


@app.route("/api/session/<session_id>/context", methods=["GET"])
def api_session_context(session_id):
    """Get context from conversation"""
    window_size = request.args.get("window_size", 5, type=int)
    conversation_manager = get_conversation_manager()
    context = conversation_manager.get_context_window(session_id, window_size)
    return jsonify(context)


@app.route("/api/build_index", methods=["POST"])
def api_build_index():
    # rebuild TF-IDF index (blocking)
    from backend import indexer
    try:
        indexer.build_tfidf()
        return jsonify({"status": "ok", "message": "TF-IDF index rebuilt."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/export-learned", methods=["POST"])
def api_export_learned():
    """Export learned data"""
    learning_engine = get_learning_engine()
    try:
        learning_engine.export_learned_data()
        return jsonify({
            "status": "ok",
            "message": "Dữ liệu học được đã được export.",
            "location": "data/learned_exports"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__=="__main__":
    # Use configured host/port/debug from config.py
    app.run(host=HOST, port=PORT, debug=DEBUG)
