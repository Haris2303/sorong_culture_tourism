"""Sistem Informasi & Chatbot Budaya-Wisata Sorong Raya.

Router utama: Portal Publik, API Chatbot RAG, API Rating Anti-Spam, dan Dashboard Admin.
"""
import os
import functools
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, session, jsonify, flash
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from core import db as dbcore
from core.security import generate_fingerprint, get_client_ip, contains_badword
from core.rag_engine import answer_query
from core.sync_engine import run_sync, get_last_sync_time

app = Flask(__name__)
app.config.from_object(Config)

dbcore.init_app(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=app.config["RATELIMIT_STORAGE_URI"],
    default_limits=[app.config["RATELIMIT_DEFAULT"]],
)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["KNOWLEDGE_DOCS_DIR"], exist_ok=True)
os.makedirs(app.config["CHROMA_PERSIST_DIR"], exist_ok=True)

BUDAYA_KATEGORI_OPTIONS = ["Tarian Tradisional", "Alat Musik", "Seni Ukir", "Upacara Adat"]
WISATA_TIKET_OPTIONS = ["Gratis / Menyesuaikan", "Rp 5.000", "Rp 10.000", "Rp 15.000", "Rp 20.000"]


# ============================================================
# Helpers
# ============================================================

def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def trimmed_average(scores: list[int]) -> float:
    """Rata-rata dengan pemotongan nilai ekstrem (trimmed mean) agar tahan outlier."""
    if not scores:
        return 0.0
    if len(scores) < 5:
        return round(sum(scores) / len(scores), 1)
    ordered = sorted(scores)
    trim_count = max(1, len(ordered) // 10)
    trimmed = ordered[trim_count:-trim_count] or ordered
    return round(sum(trimmed) / len(trimmed), 1)


def get_wisata_rating_summary(wisata_id: int) -> dict:
    rows = dbcore.query_all(
        "SELECT skor_bintang FROM ratings WHERE wisata_id = %s AND status_tampil = 'approved'",
        (wisata_id,),
    )
    scores = [r["skor_bintang"] for r in rows]
    return {"average": trimmed_average(scores), "count": len(scores)}


def save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in app.config["ALLOWED_IMAGE_EXT"]:
        return None
    filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file_storage.filename}")
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return filename


def save_uploaded_doc(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in app.config["ALLOWED_DOC_EXT"]:
        return None, None
    filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file_storage.filename}")
    file_storage.save(os.path.join(app.config["KNOWLEDGE_DOCS_DIR"], filename))
    return filename, ext


@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


# ============================================================
# PUBLIC ROUTES
# ============================================================

@app.route("/")
def index():
    highlight_budaya = dbcore.query_all(
        "SELECT id, judul, kategori, ringkasan, gambar FROM budaya ORDER BY created_at DESC LIMIT 3"
    )
    highlight_wisata = dbcore.query_all(
        "SELECT id, nama_wisata, wilayah, deskripsi, gambar FROM wisata ORDER BY created_at DESC LIMIT 3"
    )
    for w in highlight_wisata:
        w["rating"] = get_wisata_rating_summary(w["id"])

    stats = {
        "total_budaya": dbcore.query_one("SELECT COUNT(*) AS c FROM budaya")["c"],
        "total_wisata": dbcore.query_one("SELECT COUNT(*) AS c FROM wisata")["c"],
        "total_ulasan": dbcore.query_one(
            "SELECT COUNT(*) AS c FROM ratings WHERE status_tampil = 'approved'"
        )["c"],
    }

    return render_template(
        "public/index.html",
        highlight_budaya=highlight_budaya,
        highlight_wisata=highlight_wisata,
        stats=stats,
    )


