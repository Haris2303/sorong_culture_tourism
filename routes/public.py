"""Router publik: beranda, daftar & detail budaya/wisata, pencarian."""
from flask import render_template, request

from models import budaya as budaya_model
from models import ratings as ratings_model
from models import wisata as wisata_model
from services.pagination import PAGE_SIZE, paginate
from services.ratings_stats import get_wisata_rating_summary


def index():
    highlight_budaya = budaya_model.list_highlight(limit=3)
    highlight_wisata = wisata_model.list_highlight(limit=3)
    for w in highlight_wisata:
        w["rating"] = get_wisata_rating_summary(w["id"])

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
    )


def budaya_list():
    kategori = request.args.get("kategori", "").strip()
    page = request.args.get("page", 1, type=int) or 1

    total = budaya_model.count_public(kategori)
    pagination = paginate(total, page, PAGE_SIZE)
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

    return render_template("public/budaya_detail.html", item=item, galeri_images=galeri_images)


def wisata_list():
    wilayah = request.args.get("wilayah", "").strip()
    page = request.args.get("page", 1, type=int) or 1

    total = wisata_model.count_public(wilayah)
    pagination = paginate(total, page, PAGE_SIZE)
    rows = wisata_model.list_public(wilayah, pagination["per_page"], pagination["offset"])
    for r in rows:
        r["rating"] = get_wisata_rating_summary(r["id"])

    return render_template("public/wisata.html", items=rows, active_wilayah=wilayah, pagination=pagination)


def wisata_detail(wisata_id):
    item = wisata_model.get_by_id(wisata_id)
    if not item:
        return render_template("public/404.html"), 404
    ratings = ratings_model.list_approved_by_wisata(wisata_id)
    summary = get_wisata_rating_summary(wisata_id)

    galeri_images = [item["gambar"]] if item["gambar"] else []
    galeri_images += [g["gambar"] for g in wisata_model.list_galeri(wisata_id)]

    return render_template(
        "public/wisata_detail.html", item=item, ratings=ratings, summary=summary, galeri_images=galeri_images
    )


def search():
    q = request.args.get("q", "").strip()
    budaya_results, wisata_results = [], []
    if q:
        budaya_results = budaya_model.search(q, limit=20)
        wisata_results = wisata_model.search(q, limit=20)
    return render_template("public/search.html", q=q, budaya_results=budaya_results, wisata_results=wisata_results)


def register(app):
    app.add_url_rule("/", endpoint="index", view_func=index)
    app.add_url_rule("/budaya", endpoint="budaya_list", view_func=budaya_list)
    app.add_url_rule("/budaya/<int:budaya_id>", endpoint="budaya_detail", view_func=budaya_detail)
    app.add_url_rule("/wisata", endpoint="wisata_list", view_func=wisata_list)
    app.add_url_rule("/wisata/<int:wisata_id>", endpoint="wisata_detail", view_func=wisata_detail)
    app.add_url_rule("/search", endpoint="search", view_func=search)
