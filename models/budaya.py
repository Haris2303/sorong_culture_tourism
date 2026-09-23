"""Data access layer untuk entitas budaya & galeri fotonya."""
from core import db as dbcore

LIST_FIELDS = "id, judul, kategori, ringkasan, gambar"


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
