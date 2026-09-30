"""Router publik: beranda, daftar & detail budaya/wisata, pencarian."""
import os

from flask import current_app, render_template, request

from models import budaya as budaya_model
from models import ratings as ratings_model
from models import wisata as wisata_model
from utils.pagination import paginate

# Listing publik pakai grid 3 kolom (lihat .grid-3 di style.css), jadi 6
# kartu per halaman selalu memenuhi baris genap (2 baris penuh).
PUBLIC_PAGE_SIZE = 6


def _existing_photos(rows, limit):
    """Hanya item yang berkas fotonya benar-benar ada di folder upload (hindari gambar rusak)."""
    folder = current_app.config["UPLOAD_FOLDER"]
    ok = [r for r in rows if r.get("gambar") and os.path.exists(os.path.join(folder, r["gambar"]))]
    return ok[:limit]


def index():
    highlight_budaya = budaya_model.list_highlight(limit=3)
    highlight_wisata = wisata_model.list_highlight(limit=3)
    for w in highlight_wisata:
        w["rating"] = ratings_model.get_wisata_rating_summary(w["id"])

    stats = {
        "total_budaya": budaya_model.count_public(),
        "total_wisata": wisata_model.count_public(),
        "total_ulasan": ratings_model.count_approved(),
    }

    return render_template(
        "public/index.html",
        highlight_budaya=highlight_budaya,
        highlight_wisata=highlight_wisata,
        stats=stats,
        latest_reviews=ratings_model.list_latest_with_comment(3),
        about_wisata=_existing_photos(wisata_model.list_with_photo(8), 2),
        about_budaya=_existing_photos(budaya_model.list_with_photo(8), 1),
    )


def budaya_list():
    kategori = request.args.get("kategori", "").strip()
    page = request.args.get("page", 1, type=int) or 1

    total = budaya_model.count_public(kategori)
    pagination = paginate(total, page, PUBLIC_PAGE_SIZE)
    rows = budaya_model.list_public(kategori, pagination["per_page"], pagination["offset"])
    kategori_list = budaya_model.list_kategori_distinct()

    return render_template(
        "public/budaya.html", items=rows, kategori_list=kategori_list, active_kategori=kategori, pagination=pagination
    )


def budaya_detail(budaya_id):
    item = budaya_model.get_by_id(budaya_id)
    if not item:
        return render_template("public/404.html"), 404

    galeri_images = [item["gambar"]] if item["gambar"] else []
    galeri_images += [g["gambar"] for g in budaya_model.list_galeri(budaya_id)]

    # Artikel lain di kategori yang sama (kalau kurang, lengkapi dari kategori lain).
    related = [r for r in budaya_model.list_public(item["kategori"], 6, 0) if r["id"] != budaya_id]
    if len(related) < 3:
        extra = [r for r in budaya_model.list_public("", 6, 0) if r["id"] != budaya_id and r not in related]
        related += extra
    related = related[:3]

    return render_template(
        "public/budaya_detail.html", item=item, galeri_images=galeri_images, related=related
    )


def wisata_list():
    wilayah = request.args.get("wilayah", "").strip()
    page = request.args.get("page", 1, type=int) or 1

    total = wisata_model.count_public(wilayah)
    pagination = paginate(total, page, PUBLIC_PAGE_SIZE)
    rows = wisata_model.list_public(wilayah, pagination["per_page"], pagination["offset"])
    for r in rows:
        r["rating"] = ratings_model.get_wisata_rating_summary(r["id"])

    return render_template("public/wisata.html", items=rows, active_wilayah=wilayah, pagination=pagination)


def wisata_detail(wisata_id):
    item = wisata_model.get_by_id(wisata_id)
    if not item:
        return render_template("public/404.html"), 404
    ratings = ratings_model.list_approved_by_wisata(wisata_id)
    summary = ratings_model.get_wisata_rating_summary(wisata_id)

    galeri_images = [item["gambar"]] if item["gambar"] else []
    galeri_images += [g["gambar"] for g in wisata_model.list_galeri(wisata_id)]

    # Destinasi lain di wilayah yang sama (kalau kurang, lengkapi dari wilayah lain).
    related = [r for r in wisata_model.list_public(item["wilayah"], 6, 0) if r["id"] != wisata_id]
    if len(related) < 3:
        extra = [r for r in wisata_model.list_public("", 6, 0) if r["id"] != wisata_id and r not in related]
        related += extra
    related = related[:3]
    for r in related:
        r["rating"] = ratings_model.get_wisata_rating_summary(r["id"])

    return render_template(
        "public/wisata_detail.html",
        item=item, ratings=ratings, summary=summary, galeri_images=galeri_images, related=related,
    )


def search():
    q = request.args.get("q", "").strip()
    budaya_results, wisata_results = [], []
    if q:
        budaya_results = budaya_model.search(q, limit=20)
        wisata_results = wisata_model.search(q, limit=20)
        for w in wisata_results:
            w["rating"] = ratings_model.get_wisata_rating_summary(w["id"])
    return render_template("public/search.html", q=q, budaya_results=budaya_results, wisata_results=wisata_results)


def register(app):
    app.add_url_rule("/", endpoint="index", view_func=index)
    app.add_url_rule("/budaya", endpoint="budaya_list", view_func=budaya_list)
    app.add_url_rule("/budaya/<int:budaya_id>", endpoint="budaya_detail", view_func=budaya_detail)
    app.add_url_rule("/wisata", endpoint="wisata_list", view_func=wisata_list)
    app.add_url_rule("/wisata/<int:wisata_id>", endpoint="wisata_detail", view_func=wisata_detail)
    app.add_url_rule("/search", endpoint="search", view_func=search)
