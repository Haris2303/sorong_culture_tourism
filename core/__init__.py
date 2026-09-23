"""Layer CORE — infrastruktur inti aplikasi, jarang perlu disentuh saat nambah fitur.

Isinya: koneksi database (`db.py`), penjaga login admin (`auth.py`), fungsi
keamanan (`security.py`), pembersih HTML (`content.py`), helper Jinja
(`template_helpers.py`), dan engine chatbot RAG (`rag_engine.py`,
`sync_engine.py`). Kalau kamu cuma menambah fitur CRUD biasa, kemungkinan
besar kamu tidak perlu mengubah apa pun di folder ini.
"""
