"""Router API: chatbot RAG & pengiriman rating wisata (anti-spam)."""
from flask import jsonify, request

from core.rag_engine import answer_query
from core.security import contains_badword, generate_fingerprint, get_client_ip
from extensions import limiter
from models import ratings as ratings_model
from models import wisata as wisata_model


# Riwayat percakapan dikirim ulang oleh klien tiap request (chatbot-nya stateless).
# Dibatasi supaya prompt ke LLM tidak membengkak & tidak bisa dijejali kiriman besar.
MAX_HISTORY_MESSAGES = 6
MAX_HISTORY_CHARS = 600


def _clean_history(raw):
    if not isinstance(raw, list):
        return []
    cleaned = []
    for item in raw[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()[:MAX_HISTORY_CHARS]
        if text:
            cleaned.append({
                "role": "user" if item.get("role") == "user" else "bot",
                "text": text,
            })
    return cleaned


def api_chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("message") or "").strip()
    if not question:
        return jsonify({"error": "Pesan tidak boleh kosong."}), 400
    if len(question) > 500:
        return jsonify({"error": "Pesan terlalu panjang (maks 500 karakter)."}), 400

    try:
        result = answer_query(question, _clean_history(payload.get("history")))
    except Exception:
        return jsonify({
            "answer": "⚠️ Maaf, terjadi kendala teknis pada asisten virtual kami. Silakan coba lagi sebentar lagi.",
            "sources": [],
        }), 200

    return jsonify({"answer": result["answer"], "sources": result["sources"]})


def api_rating():
    payload = request.get_json(silent=True) or {}
    wisata_id = payload.get("wisata_id")
    skor = payload.get("skor_bintang")
    komentar = (payload.get("komentar") or "").strip()

    if not wisata_id or not isinstance(skor, int) or not (1 <= skor <= 5):
        return jsonify({"error": "Data rating tidak valid."}), 400

    if not wisata_model.exists(wisata_id):
        return jsonify({"error": "Destinasi wisata tidak ditemukan."}), 404

    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    fingerprint = generate_fingerprint(ip_address, user_agent)

    status = "pending" if contains_badword(komentar) else "approved"

    rating_id, err = ratings_model.create(wisata_id, skor, komentar, fingerprint, status)

    if err is not None:
        return jsonify({"error": "Perangkat ini sudah pernah memberi ulasan untuk destinasi ini."}), 409

    message = (
        "Terima kasih! Ulasan Anda sedang menunggu moderasi admin."
        if status == "pending"
        else "Terima kasih atas ulasan Anda!"
    )
    return jsonify({"success": True, "status": status, "message": message}), 201


def register(app):
    app.add_url_rule(
        "/api/chat", endpoint="api_chat",
        view_func=limiter.limit("20 per minute")(api_chat), methods=["POST"],
    )
    app.add_url_rule(
        "/api/rating", endpoint="api_rating",
        view_func=limiter.limit("3 per hour")(api_rating), methods=["POST"],
    )
