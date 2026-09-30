"""Context processor & filter Jinja global, dipakai lintas template."""
from datetime import datetime


def pending_review_count():
    """Jumlah ulasan menunggu moderasi (badge sidebar admin). Dipanggil lazy dari template."""
    from models import ratings as ratings_model
    try:
        return ratings_model.count_pending()
    except Exception:
        return 0


def footer_data():
    """Data footer publik: kategori budaya. Dipanggil lazy dari template."""
    data = {"kategori": []}
    try:
        from models import budaya as budaya_model

        data["kategori"] = [k["kategori"] for k in budaya_model.list_kategori_distinct()][:6]
    except Exception:
        pass
    return data


def inject_globals():
    return {
        "current_year": datetime.utcnow().year,
        "pending_review_count": pending_review_count,
        "footer_data": footer_data,
    }


def social_url_filter(value):
    """Pastikan link sosmed punya skema http(s), agar aman dipakai di href."""
    if not value:
        return "#"
    value = value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://{value}"


def register(app):
    app.context_processor(inject_globals)
    app.add_template_filter(social_url_filter, "social_url")
