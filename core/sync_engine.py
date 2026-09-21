"""Pipeline sinkronisasi & pelatihan ulang Vector DB ChromaDB.

Alur: Document Loader (PDF/TXT/MD) + artikel MySQL (budaya & wisata)
-> Text Splitter (RecursiveCharacterTextSplitter) -> Embedding -> Upsert ke ChromaDB.
"""
import logging
import os
import re
import time
from datetime import datetime, timezone

from flask import current_app
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader

from core import db as dbcore
from core.content import html_to_plain_text
from core.rag_engine import get_embeddings, reset_engine_cache
from langchain_community.vectorstores import Chroma

logger = logging.getLogger(__name__)

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


def _add_documents_with_retry(vectorstore, batch: list[Document]) -> None:
    attempt = 0
    while True:
        try:
            vectorstore.add_documents(batch)
            return
        except Exception as exc:
            message = str(exc)
            attempt += 1
            if not _is_quota_error(message) or attempt > _EMBED_MAX_RETRIES:
                raise
            delay = _parse_retry_delay_seconds(message)
            logger.warning(
                "Kuota embedding Gemini tercapai, menunggu %.0f detik lalu mencoba lagi (percobaan %d/%d)...",
                delay, attempt, _EMBED_MAX_RETRIES,
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
    rows = dbcore.query_all("SELECT id, nama_file, tipe_file, path_file FROM knowledge_docs")
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

    for row in dbcore.query_all("SELECT id, judul, kategori, ringkasan, konten_lengkap FROM budaya"):
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

    for row in dbcore.query_all(
        "SELECT id, nama_wisata, wilayah, deskripsi, fasilitas, alamat, tiket_masuk, jam_operasional FROM wisata"
    ):
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


def run_sync() -> dict:
    """Eksekusi penuh pipeline sinkronisasi. Mengembalikan ringkasan hasil."""
    knowledge_docs = _load_knowledge_docs()
    article_docs = _load_mysql_articles()
    all_docs = knowledge_docs + article_docs

    if not all_docs:
        return {"success": False, "message": "Tidak ada dokumen atau artikel untuk disinkronkan.", "chunks": 0}

    chunks = SPLITTER.split_documents(all_docs)

    collection_name = current_app.config["CHROMA_COLLECTION_NAME"]
    persist_dir = current_app.config["CHROMA_PERSIST_DIR"]
    embeddings = get_embeddings()

    # Rebuild koleksi secara bersih agar tidak ada duplikasi/data basi.
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    try:
        vectorstore.delete_collection()
    except Exception:
        pass

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    for i in range(0, len(chunks), _EMBED_BATCH_SIZE):
        batch = chunks[i:i + _EMBED_BATCH_SIZE]
        _add_documents_with_retry(vectorstore, batch)

    # Tandai semua dokumen pengetahuan sebagai sudah ter-index.
    dbcore.execute("UPDATE knowledge_docs SET status_indexed = TRUE")

    reset_engine_cache()

    synced_at = datetime.now(timezone.utc)
    marker_path = os.path.join(persist_dir, "last_sync.txt")
    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(synced_at.isoformat())

    return {
        "success": True,
        "message": "Sinkronisasi & pelatihan ulang vector DB berhasil.",
        "chunks": len(chunks),
        "documents": len(all_docs),
        "synced_at": synced_at.isoformat(),
    }


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
