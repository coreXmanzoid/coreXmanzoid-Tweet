from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required

from app.services.ai_service import AIService
from app.decorators import verified_user, pro_user

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/Manzoid-AI", methods=["GET", "POST"])
@login_required
# @pro_user
@verified_user
def manzoid_ai():
    
    if request.method == "POST":

        data = request.get_json()

        if not data or "message" not in data or "user_id" not in data:
            return jsonify({"error": "Message and user_id are required"}), 400

        user_id = data["user_id"]
        message = data["message"].strip()

        if not message:
            return jsonify({"error": "Empty message"}), 400

        if len(message) > 130:
            return jsonify({"error": "Message too long"}), 400

        try:
            answer = AIService.chat(user_id, message)
            return jsonify({"reply": answer})

        except Exception as e:
            print("Groq error:", e)
            return jsonify({"error": "AI service unavailable"}), 503

    return render_template("AI.html")

@ai_bp.route("/api/ai/chat", methods=["POST"])
def ai_chat():

    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    prompt = data["message"].strip()

    if not prompt:
        return jsonify({"error": "Empty message"}), 400

    if len(prompt) > 100:
        return jsonify({"error": "Message too long"}), 400

    try:
        answer = AIService.simple_chat(prompt)
        return jsonify({"reply": answer})

    except Exception as e:
        print("Groq error:", e)
        return jsonify({"error": "AI service unavailable"}), 503