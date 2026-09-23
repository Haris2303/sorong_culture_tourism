"""Data access layer untuk entitas rating/ulasan wisata."""
from core import db as dbcore


def list_approved_by_wisata(wisata_id):
    return dbcore.query_all(
        "SELECT skor_bintang, komentar, created_at FROM ratings "
        "WHERE wisata_id = %s AND status_tampil = 'approved' ORDER BY created_at DESC",
        (wisata_id,),
    )


def scores_approved_by_wisata(wisata_id):
    rows = dbcore.query_all(
        "SELECT skor_bintang FROM ratings WHERE wisata_id = %s AND status_tampil = 'approved'",
        (wisata_id,),
    )
    return [r["skor_bintang"] for r in rows]


def create(wisata_id, skor, komentar, fingerprint, status):
    """Insert rating baru. Kembalikan (rating_id, error) - error terisi jika fingerprint sudah pernah menilai."""
    return dbcore.execute_unique_safe(
        "INSERT INTO ratings (wisata_id, skor_bintang, komentar, ip_address_hash, status_tampil) "
        "VALUES (%s, %s, %s, %s, %s)",
        (wisata_id, skor, komentar or None, fingerprint, status),
    )


def list_all_with_wisata():
    return dbcore.query_all(
        "SELECT r.id, r.skor_bintang, r.komentar, r.status_tampil, r.created_at, "
        "w.nama_wisata FROM ratings r JOIN wisata w ON w.id = r.wisata_id "
        "ORDER BY r.created_at DESC"
    )


def update_status(rating_id, status):
    dbcore.execute("UPDATE ratings SET status_tampil = %s WHERE id = %s", (status, rating_id))


def delete(rating_id):
    dbcore.execute("DELETE FROM ratings WHERE id = %s", (rating_id,))


def count_all():
    return dbcore.query_one("SELECT COUNT(*) AS c FROM ratings")["c"]


def count_approved():
    return dbcore.query_one("SELECT COUNT(*) AS c FROM ratings WHERE status_tampil = 'approved'")["c"]


def count_pending():
    return dbcore.query_one("SELECT COUNT(*) AS c FROM ratings WHERE status_tampil = 'pending'")["c"]


def average_approved_score():
    row = dbcore.query_one("SELECT AVG(skor_bintang) AS avg_score FROM ratings WHERE status_tampil = 'approved'")
    return row["avg_score"]
