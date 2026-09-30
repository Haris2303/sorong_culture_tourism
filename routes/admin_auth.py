"""Router autentikasi admin: login & logout."""
from flask import Response, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from core import captcha
from extensions import limiter
from models import admins as admins_model


def admin_login():
    # Admin yang sudah masuk tidak perlu melihat halaman login lagi.
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        # CAPTCHA diperiksa lebih dulu (dan sekali pakai): tebakan password tidak diproses
        # tanpa kode yang benar, dan pesan galatnya tidak membocorkan status username.
        if not captcha.verify(session, request.form.get("captcha", "")):
            flash("Kode keamanan salah atau kedaluwarsa. Coba lagi dengan gambar yang baru.", "error")
            return render_template("admin/login.html")
        admin = admins_model.find_by_username(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["nama_lengkap"]
            flash("Berhasil masuk sebagai admin.", "success")
            next_url = request.args.get("next", "")
            # Hanya path internal ("/admin/..."); tolak URL absolut / protocol-relative ("//host").
            if not next_url.startswith("/") or next_url.startswith("//") or "\\" in next_url:
                next_url = url_for("admin_dashboard")
            return redirect(next_url)
        flash("Username atau password salah.", "error")
    return render_template("admin/login.html")


def admin_captcha():
    """Gambar CAPTCHA baru (PNG). Tiap permintaan menggantikan kode sebelumnya di session."""
    response = Response(captcha.issue_image(session), mimetype="image/png")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


def admin_logout():
    session.clear()
    flash("Anda telah keluar.", "success")
    return redirect(url_for("admin_login"))


def register(app):
    app.add_url_rule(
        "/admin/login", endpoint="admin_login",
        view_func=limiter.limit("10 per minute", methods=["POST"])(admin_login), methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/admin/captcha.png", endpoint="admin_captcha",
        view_func=limiter.limit("30 per minute")(admin_captcha), methods=["GET"],
    )
    app.add_url_rule("/admin/logout", endpoint="admin_logout", view_func=admin_logout)
