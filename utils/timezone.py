"""Zona waktu tampilan aplikasi: WIT (Waktu Indonesia Timur, Asia/Jayapura, UTC+9)."""
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    WIT = ZoneInfo("Asia/Jayapura")
except Exception:  # tzdata tidak tersedia (mis. Windows tanpa paket tzdata)
    WIT = timezone(timedelta(hours=9), "WIT")


def now_wit() -> datetime:
    return datetime.now(WIT)


def to_wit(value: datetime | None) -> datetime | None:
    """Ubah datetime ke WIT. Datetime naive dianggap UTC (format penanda sinkronisasi)."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(WIT)


def format_wit(value: datetime | None, fmt: str = "%d %b %Y %H:%M", empty: str = "-") -> str:
    converted = to_wit(value)
    return f"{converted.strftime(fmt)} WIT" if converted else empty
