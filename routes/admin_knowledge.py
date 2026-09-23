"""Router pengelolaan basis pengetahuan (dokumen) & sinkronisasi RAG."""
import os
import threading

from flask import (
    abort, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for,
)

from core.auth import admin_required
from core.sync_engine import get_sync_progress, is_sync_running, run_sync
from models import knowledge as knowledge_model
from utils.uploads import delete_knowledge_file, save_uploaded_doc


@admin_required
def admin_knowledge():
    docs = knowledge_model.list_all()
    return render_template("admin/knowledge_sync.html", docs=docs)


@admin_required
def admin_knowledge_upload():
    file = request.files.get("dokumen")
    filename, ext = save_uploaded_doc(file)
    if not filename:
        flash("Berkas tidak valid. Hanya PDF, TXT, atau MD yang diterima.", "error")
        return redirect(url_for("admin_knowledge"))
    knowledge_model.create(file.filename, ext, filename)
    flash("Dokumen berhasil diunggah. Jalankan sinkronisasi untuk melatih ulang RAG.", "success")
    return redirect(url_for("admin_knowledge"))


@admin_required
def admin_knowledge_view(doc_id):
    doc = knowledge_model.get_by_id(doc_id)
    if not doc:
        abort(404)

    directory = current_app.config["KNOWLEDGE_DOCS_DIR"]
    filename = os.path.basename(doc["path_file"])
    if not os.path.exists(os.path.join(directory, filename)):
        abort(404)

    mimetype = "text/plain" if doc["tipe_file"].lower() in ("txt", "md") else None
    return send_from_directory(
        directory, filename, mimetype=mimetype, as_attachment=False, download_name=doc["nama_file"]
    )


@admin_required
def admin_knowledge_delete(doc_id):
    doc = knowledge_model.get_by_id(doc_id)
    if doc:
        delete_knowledge_file(doc["path_file"])
        knowledge_model.delete(doc_id)
        flash("Dokumen dihapus. Jalankan sinkronisasi ulang agar vector DB diperbarui.", "success")
    return redirect(url_for("admin_knowledge"))


@admin_required
def admin_sync_knowledge():
    if is_sync_running():
        return jsonify({"success": False, "message": "Sinkronisasi lain sedang berjalan."}), 409

    app = current_app._get_current_object()

    def _run_in_background():
        with app.app_context():
            run_sync()

    threading.Thread(target=_run_in_background, daemon=True).start()
    return jsonify({"success": True, "message": "Sinkronisasi dimulai."}), 202


@admin_required
def admin_sync_knowledge_status():
    return jsonify(get_sync_progress())


def register(app):
    app.add_url_rule("/admin/knowledge", endpoint="admin_knowledge", view_func=admin_knowledge)
    app.add_url_rule(
        "/admin/knowledge/upload", endpoint="admin_knowledge_upload",
        view_func=admin_knowledge_upload, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/knowledge/<int:doc_id>/view", endpoint="admin_knowledge_view",
        view_func=admin_knowledge_view, methods=["GET"],
    )
    app.add_url_rule(
        "/admin/knowledge/<int:doc_id>/delete", endpoint="admin_knowledge_delete",
        view_func=admin_knowledge_delete, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/api/sync-knowledge", endpoint="admin_sync_knowledge",
        view_func=admin_sync_knowledge, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/api/sync-knowledge/status", endpoint="admin_sync_knowledge_status",
        view_func=admin_sync_knowledge_status, methods=["GET"],
    )
