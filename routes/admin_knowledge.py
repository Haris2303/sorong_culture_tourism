"""Router pengelolaan basis pengetahuan (dokumen) & sinkronisasi RAG."""
from flask import flash, jsonify, redirect, render_template, request, url_for

from core.auth import admin_required
from core.sync_engine import run_sync
from models import knowledge as knowledge_model
from services.uploads import delete_knowledge_file, save_uploaded_doc


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
def admin_knowledge_delete(doc_id):
    doc = knowledge_model.get_by_id(doc_id)
    if doc:
        delete_knowledge_file(doc["path_file"])
        knowledge_model.delete(doc_id)
        flash("Dokumen dihapus. Jalankan sinkronisasi ulang agar vector DB diperbarui.", "success")
    return redirect(url_for("admin_knowledge"))


@admin_required
def admin_sync_knowledge():
    try:
        result = run_sync()
    except Exception as exc:
        return jsonify({"success": False, "message": f"Gagal sinkronisasi: {exc}"}), 500
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


def register(app):
    app.add_url_rule("/admin/knowledge", endpoint="admin_knowledge", view_func=admin_knowledge)
    app.add_url_rule(
        "/admin/knowledge/upload", endpoint="admin_knowledge_upload",
        view_func=admin_knowledge_upload, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/knowledge/<int:doc_id>/delete", endpoint="admin_knowledge_delete",
        view_func=admin_knowledge_delete, methods=["POST"],
    )
    app.add_url_rule(
        "/admin/api/sync-knowledge", endpoint="admin_sync_knowledge",
        view_func=admin_sync_knowledge, methods=["POST"],
    )
