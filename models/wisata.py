"""Data access layer untuk entitas wisata & galeri fotonya."""
from core import db as dbcore

LIST_FIELDS = "id, nama_wisata, wilayah, deskripsi, gambar"

_INSERT_SQL = (
    "INSERT INTO wisata (nama_wisata, wilayah, deskripsi, fasilitas, alamat, tiket_masuk, "
    "jam_operasional, gambar, latitude, longitude, sosmed_email, sosmed_facebook, "
    "sosmed_instagram, sosmed_youtube) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
)
_UPDATE_SQL_WITH_GAMBAR = (
    "UPDATE wisata SET nama_wisata=%s, wilayah=%s, deskripsi=%s, fasilitas=%s, alamat=%s, "
    "tiket_masuk=%s, jam_operasional=%s, gambar=%s, latitude=%s, longitude=%s, "
    "sosmed_email=%s, sosmed_facebook=%s, sosmed_instagram=%s, sosmed_youtube=%s WHERE id=%s"
)
_UPDATE_SQL_WITHOUT_GAMBAR = (
    "UPDATE wisata SET nama_wisata=%s, wilayah=%s, deskripsi=%s, fasilitas=%s, alamat=%s, "
    "tiket_masuk=%s, jam_operasional=%s, latitude=%s, longitude=%s, "
    "sosmed_email=%s, sosmed_facebook=%s, sosmed_instagram=%s, sosmed_youtube=%s WHERE id=%s"
)


def count_public(wilayah=None):
    if wilayah:
        return dbcore.query_one("SELECT COUNT(*) AS c FROM wisata WHERE wilayah = %s", (wilayah,))["c"]
    return dbcore.query_one("SELECT COUNT(*) AS c FROM wisata")["c"]


def list_public(wilayah, limit, offset):
    if wilayah:
        return dbcore.query_all(
            f"SELECT {LIST_FIELDS} FROM wisata WHERE wilayah = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (wilayah, limit, offset),
        )
    return dbcore.query_all(
        f"SELECT {LIST_FIELDS} FROM wisata ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )


def list_highlight(limit=3):
    return dbcore.query_all(
        f"SELECT {LIST_FIELDS} FROM wisata ORDER BY created_at DESC LIMIT %s", (limit,)
    )


def get_by_id(wisata_id):
    return dbcore.query_one("SELECT * FROM wisata WHERE id = %s", (wisata_id,))


def get_nama(wisata_id):
    return dbcore.query_one("SELECT nama_wisata FROM wisata WHERE id = %s", (wisata_id,))


def exists(wisata_id):
    return dbcore.query_one("SELECT id FROM wisata WHERE id = %s", (wisata_id,)) is not None


def search(keyword, limit=20):
    like = f"%{keyword}%"
    return dbcore.query_all(
        f"SELECT {LIST_FIELDS} FROM wisata WHERE nama_wisata LIKE %s OR deskripsi LIKE %s LIMIT %s",
        (like, like, limit),
    )


def count_admin(keyword=None):
    if keyword:
        like = f"%{keyword}%"
        return dbcore.query_one(
            "SELECT COUNT(*) AS c FROM wisata WHERE nama_wisata LIKE %s OR wilayah LIKE %s OR alamat LIKE %s",
            (like, like, like),
        )["c"]
    return dbcore.query_one("SELECT COUNT(*) AS c FROM wisata")["c"]


def list_admin(keyword, limit, offset):
    if keyword:
        like = f"%{keyword}%"
        return dbcore.query_all(
            "SELECT * FROM wisata WHERE nama_wisata LIKE %s OR wilayah LIKE %s OR alamat LIKE %s "
            "ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (like, like, like, limit, offset),
        )
    return dbcore.query_all(
        "SELECT * FROM wisata ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, offset)
    )


def create(data: dict):
    return dbcore.execute(
        _INSERT_SQL,
        (
            data["nama_wisata"], data["wilayah"], data["deskripsi"], data["fasilitas"], data["alamat"],
            data["tiket_masuk"], data["jam_operasional"], data["gambar"], data["latitude"], data["longitude"],
            data["sosmed_email"], data["sosmed_facebook"], data["sosmed_instagram"], data["sosmed_youtube"],
        ),
    )


def update(wisata_id, data: dict):
    if data.get("gambar"):
        dbcore.execute(
            _UPDATE_SQL_WITH_GAMBAR,
            (
                data["nama_wisata"], data["wilayah"], data["deskripsi"], data["fasilitas"], data["alamat"],
                data["tiket_masuk"], data["jam_operasional"], data["gambar"], data["latitude"], data["longitude"],
                data["sosmed_email"], data["sosmed_facebook"], data["sosmed_instagram"], data["sosmed_youtube"],
                wisata_id,
            ),
        )
    else:
        dbcore.execute(
            _UPDATE_SQL_WITHOUT_GAMBAR,
            (
                data["nama_wisata"], data["wilayah"], data["deskripsi"], data["fasilitas"], data["alamat"],
                data["tiket_masuk"], data["jam_operasional"], data["latitude"], data["longitude"],
                data["sosmed_email"], data["sosmed_facebook"], data["sosmed_instagram"], data["sosmed_youtube"],
                wisata_id,
            ),
        )


def delete(wisata_id):
    dbcore.execute("DELETE FROM wisata WHERE id = %s", (wisata_id,))


def get_gambar(wisata_id):
    return dbcore.query_one("SELECT gambar FROM wisata WHERE id = %s", (wisata_id,))


def clear_gambar(wisata_id):
    dbcore.execute("UPDATE wisata SET gambar = NULL WHERE id = %s", (wisata_id,))


def list_galeri(wisata_id):
    return dbcore.query_all(
        "SELECT gambar FROM wisata_galeri WHERE wisata_id = %s ORDER BY id ASC", (wisata_id,)
    )


def list_galeri_full(wisata_id):
    return dbcore.query_all(
        "SELECT id, gambar FROM wisata_galeri WHERE wisata_id = %s ORDER BY id ASC", (wisata_id,)
    )


def add_galeri(wisata_id, filename):
    dbcore.execute("INSERT INTO wisata_galeri (wisata_id, gambar) VALUES (%s, %s)", (wisata_id, filename))


def get_galeri(galeri_id):
    return dbcore.query_one("SELECT * FROM wisata_galeri WHERE id = %s", (galeri_id,))


def delete_galeri(galeri_id):
    dbcore.execute("DELETE FROM wisata_galeri WHERE id = %s", (galeri_id,))


def list_for_sync():
    """Semua destinasi wisata untuk dijadikan dokumen pengetahuan RAG."""
    return dbcore.query_all(
        "SELECT id, nama_wisata, wilayah, deskripsi, fasilitas, alamat, tiket_masuk, jam_operasional FROM wisata"
    )
