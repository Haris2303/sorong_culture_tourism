"""Pipeline sinkronisasi & pelatihan ulang Vector DB ChromaDB.

Alur: Document Loader (PDF/TXT/MD) + artikel MySQL (budaya & wisata)
-> Text Splitter (RecursiveCharacterTextSplitter) -> Embedding -> Upsert ke ChromaDB.

Sinkronisasi bersifat inkremental: tiap chunk punya ID dari hash isi + metadata-nya,
sehingga hanya chunk baru/berubah yang dikirim ke API embedding (hemat kuota).
Koleksi lama tidak dihapus di awal; chunk basi baru dibuang setelah semua chunk baru
berhasil masuk, jadi kegagalan di tengah jalan tidak mengosongkan pengetahuan chatbot.
"""
import hashlib
import json
import logging
import math
import os
import re
import threading
import time
from datetime import datetime, timezone

from flask import current_app
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader

from core.content import html_to_plain_text
from core.rag_engine import get_embeddings, reset_engine_cache
from langchain_chroma import Chroma
from models import budaya as budaya_model
from models import knowledge as knowledge_model
from models import wisata as wisata_model
from utils.timezone import now_wit

logger = logging.getLogger(__name__)


class SyncProgress:
    """Status sinkronisasi yang dibagi antar thread agar bisa dipoll oleh frontend."""

    def __init__(self):
        self._lock = threading.Lock()
        self.status = "idle"  # idle | running | success | error
        self.percent = 0
        self.logs = []
        self.result = None

    def try_start(self) -> bool:
        with self._lock:
            if self.status == "running":
                return False
            self.status = "running"
            self.percent = 0
            self.logs = []
            self.result = None
            return True

    def log(self, message: str, percent=None):
        with self._lock:
            self.logs.append({"time": now_wit().strftime("%H:%M:%S"), "message": message})
            if percent is not None:
                self.percent = max(0, min(100, percent))
        logger.info(message)

    def finish(self, success: bool, result: dict):
        with self._lock:
            self.status = "success" if success else "error"
            self.percent = 100 if success else self.percent
            self.result = result

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "status": self.status,
                "percent": self.percent,
                "logs": list(self.logs),
                "result": self.result,
            }


SYNC_PROGRESS = SyncProgress()


def get_sync_progress() -> dict:
    return SYNC_PROGRESS.snapshot()


def is_sync_running() -> bool:
    return SYNC_PROGRESS.snapshot()["status"] == "running"


SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# Free tier Gemini embedding dibatasi ~100 request/menit. Kirim dalam batch kecil
# dan hormati jeda "retry_delay" yang dikirim Google saat kena 429, alih-alih
# gagal total di tengah sinkronisasi.
_EMBED_BATCH_SIZE = 20
_EMBED_MAX_RETRIES = 5
_EMBED_RETRY_DELAY_FALLBACK = 60
_DELETE_SLICE = 500  # hapus chunk basi per potongan agar tidak melewati batas query SQLite


