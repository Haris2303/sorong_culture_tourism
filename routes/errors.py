"""Error handler global (404, 413 & 429)."""
from flask import current_app, flash, jsonify, redirect, render_template, request, url_for


def not_found(e):
    return render_template("public/404.html"), 404


def request_entity_too_large(e):
    """Tangkap 413 (payload terlalu besar) dengan pesan jelas, bukan halaman error mentah.

    Bisa saja tetap kejadian walau gambar sudah dikompres di browser (mis. JS
    dimatikan, atau terlalu banyak foto galeri dipilih sekaligus).
    """
    max_mb = current_app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)
    message = (
        f"Data yang diunggah terlalu besar (maksimal {max_mb:.0f} MB per pengiriman). "
        "Kurangi jumlah foto galeri atau gunakan gambar berukuran lebih kecil, lalu coba lagi."
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"error": message}), 413

    flash(message, "error")
    target = request.referrer
    if target and target.startswith(request.host_url):
        return redirect(target)
    return redirect(url_for("admin_dashboard"))


def ratelimited(e):
    return jsonify({"error": "Terlalu banyak permintaan. Silakan coba lagi nanti."}), 429


def register(app):
    app.register_error_handler(404, not_found)
    app.register_error_handler(413, request_entity_too_large)
    app.register_error_handler(429, ratelimited)
