"""Router CRUD admin untuk artikel budaya."""
from flask import flash, redirect, render_template, request, url_for

from core.auth import admin_required
from models import budaya as budaya_model
from utils.pagination import PAGE_SIZE, paginate

KATEGORI_OPTIONS = ["Tarian Tradisional", "Alat Musik", "Seni Ukir", "Upacara Adat"]


@admin_required
def admin_budaya_manage():
    if request.method == "POST":
        edit_id = request.form.get("id")
        budaya_model.save_from_form(request.form, request.files, edit_id=edit_id)
        flash(
            "Artikel budaya berhasil diperbarui." if edit_id else "Artikel budaya berhasil ditambahkan.",
            "success",
        )
        return redirect(url_for("admin_budaya_manage"))

    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int) or 1

    total = budaya_model.count_admin(q)
    pagination = paginate(total, page, PAGE_SIZE)
    items = budaya_model.list_admin(q, pagination["per_page"], pagination["offset"])
    for item in items:
        item["galeri"] = budaya_model.list_galeri_full(item["id"])

    return render_template(
        "admin/budaya_manage.html", items=items, q=q, kategori_options=KATEGORI_OPTIONS, pagination=pagination
    )


@admin_required
def admin_budaya_delete(budaya_id):
    budaya_model.delete(budaya_id)
    flash("Artikel budaya dihapus.", "success")
    return redirect(url_for("admin_budaya_manage"))


@admin_required
def admin_budaya_galeri_delete(galeri_id):
    if budaya_model.delete_galeri_photo(galeri_id):
        flash("Foto galeri dihapus.", "success")
    return redirect(url_for("admin_budaya_manage"))


@admin_required
def admin_budaya_gambar_delete(budaya_id):
    if budaya_model.delete_gambar_utama(budaya_id):
        flash("Gambar utama dihapus.", "success")
    return redirect(url_for("admin_budaya_manage"))


def register(app):
    app.add_url_rule(
        "/admin/budaya", endpoint="admin_budaya_manage", view_func=admin_budaya_manage, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/admin/budaya/<int:budaya_id>/delete", endpoint="admin_budaya_delete",
        view_func=admin_budaya_delete, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/budaya/galeri/<int:galeri_id>/delete", endpoint="admin_budaya_galeri_delete",
        view_func=admin_budaya_galeri_delete, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/budaya/<int:budaya_id>/gambar/delete", endpoint="admin_budaya_gambar_delete",
        view_func=admin_budaya_gambar_delete, methods=["POST"],
    )
