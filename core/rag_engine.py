"""Inisialisasi LangChain + ChromaDB + prompt template + query ke LLM (RAG Engine).

Embedding (retrieval) tetap memakai Google Gemini. Chat/generation memakai
OpenRouter (banyak model gratis) lewat endpoint OpenAI-compatible-nya.
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# Batas waktu keras untuk panggilan LLM. Parameter `timeout=` bawaan LangChain
# tidak selalu ditegakkan saat API sedang macet (hang), jadi kita paksa
# lewat thread terpisah agar pengguna tidak menunggu tanpa batas.
_LLM_CALL_TIMEOUT_SECONDS = 20
_llm_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="rag-llm")

_embeddings = None
_vectorstore = None
_llm = None

FALLBACK_ANSWER = (
    "Maaf, informasi mengenai hal tersebut belum tersedia dalam basis pengetahuan "
    "budaya dan wisata Sorong Raya kami. Silakan ajukan pertanyaan lain seputar "
    "budaya Suku Moi atau destinasi wisata Kota/Kabupaten Sorong."
)

ERROR_ANSWER = (
    "Maaf, asisten virtual sedang mengalami kendala teknis sesaat (mis. layanan AI "
    "sedang sibuk). Silakan coba lagi dalam beberapa saat."
)

GREETING_ANSWER = (
    "Halo! Selamat datang di Sorong Raya. Saya pemandu pintar yang siap membantu "
    "menjawab pertanyaan seputar budaya Suku Moi maupun destinasi wisata Kota dan "
    "Kabupaten Sorong. Silakan tanyakan apa saja, ya!"
)

# Sapaan singkat dijawab langsung tanpa RAG/LLM — lebih cepat & hemat kuota API.
# Bentuk dasar saja (huruf berulang seperti "haloo"/"haii" dinormalisasi terlebih dahulu).
_GREETING_WORDS = {
    "halo", "hai", "hi", "hey", "hei", "helo",
    "pagi", "siang", "sore", "malam",
    "permisi", "asalamualaikum",
    "tes", "test", "cek",
}


def _collapse_repeated_letters(word: str) -> str:
    """"Haloo"/"haii"/"paagi" -> "halo"/"hai"/"pagi" agar salah ketik tetap terdeteksi."""
    return re.sub(r"(.)\1+", r"\1", word)


def _is_greeting(question: str) -> bool:
    normalized = re.sub(r"[^\w\s]", "", question.lower()).strip()
    if not normalized:
        return False
    words = [_collapse_repeated_letters(w) for w in normalized.split()]
    if len(words) > 4:
        return False
    return any(w in _GREETING_WORDS for w in words)


def _strip_markdown(text: str) -> str:
    """Buang sintaks markdown (bold/bullet) agar tidak tampil sebagai tanda bintang mentah di bubble chat."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?m)^[ \t]*\*[ \t]+", "- ", text)
    text = re.sub(r"(?m)^[ \t]*\*(?!\*)", "-", text)
    return text.strip()


SYSTEM_PROMPT = """Anda adalah asisten virtual "Sorong Raya" yang ramah dan sopan.
Tugas Anda HANYA menjawab pertanyaan seputar budaya Suku Moi dan tempat wisata di
Kota Sorong maupun Kabupaten Sorong, murni berdasarkan KONTEKS yang diberikan di bawah ini.

ATURAN KETAT:
1. Jawab HANYA berdasarkan informasi pada KONTEKS. Jangan mengarang (berhalusinasi).
2. Jika KONTEKS tidak relevan atau tidak memuat jawaban, katakan dengan sopan bahwa
   informasi tersebut belum tersedia dalam basis pengetahuan.
3. Gunakan Bahasa Indonesia yang santun, ringkas, dan mudah dipahami wisatawan.
4. Jangan menjawab pertanyaan di luar topik budaya & wisata Sorong Raya.
5. JANGAN gunakan format markdown sama sekali (tanpa tanda bintang **tebal**,
   tanpa bullet list berawalan *). Tulis jawaban sebagai kalimat/paragraf mengalir
   biasa, seperti percakapan chat WhatsApp. Jika perlu daftar, gunakan tanda hubung (-)
   atau angka (1., 2., 3.) tanpa tanda bintang.

KONTEKS:
{context}
"""


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from flask import current_app
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=current_app.config["GEMINI_EMBEDDING_MODEL"],
            google_api_key=current_app.config["GEMINI_API_KEY"],
        )
    return _embeddings


