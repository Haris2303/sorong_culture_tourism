"""Logika bisnis pagination untuk listing publik & admin."""
import math

PAGE_SIZE = 5


def paginate(total: int, page: int, per_page: int) -> dict:
    """Hitung metadata pagination (klem nomor halaman ke rentang valid)."""
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
