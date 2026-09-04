"""Fungsi keamanan: fingerprint hash IP+User-Agent dan filter kata kasar sederhana."""
import hashlib
import re

# Daftar kata kasar/sara sederhana (Bahasa Indonesia). Silakan diperluas sesuai kebutuhan.
BADWORDS = {
    "anjing", "bangsat", "bajingan", "kontol", "memek", "goblok", "tolol",
    "brengsek", "bego", "idiot", "keparat", "sialan", "monyet", "babi",
    "kampret", "tai", "asu", "jancok", "pukimak",
}

_word_re = re.compile(r"[a-zA-Z0-9']+")


def generate_fingerprint(ip_address: str, user_agent: str) -> str:
    """SHA256(IP_Address + User_Agent) -> hex digest 64 karakter."""
    raw = f"{ip_address}|{user_agent}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def get_client_ip(request) -> str:
    """Ambil IP klien, memperhitungkan header X-Forwarded-For jika di belakang proxy."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"


def contains_badword(text: str) -> bool:
    """True jika teks komentar mengandung salah satu kata pada daftar badword."""
    if not text:
        return False
    words = {w.lower() for w in _word_re.findall(text)}
    return not words.isdisjoint(BADWORDS)
