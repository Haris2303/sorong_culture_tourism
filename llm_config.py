"""Konfigurasi LLM chatbot: DeepSeek lewat Hive AI (API OpenAI-compatible).

Semua nilai dibaca dari .env, jadi model/provider diganti tanpa menyentuh kode:
  HIVE_API_KEY     rahasia, TIDAK punya default (isi sendiri di .env)
  HIVE_BASE_URL    default https://api-cdn.thehive.ai/api/v3
  HIVE_MODEL_NAME  default deepseek-ai/deepseek-v4.1-flash
  HIVE_TIMEOUT     opsional, detik (default 20)
  HIVE_REASONING_EFFORT  opsional, default "none". DeepSeek v4.1 adalah model reasoning; tanpa ini
                         jawaban sering hanya terisi di reasoning_content dan content kosong. Kosongkan
                         nilainya (HIVE_REASONING_EFFORT=) untuk tidak mengirim parameter ini, mis. saat
                         memakai provider/model lain.

Untuk pindah ke provider OpenAI-compatible lain, ubah ketiga variabel di atas.
"""
import os
from concurrent.futures import TimeoutError as FutureTimeoutError

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

load_dotenv()

DEFAULT_BASE_URL = "https://api-cdn.thehive.ai/api/v3"
DEFAULT_MODEL = "deepseek-ai/deepseek-v4.1-flash"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_REASONING_EFFORT = "none"

# Jawaban chatbot harus konsisten & berpegang pada konteks, bukan kreatif.
TEMPERATURE = 0.2

# 429 (rate limit) dicoba ulang maksimal 2 kali dengan jeda. Batas Hive 5 request/detik,
# jadi jeda singkat sudah cukup untuk pulih.
RATE_LIMIT_RETRIES = 2
RATE_LIMIT_RETRY_DELAY_SECONDS = 2

# Kategori galat dari classify_error().
RATE_LIMIT = "rate_limit"                    # HTTP 429
INSUFFICIENT_BALANCE = "insufficient_balance"  # HTTP 405: saldo organisasi Hive habis
TIMEOUT = "timeout"
OTHER = "other"


class LLMConfigError(RuntimeError):
    """Konfigurasi LLM belum lengkap (mis. HIVE_API_KEY kosong)."""


def get_hive_settings() -> dict:
    """Baca pengaturan dari environment. Nilai kosong di .env memakai default (kecuali API key)."""
    return {
        "api_key": os.getenv("HIVE_API_KEY", "").strip(),
        "base_url": os.getenv("HIVE_BASE_URL", "").strip() or DEFAULT_BASE_URL,
        "model": os.getenv("HIVE_MODEL_NAME", "").strip() or DEFAULT_MODEL,
        "timeout": float(os.getenv("HIVE_TIMEOUT", "").strip() or DEFAULT_TIMEOUT_SECONDS),
        # Beda dengan variabel lain: nilai kosong yang DISENGAJA berarti "jangan kirim".
        "reasoning_effort": os.getenv("HIVE_REASONING_EFFORT", DEFAULT_REASONING_EFFORT).strip(),
    }


def hive_configured() -> bool:
    return bool(get_hive_settings()["api_key"])


def build_hive_llm():
    """Buat ChatOpenAI untuk Hive. Percobaan ulang diatur pemanggil (max_retries=0 di sini)."""
    from langchain_openai import ChatOpenAI

    settings = get_hive_settings()
    if not settings["api_key"]:
        raise LLMConfigError("HIVE_API_KEY belum diisi di .env")
    return ChatOpenAI(
        model=settings["model"],
        api_key=settings["api_key"],
        base_url=settings["base_url"],
        temperature=TEMPERATURE,
        timeout=settings["timeout"],
        max_retries=0,
        extra_body={"reasoning_effort": settings["reasoning_effort"]} if settings["reasoning_effort"] else None,
    )


def classify_error(exc: Exception) -> str:
    """Petakan galat panggilan LLM ke RATE_LIMIT / INSUFFICIENT_BALANCE / TIMEOUT / OTHER."""
    if isinstance(exc, RateLimitError) or getattr(exc, "status_code", None) == 429:
        return RATE_LIMIT
    if isinstance(exc, APIStatusError) and exc.status_code == 405:
        return INSUFFICIENT_BALANCE
    if isinstance(exc, (APITimeoutError, FutureTimeoutError, TimeoutError)):
        return TIMEOUT
    return OTHER


def describe_error(exc: Exception) -> str:
    """Ringkasan teknis satu baris untuk log server (tidak pernah memuat API key)."""
    if isinstance(exc, APIStatusError):
        return f"HTTP {exc.status_code}: {str(exc.message)[:200]}"
    if isinstance(exc, APIConnectionError):
        return f"koneksi gagal: {type(exc).__name__}"
    return f"{type(exc).__name__}: {str(exc)[:200]}"
