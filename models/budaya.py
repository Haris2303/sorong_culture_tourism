"""Semua yang berhubungan dengan data budaya & galeri fotonya.

Bagian 1 (QUERY): fungsi baca/tulis langsung ke tabel `budaya` & `budaya_galeri`.
Bagian 2 (ATURAN BISNIS): fungsi tingkat lebih tinggi yang dipanggil router,
menggabungkan beberapa query + aturan (mis. "kalau upload gambar baru gagal,
gambar lama tetap dipakai") jadi satu langkah saja.
"""
from core import db as dbcore
from core.content import sanitize_content_html
from utils.uploads import delete_upload_file, save_uploaded_image, save_uploaded_images

LIST_FIELDS = "id, judul, kategori, ringkasan, gambar"


# ============================================================
# QUERY: baca & tulis tabel budaya + budaya_galeri
# ============================================================

def count_public(kategori=None):
    if kategori:
        return dbcore.query_one("SELECT COUNT(*) AS c FROM budaya WHERE kategori = %s", (kategori,))["c"]
    return dbcore.query_one("SELECT COUNT(*) AS c FROM budaya")["c"]


def list_public(kategori, limit, offset):
    if kategori:
        return dbcore.query_all(
            f"SELECT {LIST_FIELDS} FROM budaya WHERE kategori = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (kategori, limit, offset),
        )
    return dbcore.query_all(
        f"SELECT {LIST_FIELDS} FROM budaya ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )


def list_highlight(limit=3):
    return dbcore.query_all(
        f"SELECT {LIST_FIELDS} FROM budaya ORDER BY created_at DESC LIMIT %s", (limit,)
    )


def list_kategori_distinct():
    return dbcore.query_all("SELECT DISTINCT kategori FROM budaya ORDER BY kategori")


def get_by_id(budaya_id):
    return dbcore.query_one("SELECT * FROM budaya WHERE id = %s", (budaya_id,))


def get_title(budaya_id):
    return dbcore.query_one("SELECT judul FROM budaya WHERE id = %s", (budaya_id,))


def search(keyword, limit=20):
    like = f"%{keyword}%"
    return dbcore.query_all(
        f"SELECT {LIST_FIELDS} FROM budaya WHERE judul LIKE %s OR ringkasan LIKE %s OR konten_lengkap LIKE %s "
        "LIMIT %s",
        (like, like, like, limit),
    )


def count_admin(keyword=None):
    if keyword:
        like = f"%{keyword}%"
        return dbcore.query_one(
            "SELECT COUNT(*) AS c FROM budaya WHERE judul LIKE %s OR kategori LIKE %s OR ringkasan LIKE %s",
            (like, like, like),
        )["c"]
    return dbcore.query_one("SELECT COUNT(*) AS c FROM budaya")["c"]


def list_admin(keyword, limit, offset):
    if keyword:
        like = f"%{keyword}%"
        return dbcore.query_all(
            "SELECT * FROM budaya WHERE judul LIKE %s OR kategori LIKE %s OR ringkasan LIKE %s "
            "ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (like, like, like, limit, offset),
        )
    return dbcore.query_all(
        "SELECT * FROM budaya ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, offset)
    )


def create(judul, kategori, ringkasan, konten, gambar):
    return dbcore.execute(
        "INSERT INTO budaya (judul, kategori, ringkasan, konten_lengkap, gambar) VALUES (%s,%s,%s,%s,%s)",
        (judul, kategori, ringkasan, konten, gambar),
    )


def update(budaya_id, judul, kategori, ringkasan, konten, gambar=None):
    if gambar:
        dbcore.execute(
            "UPDATE budaya SET judul=%s, kategori=%s, ringkasan=%s, konten_lengkap=%s, gambar=%s WHERE id=%s",
            (judul, kategori, ringkasan, konten, gambar, budaya_id),
        )
    else:
        dbcore.execute(
            "UPDATE budaya SET judul=%s, kategori=%s, ringkasan=%s, konten_lengkap=%s WHERE id=%s",
            (judul, kategori, ringkasan, konten, budaya_id),
        )


def delete(budaya_id):
    dbcore.execute("DELETE FROM budaya WHERE id = %s", (budaya_id,))


def get_gambar(budaya_id):
    return dbcore.query_one("SELECT gambar FROM budaya WHERE id = %s", (budaya_id,))


def clear_gambar(budaya_id):
    dbcore.execute("UPDATE budaya SET gambar = NULL WHERE id = %s", (budaya_id,))


def list_galeri(budaya_id):
    return dbcore.query_all(
        "SELECT gambar FROM budaya_galeri WHERE budaya_id = %s ORDER BY id ASC", (budaya_id,)
    )


def list_galeri_full(budaya_id):
    return dbcore.query_all(
        "SELECT id, gambar FROM budaya_galeri WHERE budaya_id = %s ORDER BY id ASC", (budaya_id,)
    )


def add_galeri(budaya_id, filename):
    dbcore.execute("INSERT INTO budaya_galeri (budaya_id, gambar) VALUES (%s, %s)", (budaya_id, filename))


def get_galeri(galeri_id):
    return dbcore.query_one("SELECT * FROM budaya_galeri WHERE id = %s", (galeri_id,))


def delete_galeri(galeri_id):
    dbcore.execute("DELETE FROM budaya_galeri WHERE id = %s", (galeri_id,))


def list_for_sync():
    """Semua artikel budaya untuk dijadikan dokumen pengetahuan RAG."""
    return dbcore.query_all("SELECT id, judul, kategori, ringkasan, konten_lengkap FROM budaya")


def list_names():
    """Id + judul seluruh artikel budaya, untuk mendeteksi budaya mana saja yang
    disebut di dalam jawaban chatbot sehingga bisa diberi tombol link detail."""
    return dbcore.query_all("SELECT id, judul FROM budaya")


# ============================================================
# ATURAN BISNIS: dipanggil langsung oleh routes/admin_budaya.py
# ============================================================

def save_from_form(form, files, edit_id=None):
    """Simpan (insert/update) artikel budaya beserta galerinya dari form admin.

    Konten HTML disaring dulu lewat `sanitize_content_html` (cegah stored XSS)
    sebelum disimpan — JANGAN pernah simpan `konten_lengkap` mentah dari form.

    Return (budaya_id, warnings) - warnings berisi pesan non-fatal (mis. ada
    berkas gambar yang ditolak karena bukan gambar valid) yang perlu
    ditampilkan ke admin tapi tidak membatalkan penyimpanan data lain.
    """
    warnings = []

    judul = form.get("judul", "").strip()
    kategori = form.get("kategori", "").strip()
    ringkasan = form.get("ringkasan", "").strip()
    konten = sanitize_content_html(form.get("konten_lengkap", "").strip())
    gambar, gambar_warning = save_uploaded_image(files.get("gambar"))
    if gambar_warning:
        warnings.append(gambar_warning)
    galeri_filenames, galeri_warnings = save_uploaded_images(files.getlist("galeri"))
    warnings.extend(galeri_warnings)

    if edit_id:
        update(edit_id, judul, kategori, ringkasan, konten, gambar)
        budaya_id = edit_id
    else:
        budaya_id = create(judul, kategori, ringkasan, konten, gambar)

    for filename in galeri_filenames:
        add_galeri(budaya_id, filename)

    return budaya_id, warnings


def delete_galeri_photo(galeri_id) -> bool:
    """Hapus satu foto galeri (record + berkas). Return True jika ada yang dihapus."""
    foto = get_galeri(galeri_id)
    if not foto:
        return False
    delete_upload_file(foto["gambar"])
    delete_galeri(galeri_id)
    return True


def delete_gambar_utama(budaya_id) -> bool:
    """Hapus gambar utama artikel (record + berkas). Return True jika ada yang dihapus."""
    budaya = get_gambar(budaya_id)
    if not budaya or not budaya["gambar"]:
        return False
    delete_upload_file(budaya["gambar"])
    clear_gambar(budaya_id)
    return True
