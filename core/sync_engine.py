"""Pipeline sinkronisasi & pelatihan ulang Vector DB ChromaDB.

Alur: Document Loader (PDF/TXT/MD) + artikel MySQL (budaya & wisata)
-> Text Splitter (RecursiveCharacterTextSplitter) -> Embedding -> Upsert ke ChromaDB.
"""
import os
from datetime import datetime, timezone

from flask import current_app
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader

from core import db as dbcore
from core.rag_engine import get_embeddings, reset_engine_cache
from langchain_community.vectorstores import Chroma

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " ", ""],
)


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
            f"Detail: {row['konten_lengkap']}"
        )
        docs.append(Document(
            page_content=content,
            metadata={"source": f"budaya:{row['judul']}", "table": "budaya", "record_id": row["id"]},
        ))

    for row in dbcore.query_all(
        "SELECT id, nama_wisata, wilayah, deskripsi, fasilitas, lokasi, tiket_masuk, jam_operasional FROM wisata"
    ):
        content = (
            f"Nama Wisata: {row['nama_wisata']}\n"
            f"Wilayah: {row['wilayah']}\n"
            f"Deskripsi: {row['deskripsi']}\n"
            f"Fasilitas: {row['fasilitas']}\n"
            f"Lokasi: {row['lokasi']}\n"
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

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_dir,
    )

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
