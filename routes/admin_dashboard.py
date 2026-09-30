"""Router dashboard ringkasan admin."""
from flask import render_template

from core.auth import admin_required
from core.sync_engine import get_last_sync_time
from models import budaya as budaya_model
from models import growth as growth_model
from models import knowledge as knowledge_model
from models import ratings as ratings_model
from models import wisata as wisata_model
from utils.timezone import format_wit


@admin_required
def admin_dashboard():
    avg_score_raw = ratings_model.average_approved_score()
    stats = {
        "total_budaya": budaya_model.count_public(),
        "total_wisata": wisata_model.count_public(),
        "total_ratings": ratings_model.count_all(),
        "total_docs": knowledge_model.count_all(),
        "avg_score": round(avg_score_raw, 2) if avg_score_raw else 0,
        "last_sync": get_last_sync_time(),
        "last_sync_label": format_wit(get_last_sync_time(), empty="Belum pernah"),
    }

    dist = ratings_model.distribution_approved()
    total_approved = sum(dist.values())
    distribution = [
        {"star": star, "count": dist[star], "pct": round(dist[star] * 100 / total_approved) if total_approved else 0}
        for star in range(5, 0, -1)
    ]

    # Penanda sync disimpan UTC (aware), sedangkan updated_at MySQL naive waktu
    # lokal server; samakan dulu ke naive lokal sebelum dibandingkan.
    last_sync = stats["last_sync"]
    if last_sync is not None and last_sync.tzinfo is not None:
        last_sync = last_sync.astimezone().replace(tzinfo=None)

    # Konten "belum tersinkron": dokumen yang belum ter-index, plus artikel
    # budaya/wisata yang dibuat/diubah setelah sinkronisasi terakhir.
    unsynced = {
        "dokumen": knowledge_model.count_unindexed(),
        "budaya": budaya_model.count_changed_since(last_sync),
        "wisata": wisata_model.count_changed_since(last_sync),
    }
    unsynced_total = sum(unsynced.values())

    kpis = [
        {
            "key": "budaya", "label": "Artikel Budaya", "value": stats["total_budaya"],
            "unit": "artikel", "growth": growth_model.growth("budaya"),
            "link": "admin_budaya_manage", "link_label": "Kelola budaya",
        },
        {
            "key": "wisata", "label": "Destinasi Wisata", "value": stats["total_wisata"],
            "unit": "destinasi", "growth": growth_model.growth("wisata"),
            "link": "admin_wisata_manage", "link_label": "Kelola wisata",
        },
        {
            "key": "ulasan", "label": "Ulasan Masuk", "value": stats["total_ratings"],
            "unit": "ulasan", "growth": growth_model.growth("ratings"),
            "link": "admin_rating_manage", "link_label": "Moderasi ulasan",
        },
    ]

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        kpis=kpis,
        distribution=distribution,
        total_approved=total_approved,
        top_wisata=wisata_model.top_rated(5),
        unsynced=unsynced,
        unsynced_total=unsynced_total,
    )


def register(app):
    app.add_url_rule("/admin/dashboard", endpoint="admin_dashboard", view_func=admin_dashboard)