@app.route("/budaya")
def budaya_list():
    kategori = request.args.get("kategori", "").strip()
    if kategori:
        rows = dbcore.query_all(
            "SELECT id, judul, kategori, ringkasan, gambar FROM budaya WHERE kategori = %s ORDER BY created_at DESC",
            (kategori,),
        )
    else:
        rows = dbcore.query_all(
            "SELECT id, judul, kategori, ringkasan, gambar FROM budaya ORDER BY created_at DESC"
        )
    kategori_list = dbcore.query_all("SELECT DISTINCT kategori FROM budaya ORDER BY kategori")
    return render_template("public/budaya.html", items=rows, kategori_list=kategori_list, active_kategori=kategori)


@app.route("/budaya/<int:budaya_id>")
def budaya_detail(budaya_id):
    item = dbcore.query_one("SELECT * FROM budaya WHERE id = %s", (budaya_id,))
    if not item:
        return render_template("public/404.html"), 404
    return render_template("public/budaya_detail.html", item=item)


@app.route("/wisata")
def wisata_list():
    wilayah = request.args.get("wilayah", "").strip()
    if wilayah:
        rows = dbcore.query_all(
            "SELECT id, nama_wisata, wilayah, deskripsi, gambar FROM wisata WHERE wilayah = %s ORDER BY created_at DESC",
            (wilayah,),
        )
    else:
        rows = dbcore.query_all(
            "SELECT id, nama_wisata, wilayah, deskripsi, gambar FROM wisata ORDER BY created_at DESC"
        )
    for r in rows:
        r["rating"] = get_wisata_rating_summary(r["id"])
    return render_template("public/wisata.html", items=rows, active_wilayah=wilayah)


@app.route("/wisata/<int:wisata_id>")
def wisata_detail(wisata_id):
    item = dbcore.query_one("SELECT * FROM wisata WHERE id = %s", (wisata_id,))
    if not item:
        return render_template("public/404.html"), 404
    ratings = dbcore.query_all(
        "SELECT skor_bintang, komentar, created_at FROM ratings "
        "WHERE wisata_id = %s AND status_tampil = 'approved' ORDER BY created_at DESC",
        (wisata_id,),
    )
    summary = get_wisata_rating_summary(wisata_id)
    return render_template("public/wisata_detail.html", item=item, ratings=ratings, summary=summary)


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    budaya_results, wisata_results = [], []
    if q:
        like = f"%{q}%"
        budaya_results = dbcore.query_all(
            "SELECT id, judul, kategori, ringkasan, gambar FROM budaya "
            "WHERE judul LIKE %s OR ringkasan LIKE %s OR konten_lengkap LIKE %s LIMIT 20",
            (like, like, like),
        )
        wisata_results = dbcore.query_all(
            "SELECT id, nama_wisata, wilayah, deskripsi, gambar FROM wisata "
            "WHERE nama_wisata LIKE %s OR deskripsi LIKE %s LIMIT 20",
            (like, like),
        )
    return render_template("public/search.html", q=q, budaya_results=budaya_results, wisata_results=wisata_results)


# ============================================================
# API: CHATBOT RAG
# ============================================================

@app.route("/api/chat", methods=["POST"])
@limiter.limit("20 per minute")
def api_chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("message") or "").strip()
    if not question:
        return jsonify({"error": "Pesan tidak boleh kosong."}), 400
    if len(question) > 500:
        return jsonify({"error": "Pesan terlalu panjang (maks 500 karakter)."}), 400

    try:
        result = answer_query(question)
    except Exception:
        return jsonify({
            "answer": "Maaf, terjadi kendala teknis pada asisten virtual kami. Silakan coba lagi sebentar lagi.",
            "sources": [],
        }), 200

    return jsonify({"answer": result["answer"], "sources": result["sources"]})


# ============================================================
# API: RATING ANTI-SPAM
# ============================================================

