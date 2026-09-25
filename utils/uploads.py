"""Logika bisnis penyimpanan & penghapusan berkas unggahan (gambar & dokumen).

Setiap gambar yang masuk (gambar utama maupun galeri) diverifikasi ulang
isinya (bukan cuma percaya ekstensi filename), lalu otomatis di-resize dan
dikonversi ke WebP sebelum disimpan. Ini jadi jaring pengaman di server
seandainya kompresi di browser (static/js/image-optimizer.js) dilewati
(JS mati, upload langsung ke API, dsb) - hasil akhir tetap ringan & konsisten.
"""
import io
import os
from datetime import datetime

from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename


def _read_and_reset(file_storage):
    raw = file_storage.read()
    file_storage.stream.seek(0)
    return raw


def _process_image(raw_bytes, max_dimension, quality):
    """Validasi isi berkas & hasilkan versi WebP yang sudah di-resize.

    Return (webp_bytes, None) kalau berhasil, atau (None, alasan_gagal) kalau
    berkas bukan gambar asli/rusak/melewati batas dekompresi.
    """
    try:
        with Image.open(io.BytesIO(raw_bytes)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(raw_bytes)) as img:
            img.load()
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=quality, method=6)
            return buffer.getvalue(), None
    except Image.DecompressionBombError:
        return None, "resolusi gambar terlalu besar"
    except (UnidentifiedImageError, OSError, ValueError):
        return None, "berkas bukan gambar yang valid"


def save_uploaded_image(file_storage):
    """Simpan satu gambar (validasi isi + resize + konversi ke WebP otomatis).

    Return (filename, warning). `filename` None kalau tidak ada berkas
    dipilih atau berkas ditolak; `warning` berisi pesan yang perlu
    ditampilkan ke admin (None kalau tidak ada masalah).
    """
    if not file_storage or not file_storage.filename:
        return None, None

    original_name = file_storage.filename
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in current_app.config["ALLOWED_IMAGE_EXT"]:
        return None, f"'{original_name}' dilewati: format tidak didukung (hanya PNG/JPG/JPEG/WEBP)."

    raw = _read_and_reset(file_storage)
    webp_bytes, error = _process_image(
        raw,
        current_app.config["IMAGE_MAX_DIMENSION"],
        current_app.config["IMAGE_WEBP_QUALITY"],
    )
    if error:
        return None, f"'{original_name}' dilewati: {error}."

    base = secure_filename(original_name.rsplit(".", 1)[0]) or "gambar"
    filename = f"{datetime.utcnow().timestamp()}_{base}.webp"
    with open(os.path.join(current_app.config["UPLOAD_FOLDER"], filename), "wb") as f:
        f.write(webp_bytes)
    return filename, None


def save_uploaded_images(file_storages):
    """Simpan beberapa gambar galeri sekaligus (resize + konversi WebP otomatis).

    Return (filenames, warnings) - filenames berisi nama berkas yang berhasil
    disimpan, warnings berisi pesan berkas yang dilewati/ditolak.
    """
    filenames = []
    warnings = []
    accepted = [f for f in file_storages if f and f.filename]

    limit = current_app.config["MAX_GALERI_FILES"]
    if len(accepted) > limit:
        warnings.append(
            f"Hanya {limit} foto galeri pertama yang disimpan (batas {limit} foto per unggahan)."
        )
        accepted = accepted[:limit]

    for file_storage in accepted:
        filename, warning = save_uploaded_image(file_storage)
        if filename:
            filenames.append(filename)
        if warning:
            warnings.append(warning)
    return filenames, warnings


def save_uploaded_doc(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_DOC_EXT"]:
        return None, None
    filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file_storage.filename}")
    file_storage.save(os.path.join(current_app.config["KNOWLEDGE_DOCS_DIR"], filename))
    return filename, ext


def delete_upload_file(filename):
    """Hapus file di folder upload gambar publik, jika ada."""
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)


def delete_knowledge_file(filename):
    """Hapus file di folder dokumen basis pengetahuan, jika ada."""
    path = os.path.join(current_app.config["KNOWLEDGE_DOCS_DIR"], filename)
    if os.path.exists(path):
        os.remove(path)