def get_vectorstore(fresh=False):
    """Kembalikan instance Chroma vectorstore (persisted lokal)."""
    global _vectorstore
    if fresh or _vectorstore is None:
        from flask import current_app
        _vectorstore = Chroma(
            collection_name=current_app.config["CHROMA_COLLECTION_NAME"],
            embedding_function=get_embeddings(),
            persist_directory=current_app.config["CHROMA_PERSIST_DIR"],
        )
    return _vectorstore


def get_llm():
    """LLM chat/generation via OpenRouter (endpoint OpenAI-compatible)."""
    global _llm
    if _llm is None:
        from flask import current_app
        _llm = ChatOpenAI(
            model=current_app.config["OPENROUTER_CHAT_MODEL"],
            api_key=current_app.config["OPENROUTER_API_KEY"],
            base_url=current_app.config["OPENROUTER_BASE_URL"],
            temperature=0.3,
            timeout=20,
            max_retries=1,
            default_headers={
                "HTTP-Referer": "https://sorong-raya.local",
                "X-Title": "Sorong Raya Chatbot",
            },
        )
    return _llm


def reset_engine_cache():
    """Dipanggil setelah re-sync agar vectorstore dimuat ulang dari disk."""
    global _vectorstore
    _vectorstore = None


def answer_query(question: str) -> dict:
    """Jalankan retrieval + generation. Return dict {answer, sources, grounded}."""
    from flask import current_app

    question = (question or "").strip()
    if not question:
        return {"answer": FALLBACK_ANSWER, "sources": [], "grounded": False}

    if _is_greeting(question):
        return {"answer": GREETING_ANSWER, "sources": [], "grounded": False}

    vectorstore = get_vectorstore()
    top_k = current_app.config["RAG_TOP_K"]
    threshold = current_app.config["RAG_SIMILARITY_THRESHOLD"]

    try:
        results = vectorstore.similarity_search_with_relevance_scores(question, k=top_k)
    except Exception:
        logger.exception("RAG retrieval gagal untuk pertanyaan: %r", question)
        results = []

    relevant = [(doc, score) for doc, score in results if score >= threshold]

    if not relevant:
        return {"answer": FALLBACK_ANSWER, "sources": [], "grounded": False}

    context_text = "\n\n---\n\n".join(doc.page_content for doc, _ in relevant)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT.format(context=context_text)),
        ("human", "{question}"),
    ])

    chain = prompt | get_llm()
    try:
        future = _llm_executor.submit(chain.invoke, {"question": question})
        response = future.result(timeout=_LLM_CALL_TIMEOUT_SECONDS)
        answer_text = _strip_markdown(response.content.strip())
    except FutureTimeoutError:
        logger.warning("RAG generation timeout (>%ss) untuk pertanyaan: %r", _LLM_CALL_TIMEOUT_SECONDS, question)
        return {"answer": ERROR_ANSWER, "sources": [], "grounded": False}
    except Exception:
        logger.exception("RAG generation gagal untuk pertanyaan: %r", question)
        return {"answer": ERROR_ANSWER, "sources": [], "grounded": False}

    sources = _build_sources(relevant)

    return {"answer": answer_text, "sources": sources, "grounded": True}


def _build_sources(relevant: list) -> list[dict]:
    """Bangun daftar sumber {title, url} dari metadata dokumen relevan.

    Judul & link diambil langsung dari MySQL (bukan dari teks vector yang ter-cache)
    supaya selalu mencerminkan data wisata/budaya terkini, dan otomatis hilang
    kalau record-nya sudah dihapus sejak terakhir sinkronisasi.
    """
    from flask import url_for
    from core import db as dbcore

    sources = []
    seen = set()
    for doc, _ in relevant:
        meta = doc.metadata
        table = meta.get("table")
        record_id = meta.get("record_id")
        key = (table, record_id) if table and record_id else meta.get("source")
        if key in seen:
            continue
        seen.add(key)

        if table == "wisata" and record_id:
            row = dbcore.query_one("SELECT nama_wisata FROM wisata WHERE id = %s", (record_id,))
            if row:
                sources.append({
                    "title": row["nama_wisata"],
                    "url": url_for("wisata_detail", wisata_id=record_id),
                })
        elif table == "budaya" and record_id:
            row = dbcore.query_one("SELECT judul FROM budaya WHERE id = %s", (record_id,))
            if row:
                sources.append({
                    "title": row["judul"],
                    "url": url_for("budaya_detail", budaya_id=record_id),
                })
        else:
            sources.append({"title": meta.get("source", "Dokumen tidak diketahui"), "url": None})

    return sources
