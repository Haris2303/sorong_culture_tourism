"""Logika bisnis pagination untuk listing publik & admin."""
import math

PAGE_SIZE = 5

# Pilihan jumlah data per halaman yang bisa dipilih admin lewat dropdown
# ("Semua" direpresentasikan terpisah sebagai per_page=None, lihat parse_per_page).
PER_PAGE_OPTIONS = [5, 10, 15]


def paginate(total: int, page: int, per_page: int | None) -> dict:
    """Hitung metadata pagination (klem nomor halaman ke rentang valid).

    `per_page=None` berarti tampilkan semua data dalam satu halaman.
    """
    if per_page is None:
        return {
            "page": 1,
            "per_page": total,
            "total": total,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "offset": 0,
        }
    total_pages = max(1, math.ceil(total / per_page))
    page = min(max(page, 1), total_pages)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "offset": (page - 1) * per_page,
    }


def parse_per_page(raw, default: int = PAGE_SIZE):
    """Parse nilai `per_page` dari query string listing admin.

    Return tuple `(choice, per_page)`:
    - `choice`: representasi string untuk dipakai lagi di dropdown & link
      pagination ("5"/"10"/"15"/"all").
    - `per_page`: nilai int untuk dipakai kueri (None berarti "all"/semua).
    Nilai yang tidak dikenali (bukan salah satu PER_PAGE_OPTIONS atau "all")
    jatuh balik ke `default`.
    """
    if raw == "all":
        return "all", None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    if value not in PER_PAGE_OPTIONS:
        value = default
    return str(value), value
