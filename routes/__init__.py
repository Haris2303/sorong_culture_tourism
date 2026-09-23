"""Layer ROUTES — pintu masuk semua request dari browser/JS, & registrasinya ke Flask.

Tugas tiap file di sini cuma 3 langkah: (1) ambil input dari `request`,
(2) panggil fungsi di `models/` (kadang dibantu `utils/`), (3) kirim balik
response lewat `render_template(...)` atau `jsonify(...)`.

Jangan tulis query SQL atau logika bisnis panjang langsung di sini — itu
tugas `models/`. Kalau rute butuh login admin, selalu pasang dekorator
`@admin_required` dari `core.auth` di baris paling atas fungsinya.
"""
from routes import (
    admin_auth,
    admin_budaya,
    admin_dashboard,
    admin_knowledge,
    admin_ratings,
    admin_wisata,
    api,
    errors,
    public,
)


def register_routes(app):
    public.register(app)
    api.register(app)
    admin_auth.register(app)
    admin_dashboard.register(app)
    admin_budaya.register(app)
    admin_wisata.register(app)
    admin_ratings.register(app)
    admin_knowledge.register(app)
    errors.register(app)
