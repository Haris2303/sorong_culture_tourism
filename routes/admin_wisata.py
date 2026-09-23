"""Router CRUD admin untuk destinasi wisata."""
from flask import flash, redirect, render_template, request, url_for

from core.auth import admin_required
from models import wisata as wisata_model
from utils.pagination import PAGE_SIZE, paginate

TIKET_OPTIONS = ["Gratis / Menyesuaikan", "Rp 5.000", "Rp 10.000", "Rp 15.000", "Rp 20.000"]


@admin_required
def admin_wisata_manage():
    if request.method == "POST":
        edit_id = request.form.get("id")
        _, warnings = wisata_model.save_from_form(request.form, request.files, edit_id=edit_id)
        for warning in warnings:
            flash(warning, "error")
        flash(
            "Data wisata berhasil diperbarui." if edit_id else "Data wisata berhasil ditambahkan.",
            "success",
        )
        return redirect(url_for("admin_wisata_manage"))

    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int) or 1

    total = wisata_model.count_admin(q)
    pagination = paginate(total, page, PAGE_SIZE)
    items = wisata_model.list_admin(q, pagination["per_page"], pagination["offset"])
    for item in items:
        item["galeri"] = wisata_model.list_galeri_full(item["id"])

    return render_template(
        "admin/wisata_manage.html", items=items, q=q, tiket_options=TIKET_OPTIONS, pagination=pagination
    )


@admin_required
def admin_wisata_delete(wisata_id):
    wisata_model.delete(wisata_id)
    flash("Data wisata dihapus.", "success")
    return redirect(url_for("admin_wisata_manage"))


@admin_required
def admin_wisata_galeri_delete(galeri_id):
    if wisata_model.delete_galeri_photo(galeri_id):
        flash("Foto galeri dihapus.", "success")
    return redirect(url_for("admin_wisata_manage"))


@admin_required
def admin_wisata_gambar_delete(wisata_id):
    if wisata_model.delete_gambar_utama(wisata_id):
        flash("Gambar utama dihapus.", "success")
    return redirect(url_for("admin_wisata_manage"))


def register(app):
    app.add_url_rule(
        "/admin/wisata", endpoint="admin_wisata_manage", view_func=admin_wisata_manage, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/admin/wisata/<int:wisata_id>/delete", endpoint="admin_wisata_delete",
        view_func=admin_wisata_delete, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/wisata/galeri/<int:galeri_id>/delete", endpoint="admin_wisata_galeri_delete",
        view_func=admin_wisata_galeri_delete, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/wisata/<int:wisata_id>/gambar/delete", endpoint="admin_wisata_gambar_delete",
        view_func=admin_wisata_gambar_delete, methods=["POST"],
    )
