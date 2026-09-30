"""Job asinkron untuk /api/chat.

Situs ini multi-halaman (bukan SPA), jadi request fetch biasa otomatis
terputus begitu pengguna pindah halaman sebelum jawabannya selesai —
jawaban yang sudah separuh jalan diproses LLM akan hilang percuma. Di sini
pemrosesan jawaban dijalankan di background thread lepas dari siklus hidup
request HTTP; klien cuma menerima `job_id` lalu polling statusnya, dan
polling itu bisa dilanjutkan dari halaman manapun karena job_id disimpan
di sessionStorage sisi klien (lihat static/js/chat.js).
"""
import logging
import threading
import time
import uuid

from flask import copy_current_request_context

from core.rag_engine import answer_query

logger = logging.getLogger(__name__)

_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()
_JOB_TTL_SECONDS = 300  # job yang tidak pernah diambil dibersihkan otomatis

_FALLBACK_ANSWER = {
    "answer": "⚠️ Maaf, terjadi kendala teknis pada asisten virtual kami. Silakan coba lagi sebentar lagi.",
    "sources": [],
}


def _cleanup_expired_locked():
    now = time.time()
    expired = [jid for jid, job in _JOBS.items() if now - job["created_at"] > _JOB_TTL_SECONDS]
    for jid in expired:
        _JOBS.pop(jid, None)


def start_job(question: str, history: list) -> str:
    """Mulai job di background thread, kembalikan job_id-nya segera.

    Wajib dipanggil di dalam request: thread membawa salinan request context
    supaya url_for() (dipakai answer_query untuk tombol link detail
    wisata/budaya) bisa jalan. Dengan app context saja, url_for gagal dan
    setiap jawaban berubah jadi pesan "kendala teknis".
    """
    job_id = uuid.uuid4().hex
    with _JOBS_LOCK:
        _cleanup_expired_locked()
        _JOBS[job_id] = {"status": "running", "result": None, "created_at": time.time()}

    @copy_current_request_context
    def _run():
        try:
            result = answer_query(question, history)
            outcome = {"answer": result["answer"], "sources": result["sources"]}
        except Exception:
            logger.exception("Chat job %s gagal untuk pertanyaan: %r", job_id, question)
            outcome = dict(_FALLBACK_ANSWER)
        with _JOBS_LOCK:
            job = _JOBS.get(job_id)
            if job is not None:
                job["status"] = "done"
                job["result"] = outcome

    threading.Thread(target=_run, daemon=True).start()
    return job_id


def get_job(job_id: str) -> dict | None:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job is not None else None
