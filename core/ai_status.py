"""Status kuota asisten AI (indikator hijau / kuning / merah di chatbot).

Penyedia jawaban: "hive" (utama bila HIVE_API_KEY diisi), "openrouter" (model gratis) dan "gemini" (cadangan). Status dihitung
dari gabungan keduanya:

  hijau  (ok)       semua normal
  kuning (warn)     ada yang terbatas tapi bot masih menjawab: batas per-menit/provider sibuk,
                    gangguan sesaat, kredit menipis, atau model utama habis harian dan
                    jawaban dialihkan ke model cadangan
  merah  (limited)  SEMUA penyedia habis batas harian / tidak valid. Bot masih menampilkan halaman
                    rujukan dari pencarian pengetahuan (tanpa LLM), jadi input tidak dimatikan.

Sumber sinyal:
  1. REAKTIF (paling andal): hasil panggilan LLM yang sebenarnya. Balasan 429 OpenRouter memuat
     pesan & header batas (mis. "free-models-per-day", X-RateLimit-Reset) sehingga diketahui batas
     per-menit atau harian dan kapan pulih. Untuk Gemini, pesan kuota dibaca dari teks galatnya.
  2. PROAKTIF: GET https://openrouter.ai/api/v1/key dicek berkala di latar belakang untuk mendeteksi
     key tidak valid atau kredit habis/menipis. Endpoint ini melaporkan kredit, BUKAN jumlah
     permintaan model gratis per hari, jadi batas harian baru terdeteksi lewat sinyal reaktif.

Status disimpan di memori proses. Pada deployment multi-worker tiap proses punya status sendiri
(cukup untuk indikator; bukan penghitung kuota resmi).
"""
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

HIVE = "hive"
OPENROUTER = "openrouter"
GEMINI = "gemini"
PROVIDERS = (HIVE, OPENROUTER, GEMINI)

WARN_AFTER_ERROR_SECONDS = 300      # gangguan non-kuota dianggap "kuning" selama 5 menit
DEFAULT_MINUTE_BLOCK_SECONDS = 60   # batas per-menit: kuning selama ~1 menit
PROBE_INTERVAL_SECONDS = 300        # cek info key ke OpenRouter tiap 5 menit
PROBE_TIMEOUT_SECONDS = 4
LOW_CREDIT_RATIO = 0.15             # sisa kredit < 15% dianggap menipis

_lock = threading.Lock()


def _blank():
    return {"daily_until": 0.0, "minute_until": 0.0, "error_until": 0.0, "last_ok": 0.0, "last_event": ""}


_state = {HIVE: _blank(), OPENROUTER: _blank(), GEMINI: _blank(), "probe": None, "probe_at": 0.0, "probing": False}


def _now():
    return time.time()


