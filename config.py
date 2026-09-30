import os
from dotenv import load_dotenv

load_dotenv()

# Matikan telemetri anonim ChromaDB (statistik pemakaian dikirim ke server Chroma);
# tidak dibutuhkan aplikasi. Harus diset sebelum klien Chroma pertama dibuat.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


# Set FLASK_ENV=production di server produksi. Ini memaksa DEBUG mati (apa pun nilai
# FLASK_DEBUG) dan mengaktifkan cookie session HTTPS-only, terlepas dari lupa/tidaknya
# variabel lain diset dengan benar.
FLASK_ENV = os.getenv("FLASK_ENV", "development").strip().lower()
IS_PRODUCTION = FLASK_ENV == "production"

# Nilai contekan dari kode & dari .env.example -- kalau salah satu ini yang kepakai
# di production berarti SECRET_KEY belum benar-benar diganti.
DEFAULT_SECRET_KEY = "dev-secret-key-change-me"
INSECURE_SECRET_KEYS = {DEFAULT_SECRET_KEY, "ganti-dengan-random-secret-key-yang-panjang"}


class Config:
    # --- Flask core ---
    ENV = FLASK_ENV
    IS_PRODUCTION = IS_PRODUCTION
    SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
    DEBUG = False if IS_PRODUCTION else _bool(os.getenv("FLASK_DEBUG"), True)

    # --- Session ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Default ikut mode produksi, tapi tetap bisa dipaksa manual lewat env (mis. server
    # produksi yang belum pasang HTTPS).
    SESSION_COOKIE_SECURE = _bool(os.getenv("SESSION_COOKIE_SECURE"), IS_PRODUCTION)
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 4  # 4 jam

    # --- MySQL ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "sorong_culture_tourism")

    # --- Gemini (embedding RAG) ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
    # Model cadangan untuk MENYUSUN JAWABAN saat OpenRouter kena batas (memakai GEMINI_API_KEY yang
    # sama). Nama model Gemini berganti cepat; bila 404 "no longer available", ganti lewat .env
    # (daftar model: genai.list_models()). Kosongkan untuk menonaktifkan cadangan ini.
    GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite")

    # --- OpenRouter (chat/generation chatbot) ---
    # Model gratis OpenRouter kadang penuh/di-deprecate tanpa peringatan, jadi dipakai
    # daftar fallback: dicoba berurutan sampai salah satu berhasil menjawab.
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_CHAT_MODEL = os.getenv("OPENROUTER_CHAT_MODEL", "inclusionai/ling-3.0-flash-sante:free")
    OPENROUTER_CHAT_MODEL_FALLBACKS = [
        m.strip() for m in os.getenv(
            "OPENROUTER_CHAT_MODEL_FALLBACKS",
            "nvidia/nemotron-3-super-120b-a12b:free,google/gemma-4-31b-it:free,"
            "qwen/qwen3.8-27b:free,openrouter/free",
        ).split(",") if m.strip()
    ]
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # --- ChromaDB / RAG ---
    CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "data_store", "chroma_db")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "sorong_knowledge")
    KNOWLEDGE_DOCS_DIR = os.path.join(BASE_DIR, "data_store", "knowledge_docs")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", 4))
    RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", 0.55))

    # --- Upload ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    # Batas ukuran request dinaikkan dari 5MB -> 15MB sebagai jaring pengaman server;
    # gambar tetap dikompres otomatis di browser (lihat static/js/image-optimizer.js)
    # sebelum diunggah, jadi request normal jauh di bawah batas ini.
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 15)) * 1024 * 1024
    ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
    ALLOWED_DOC_EXT = {"pdf", "txt", "md"}
    # Semua gambar unggahan otomatis di-resize & dikonversi ke WebP di server
    # (lihat utils/uploads.py) supaya konsisten ringan walau JS di browser dilewati.
    IMAGE_MAX_DIMENSION = int(os.getenv("IMAGE_MAX_DIMENSION", 1920))
    IMAGE_WEBP_QUALITY = int(os.getenv("IMAGE_WEBP_QUALITY", 82))
    MAX_GALERI_FILES = int(os.getenv("MAX_GALERI_FILES", 12))

    # --- Rate Limiter ---
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