def _parse_retry_delay_seconds(message: str) -> float:
    match = re.search(r"retry in ([\d.]+)\s*s", message, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1
    match = re.search(r"seconds:\s*(\d+)", message)
    if match:
        return float(match.group(1)) + 1
    return _EMBED_RETRY_DELAY_FALLBACK


def _is_quota_error(message: str) -> bool:
    lowered = message.lower()
    return "429" in message or "quota" in lowered or "resource_exhausted" in lowered


def _is_daily_quota(message: str) -> bool:
    """Kuota HARIAN (mis. EmbedContentRequestsPerDay...) tidak akan pulih dalam hitungan menit."""
    return "perday" in re.sub(r"[\s_]", "", message.lower())


class KuotaEmbeddingHabis(Exception):
    """Kuota harian embedding habis; mengulang permintaan tidak ada gunanya."""


def _pesan_ramah(exc: Exception) -> str:
    """Pesan aman untuk admin. Detail asli sudah dicatat lewat logger.exception."""
    if isinstance(exc, KuotaEmbeddingHabis) or _is_quota_error(str(exc)):
        return (
            "Kuota layanan embedding AI sedang habis. Data yang sudah ter-index tidak hilang; "
            "coba sinkronkan lagi nanti."
        )
    return "Terjadi kesalahan di server. Detail tercatat di log server."


def _chunk_id(doc: Document) -> str:
    """ID tetap dari isi + metadata: chunk yang sama antar sinkronisasi tidak di-embed ulang."""
    meta = json.dumps(doc.metadata or {}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(f"{meta}\n{doc.page_content}".encode("utf-8")).hexdigest()


def _add_documents_with_retry(
    vectorstore, batch: list[Document], progress: SyncProgress, ids: list[str] | None = None
) -> None:
    attempt = 0
    while True:
        try:
            vectorstore.add_documents(batch, ids=ids)
            return
        except Exception as exc:
            message = str(exc)
            if _is_quota_error(message) and _is_daily_quota(message):
                raise KuotaEmbeddingHabis(message) from exc
            attempt += 1
            if not _is_quota_error(message) or attempt > _EMBED_MAX_RETRIES:
                raise
            delay = _parse_retry_delay_seconds(message)
            progress.log(
                f"Kuota embedding tercapai, menunggu {delay:.0f} detik lalu mencoba lagi "
                f"(percobaan {attempt}/{_EMBED_MAX_RETRIES})..."
            )
            time.sleep(delay)


def _load_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _load_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _load_knowledge_docs() -> list[Document]:
    """Muat seluruh dokumen di tabel knowledge_docs dari direktori lokal."""
    docs = []
    rows = knowledge_model.list_for_sync()
    for row in rows:
        full_path = row["path_file"]
        if not os.path.isabs(full_path):
            full_path = os.path.join(current_app.config["KNOWLEDGE_DOCS_DIR"], os.path.basename(full_path))
        if not os.path.exists(full_path):
            continue
        ext = row["tipe_file"].lower()
        try:
            if ext == "pdf":
                text = _load_pdf(full_path)
            else:
                text = _load_txt(full_path)
        except Exception:
            continue
        if text.strip():
            docs.append(Document(page_content=text, metadata={"source": row["nama_file"], "doc_id": row["id"]}))
    return docs


def _load_mysql_articles() -> list[Document]:
    """Muat artikel budaya & wisata dari MySQL sebagai dokumen pengetahuan tambahan."""
    docs = []

    for row in budaya_model.list_for_sync():
        content = (
            f"Judul Budaya: {row['judul']}\n"
            f"Kategori: {row['kategori']}\n"
            f"Ringkasan: {row['ringkasan']}\n"
            f"Detail: {html_to_plain_text(row['konten_lengkap'])}"
        )
        docs.append(Document(
            page_content=content,
            metadata={"source": f"budaya:{row['judul']}", "table": "budaya", "record_id": row["id"]},
        ))

    for row in wisata_model.list_for_sync():
        content = (
            f"Nama Wisata: {row['nama_wisata']}\n"
            f"Wilayah: {row['wilayah']}\n"
            f"Deskripsi: {html_to_plain_text(row['deskripsi'])}\n"
            f"Fasilitas: {row['fasilitas']}\n"
            f"Alamat: {row['alamat']}\n"
            f"Tiket Masuk: {row['tiket_masuk']}\n"
            f"Jam Operasional: {row['jam_operasional']}"
        )
        docs.append(Document(
            page_content=content,
            metadata={"source": f"wisata:{row['nama_wisata']}", "table": "wisata", "record_id": row["id"]},
        ))

    return docs


def run_sync(full_rebuild: bool = False) -> dict:
    """Eksekusi penuh pipeline sinkronisasi. Mengembalikan ringkasan hasil.

    Progres tiap tahap dicatat ke `SYNC_PROGRESS` agar bisa dipoll frontend
    sebagai log & persentase realtime, karena embedding via API eksternal
    (rate-limited) bisa memakan waktu cukup lama.

    Inkremental: hanya chunk baru/berubah yang di-embed. `full_rebuild=True` mengosongkan
    koleksi dan meng-embed ulang semuanya; wajib dipakai sekali bila model embedding diganti
    (dimensi/ruang vektor lama tidak cocok lagi).
    """
    progress = SYNC_PROGRESS
    if not progress.try_start():
        return {"success": False, "message": "Sinkronisasi lain sedang berjalan.", "chunks": 0}

    try:
        progress.log("Memuat dokumen pengetahuan (PDF/TXT/MD)...", percent=2)
        knowledge_docs = _load_knowledge_docs()
        progress.log(f"{len(knowledge_docs)} dokumen pengetahuan dimuat.", percent=5)

        progress.log("Memuat artikel budaya & wisata dari database...", percent=7)
        article_docs = _load_mysql_articles()
        progress.log(f"{len(article_docs)} artikel budaya/wisata dimuat.", percent=10)

        all_docs = knowledge_docs + article_docs

        if not all_docs:
            result = {"success": False, "message": "Tidak ada dokumen atau artikel untuk disinkronkan.", "chunks": 0}
            progress.log(result["message"])
            progress.finish(False, result)
            return result

        progress.log("Memecah teks menjadi potongan (chunking)...", percent=12)
        chunks = SPLITTER.split_documents(all_docs)
        progress.log(f"{len(chunks)} potongan teks dihasilkan dari {len(all_docs)} dokumen.", percent=15)

        collection_name = current_app.config["CHROMA_COLLECTION_NAME"]
        persist_dir = current_app.config["CHROMA_PERSIST_DIR"]
        embeddings = get_embeddings()

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )
        if full_rebuild:
            progress.log("Mode rebuild penuh: mengosongkan koleksi vector lama...", percent=17)
            try:
                vectorstore.delete_collection()
            except Exception:
                pass
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=persist_dir,
            )

        # Bandingkan chunk sekarang dengan isi koleksi lewat ID berbasis hash:
        # yang sama dilewati, yang baru di-embed, yang sudah tidak ada dibuang.
        wanted: dict[str, Document] = {}
        for chunk in chunks:
            wanted.setdefault(_chunk_id(chunk), chunk)

        existing_ids = set(vectorstore.get(include=[]).get("ids", []))
        new_ids = [cid for cid in wanted if cid not in existing_ids]
        stale_ids = [cid for cid in existing_ids if cid not in wanted]
        skipped = len(wanted) - len(new_ids)

        total_batches = math.ceil(len(new_ids) / _EMBED_BATCH_SIZE)
        progress.log(
            f"{skipped} chunk tidak berubah (dilewati), {len(new_ids)} chunk baru/berubah "
            f"akan di-embed ({total_batches} batch), {len(stale_ids)} chunk lama akan dihapus.",
            percent=20,
        )

        # Tambah dulu. Bila gagal di tengah (mis. kuota habis), koleksi lama tetap utuh
        # dan sinkronisasi berikutnya melanjutkan sisanya.
        for batch_idx, i in enumerate(range(0, len(new_ids), _EMBED_BATCH_SIZE), start=1):
            batch_ids = new_ids[i:i + _EMBED_BATCH_SIZE]
            _add_documents_with_retry(vectorstore, [wanted[cid] for cid in batch_ids], progress, ids=batch_ids)
            batch_percent = 20 + round(70 * batch_idx / total_batches)
            progress.log(
                f"Batch embedding {batch_idx}/{total_batches} selesai ({len(batch_ids)} chunk).",
                percent=batch_percent,
            )

        # Buang chunk basi hanya setelah semua chunk baru berhasil masuk.
        if stale_ids:
            progress.log(f"Menghapus {len(stale_ids)} chunk basi...", percent=91)
            for i in range(0, len(stale_ids), _DELETE_SLICE):
                vectorstore.delete(ids=stale_ids[i:i + _DELETE_SLICE])

        progress.log("Menandai dokumen sebagai sudah ter-index...", percent=92)
        knowledge_model.mark_all_indexed()

        progress.log("Membersihkan cache engine RAG...", percent=95)
        reset_engine_cache()

        synced_at = datetime.now(timezone.utc)
        marker_path = os.path.join(persist_dir, "last_sync.txt")
        with open(marker_path, "w", encoding="utf-8") as f:
            f.write(synced_at.isoformat())

        result = {
            "success": True,
            "message": "Sinkronisasi & pelatihan ulang vector DB berhasil.",
            "chunks": len(wanted),
            "documents": len(all_docs),
            "embedded": len(new_ids),
            "skipped": skipped,
            "removed": len(stale_ids),
            "synced_at": synced_at.isoformat(),
        }
        progress.log("Sinkronisasi & pelatihan ulang vector DB berhasil.", percent=100)
        progress.finish(True, result)
        return result
    except Exception as exc:
        logger.exception("Sinkronisasi vector DB gagal")  # detail asli hanya ke log server
        pesan = _pesan_ramah(exc)
        result = {"success": False, "message": f"Gagal sinkronisasi: {pesan}", "chunks": 0}
        progress.log(f"Terjadi error: {pesan}")
        progress.finish(False, result)
        return result


