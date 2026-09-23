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
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

# Batas waktu keras untuk panggilan LLM. Parameter `timeout=` bawaan LangChain
# tidak selalu ditegakkan saat API sedang macet (hang), jadi kita paksa
# lewat thread terpisah agar pengguna tidak menunggu tanpa batas.
# Model gratis OpenRouter biasanya menjawab 7-12 detik, dan lebih lambat lagi saat
# providernya ramai. Ambang 15 detik membuat jawaban yang sebenarnya hampir jadi
# ikut dibuang jadi pesan "kendala teknis" (berikut tombol link-nya), jadi diberi
# kelonggaran. Kegagalan yang benar-benar fatal (429/503) tetap kembali cepat.
_LLM_CALL_TIMEOUT_SECONDS = 25
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
Cakupan Anda HANYA budaya Suku Moi dan tempat wisata di Kota Sorong maupun
Kabupaten Sorong.

ATURAN KETAT:
1. FAKTA SPESIFIK — nama tempat, harga tiket, jam operasional, alamat/lokasi,
   fasilitas, serta isi adat/tradisi — HANYA boleh diambil dari KONTEKS di bawah.
   Jangan pernah mengarang atau menebak angka maupun nama. Kalau KONTEKS tidak
   memuatnya, katakan dengan sopan bahwa detail itu belum tersedia di basis
   pengetahuan kami.
2. Untuk pertanyaan ringan yang masih seputar wisata/budaya Sorong Raya tetapi
   bukan soal data spesifik — misalnya tips bepergian sendiri dengan aman, barang
   yang perlu dibawa, etiket saat berkunjung ke kampung adat, atau waktu terbaik
   berkunjung — Anda BOLEH menjawab memakai pengetahuan umum yang masuk akal dan
   berhati-hati, walaupun tidak ada di KONTEKS. Sampaikan sebagai saran umum.
3. Jika pertanyaannya benar-benar di luar topik budaya & wisata Sorong Raya
   (mis. politik, pemrograman, hal pribadi), tolak dengan sopan lalu arahkan
   kembali ke topik budaya & wisata Sorong Raya.
4. Perhatikan riwayat percakapan sebelumnya. Kalau pengguna memakai kata rujukan
   seperti "di sana", "tempat itu", "wisata tersebut", atau "tiketnya", pahami
   maksudnya dari percakapan sebelumnya tanpa perlu bertanya ulang.
