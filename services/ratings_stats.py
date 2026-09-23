"""Logika bisnis statistik rating/ulasan wisata."""
from models import ratings as ratings_model


def trimmed_average(scores: list[int]) -> float:
    """Rata-rata dengan pemotongan nilai ekstrem (trimmed mean) agar tahan outlier."""
    if not scores:
        return 0.0
    if len(scores) < 5:
        return round(sum(scores) / len(scores), 1)
    ordered = sorted(scores)
    trim_count = max(1, len(ordered) // 10)
    trimmed = ordered[trim_count:-trim_count] or ordered
    return round(sum(trimmed) / len(trimmed), 1)


def get_wisata_rating_summary(wisata_id: int) -> dict:
    scores = ratings_model.scores_approved_by_wisata(wisata_id)
    return {"average": trimmed_average(scores), "count": len(scores)}