def _next_utc_midnight(now):
    """OpenRouter mereset batas harian pada 00:00 UTC."""
    return (int(now // 86400) + 1) * 86400.0


def _next_pacific_midnight(now):
    """Kuota harian Gemini API direset tengah malam waktu Pasifik."""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
        local = datetime.fromtimestamp(now, tz)
        nxt = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return nxt.timestamp()
    except Exception:  # tzdata tidak ada: anggap ~8 jam (perkiraan aman)
        return now + 8 * 3600


# ---------------------------------------------------------------- pencatatan kejadian
def _parse_rate_limit(exc):
    """(is_daily, reset_epoch|None, message) dari galat 429 OpenRouter (openai) atau Gemini."""
    body = getattr(exc, "body", None)
    err = body.get("error", body) if isinstance(body, dict) else {}
    if not isinstance(err, dict):
        err = {}
    message = str(err.get("message") or getattr(exc, "message", "") or exc)
    meta = err.get("metadata") or {}
    headers = dict(meta.get("headers") or {})

    response = getattr(exc, "response", None)
    resp_headers = getattr(response, "headers", None)
    if resp_headers:
        for key in ("x-ratelimit-reset", "x-ratelimit-remaining"):
            if key in resp_headers and key.title() not in headers:
                headers[key] = resp_headers[key]
    lowered = {str(k).lower(): v for k, v in headers.items()}

    reset_epoch = None
    raw_reset = lowered.get("x-ratelimit-reset")
    if raw_reset:
        try:
            value = float(raw_reset)
            reset_epoch = value / 1000.0 if value > 1e11 else value  # ms atau detik
        except (TypeError, ValueError):
            reset_epoch = None

    # Gemini: "...GenerateRequestsPerDayPerProjectPerModel-FreeTier..." / "retry_delay { seconds: 34 }"
    squashed = re.sub(r"[\s_\-]+", "", message.lower())
    is_daily = any(k in squashed for k in ("perday", "daily", "freemodelsperday"))
    if reset_epoch is None:
        m = re.search(r"retry(?:_delay|\s*in)?\D{0,20}?(\d+(?:\.\d+)?)\s*s", message.lower())
        if m:
            reset_epoch = _now() + float(m.group(1)) + 1
    return is_daily, reset_epoch, message


def record_rate_limit(exc, provider=OPENROUTER):
    """Dipanggil tiap kali penyedia membalas 429 / kuota habis."""
    is_daily, reset_epoch, message = _parse_rate_limit(exc)
    now = _now()
    with _lock:
        st = _state[provider]
        if is_daily:
            default_reset = _next_pacific_midnight(now) if provider == GEMINI else _next_utc_midnight(now)
            until = reset_epoch if reset_epoch and reset_epoch > now + 900 else default_reset
            st["daily_until"] = max(st["daily_until"], until)
            st["last_event"] = "Batas harian tercapai"
        else:
            until = reset_epoch if reset_epoch and now < reset_epoch < now + 900 else now + DEFAULT_MINUTE_BLOCK_SECONDS
            st["minute_until"] = max(st["minute_until"], until)
            st["last_event"] = "Terkena batas per menit / provider sibuk"
    logger.info("Status AI [%s]: rate limit tercatat (%s) daily=%s", provider, message[:120], is_daily)


def record_error(summary="", provider=OPENROUTER):
    """Gangguan non-kuota (timeout, 5xx, koneksi putus)."""
    with _lock:
        st = _state[provider]
        st["error_until"] = _now() + WARN_AFTER_ERROR_SECONDS
        st["last_event"] = summary or "Gangguan pada layanan AI"


def record_quota_hint(exc):
    """Kegagalan retrieval/embedding: hanya menandai kuning bila pesannya menyiratkan kuota."""
    text = str(exc).lower()
    if "429" in text or "quota" in text or "resource_exhausted" in text or "rate" in text:
        with _lock:
            st = _state[GEMINI]
            st["minute_until"] = max(st["minute_until"], _now() + DEFAULT_MINUTE_BLOCK_SECONDS)
            st["last_event"] = "Kuota embedding terbatas"


def record_success(provider=OPENROUTER):
    with _lock:
        st = _state[provider]
        st["last_ok"] = _now()
        # Gangguan sementara sudah lewat; batas harian tetap dipertahankan sampai waktu resetnya.
        st["error_until"] = 0.0


def is_daily_limited(provider=OPENROUTER):
    with _lock:
        return _state[provider]["daily_until"] > _now()


# ---------------------------------------------------------------- pengecekan key (proaktif)
def _probe(api_key, base_url):
    """Ambil info key dari OpenRouter. Hasil: dict ringkas; tidak pernah melempar."""
    result = {"checked": _now(), "invalid": False, "remaining": None, "limit": None, "error": ""}
    if not api_key:
        result["invalid"] = True
        result["error"] = "API key belum dikonfigurasi"
        return result
    req = urllib.request.Request(
        base_url.rstrip("/") + "/key",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT_SECONDS) as resp:
            data = (json.loads(resp.read().decode("utf-8")) or {}).get("data") or {}
        limit = data.get("limit")
        remaining = data.get("limit_remaining")
        result["limit"] = float(limit) if limit is not None else None
        result["remaining"] = float(remaining) if remaining is not None else None
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            result["invalid"] = True
            result["error"] = "API key tidak valid"
        else:
            result["error"] = f"HTTP {exc.code}"
    except Exception as exc:  # jaringan putus / timeout: jangan jadikan merah
        result["error"] = type(exc).__name__
    return result


def _refresh_probe_async(api_key, base_url):
    def worker():
        res = _probe(api_key, base_url)
        with _lock:
            _state["probe"] = res
            _state["probe_at"] = _now()
            _state["probing"] = False

    with _lock:
        if _state["probing"] or _now() - _state["probe_at"] < PROBE_INTERVAL_SECONDS:
            return
        _state["probing"] = True
    threading.Thread(target=worker, daemon=True).start()


# ---------------------------------------------------------------- ringkasan untuk klien
def snapshot(api_key="", base_url="https://openrouter.ai/api/v1", gemini_key="", hive_key=""):
    """{level, message, detail, reset_at, mode, blocked}.

    mode: "normal" | "fallback" (memakai model cadangan) | "retrieval" (tanpa LLM, hanya rujukan)
    blocked: True hanya bila tidak ada penyedia sama sekali (input dimatikan).
    """
    if api_key:
        _refresh_probe_async(api_key, base_url)
    now = _now()
    with _lock:
        s = {p: dict(_state[p]) for p in PROVIDERS}
        probe = _state["probe"]

    configured = []
    if hive_key:
        configured.append(HIVE)
    if api_key:
        configured.append(OPENROUTER)
    if gemini_key:
        configured.append(GEMINI)
    if not configured:
        return {"level": "limited", "message": "Asisten AI belum dikonfigurasi",
                "detail": "API key belum diatur oleh pengelola.", "reset_at": None,
                "mode": "retrieval", "blocked": True}

    def unavailable(p):
        if s[p]["daily_until"] > now:
            return True
        if p == OPENROUTER and probe and probe["invalid"]:
            return True
        if p == OPENROUTER and probe and probe["remaining"] is not None and probe["remaining"] <= 0:
            return True
        return False

    usable = [p for p in configured if not unavailable(p)]
    daily_resets = [s[p]["daily_until"] for p in configured if s[p]["daily_until"] > now]
    reset_at = min(daily_resets) if daily_resets else None

    # --- MERAH: tidak ada penyedia yang bisa menjawab ---
    if not usable:
        if daily_resets:
            return {"level": "limited", "message": "Batas harian asisten AI tercapai",
                    "detail": "Asisten belum bisa menyusun jawaban, tetapi tetap menampilkan halaman "
                              "rujukan yang paling relevan dengan pertanyaan Anda.",
                    "reset_at": reset_at, "mode": "retrieval", "blocked": False}
        return {"level": "limited", "message": "Asisten AI tidak tersedia",
                "detail": (probe or {}).get("error") or "API key tidak valid atau kredit habis.",
                "reset_at": None, "mode": "retrieval", "blocked": False}

    # --- KUNING ---
    if any(unavailable(p) for p in configured):
        return {"level": "warn", "message": "Model cadangan sedang dipakai",
                "detail": "Model utama mencapai batas; jawaban dialihkan ke model cadangan dan "
                          "mungkin sedikit berbeda gayanya.",
                "reset_at": reset_at, "mode": "fallback", "blocked": False}
    soonest_minute = max((s[p]["minute_until"] for p in usable), default=0)
    if soonest_minute > now:
        return {"level": "warn", "message": "Asisten sedang padat",
                "detail": "Permintaan dibatasi sementara; jawaban mungkin lebih lambat atau gagal.",
                "reset_at": soonest_minute, "mode": "normal", "blocked": False}
    err = [p for p in usable if s[p]["error_until"] > now]
    if err:
        return {"level": "warn", "message": "Layanan AI sedang terganggu",
                "detail": s[err[0]]["last_event"] or "Beberapa jawaban mungkin gagal.",
                "reset_at": None, "mode": "normal", "blocked": False}
    if probe and probe["limit"] and probe["remaining"] is not None \
            and probe["remaining"] / probe["limit"] < LOW_CREDIT_RATIO:
        return {"level": "warn", "message": "Kuota asisten AI menipis",
                "detail": "Sisa kredit API key tinggal sedikit.", "reset_at": None,
                "mode": "normal", "blocked": False}

    return {"level": "ok", "message": "Online", "detail": "Siap membantu Anda.", "reset_at": None,
            "mode": "normal", "blocked": False}


def reset_for_tests():
    with _lock:
        for p in PROVIDERS:
            _state[p] = _blank()
        _state.update(probe=None, probe_at=_now(), probing=False)


def to_iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat() if epoch else None