5. Gunakan Bahasa Indonesia yang santun, ringkas, dan mudah dipahami wisatawan.
6. Format jawaban HANYA dengan gaya berikut (jangan pakai heading #, tabel, atau blok kode):
   - Tebalkan (pakai **teks**) nama setiap destinasi/budaya yang Anda sebutkan, supaya
     mudah dikenali wisatawan. Jangan menebalkan kata lain selain nama destinasi/budaya
     dan istilah penting (mis. harga tiket).
   - Untuk daftar/rekomendasi lebih dari satu tempat, gunakan tanda hubung (-) atau
     angka (1., 2., 3.) di awal baris, satu tempat per baris.
   - Selipkan emoji yang relevan dan secukupnya (maksimal 1 per kalimat/poin) supaya
     jawaban terasa hangat, misalnya 📍 lokasi, 🎟️ tiket, ⏰ jam operasional,
     🏖️ pantai, 🌊 pulau, 🌿 alam, 🏛️ budaya/sejarah. Jangan berlebihan.
7. Sebutkan nama destinasi/budaya persis seperti pada KONTEKS (jangan disingkat atau
   diganti nama lain) — sistem akan otomatis menampilkan tombol link menuju halaman
   detailnya di bawah jawaban Anda berdasarkan nama yang Anda sebutkan itu.
8. JANGAN menuliskan URL/tautan apapun sendiri di dalam jawaban. JANGAN PERNAH
   menyebutkan, menjelaskan, atau mengomentari kepada pengguna bahwa jawaban Anda
   ditebalkan supaya sistem menampilkan tombol/link — itu instruksi internal untuk
   Anda saja, bukan sesuatu yang boleh dibaca atau diketahui pengguna.

KONTEKS:
{context}
"""

EMPTY_CONTEXT = (
    "(Tidak ada dokumen yang cocok untuk pertanyaan ini. Jangan menyebutkan fakta "
    "spesifik apa pun tentang destinasi/budaya tertentu. Anda tetap boleh memberi "
    "saran umum sesuai aturan 2, atau menolak sopan sesuai aturan 3.)"
)


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


# Kata rujukan penanda pertanyaan lanjutan ("berapa tiketnya?", "di sana aman?").
# Pertanyaan seperti ini tidak menyebut subjeknya, jadi kueri retrieval-nya perlu
# digabung dengan pertanyaan pengguna sebelumnya agar dokumennya tetap ketemu.
_REFERENTIAL_WORDS = {"tersebut", "itu", "sana", "situ", "ini", "tadi", "sebelumnya"}


def _is_follow_up(question: str) -> bool:
    words = re.findall(r"\w+", question.lower())
    return any(w in _REFERENTIAL_WORDS or w.endswith("nya") for w in words)


def _retrieval_query(question: str, history: list) -> str:
    if not history or not _is_follow_up(question):
        return question
    last_user = next(
        (h["text"] for h in reversed(history) if h.get("role") == "user" and h.get("text")),
        None,
    )
    return f"{last_user} {question}" if last_user else question


def _history_messages(history: list) -> list:
    """Ubah riwayat percakapan dari klien menjadi pesan LangChain agar chatbot
    ingat jawaban sebelumnya. Isi riwayat sudah dibatasi jumlah & panjangnya di
    routes/api.py sebelum sampai ke sini."""
    messages = []
    for item in history or []:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        role = item.get("role")
        messages.append(HumanMessage(content=text) if role == "user" else AIMessage(content=text))
    return messages


def answer_query(question: str, history: list | None = None) -> dict:
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
        results = vectorstore.similarity_search_with_relevance_scores(
            _retrieval_query(question, history), k=top_k
        )
    except Exception:
        logger.exception("RAG retrieval gagal untuk pertanyaan: %r", question)
        results = []

    relevant = [(doc, score) for doc, score in results if score >= threshold]

    # Tanpa dokumen yang cocok, pertanyaan TIDAK langsung ditolak: LLM tetap
    # dipanggil dengan konteks kosong supaya pertanyaan ringan yang masih seputar
    # wisata/budaya (mis. "aman tidak kalau ke sana sendirian?") tetap terjawab,
    # sementara pertanyaan di luar topik ditolak oleh aturan 3 pada prompt.
    context_text = (
        "\n\n---\n\n".join(doc.page_content for doc, _ in relevant) if relevant else EMPTY_CONTEXT
    )
    # Konten sistem & riwayat dikirim sebagai objek pesan (bukan string template)
    # supaya tanda kurung kurawal di dokumen/percakapan tidak dianggap placeholder.
    base_messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context_text))]
    base_messages += _history_messages(history)
    base_messages.append(HumanMessage(content=question))

    answer_text = None
    for model in _candidate_models(current_app):
        llm = get_llm(model)
        for attempt in range(_QUOTA_RETRIES_PER_MODEL + 1):
            try:
                future = _llm_executor.submit(llm.invoke, base_messages)
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

    return {"answer": answer_text, "sources": sources, "grounded": bool(relevant)}


def _normalize_for_match(text: str) -> str:
    """Samakan bentuk teks sebelum dicocokkan: huruf kecil, tanda baca & emoji
    (mis. markdown **, tanda kurung, titik) jadi spasi."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]+", " ", (text or "").lower())).strip()


def _is_mentioned(haystack: str, name: str) -> bool:
    """True kalau nama dari DB benar-benar disebut di jawaban. Nama bertanda kurung
    seperti "Pulau Raam (Pulau Buaya)" juga cocok saat LLM hanya menulis bagian
    depannya. Pencocokan dibatasi batas kata supaya "Pulau Um" tidak ikut cocok
    pada "Pulau Umbrella"."""
    padded = f" {haystack} "
    variants = {_normalize_for_match(name), _normalize_for_match(name.split("(")[0])}
    return any(len(v) >= 4 and f" {v} " in padded for v in variants)


def _build_sources(relevant: list, answer_text: str = "") -> list[dict]:
    """Bangun daftar sumber {title, url} agar chatbot bisa menampilkan tombol link
    menuju halaman detail wisata/budaya.

    Judul & link diambil langsung dari MySQL (bukan dari teks vector yang ter-cache)
    supaya selalu mencerminkan data wisata/budaya terkini, dan otomatis hilang
    kalau record-nya sudah dihapus sejak terakhir sinkronisasi.

    Dua tahap:
    1. Dari dokumen yang lolos ambang batas relevansi retrieval (`relevant`).
    2. Dari pemindaian teks jawaban terhadap seluruh nama wisata/budaya di DB.
       Tahap ini yang membuat pertanyaan rekomendasi dapat tombol untuk SETIAP
       destinasi yang disebut, bukan cuma yang kebetulan lolos top-k retrieval —
       dan tidak bergantung pada LLM menebalkan namanya dengan benar.
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

    haystack = _normalize_for_match(answer_text)
    if haystack:
        for row in wisata_model.list_names():
            if _is_mentioned(haystack, row["nama_wisata"]):
                add_source(
                    ("wisata", row["id"]), row["nama_wisata"],
                    url_for("wisata_detail", wisata_id=row["id"]),
                )
        for row in budaya_model.list_names():
            if _is_mentioned(haystack, row["judul"]):
                add_source(
                    ("budaya", row["id"]), row["judul"],
                    url_for("budaya_detail", budaya_id=row["id"]),
                )

    return sources
