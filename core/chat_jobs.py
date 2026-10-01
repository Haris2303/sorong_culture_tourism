"""Job asinkron untuk /api/chat.

Situs ini multi-halaman (bukan SPA), jadi request fetch biasa otomatis
terputus begitu pengguna pindah halaman sebelum jawabannya selesai —
jawaban yang sudah separuh jalan diproses LLM akan hilang percuma. Di sini
pemrosesan jawaban dijalankan di background thread lepas dari siklus hidup
request HTTP; klien cuma menerima `job_id` lalu polling statusnya, dan
polling itu bisa dilanjutkan dari halaman manapun karena job_id disimpan
di sessionStorage sisi klien (lihat static/js/chat.js).

Job disimpan di tabel MySQL `chat_jobs` (bukan memori proses) karena di hosting
aplikasi berjalan dengan beberapa worker: request POST dan polling status bisa
mendarat di proses berbeda, sehingga dict di memori tidak terlihat bersama.
"""
import json
import logging
import threading
import time
import uuid

from flask import copy_current_request_context

from core import db
from core.rag_engine import answer_query

logger = logging.getLogger(__name__)

_JOB_TTL_SECONDS = 300  # job yang tidak pernah diambil dibersihkan otomatis

_FALLBACK_ANSWER = {
    "answer": "⚠️ Maaf, terjadi kendala teknis pada asisten virtual kami. Silakan coba lagi sebentar lagi.",
    "sources": [],
}

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_jobs (
    job_id CHAR(32) PRIMARY KEY,
    status VARCHAR(10) NOT NULL DEFAULT 'running',
    result LONGTEXT NULL,
    created_at BIGINT NOT NULL,
    INDEX idx_chat_jobs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

_table_ready = False
_table_lock = threading.Lock()


def _ensure_table():
    """Buat tabel chat_jobs sekali per proses kalau belum ada (aman dijalankan paralel)."""
    global _table_ready
    if _table_ready:
        return
    with _table_lock:
        if not _table_ready:
            db.execute(_CREATE_TABLE_SQL)
            _table_ready = True


def start_job(question: str, history: list) -> str:
    """Mulai job di background thread, kembalikan job_id-nya segera.

    Wajib dipanggil di dalam request: thread membawa salinan request context
    supaya url_for() (dipakai answer_query untuk tombol link detail
    wisata/budaya) bisa jalan. Dengan app context saja, url_for gagal dan
    setiap jawaban berubah jadi pesan "kendala teknis".
    """
    _ensure_table()
    job_id = uuid.uuid4().hex
    now = int(time.time())
    db.execute("DELETE FROM chat_jobs WHERE created_at < %s", (now - _JOB_TTL_SECONDS,))
    db.execute(
        "INSERT INTO chat_jobs (job_id, status, created_at) VALUES (%s, 'running', %s)",
        (job_id, now),
    )

    @copy_current_request_context
    def _run():
        try:
            result = answer_query(question, history)
            outcome = {"answer": result["answer"], "sources": result["sources"]}
        except Exception:
            logger.exception("Chat job %s gagal untuk pertanyaan: %r", job_id, question)
            outcome = dict(_FALLBACK_ANSWER)
        try:
            db.execute(
                "UPDATE chat_jobs SET status = 'done', result = %s WHERE job_id = %s",
                (json.dumps(outcome, ensure_ascii=False), job_id),
            )
        except Exception:
            logger.exception("Chat job %s: gagal menyimpan hasil ke database", job_id)

    threading.Thread(target=_run, daemon=True).start()
    return job_id


def get_job(job_id: str) -> dict | None:
    _ensure_table()
    row = db.query_one(
        "SELECT status, result, created_at FROM chat_jobs WHERE job_id = %s AND created_at >= %s",
        (job_id, int(time.time()) - _JOB_TTL_SECONDS),
    )
    if row is None:
        return None
    return {
        "status": row["status"],
        "result": json.loads(row["result"]) if row["result"] else None,
        "created_at": row["created_at"],
    }
