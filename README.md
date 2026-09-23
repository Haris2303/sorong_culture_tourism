# Sistem Informasi & Chatbot Budaya-Wisata Sorong Raya

Boilerplate Flask + MySQL (XAMPP) + ChromaDB + LangChain (Gemini) sesuai PRD skripsi.

## Arsitektur Proyek

Kode ditata berlapis (router → service → model) supaya tiap bagian punya tanggung
jawab yang jelas dan mudah dikembangkan/di-test terpisah:

```
app.py                 # Entry point: setup Flask, ekstensi, & registrasi router
extensions.py           # Instance ekstensi bersama (Flask-Limiter)
config.py               # Konfigurasi aplikasi (baca dari .env)

core/                   # Infrastruktur & utilitas lintas layer
  db.py                    # Koneksi & helper query MySQL (PyMySQL)
  auth.py                   # Guard @admin_required (session-based)
  security.py                # Fingerprint anti-spam & filter kata kasar
  content.py                   # Sanitasi HTML dari editor WYSIWYG
  template_helpers.py            # Context processor & filter Jinja global
  rag_engine.py                    # Engine chatbot RAG (retrieval + LLM)
  sync_engine.py                     # Pipeline sinkronisasi vector DB (ChromaDB)

models/                 # Data access layer — satu modul per entitas, isinya query SQL
  budaya.py, wisata.py, ratings.py, admins.py, knowledge.py

services/               # Business logic — validasi, upload, pagination, orkestrasi CRUD
  pagination.py, uploads.py, coordinates.py, validators.py,
  ratings_stats.py, budaya_service.py, wisata_service.py

routes/                 # Router — terima request, panggil service/model, kirim response
  public.py                # Halaman publik: beranda, budaya, wisata, search
  api.py                     # API chatbot RAG & pengiriman rating
  admin_auth.py                # Login/logout admin
  admin_dashboard.py             # Dashboard ringkasan
  admin_budaya.py                  # CRUD artikel budaya
  admin_wisata.py                    # CRUD destinasi wisata
  admin_ratings.py                     # Moderasi ulasan/rating
  admin_knowledge.py                     # Kelola dokumen & sinkronisasi RAG
  errors.py                                # Error handler (404, 429)

templates/              # View — template Jinja2 (public/ & admin/)
static/                 # Aset statis (CSS, JS, gambar, hasil upload)
```

Alur satu request:

1. **Router** (`routes/`) menerima request, ambil input dari `request`, panggil
   fungsi di `services/` dan/atau `models/`, lalu `render_template(...)` atau
   `jsonify(...)`. Router tidak berisi query SQL maupun logika bisnis.
2. **Service** (`services/`) berisi logika bisnis murni: validasi koordinat/email,
   simpan file upload, hitung pagination, orkestrasi simpan form budaya/wisata
   (termasuk galerinya). Tidak bergantung pada objek `request`/`response` Flask.
3. **Model** (`models/`) hanya berisi query SQL mentah ke MySQL lewat `core/db.py`,
   satu modul per tabel/entitas (`budaya`, `wisata`, `ratings`, `admins`,
   `knowledge_docs`). Tidak ada logika bisnis di sini.
4. **View** (`templates/`) murni presentasi — menerima data yang sudah siap pakai
   dari router, tanpa mengakses database.

Seluruh nama rute, method HTTP, dan `url_for()` di template tetap sama seperti
sebelumnya — pemisahan ini murni penataan ulang struktur kode, tanpa mengubah
perilaku aplikasi.

## 1. Setup Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # lalu isi GEMINI_API_KEY dan kredensial DB
```

## 2. Setup Database (XAMPP)

1. Jalankan **Apache** dan **MySQL** dari XAMPP Control Panel.
2. Buka phpMyAdmin (`http://localhost/phpmyadmin`), lalu import `schema.sql`
   (atau jalankan via CLI: `mysql -u root -p < schema.sql`).
3. Sesuaikan `.env` dengan kredensial MySQL Anda (default XAMPP: user `root`, password kosong).

## 3. Isi API Key Gemini

Dapatkan API key di [Google AI Studio](https://aistudio.google.com/app/apikey), lalu isi
`GEMINI_API_KEY` di `.env`.

## 4. Jalankan Aplikasi

```bash
python app.py
```

Buka `http://localhost:5000`.

## 5. Login Admin

- URL: `http://localhost:5000/admin/login`
- Username: `admin`
- Password: `admin123`

**Segera ganti password ini setelah login pertama** (via query manual ke tabel `admins`
menggunakan `werkzeug.security.generate_password_hash`, karena boilerplate belum
menyertakan fitur ganti password di UI).

## 6. Melatih Chatbot RAG

1. Masuk ke **Dashboard Admin > Knowledge Base**.
2. Unggah dokumen PDF/TXT/MD terkait budaya Suku Moi & wisata Sorong Raya.
3. Klik **"Sinkronkan & Latih Ulang Vector DB"** — sistem akan meng-chunk dokumen +
   artikel budaya/wisata di MySQL, menghitung embedding, dan menyimpannya ke ChromaDB
   lokal (`./data_store/chroma_db/`).
4. Chatbot di landing page siap menjawab berdasarkan basis pengetahuan tersebut.

## Catatan Produksi

- Ganti `SECRET_KEY` di `.env` dengan nilai acak yang kuat.
- CAPTCHA (reCAPTCHA v3 / Turnstile) pada FR-06 Layer 4 belum diimplementasikan di
  boilerplate ini — tambahkan verifikasi token di endpoint `POST /api/rating` sesuai
  provider yang dipilih.
- Untuk beban tinggi, ganti `RATELIMIT_STORAGE_URI` dari `memory://` ke Redis.
