import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Flask core ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DEBUG = _bool(os.getenv("FLASK_DEBUG"), True)

    # --- Session ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
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

    # --- OpenRouter (chat/generation chatbot) ---
    # Model gratis OpenRouter kadang penuh/di-deprecate tanpa peringatan, jadi dipakai
    # daftar fallback: dicoba berurutan sampai salah satu berhasil menjawab.
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_CHAT_MODEL = os.getenv("OPENROUTER_CHAT_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
    OPENROUTER_CHAT_MODEL_FALLBACKS = [
        m.strip() for m in os.getenv(
            "OPENROUTER_CHAT_MODEL_FALLBACKS",
            "nvidia/nemotron-3-super-120b-a12b:free,google/gemma-4-31b-it:free,z-ai/glm-5.2:free,"
            "google/gemma-4-26b-a4b-it:free,qwen/qwen3.8-27b:free,"
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free,inclusionai/ling-3.0-flash-vl:free",
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
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 5)) * 1024 * 1024
    ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
    ALLOWED_DOC_EXT = {"pdf", "txt", "md"}

    # --- Rate Limiter ---
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
