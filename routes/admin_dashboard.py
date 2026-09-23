"""Router dashboard ringkasan admin."""
from flask import render_template

from core.auth import admin_required
from core.sync_engine import get_last_sync_time
from models import budaya as budaya_model
from models import knowledge as knowledge_model
from models import ratings as ratings_model
from models import wisata as wisata_model


@admin_required
def admin_dashboard():
    avg_score_raw = ratings_model.average_approved_score()
    stats = {
        "total_budaya": budaya_model.count_public(),
        "total_wisata": wisata_model.count_public(),
        "total_ratings": ratings_model.count_all(),
        "pending_ratings": ratings_model.count_pending(),
        "total_docs": knowledge_model.count_all(),
        "avg_score": round(avg_score_raw, 2) if avg_score_raw else 0,
        "last_sync": get_last_sync_time(),
    }
    return render_template("admin/dashboard.html", stats=stats)


def register(app):
    app.add_url_rule("/admin/dashboard", endpoint="admin_dashboard", view_func=admin_dashboard)
