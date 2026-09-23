"""Router moderasi ulasan/rating wisata oleh admin."""
from flask import flash, redirect, render_template, request, url_for

from core.auth import admin_required
from models import ratings as ratings_model


@admin_required
def admin_rating_manage():
    items = ratings_model.list_all_with_wisata()
    return render_template("admin/rating_manage.html", items=items)


@admin_required
def admin_rating_status(rating_id):
    new_status = request.form.get("status")
    if new_status not in ("approved", "pending", "rejected"):
        flash("Status tidak valid.", "error")
        return redirect(url_for("admin_rating_manage"))
    ratings_model.update_status(rating_id, new_status)
    flash("Status ulasan diperbarui.", "success")
    return redirect(url_for("admin_rating_manage"))


@admin_required
def admin_rating_delete(rating_id):
    ratings_model.delete(rating_id)
    flash("Ulasan dihapus.", "success")
    return redirect(url_for("admin_rating_manage"))


def register(app):
    app.add_url_rule("/admin/ratings", endpoint="admin_rating_manage", view_func=admin_rating_manage)
    app.add_url_rule(
        "/admin/ratings/<int:rating_id>/status", endpoint="admin_rating_status",
        view_func=admin_rating_status, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/ratings/<int:rating_id>/delete", endpoint="admin_rating_delete",
        view_func=admin_rating_delete, methods=["POST"],
    )
