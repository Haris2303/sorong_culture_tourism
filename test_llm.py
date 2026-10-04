"""Uji cepat LLM (Hive/DeepSeek) lewat chain RAG: kirim satu pertanyaan, cetak jawaban & sumber.

Jalankan dari root proyek:  python test_llm.py ["pertanyaan opsional"]
Butuh HIVE_API_KEY di .env dan MySQL/ChromaDB lokal (sama seperti saat aplikasi berjalan).
"""
import re
import sys

import llm_config

DEFAULT_QUESTION = "Apa saja wisata yang ada di Raja Ampat Sorong dan berapa harga tiketnya?"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # emoji pada jawaban gagal dicetak di konsol Windows (cp1252)
    if not llm_config.hive_configured():
        print("HIVE_API_KEY belum diisi di .env. Isi dulu, lalu jalankan ulang skrip ini.")
        return 1

    settings = llm_config.get_hive_settings()
    print(f"Model   : {settings['model']}")
    print(f"Base URL: {settings['base_url']}")

    from app import app
    from core.rag_engine import answer_query

    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION
    print(f"\nPertanyaan: {question}\n")
    with app.test_request_context():
        result = answer_query(question)

    answer = re.sub(r"<[^>]+>", " ", result["answer"].replace("</p>", "\n").replace("</li>", "\n"))
    print("Jawaban:\n" + re.sub(r"[ \t]+", " ", answer).strip())
    print(f"\nGrounded: {result.get('grounded')}  Mode: {result.get('mode', 'normal')}")
    print("Sumber:")
    for src in result["sources"] or []:
        print(f"  - {src['title']} -> {src.get('url') or '(dokumen)'}")
    if not result["sources"]:
        print("  (tidak ada)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