@app.route("/api/rating", methods=["POST"])
@limiter.limit("3 per hour")
def api_rating():
    payload = request.get_json(silent=True) or {}
    wisata_id = payload.get("wisata_id")
    skor = payload.get("skor_bintang")
    komentar = (payload.get("komentar") or "").strip()

    if not wisata_id or not isinstance(skor, int) or not (1 <= skor <= 5):
        return jsonify({"error": "Data rating tidak valid."}), 400

    wisata = dbcore.query_one("SELECT id FROM wisata WHERE id = %s", (wisata_id,))
    if not wisata:
        return jsonify({"error": "Destinasi wisata tidak ditemukan."}), 404

    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    fingerprint = generate_fingerprint(ip_address, user_agent)

    status = "pending" if contains_badword(komentar) else "approved"

    rating_id, err = dbcore.execute_unique_safe(
        "INSERT INTO ratings (wisata_id, skor_bintang, komentar, ip_address_hash, status_tampil) "
        "VALUES (%s, %s, %s, %s, %s)",
        (wisata_id, skor, komentar or None, fingerprint, status),
    )

    if err is not None:
        return jsonify({"error": "Perangkat ini sudah pernah memberi ulasan untuk destinasi ini."}), 409

    message = (
        "Terima kasih! Ulasan Anda sedang menunggu moderasi admin."
        if status == "pending"
        else "Terima kasih atas ulasan Anda!"
    )
    return jsonify({"success": True, "status": status, "message": message}), 201


# ============================================================
# ADMIN: AUTH
# ============================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = dbcore.query_one("SELECT * FROM admins WHERE username = %s", (username,))
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["nama_lengkap"]
            flash("Berhasil masuk sebagai admin.", "success")
            next_url = request.args.get("next") or url_for("admin_dashboard")
            return redirect(next_url)
        flash("Username atau password salah.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Anda telah keluar.", "success")
    return redirect(url_for("admin_login"))


