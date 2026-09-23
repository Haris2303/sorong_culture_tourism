"""Layer MODELS — semua yang berhubungan dengan data.

Tiap file di sini isinya query SQL ke satu tabel (SELECT/INSERT/UPDATE/DELETE)
DAN aturan bisnis yang menempel ke data itu (mis. "simpan galeri setelah data
utama tersimpan", "hapus berkas gambar saat record-nya dihapus").

Aturan gampang buat nentuin taruh kode di sini atau tidak:
kalau butuh `dbcore.query_*` / `dbcore.execute` -> taruh di sini.
Jangan taruh kode yang berurusan langsung dengan `request` / `render_template`
(itu tugas layer `routes/`).
"""
