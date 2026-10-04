"""Inisialisasi LangChain + ChromaDB + prompt template + query ke LLM (RAG Engine).

Embedding (retrieval) tetap memakai Google Gemini. Chat/generation memakai
DeepSeek lewat Hive AI (lihat llm_config.py) bila HIVE_API_KEY diisi, dengan
OpenRouter dan Gemini sebagai cadangan.
"""
import html as html_lib
import logging
import re
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from openai import APIConnectionError, APIStatusError, RateLimitError

import llm_config
from core import ai_status
from langchain_chroma import Chroma
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

# Model gratis OpenRouter dibatasi ketat per akun (bukan per-model — lihat
# https://openrouter.ai/docs/api-reference/limits): 20 request/menit dan
# 50 request/hari gabungan semua model `:free`. Pertanyaan yang identik
# (mis. tombol saran cepat yang sama diklik banyak pengunjung berbeda, atau
# pertanyaan FAQ yang sering berulang) tidak perlu memanggil LLM lagi selama
# masih dalam TTL, supaya kuota harian yang kecil itu tidak cepat habis.
# Hanya dipakai untuk pertanyaan TANPA riwayat percakapan (giliran pertama) —
# jawaban lanjutan yang bergantung konteks personal tidak di-cache.
_answer_cache: "OrderedDict[str, tuple[float, dict]]" = OrderedDict()
_ANSWER_CACHE_TTL_SECONDS = 2 * 3600
_ANSWER_CACHE_MAX_ENTRIES = 200

FALLBACK_ANSWER = (
    "🙏 Maaf, informasi mengenai hal tersebut belum tersedia dalam basis pengetahuan "
    "budaya dan wisata Sorong Raya kami. Silakan ajukan pertanyaan lain seputar "
    "budaya Suku Moi atau destinasi wisata Kota/Kabupaten Sorong."
)

ERROR_ANSWER = (
    "⚠️ Maaf, asisten virtual sedang mengalami kendala teknis sesaat (mis. layanan AI "
    "sedang sibuk). Silakan coba lagi dalam beberapa saat."
)

# Dipakai khusus saat SEMUA model fallback gagal karena rate-limit (bukan error
# lain seperti timeout) — kondisi ini nyaris selalu berarti kuota harian akun
# OpenRouter untuk model gratis sudah habis (reset tiap 24 jam), jadi "coba lagi
# sebentar lagi" menyesatkan; kita jujur bilang perlu menunggu sampai besok.
QUOTA_EXHAUSTED_ANSWER = (
    "🙏 Maaf, kuota harian asisten AI kami untuk hari ini sudah habis. Silakan coba "
    "lagi besok, atau jelajahi langsung katalog Budaya dan Wisata kami lewat menu di atas."
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
# Dijalankan setelah _BOLD_RE (yang sudah melahap semua pasangan **), jadi tanda
# bintang tunggal yang tersisa dianggap juga sebagai penekanan LLM (mis. *Open
# Trip*) dan ditampilkan bold — bukan italic terpisah, biar konsisten dengan
# satu-satunya gaya highlight yang dipakai bubble chat.
_ITALIC_RE = re.compile(r"\*(.+?)\*")


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
    html_out = _ITALIC_RE.sub(r'<strong class="chat-highlight">\1</strong>', html_out)
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
2. Jawab HANYA berdasarkan KONTEKS di bawah. Jika KONTEKS tidak memuat informasi
   yang cukup untuk menjawab pertanyaan (termasuk tips umum atau saran yang tidak
   tertulis di KONTEKS), katakan dengan jujur dan sopan bahwa informasi tersebut
   belum tersedia di basis pengetahuan kami, lalu tawarkan topik budaya Suku Moi
   atau wisata Sorong Raya yang bisa Anda bantu. Jangan menambahkan pengetahuan
   dari luar KONTEKS.
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
    "spesifik apa pun. Jawab jujur bahwa informasinya belum tersedia sesuai aturan 2, "
    "atau tolak sopan sesuai aturan 3 bila di luar topik.)"
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


def _get_hive_llm():
    """LLM utama (DeepSeek via Hive AI); instance di-cache. Pengaturan ada di llm_config.py."""
    if "hive" not in _llm_by_model:
        _llm_by_model["hive"] = llm_config.build_hive_llm()
    return _llm_by_model["hive"]


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
            # Hampir semua model gratis OpenRouter adalah model "reasoning" yang
            # berpikir dulu sebelum menjawab: 20-30 detik, sering lewat batas
            # _LLM_CALL_TIMEOUT_SECONDS. Chatbot ini cuma merangkum KONTEKS hasil
            # retrieval, tidak butuh rantai penalaran, jadi dimatikan (terukur
            # 28s -> 4s). Model tanpa dukungan reasoning mengabaikan parameter ini.
            extra_body={"reasoning": {"enabled": False}},
            default_headers={
                "HTTP-Referer": "https://sorong-raya.local",
                "X-Title": "Sorong Raya Chatbot",
            },
        )
    return _llm_by_model[model]