# ============================================================
# ADMIN: DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    total_budaya = dbcore.query_one("SELECT COUNT(*) AS c FROM budaya")["c"]
    total_wisata = dbcore.query_one("SELECT COUNT(*) AS c FROM wisata")["c"]
    total_ratings = dbcore.query_one("SELECT COUNT(*) AS c FROM ratings")["c"]
    pending_ratings = dbcore.query_one("SELECT COUNT(*) AS c FROM ratings WHERE status_tampil = 'pending'")["c"]
    total_docs = dbcore.query_one("SELECT COUNT(*) AS c FROM knowledge_docs")["c"]
    avg_row = dbcore.query_one(
        "SELECT AVG(skor_bintang) AS avg_score FROM ratings WHERE status_tampil = 'approved'"
    )
    avg_score = round(avg_row["avg_score"], 2) if avg_row["avg_score"] else 0

    stats = {
        "total_budaya": total_budaya,
        "total_wisata": total_wisata,
        "total_ratings": total_ratings,
        "pending_ratings": pending_ratings,
        "total_docs": total_docs,
        "avg_score": avg_score,
        "last_sync": get_last_sync_time(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# ============================================================
# ADMIN: CRUD BUDAYA
# ============================================================

@app.route("/admin/budaya", methods=["GET", "POST"])
@admin_required
def admin_budaya_manage():
    if request.method == "POST":
        judul = request.form.get("judul", "").strip()
        kategori = request.form.get("kategori", "").strip()
        ringkasan = request.form.get("ringkasan", "").strip()
        konten = request.form.get("konten_lengkap", "").strip()
        gambar = save_uploaded_image(request.files.get("gambar"))

        edit_id = request.form.get("id")
        if edit_id:
            if gambar:
                dbcore.execute(
                    "UPDATE budaya SET judul=%s, kategori=%s, ringkasan=%s, konten_lengkap=%s, gambar=%s WHERE id=%s",
                    (judul, kategori, ringkasan, konten, gambar, edit_id),
                )
            else:
                dbcore.execute(
                    "UPDATE budaya SET judul=%s, kategori=%s, ringkasan=%s, konten_lengkap=%s WHERE id=%s",
                    (judul, kategori, ringkasan, konten, edit_id),
                )
            flash("Artikel budaya berhasil diperbarui.", "success")
        else:
            dbcore.execute(
                "INSERT INTO budaya (judul, kategori, ringkasan, konten_lengkap, gambar) VALUES (%s,%s,%s,%s,%s)",
                (judul, kategori, ringkasan, konten, gambar),
            )
            flash("Artikel budaya berhasil ditambahkan.", "success")
        return redirect(url_for("admin_budaya_manage"))

    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        items = dbcore.query_all(
            "SELECT * FROM budaya WHERE judul LIKE %s OR kategori LIKE %s OR ringkasan LIKE %s "
            "ORDER BY created_at DESC",
            (like, like, like),
        )
    else:
        items = dbcore.query_all("SELECT * FROM budaya ORDER BY created_at DESC")
    return render_template("admin/budaya_manage.html", items=items, q=q, kategori_options=BUDAYA_KATEGORI_OPTIONS)


@app.route("/admin/budaya/<int:budaya_id>/delete", methods=["POST"])
@admin_required
def admin_budaya_delete(budaya_id):
    dbcore.execute("DELETE FROM budaya WHERE id = %s", (budaya_id,))
    flash("Artikel budaya dihapus.", "success")
    return redirect(url_for("admin_budaya_manage"))


# ============================================================
# ADMIN: CRUD WISATA
# ============================================================

@app.route("/admin/wisata", methods=["GET", "POST"])
@admin_required
def admin_wisata_manage():
    if request.method == "POST":
        nama_wisata = request.form.get("nama_wisata", "").strip()
        wilayah = request.form.get("wilayah", "").strip()
        deskripsi = request.form.get("deskripsi", "").strip()
        fasilitas = request.form.get("fasilitas", "").strip()
        lokasi = request.form.get("lokasi", "").strip()
        tiket_choice = request.form.get("tiket_masuk", "").strip()
        if tiket_choice == "__custom__":
            tiket_masuk = request.form.get("tiket_masuk_custom", "").strip() or "Gratis / Menyesuaikan"
        else:
            tiket_masuk = tiket_choice or "Gratis / Menyesuaikan"
        jam_operasional = request.form.get("jam_operasional", "Setiap Hari").strip()
        gambar = save_uploaded_image(request.files.get("gambar"))

        edit_id = request.form.get("id")
        if edit_id:
            if gambar:
                dbcore.execute(
                    "UPDATE wisata SET nama_wisata=%s, wilayah=%s, deskripsi=%s, fasilitas=%s, lokasi=%s, "
                    "tiket_masuk=%s, jam_operasional=%s, gambar=%s WHERE id=%s",
                    (nama_wisata, wilayah, deskripsi, fasilitas, lokasi, tiket_masuk, jam_operasional, gambar, edit_id),
                )
            else:
                dbcore.execute(
                    "UPDATE wisata SET nama_wisata=%s, wilayah=%s, deskripsi=%s, fasilitas=%s, lokasi=%s, "
                    "tiket_masuk=%s, jam_operasional=%s WHERE id=%s",
                    (nama_wisata, wilayah, deskripsi, fasilitas, lokasi, tiket_masuk, jam_operasional, edit_id),
                )
            flash("Data wisata berhasil diperbarui.", "success")
        else:
            dbcore.execute(
                "INSERT INTO wisata (nama_wisata, wilayah, deskripsi, fasilitas, lokasi, tiket_masuk, jam_operasional, gambar) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (nama_wisata, wilayah, deskripsi, fasilitas, lokasi, tiket_masuk, jam_operasional, gambar),
            )
            flash("Data wisata berhasil ditambahkan.", "success")
        return redirect(url_for("admin_wisata_manage"))

    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        items = dbcore.query_all(
            "SELECT * FROM wisata WHERE nama_wisata LIKE %s OR wilayah LIKE %s OR lokasi LIKE %s "
            "ORDER BY created_at DESC",
            (like, like, like),
        )
    else:
        items = dbcore.query_all("SELECT * FROM wisata ORDER BY created_at DESC")
    return render_template("admin/wisata_manage.html", items=items, q=q, tiket_options=WISATA_TIKET_OPTIONS)


@app.route("/admin/wisata/<int:wisata_id>/delete", methods=["POST"])
@admin_required
def admin_wisata_delete(wisata_id):
    dbcore.execute("DELETE FROM wisata WHERE id = %s", (wisata_id,))
    flash("Data wisata dihapus.", "success")
    return redirect(url_for("admin_wisata_manage"))


# ============================================================
# ADMIN: MODERASI RATING
# ============================================================

@app.route("/admin/ratings")
@admin_required
def admin_rating_manage():
    rows = dbcore.query_all(
        "SELECT r.id, r.skor_bintang, r.komentar, r.status_tampil, r.created_at, "
        "w.nama_wisata FROM ratings r JOIN wisata w ON w.id = r.wisata_id "
        "ORDER BY r.created_at DESC"
    )
    return render_template("admin/rating_manage.html", items=rows)


@app.route("/admin/ratings/<int:rating_id>/status", methods=["POST"])
@admin_required
def admin_rating_status(rating_id):
    new_status = request.form.get("status")
    if new_status not in ("approved", "pending", "rejected"):
        flash("Status tidak valid.", "error")
        return redirect(url_for("admin_rating_manage"))
    dbcore.execute("UPDATE ratings SET status_tampil = %s WHERE id = %s", (new_status, rating_id))
    flash("Status ulasan diperbarui.", "success")
    return redirect(url_for("admin_rating_manage"))


@app.route("/admin/ratings/<int:rating_id>/delete", methods=["POST"])
@admin_required
def admin_rating_delete(rating_id):
    dbcore.execute("DELETE FROM ratings WHERE id = %s", (rating_id,))
    flash("Ulasan dihapus.", "success")
    return redirect(url_for("admin_rating_manage"))


# ============================================================
# ADMIN: KNOWLEDGE BASE & RE-TRAIN
# ============================================================

@app.route("/admin/knowledge")
@admin_required
def admin_knowledge():
    docs = dbcore.query_all("SELECT * FROM knowledge_docs ORDER BY uploaded_at DESC")
    return render_template("admin/knowledge_sync.html", docs=docs)


@app.route("/admin/knowledge/upload", methods=["POST"])
@admin_required
def admin_knowledge_upload():
    file = request.files.get("dokumen")
    filename, ext = save_uploaded_doc(file)
    if not filename:
        flash("Berkas tidak valid. Hanya PDF, TXT, atau MD yang diterima.", "error")
        return redirect(url_for("admin_knowledge"))
    dbcore.execute(
        "INSERT INTO knowledge_docs (nama_file, tipe_file, path_file, status_indexed) VALUES (%s,%s,%s,FALSE)",
        (file.filename, ext, filename),
    )
    flash("Dokumen berhasil diunggah. Jalankan sinkronisasi untuk melatih ulang RAG.", "success")
    return redirect(url_for("admin_knowledge"))


@app.route("/admin/knowledge/<int:doc_id>/delete", methods=["POST"])
@admin_required
def admin_knowledge_delete(doc_id):
    doc = dbcore.query_one("SELECT * FROM knowledge_docs WHERE id = %s", (doc_id,))
    if doc:
        path = os.path.join(app.config["KNOWLEDGE_DOCS_DIR"], doc["path_file"])
        if os.path.exists(path):
            os.remove(path)
        dbcore.execute("DELETE FROM knowledge_docs WHERE id = %s", (doc_id,))
        flash("Dokumen dihapus. Jalankan sinkronisasi ulang agar vector DB diperbarui.", "success")
    return redirect(url_for("admin_knowledge"))


@app.route("/admin/api/sync-knowledge", methods=["POST"])
@admin_required
def admin_sync_knowledge():
    try:
        result = run_sync()
    except Exception as exc:
        return jsonify({"success": False, "message": f"Gagal sinkronisasi: {exc}"}), 500
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("public/404.html"), 404


@app.errorhandler(429)
def ratelimited(e):
    return jsonify({"error": "Terlalu banyak permintaan. Silakan coba lagi nanti."}), 429


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"], threaded=True)
