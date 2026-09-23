"""Inisialisasi LangChain + ChromaDB + prompt template + query ke LLM (RAG Engine).

Embedding (retrieval) tetap memakai Google Gemini. Chat/generation memakai
OpenRouter (banyak model gratis) lewat endpoint OpenAI-compatible-nya.
"""
import html as html_lib
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from openai import RateLimitError
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# Batas waktu keras untuk panggilan LLM. Parameter `timeout=` bawaan LangChain
# tidak selalu ditegakkan saat API sedang macet (hang), jadi kita paksa
# lewat thread terpisah agar pengguna tidak menunggu tanpa batas.
_LLM_CALL_TIMEOUT_SECONDS = 15
_llm_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="rag-llm")

# Model gratis OpenRouter kadang kena rate-limit sesaat di provider upstream-nya
# (bukan kuota akun kita). Sebelum pindah ke model fallback berikutnya, coba lagi
# sekali dulu di model yang sama setelah jeda singkat — sering kali sudah pulih.
_QUOTA_RETRY_DELAY_SECONDS = 3
_QUOTA_RETRIES_PER_MODEL = 1

_embeddings = None
_vectorstore = None
_llm_by_model = {}

FALLBACK_ANSWER = (
    "🙏 Maaf, informasi mengenai hal tersebut belum tersedia dalam basis pengetahuan "
    "budaya dan wisata Sorong Raya kami. Silakan ajukan pertanyaan lain seputar "
    "budaya Suku Moi atau destinasi wisata Kota/Kabupaten Sorong."
)

ERROR_ANSWER = (
    "⚠️ Maaf, asisten virtual sedang mengalami kendala teknis sesaat (mis. layanan AI "
    "sedang sibuk). Silakan coba lagi dalam beberapa saat."
)

