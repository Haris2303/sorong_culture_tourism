"""Statistik pertumbuhan konten (jumlah data baru per bulan) untuk kartu KPI dashboard."""
from datetime import date, datetime, timedelta

from core import db as dbcore

# Nama tabel tidak boleh datang dari input pengguna; dibatasi whitelist ini.
_TABLES = {"budaya", "wisata", "ratings"}

_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _month_starts(months: int) -> list[date]:
    """Tanggal 1 tiap bulan, dari `months - 1` bulan lalu sampai bulan ini."""
    today = date.today()
    y, m = today.year, today.month
    starts = []
    for _ in range(months):
        starts.append(date(y, m, 1))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(starts))


def growth(table: str, months: int = 6) -> dict:
    """Jumlah data baru per bulan (untuk sparkline) + jumlah 30 hari terakhir."""
    if table not in _TABLES:
        raise ValueError(f"Tabel tidak diizinkan: {table}")

    starts = _month_starts(months)
    rows = dbcore.query_all(
        f"SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS ym, COUNT(*) AS c FROM {table} "
        "WHERE created_at >= %s GROUP BY ym",
        (starts[0],),
    )
    by_month = {r["ym"]: r["c"] for r in rows}
    monthly = [
        {"label": _BULAN[d.month - 1], "count": by_month.get(d.strftime("%Y-%m"), 0)}
        for d in starts
    ]

    since = datetime.now() - timedelta(days=30)
    last30 = dbcore.query_one(
        f"SELECT COUNT(*) AS c FROM {table} WHERE created_at >= %s", (since,)
    )["c"]

    peak = max((m["count"] for m in monthly), default=0)
    for m in monthly:
        # Tinggi batang minimum 8% supaya bulan kosong tetap terlihat sebagai dasar grafik.
        m["pct"] = max(8, round(m["count"] * 100 / peak)) if peak else 8
    return {"monthly": monthly, "last30": last30}