def _upstream_error_summary(exc: Exception) -> str | None:
    """Ringkasan satu baris kalau `exc` adalah gangguan dari OpenRouter/provider
    (bukan bug di kode kita), atau None kalau bukan."""
    if isinstance(exc, APIStatusError):
        body = exc.body if isinstance(exc.body, dict) else {}
        provider = (body.get("metadata") or {}).get("provider_name", "?")
        return f"HTTP {exc.status_code} dari {provider}: {body.get('message', exc.message)}"
    if isinstance(exc, APIConnectionError):
        return f"koneksi gagal: {type(exc).__name__}"
    # langchain_openai melempar ValueError(dict) kalau OpenRouter membalas 200
    # tapi isinya error, mis. "Upstream error from Nvidia: Service temporarily unavailable".
    if isinstance(exc, ValueError) and exc.args and isinstance(exc.args[0], dict):
        return str(exc.args[0].get("message", exc.args[0]))[:160]
    return None


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
    """Dipanggil setelah re-sync agar vectorstore dimuat ulang dari disk, dan cache
    jawaban lama (yang mungkin memuat data wisata/budaya yang sudah berubah) tidak
    dipakai lagi."""
    global _vectorstore
    _vectorstore = None
    _answer_cache.clear()


def _cache_key(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def _cache_get(question: str) -> dict | None:
    entry = _answer_cache.get(_cache_key(question))
    if entry is None:
        return None
    cached_at, result = entry
    if time.time() - cached_at > _ANSWER_CACHE_TTL_SECONDS:
        return None
    return result


def _cache_set(question: str, result: dict) -> None:
    key = _cache_key(question)
    _answer_cache[key] = (time.time(), result)
    _answer_cache.move_to_end(key)
    while len(_answer_cache) > _ANSWER_CACHE_MAX_ENTRIES:
        _answer_cache.popitem(last=False)


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


def _get_gemini_llm(model: str):
    """LLM cadangan (Gemini) untuk menyusun jawaban; instance di-cache per nama model."""
    if model not in _llm_by_model:
        from flask import current_app
        from langchain_google_genai import ChatGoogleGenerativeAI

        _llm_by_model[f"gemini:{model}"] = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=current_app.config["GEMINI_API_KEY"],
            temperature=0.3,
            timeout=20,
            max_retries=0,  # percobaan ulang diatur sendiri oleh answer_query
        )
        _llm_by_model[model] = _llm_by_model[f"gemini:{model}"]
    return _llm_by_model[model]


def _message_text(response) -> str:
    """Isi teks dari balasan model; Gemini bisa mengembalikan daftar bagian (parts)."""
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "".join(
            part if isinstance(part, str) else (part.get("text", "") if isinstance(part, dict) else "")
            for part in content
        )
    return content if isinstance(content, str) else str(content or "")