GREETING_ANSWER = (
    "👋 Halo! Selamat datang di Sorong Raya. Saya pemandu pintar yang siap membantu "
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


_BULLET_RE = re.compile(r"^[\-\*]\s+(.*)")
_NUMBERED_RE = re.compile(r"^\d+[.)]\s+(.*)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _render_rich_answer(text: str) -> str:
    """Escape HTML lalu ubah subset markdown (bold & bullet/nomor list) milik LLM
    menjadi HTML aman, supaya bubble chat menampilkan highlight & daftar rapi
    alih-alih teks abu-abu polos atau tanda bintang mentah."""
    text = (text or "").strip()
    if not text:
        return ""

    parts: list[str] = []
    list_buffer: list[str] = []
    list_tag: str | None = None

    def flush_list():
        nonlocal list_tag
        if list_buffer:
            items = "".join(f"<li>{item}</li>" for item in list_buffer)
            parts.append(f"<{list_tag}>{items}</{list_tag}>")
            list_buffer.clear()
        list_tag = None

    for raw_line in text.splitlines():
        line = html_lib.escape(raw_line.strip(), quote=False)
        bullet_match = _BULLET_RE.match(line)
        numbered_match = _NUMBERED_RE.match(line)
        if bullet_match:
            if list_tag != "ul":
                flush_list()
                list_tag = "ul"
            list_buffer.append(bullet_match.group(1))
        elif numbered_match:
            if list_tag != "ol":
                flush_list()
                list_tag = "ol"
            list_buffer.append(numbered_match.group(1))
        else:
            flush_list()
            if line:
                parts.append(f"<p>{line}</p>")
    flush_list()

    html_out = "".join(parts) if parts else f"<p>{html_lib.escape(text, quote=False)}</p>"
    html_out = _BOLD_RE.sub(r'<strong class="chat-highlight">\1</strong>', html_out)
    return html_out


SYSTEM_PROMPT = """Anda adalah asisten virtual "Sorong Raya" yang ramah dan sopan.
Tugas Anda HANYA menjawab pertanyaan seputar budaya Suku Moi dan tempat wisata di
Kota Sorong maupun Kabupaten Sorong, murni berdasarkan KONTEKS yang diberikan di bawah ini.

ATURAN KETAT:
1. Jawab HANYA berdasarkan informasi pada KONTEKS. Jangan mengarang (berhalusinasi).
2. Jika KONTEKS tidak relevan atau tidak memuat jawaban, katakan dengan sopan bahwa
   informasi tersebut belum tersedia dalam basis pengetahuan.
3. Gunakan Bahasa Indonesia yang santun, ringkas, dan mudah dipahami wisatawan.
4. Jangan menjawab pertanyaan di luar topik budaya & wisata Sorong Raya.
5. Format jawaban HANYA dengan gaya berikut (jangan pakai heading #, tabel, atau blok kode):
   - Tebalkan (pakai **teks**) nama setiap destinasi/budaya yang Anda sebutkan, supaya
     mudah dikenali wisatawan. Jangan menebalkan kata lain selain nama destinasi/budaya
     dan istilah penting (mis. harga tiket).
   - Untuk daftar/rekomendasi lebih dari satu tempat, gunakan tanda hubung (-) atau
     angka (1., 2., 3.) di awal baris, satu tempat per baris.
   - Selipkan emoji yang relevan dan secukupnya (maksimal 1 per kalimat/poin) supaya
     jawaban terasa hangat, misalnya 📍 lokasi, 🎟️ tiket, ⏰ jam operasional,
     🏖️ pantai, 🌊 pulau, 🌿 alam, 🏛️ budaya/sejarah. Jangan berlebihan.
6. Sebutkan nama destinasi/budaya persis seperti pada KONTEKS (jangan disingkat atau
   diganti nama lain) — sistem akan otomatis menampilkan tombol link menuju halaman
   detailnya di bawah jawaban Anda berdasarkan nama yang Anda tebalkan tersebut.
7. JANGAN menuliskan URL/tautan apapun sendiri di dalam jawaban. JANGAN PERNAH
   menyebutkan, menjelaskan, atau mengomentari kepada pengguna bahwa jawaban Anda
   ditebalkan supaya sistem menampilkan tombol/link — itu instruksi internal untuk
   Anda saja, bukan sesuatu yang boleh dibaca atau diketahui pengguna.

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


def get_llm(model: str):
    """LLM chat/generation via OpenRouter (endpoint OpenAI-compatible), per-model instance di-cache."""
    if model not in _llm_by_model:
        from flask import current_app
        _llm_by_model[model] = ChatOpenAI(
            model=model,
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
    return _llm_by_model[model]


def _candidate_models(current_app) -> list[str]:
    models = [current_app.config["OPENROUTER_CHAT_MODEL"]]
    models += current_app.config.get("OPENROUTER_CHAT_MODEL_FALLBACKS", [])
    seen = set()
    ordered = []
    for m in models:
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered


def reset_engine_cache():
    """Dipanggil setelah re-sync agar vectorstore dimuat ulang dari disk."""
    global _vectorstore
    _vectorstore = None


def answer_query(question: str) -> dict:
    """Jalankan retrieval + generation. Return dict {answer, sources, grounded}."""
    from flask import current_app

    question = (question or "").strip()
    if not question:
        return {"answer": _render_rich_answer(FALLBACK_ANSWER), "sources": [], "grounded": False}

    if _is_greeting(question):
        return {"answer": _render_rich_answer(GREETING_ANSWER), "sources": [], "grounded": False}

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
        return {"answer": _render_rich_answer(FALLBACK_ANSWER), "sources": [], "grounded": False}

    context_text = "\n\n---\n\n".join(doc.page_content for doc, _ in relevant)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT.format(context=context_text)),
        ("human", "{question}"),
    ])

    answer_text = None
    for model in _candidate_models(current_app):
        chain = prompt | get_llm(model)
        for attempt in range(_QUOTA_RETRIES_PER_MODEL + 1):
            try:
                future = _llm_executor.submit(chain.invoke, {"question": question})
                response = future.result(timeout=_LLM_CALL_TIMEOUT_SECONDS)
                raw_answer = response.content.strip()
                answer_text = _render_rich_answer(raw_answer)
                break
            except FutureTimeoutError:
                logger.warning(
                    "RAG generation timeout (>%ss) model=%s untuk pertanyaan: %r",
                    _LLM_CALL_TIMEOUT_SECONDS, model, question,
                )
                break
            except RateLimitError:
                if attempt < _QUOTA_RETRIES_PER_MODEL:
                    logger.warning(
                        "Model %s rate-limited upstream, coba lagi dalam %ss...",
                        model, _QUOTA_RETRY_DELAY_SECONDS,
                    )
                    time.sleep(_QUOTA_RETRY_DELAY_SECONDS)
                    continue
                logger.warning("Model %s tetap rate-limited, pindah ke model fallback berikutnya.", model)
            except Exception:
                logger.warning(
                    "RAG generation gagal model=%s untuk pertanyaan: %r, coba model fallback berikutnya.",
                    model, question, exc_info=True,
                )
                break
        if answer_text is not None:
            break

    if answer_text is None:
        return {"answer": _render_rich_answer(ERROR_ANSWER), "sources": [], "grounded": False}

    sources = _build_sources(relevant, raw_answer)

    return {"answer": answer_text, "sources": sources, "grounded": True}


def _build_sources(relevant: list, answer_text: str = "") -> list[dict]:
    """Bangun daftar sumber {title, url} agar chatbot bisa menampilkan tombol link
    menuju halaman detail wisata/budaya.

    Judul & link diambil langsung dari MySQL (bukan dari teks vector yang ter-cache)
    supaya selalu mencerminkan data wisata/budaya terkini, dan otomatis hilang
    kalau record-nya sudah dihapus sejak terakhir sinkronisasi.

    Dua tahap:
    1. Dari dokumen yang lolos ambang batas relevansi retrieval (`relevant`).
    2. Dari SEMUA nama yang ditebalkan (**...**) di jawaban LLM tapi belum tercakup
       tahap 1 — supaya pertanyaan rekomendasi yang menyebut banyak destinasi tetap
       dapat tombol untuk tiap destinasi yang benar-benar ada di DB, bukan cuma yang
       kebetulan lolos top-k retrieval.
    """
    from flask import url_for
    from models import budaya as budaya_model
    from models import wisata as wisata_model

    sources = []
    seen = set()

    def add_source(key, title, url):
        if key in seen:
            return
        seen.add(key)
        sources.append({"title": title, "url": url})

    for doc, _ in relevant:
        meta = doc.metadata
        table = meta.get("table")
        record_id = meta.get("record_id")

        if table == "wisata" and record_id:
            row = wisata_model.get_nama(record_id)
            if row:
                add_source(
                    ("wisata", record_id), row["nama_wisata"],
                    url_for("wisata_detail", wisata_id=record_id),
                )
        elif table == "budaya" and record_id:
            row = budaya_model.get_title(record_id)
            if row:
                add_source(
                    ("budaya", record_id), row["judul"],
                    url_for("budaya_detail", budaya_id=record_id),
                )
        else:
            source_name = meta.get("source")
            add_source(("doc", source_name), source_name or "Dokumen tidak diketahui", None)

    known_titles = {s["title"] for s in sources}
    bold_names = {m.strip() for m in _BOLD_RE.findall(answer_text) if m.strip()}
    bold_names -= known_titles
    if bold_names:
        for row in wisata_model.find_ids_by_names(bold_names):
            add_source(
                ("wisata", row["id"]), row["nama_wisata"],
                url_for("wisata_detail", wisata_id=row["id"]),
            )
        for row in budaya_model.find_ids_by_names(bold_names):
            add_source(
                ("budaya", row["id"]), row["judul"],
                url_for("budaya_detail", budaya_id=row["id"]),
            )

    return sources
