"""CAPTCHA gambar untuk login admin (tanpa layanan eksternal).

Alur:
  1. `issue_image()` membuat teks acak, merendernya jadi gambar PNG terdistorsi, dan menyimpan
     HMAC jawabannya (bukan jawabannya) di session. Session Flask hanya ditandatangani, tidak
     dienkripsi, jadi jawaban polos tidak boleh ditaruh di sana; HMAC dengan SECRET_KEY tidak
     bisa dibalik tanpa kunci.
  2. `verify()` dipakai sekali saja: entri dihapus dari session begitu diperiksa (benar atau
     salah), sehingga satu gambar tidak bisa dicoba berkali-kali, dan kedaluwarsa setelah 5 menit.

Teks dirender sebagai piksel (bukan teks SVG/HTML) supaya tidak bisa dibaca langsung dari sumber.
"""
import hashlib
import hmac
import io
import math
import random
import secrets
import time

from flask import current_app
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Tanpa karakter yang mudah tertukar (0/O, 1/I/L).
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LENGTH = 5
TTL_SECONDS = 300
SESSION_KEY = "captcha"
WIDTH, HEIGHT = 290, 70

_FONT_CANDIDATES = ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf")


def _font(size):
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1 (FreeType)
    except TypeError:  # pragma: no cover - Pillow lama
        return ImageFont.load_default()


def _normalize(value):
    return "".join((value or "").split()).upper()


def _digest(answer):
    key = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(key, _normalize(answer).encode("utf-8"), hashlib.sha256).hexdigest()


def _render(text):
    rnd = random.SystemRandom()
    base = Image.new("RGB", (WIDTH, HEIGHT), (238, 245, 252))
    draw = ImageDraw.Draw(base)

    # latar bergradasi tipis + bintik halus
    for y in range(HEIGHT):
        shade = int(232 + 14 * math.sin(y / HEIGHT * math.pi))
        draw.line([(0, y), (WIDTH, y)], fill=(shade - 6, shade, 252))
    for _ in range(260):
        x, y = rnd.randrange(WIDTH), rnd.randrange(HEIGHT)
        c = rnd.randrange(170, 225)
        draw.point((x, y), fill=(c, c + 10, 240))

    # garis pengganggu di belakang huruf
    for _ in range(4):
        draw.line(
            [(rnd.randrange(WIDTH), rnd.randrange(HEIGHT)), (rnd.randrange(WIDTH), rnd.randrange(HEIGHT))],
            fill=(rnd.randrange(120, 200), rnd.randrange(150, 210), rnd.randrange(200, 245)),
            width=rnd.randrange(1, 3),
        )

    # tiap huruf digambar di lapisan sendiri, diputar & digeser acak
    font = _font(rnd.randrange(38, 44))
    step = (WIDTH - 30) / len(text)
    for i, ch in enumerate(text):
        layer = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(
            (32, 32), ch, font=font, anchor="mm",
            fill=(rnd.randrange(10, 70), rnd.randrange(40, 100), rnd.randrange(90, 150), 255),
        )
        layer = layer.rotate(rnd.uniform(-26, 26), resample=Image.BICUBIC, expand=False)
        x = int(15 + i * step - 6 + rnd.randrange(-3, 4))
        y = int((HEIGHT - 64) / 2 + rnd.randrange(-6, 7))
        base.paste(layer, (x, y), layer)

    # distorsi gelombang pada seluruh gambar
    amp, period, phase = rnd.uniform(2.0, 3.6), rnd.uniform(38, 60), rnd.uniform(0, math.tau)
    warped = Image.new("RGB", (WIDTH, HEIGHT), (238, 245, 252))
    for x in range(WIDTH):
        shift = int(amp * math.sin(x / period * math.tau + phase))
        warped.paste(base.crop((x, 0, x + 1, HEIGHT)), (x, shift))
    draw = ImageDraw.Draw(warped)

    # garis & bintik di depan huruf
    for _ in range(3):
        pts = [(0, rnd.randrange(HEIGHT))]
        for x in range(20, WIDTH + 20, 20):
            pts.append((x, rnd.randrange(HEIGHT)))
        draw.line(pts, fill=(rnd.randrange(30, 110), rnd.randrange(80, 150), rnd.randrange(130, 200)), width=1)
    for _ in range(70):
        x, y = rnd.randrange(WIDTH), rnd.randrange(HEIGHT)
        draw.ellipse((x, y, x + 1, y + 1), fill=(rnd.randrange(40, 120), rnd.randrange(80, 150), 190))

    return warped.filter(ImageFilter.SMOOTH)


def issue_image(session):
    """Buat CAPTCHA baru, simpan HMAC jawabannya di session, kembalikan PNG (bytes)."""
    text = "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))
    session[SESSION_KEY] = {"h": _digest(text), "t": int(time.time())}
    buf = io.BytesIO()
    _render(text).save(buf, format="PNG")
    return buf.getvalue()


def verify(session, submitted):
    """Periksa jawaban. Sekali pakai: entri selalu dihapus, apa pun hasilnya."""
    entry = session.pop(SESSION_KEY, None)
    if not entry or not submitted:
        return False
    if int(time.time()) - int(entry.get("t", 0)) > TTL_SECONDS:
        return False
    return hmac.compare_digest(entry.get("h", ""), _digest(submitted))
