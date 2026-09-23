"""Logika bisnis parsing koordinat lokasi wisata (format desimal & DMS)."""
import re

_KOORDINAT_DECIMAL_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$")
_KOORDINAT_DMS_RE = re.compile(
    r"(\d+(?:\.\d+)?)[°:]\s*(\d+(?:\.\d+)?)['’′]\s*(\d+(?:\.\d+)?)[\"”″]?\s*([NSEWnsew])"
)


def parse_koordinat(text: str):
    """Ubah teks koordinat (desimal "-0.859042, 131.247695" atau DMS
    0°44'11.6"S 131°35'01.1"E) menjadi (latitude, longitude) float, atau None jika tidak valid."""
    text = (text or "").strip()
    if not text:
        return None

    decimal_match = _KOORDINAT_DECIMAL_RE.match(text)
    if decimal_match:
        lat, lon = float(decimal_match.group(1)), float(decimal_match.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return round(lat, 6), round(lon, 6)
        return None

    matches = _KOORDINAT_DMS_RE.findall(text)
    if len(matches) != 2:
        return None

    values = {}
    for deg, minute, sec, direction in matches:
        decimal = float(deg) + float(minute) / 60 + float(sec) / 3600
        direction = direction.upper()
        if direction in ("S", "W"):
            decimal = -decimal
        values["lat" if direction in ("N", "S") else "lon"] = decimal

    if "lat" not in values or "lon" not in values:
        return None
    lat, lon = values["lat"], values["lon"]
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return round(lat, 6), round(lon, 6)
    return None
