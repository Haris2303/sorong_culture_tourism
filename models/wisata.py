"""Semua yang berhubungan dengan data wisata & galeri fotonya.

Bagian 1 (QUERY): fungsi baca/tulis langsung ke tabel `wisata` & `wisata_galeri`.
Bagian 2 (ATURAN BISNIS): fungsi tingkat lebih tinggi yang dipanggil router,
menggabungkan beberapa query + aturan (validasi koordinat/email, dsb) jadi
satu langkah saja.
"""
from core import db as dbcore
from core.content import sanitize_content_html
from utils.coordinates import parse_koordinat
from utils.uploads import delete_upload_file, save_uploaded_image, save_uploaded_images
from utils.validators import is_valid_email

LIST_FIELDS = "id, nama_wisata, wilayah, deskripsi, gambar"

DEFAULT_TIKET = "Gratis / Menyesuaikan"

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


# ============================================================
# QUERY: baca & tulis tabel wisata + wisata_galeri
# ============================================================

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


def list_names():
    """Id + nama seluruh destinasi, untuk mendeteksi destinasi mana saja yang
    disebut di dalam jawaban chatbot sehingga bisa diberi tombol link detail."""
    return dbcore.query_all("SELECT id, nama_wisata FROM wisata")


# ============================================================
# ATURAN BISNIS: dipanggil langsung oleh routes/admin_wisata.py
# ============================================================

def save_from_form(form, files, edit_id=None):
    """Simpan (insert/update) destinasi wisata beserta galerinya dari form admin.

    Deskripsi HTML disaring dulu lewat `sanitize_content_html` (cegah stored
    XSS) sebelum disimpan — JANGAN pernah simpan `deskripsi` mentah dari form.

    Return (wisata_id, warnings) - warnings berisi pesan non-fatal (format
    koordinat atau email tidak valid) yang perlu ditampilkan ke admin tapi
    tidak membatalkan penyimpanan data lain.
    """
    warnings = []

    nama_wisata = form.get("nama_wisata", "").strip()
    wilayah = form.get("wilayah", "").strip()
    deskripsi = sanitize_content_html(form.get("deskripsi", "").strip())
    fasilitas = form.get("fasilitas", "").strip()
    alamat = form.get("alamat", "").strip()
    tiket_choice = form.get("tiket_masuk", "").strip()
    if tiket_choice == "__custom__":
        tiket_masuk = form.get("tiket_masuk_custom", "").strip() or DEFAULT_TIKET
    else:
        tiket_masuk = tiket_choice or DEFAULT_TIKET
    jam_operasional = form.get("jam_operasional", "Setiap Hari").strip()
    gambar = save_uploaded_image(files.get("gambar"))
    galeri_filenames = save_uploaded_images(files.getlist("galeri"))

    latitude, longitude = None, None
    koordinat_input = form.get("koordinat", "").strip()
    if koordinat_input:
        parsed = parse_koordinat(koordinat_input)
        if parsed:
            latitude, longitude = parsed
        else:
            warnings.append(
                "Format koordinat tidak dikenali. Gunakan format desimal (-0.859042, 131.247695) "
                "atau DMS (0°44'11.6\"S 131°35'01.1\"E). Lokasi peta tidak disimpan."
            )

    sosmed_email = form.get("sosmed_email", "").strip()
    if sosmed_email and not is_valid_email(sosmed_email):
        warnings.append("Format email tidak valid. Email tidak disimpan.")
        sosmed_email = ""
    sosmed_facebook = form.get("sosmed_facebook", "").strip()
    sosmed_instagram = form.get("sosmed_instagram", "").strip()
    sosmed_youtube = form.get("sosmed_youtube", "").strip()

    data = {
        "nama_wisata": nama_wisata,
        "wilayah": wilayah,
        "deskripsi": deskripsi,
        "fasilitas": fasilitas,
        "alamat": alamat,
        "tiket_masuk": tiket_masuk,
        "jam_operasional": jam_operasional,
        "gambar": gambar,
        "latitude": latitude,
        "longitude": longitude,
        "sosmed_email": sosmed_email or None,
        "sosmed_facebook": sosmed_facebook or None,
        "sosmed_instagram": sosmed_instagram or None,
        "sosmed_youtube": sosmed_youtube or None,
    }

    if edit_id:
        update(edit_id, data)
        wisata_id = edit_id
    else:
        wisata_id = create(data)

    for filename in galeri_filenames:
        add_galeri(wisata_id, filename)

    return wisata_id, warnings


def delete_galeri_photo(galeri_id) -> bool:
    """Hapus satu foto galeri (record + berkas). Return True jika ada yang dihapus."""
    foto = get_galeri(galeri_id)
    if not foto:
        return False
    delete_upload_file(foto["gambar"])
    delete_galeri(galeri_id)
    return True


def delete_gambar_utama(wisata_id) -> bool:
    """Hapus gambar utama destinasi (record + berkas). Return True jika ada yang dihapus."""
    wisata = get_gambar(wisata_id)
    if not wisata or not wisata["gambar"]:
        return False
    delete_upload_file(wisata["gambar"])
    clear_gambar(wisata_id)
    return True
