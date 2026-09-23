"""Error handler global (404 & 429)."""
from flask import jsonify, render_template


def not_found(e):
    return render_template("public/404.html"), 404


def ratelimited(e):
    return jsonify({"error": "Terlalu banyak permintaan. Silakan coba lagi nanti."}), 429


def register(app):
    app.register_error_handler(404, not_found)
    app.register_error_handler(429, ratelimited)
