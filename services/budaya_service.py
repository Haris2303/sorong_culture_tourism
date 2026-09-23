"""Logika bisnis pengelolaan artikel budaya (form admin: simpan & hapus foto)."""
from core.content import sanitize_content_html
from models import budaya as budaya_model
from services.uploads import save_uploaded_image, save_uploaded_images, delete_upload_file


def save_from_form(form, files, edit_id=None):
    """Simpan (insert/update) artikel budaya beserta galerinya dari form admin.

    Return budaya_id (hasil insert atau edit_id yang diteruskan).
    """
    judul = form.get("judul", "").strip()
    kategori = form.get("kategori", "").strip()
    ringkasan = form.get("ringkasan", "").strip()
    konten = sanitize_content_html(form.get("konten_lengkap", "").strip())
    gambar = save_uploaded_image(files.get("gambar"))
    galeri_filenames = save_uploaded_images(files.getlist("galeri"))

    if edit_id:
        budaya_model.update(edit_id, judul, kategori, ringkasan, konten, gambar)
        budaya_id = edit_id
    else:
        budaya_id = budaya_model.create(judul, kategori, ringkasan, konten, gambar)

    for filename in galeri_filenames:
        budaya_model.add_galeri(budaya_id, filename)

    return budaya_id


def delete_galeri_photo(galeri_id) -> bool:
    """Hapus satu foto galeri (record + berkas). Return True jika ada yang dihapus."""
    foto = budaya_model.get_galeri(galeri_id)
    if not foto:
        return False
    delete_upload_file(foto["gambar"])
    budaya_model.delete_galeri(galeri_id)
    return True


def delete_gambar_utama(budaya_id) -> bool:
    """Hapus gambar utama artikel (record + berkas). Return True jika ada yang dihapus."""
    budaya = budaya_model.get_gambar(budaya_id)
    if not budaya or not budaya["gambar"]:
        return False
    delete_upload_file(budaya["gambar"])
    budaya_model.clear_gambar(budaya_id)
    return True
