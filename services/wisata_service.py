"""Logika bisnis pengelolaan destinasi wisata (form admin: simpan & hapus foto)."""
from core.content import sanitize_content_html
from models import wisata as wisata_model
from services.coordinates import parse_koordinat
from services.uploads import save_uploaded_image, save_uploaded_images, delete_upload_file
from services.validators import is_valid_email

DEFAULT_TIKET = "Gratis / Menyesuaikan"


def save_from_form(form, files, edit_id=None):
    """Simpan (insert/update) destinasi wisata beserta galerinya dari form admin.

    Return (wisata_id, warnings) - warnings berisi pesan non-fatal (format koordinat
    atau email tidak valid) yang perlu ditampilkan ke admin tapi tidak membatalkan
    penyimpanan data lain.
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
        wisata_model.update(edit_id, data)
        wisata_id = edit_id
    else:
        wisata_id = wisata_model.create(data)

    for filename in galeri_filenames:
        wisata_model.add_galeri(wisata_id, filename)

    return wisata_id, warnings


def delete_galeri_photo(galeri_id) -> bool:
    """Hapus satu foto galeri (record + berkas). Return True jika ada yang dihapus."""
    foto = wisata_model.get_galeri(galeri_id)
    if not foto:
        return False
    delete_upload_file(foto["gambar"])
    wisata_model.delete_galeri(galeri_id)
    return True


def delete_gambar_utama(wisata_id) -> bool:
    """Hapus gambar utama destinasi (record + berkas). Return True jika ada yang dihapus."""
    wisata = wisata_model.get_gambar(wisata_id)
    if not wisata or not wisata["gambar"]:
        return False
    delete_upload_file(wisata["gambar"])
    wisata_model.clear_gambar(wisata_id)
    return True