def _is_quota_error(exc: Exception) -> bool:
    """Apakah galat ini berarti kuota/rate-limit (khusus Gemini, yang tidak memakai RateLimitError openai)."""
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return (
        "resourceexhausted" in name
        or "toomanyrequests" in name
        or "429" in text
        or "quota" in text
        or "resource_exhausted" in text
    )


# Dipakai saat TIDAK ADA model yang bisa menjawab (kuota habis / semua gagal) tetapi pencarian
# pengetahuan (yang hanya butuh embedding) masih menemukan halaman yang relevan.
LIMITED_MODE_ANSWER = (
    "ℹ️ Asisten AI sedang mencapai batas penggunaannya, jadi saya belum bisa menyusun jawaban "
    "lengkap. Namun berikut halaman di portal yang paling relevan dengan pertanyaan Anda, "
    "silakan dibuka untuk informasi detailnya."
)


def _limited_mode_result(relevant: list, only_rate_limited: bool) -> dict:
    """Jawaban tanpa LLM: tautan ke halaman paling relevan hasil retrieval (maks 3).
    Bila tidak ada yang relevan, kembali ke pesan kuota / kendala teknis biasa."""
    sources = [s for s in _build_sources(relevant) if s.get("url")][:3] if relevant else []
    if sources:
        return {
            "answer": _render_rich_answer(LIMITED_MODE_ANSWER),
            "sources": sources,
            "grounded": True,
            "mode": "limited",
        }
    fallback = QUOTA_EXHAUSTED_ANSWER if only_rate_limited else ERROR_ANSWER
    return {"answer": _render_rich_answer(fallback), "sources": [], "grounded": False, "mode": "limited"}