def get_last_sync_time():
    """Baca timestamp sinkronisasi terakhir dari marker file, jika ada."""
    marker_path = os.path.join(current_app.config["CHROMA_PERSIST_DIR"], "last_sync.txt")
    if not os.path.exists(marker_path):
        return None
    with open(marker_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


# ============================================================
# INSPEKSI: lihat isi vector DB hasil pelatihan
# ============================================================

def _open_vectorstore_readonly() -> Chroma:
    """Buka koleksi Chroma tanpa embedding: cukup untuk membaca isi, tanpa memanggil API."""
    return Chroma(
        collection_name=current_app.config["CHROMA_COLLECTION_NAME"],
        persist_directory=current_app.config["CHROMA_PERSIST_DIR"],
    )


def _source_kind(metadata: dict) -> str:
    return metadata.get("table") or "dokumen"


def inspect_vector_store() -> dict:
    """Ringkasan isi vector DB: total chunk dan rincian per sumber."""
    data = _open_vectorstore_readonly().get(include=["documents", "metadatas"])
    documents = data.get("documents") or []
    metadatas = data.get("metadatas") or []

    sources: dict[str, dict] = {}
    for text, meta in zip(documents, metadatas):
        meta = meta or {}
        name = meta.get("source") or "(tanpa sumber)"
        entry = sources.setdefault(name, {"source": name, "kind": _source_kind(meta), "chunks": 0, "chars": 0})
        entry["chunks"] += 1
        entry["chars"] += len(text or "")

    by_kind = {"dokumen": 0, "budaya": 0, "wisata": 0}
    for entry in sources.values():
        by_kind[entry["kind"]] = by_kind.get(entry["kind"], 0) + 1

    total_chunks = len(documents)
    total_chars = sum(e["chars"] for e in sources.values())
    return {
        "total_chunks": total_chunks,
        "total_sources": len(sources),
        "avg_chunk_chars": round(total_chars / total_chunks) if total_chunks else 0,
        "by_kind": by_kind,
        "sources": sorted(sources.values(), key=lambda e: (e["kind"], e["source"].lower())),
    }


def list_source_chunks(source: str) -> list[dict]:
    """Seluruh potongan teks (chunk) milik satu sumber, sesuai urutan tersimpan."""
    data = _open_vectorstore_readonly().get(where={"source": source}, include=["documents"])
    return [{"index": i + 1, "text": text} for i, text in enumerate(data.get("documents") or [])]