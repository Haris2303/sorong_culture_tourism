"""Router autentikasi admin: login & logout."""
from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from models import admins as admins_model


def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = admins_model.find_by_username(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["nama_lengkap"]
            flash("Berhasil masuk sebagai admin.", "success")
            next_url = request.args.get("next") or url_for("admin_dashboard")
            return redirect(next_url)
        flash("Username atau password salah.", "error")
    return render_template("admin/login.html")


def admin_logout():
    session.clear()
    flash("Anda telah keluar.", "success")
    return redirect(url_for("admin_login"))


def register(app):
    app.add_url_rule("/admin/login", endpoint="admin_login", view_func=admin_login, methods=["GET", "POST"])
    app.add_url_rule("/admin/logout", endpoint="admin_logout", view_func=admin_logout)
