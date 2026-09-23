"""Logika bisnis penyimpanan & penghapusan berkas unggahan (gambar & dokumen)."""
import os
from datetime import datetime

from flask import current_app
from werkzeug.utils import secure_filename


def save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_IMAGE_EXT"]:
        return None
    filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file_storage.filename}")
    file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename


def save_uploaded_images(file_storages):
    """Simpan beberapa gambar galeri sekaligus, kembalikan daftar nama file yang valid."""
    filenames = []
    for file_storage in file_storages:
        filename = save_uploaded_image(file_storage)
        if filename:
            filenames.append(filename)
    return filenames


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
