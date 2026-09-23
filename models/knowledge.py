"""Data access layer untuk entitas dokumen basis pengetahuan (knowledge_docs)."""
from core import db as dbcore


def list_all():
    return dbcore.query_all("SELECT * FROM knowledge_docs ORDER BY uploaded_at DESC")


def count_all():
    return dbcore.query_one("SELECT COUNT(*) AS c FROM knowledge_docs")["c"]


def create(nama_file, tipe_file, path_file):
    return dbcore.execute(
        "INSERT INTO knowledge_docs (nama_file, tipe_file, path_file, status_indexed) VALUES (%s,%s,%s,FALSE)",
        (nama_file, tipe_file, path_file),
    )


def get_by_id(doc_id):
    return dbcore.query_one("SELECT * FROM knowledge_docs WHERE id = %s", (doc_id,))


def delete(doc_id):
    dbcore.execute("DELETE FROM knowledge_docs WHERE id = %s", (doc_id,))


def list_for_sync():
    return dbcore.query_all("SELECT id, nama_file, tipe_file, path_file FROM knowledge_docs")


def mark_all_indexed():
    dbcore.execute("UPDATE knowledge_docs SET status_indexed = TRUE")