def answer_query(question: str, history: list | None = None) -> dict:
    """Jalankan retrieval + generation. Return dict {answer, sources, grounded}."""
    from flask import current_app

    question = (question or "").strip()
    if not question:
        return {"answer": _render_rich_answer(FALLBACK_ANSWER), "sources": [], "grounded": False}

    if _is_greeting(question):
        return {"answer": _render_rich_answer(GREETING_ANSWER), "sources": [], "grounded": False}

    if not history:
        cached = _cache_get(question)
        if cached is not None:
            return cached

    vectorstore = get_vectorstore()
    top_k = current_app.config["RAG_TOP_K"]
    threshold = current_app.config["RAG_SIMILARITY_THRESHOLD"]

    try:
        results = vectorstore.similarity_search_with_relevance_scores(
            _retrieval_query(question, history), k=top_k
        )
    except Exception as exc:
        logger.exception("RAG retrieval gagal untuk pertanyaan: %r", question)
        ai_status.record_quota_hint(exc)
        results = []

    relevant = [(doc, score) for doc, score in results if score >= threshold]

    # Tanpa dokumen yang cocok, LLM tetap dipanggil dengan konteks kosong supaya
    # jawabannya jujur ("informasi belum tersedia", aturan 2) atau menolak sopan
    # pertanyaan di luar topik (aturan 3), bukan jawaban template yang kaku.
    context_text = (
        "\n\n---\n\n".join(doc.page_content for doc, _ in relevant) if relevant else EMPTY_CONTEXT
    )
    # Konten sistem & riwayat dikirim sebagai objek pesan (bukan string template)
    # supaya tanda kurung kurawal di dokumen/percakapan tidak dianggap placeholder.
    base_messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context_text))]
    base_messages += _history_messages(history)
    base_messages.append(HumanMessage(content=question))

    # Urutan percobaan: Hive (DeepSeek) bila dikonfigurasi, lalu model OpenRouter (gratis),
    # lalu Gemini sebagai cadangan. Penyedia yang batas hariannya sudah diketahui dilewati
    # supaya tidak membuang waktu/kuota.
    attempts = []
    if llm_config.hive_configured():
        attempts.append((ai_status.HIVE, llm_config.get_hive_settings()["model"]))
    if current_app.config.get("OPENROUTER_API_KEY"):
        attempts += [(ai_status.OPENROUTER, m) for m in _candidate_models(current_app)]
    gemini_model = current_app.config.get("GEMINI_CHAT_MODEL")
    if gemini_model and current_app.config.get("GEMINI_API_KEY"):
        attempts.append((ai_status.GEMINI, gemini_model))

    answer_text = None
    raw_answer = ""
    # Tetap True hanya jika SEMUA percobaan yang dilakukan gagal karena kuota/rate-limit
    # — dipakai untuk membedakan pesan "kuota harian habis" dari kendala teknis lain.
    only_rate_limited = True
    for provider, model in attempts:
        if ai_status.is_daily_limited(provider):
            continue
        if provider == ai_status.HIVE:
            llm = _get_hive_llm()
            retries, retry_delay = llm_config.RATE_LIMIT_RETRIES, llm_config.RATE_LIMIT_RETRY_DELAY_SECONDS
        else:
            llm = _get_gemini_llm(model) if provider == ai_status.GEMINI else get_llm(model)
            retries, retry_delay = _QUOTA_RETRIES_PER_MODEL, _QUOTA_RETRY_DELAY_SECONDS
        for attempt in range(retries + 1):
            try:
                future = _llm_executor.submit(llm.invoke, base_messages)
                response = future.result(timeout=_LLM_CALL_TIMEOUT_SECONDS)
                raw_answer = _message_text(response).strip()
                if not raw_answer:
                    raise ValueError("respons kosong dari model")
                answer_text = _render_rich_answer(raw_answer)
                ai_status.record_success(provider)
                break
            except FutureTimeoutError:
                only_rate_limited = False
                ai_status.record_error("Jawaban AI melewati batas waktu", provider)
                logger.warning(
                    "RAG generation timeout (>%ss) %s/%s untuk pertanyaan: %r",
                    _LLM_CALL_TIMEOUT_SECONDS, provider, model, question,
                )
                break
            except Exception as exc:
                if isinstance(exc, RateLimitError) or (provider == ai_status.GEMINI and _is_quota_error(exc)):
                    ai_status.record_rate_limit(exc, provider)
                    if ai_status.is_daily_limited(provider):
                        # Batas harian: percobaan ulang & model lain di penyedia ini pasti gagal juga.
                        break
                    if attempt < retries:
                        logger.warning(
                            "%s/%s rate-limited, coba lagi dalam %ss...",
                            provider, model, retry_delay,
                        )
                        time.sleep(retry_delay)
                        continue
                    logger.warning("%s/%s tetap rate-limited, pindah ke percobaan berikutnya.", provider, model)
                    break
                only_rate_limited = False
                if llm_config.classify_error(exc) == llm_config.INSUFFICIENT_BALANCE:
                    # 405 dari Hive: saldo organisasi habis. Perlu top-up oleh pengelola;
                    # pengguna cukup melihat pesan kendala teknis biasa (tanpa detail billing).
                    ai_status.record_error("Saldo layanan AI habis", provider)
                    logger.error("%s/%s: saldo organisasi Hive tidak cukup (%s). Isi ulang saldo.",
                                 provider, model, llm_config.describe_error(exc))
                    break
                upstream = _upstream_error_summary(exc)
                ai_status.record_error(upstream or "Gangguan pada layanan AI", provider)
                if upstream:
                    # Gangguan di sisi provider (502, layanan down, koneksi putus) itu hal biasa di
                    # model gratis dan sudah ditangani lewat fallback: cukup satu baris log.
                    logger.warning("%s/%s gagal di upstream (%s), pindah ke percobaan berikutnya.", provider, model, upstream)
                else:
                    logger.warning(
                        "RAG generation gagal %s/%s untuk pertanyaan: %r, coba percobaan berikutnya.",
                        provider, model, question, exc_info=True,
                    )
                break
        if answer_text is not None:
            break

    if answer_text is None:
        return _limited_mode_result(relevant, only_rate_limited)

    sources = _build_sources(relevant, raw_answer)

    result = {"answer": answer_text, "sources": sources, "grounded": bool(relevant)}
    if not history:
        _cache_set(question, result)
    return result


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
