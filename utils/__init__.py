"""Layer UTILS — fungsi bantu kecil yang generik, bisa dipakai di mana saja.

Bedanya dengan `models/`: fungsi di sini TIDAK menyentuh database dan TIDAK
tahu apa itu "budaya" atau "wisata" secara spesifik — semuanya reusable.
Contoh: hitung pagination, simpan file upload, validasi format email/koordinat.

Aturan gampang buat nentuin taruh kode di sini atau di `models/`:
"apakah fungsi ini menyentuh database (query SQL)?"
Kalau ya -> `models/`. Kalau tidak -> `utils/`.
"""
