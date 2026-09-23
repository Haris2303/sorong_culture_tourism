# Sistem Informasi & Chatbot Budaya-Wisata Sorong Raya

Boilerplate Flask + MySQL (XAMPP) + ChromaDB + LangChain (Gemini) sesuai PRD skripsi.

## Arsitektur Proyek (versi gampang dipahami)

Cukup ingat **3 folder utama** — itu yang paling sering kamu sentuh saat nambah fitur:

```
routes/   ->  terima request dari browser, panggil models/, balikin response
models/   ->  semua urusan data: query SQL + aturan simpan/hapusnya
utils/    ->  fungsi bantu kecil & generik (pagination, upload file, validasi)
```

Kalau dianalogikan seperti restoran:

- **`routes/`** = pelayan. Terima pesanan (request) dari pelanggan (browser/JS),
  teruskan ke dapur, lalu antar hasilnya balik. Pelayan tidak masak sendiri.
- **`models/`** = dapur. Di sinilah data benar-benar diolah & disimpan ke
  "gudang" (database MySQL).
- **`utils/`** = alat dapur generik (timbangan, kalkulator) — dipakai di banyak
  resep tapi tidak spesifik ke satu menu (mis. hitung pagination, simpan file).
- **`templates/`** = piring saji — cara data ditampilkan ke pelanggan (HTML).

Selain 3 folder itu, ada `core/` untuk infrastruktur inti (koneksi database,
penjaga login admin, engine chatbot) yang **jarang perlu disentuh** kecuali
kamu memang sedang mengubah bagian inti aplikasi.

```
app.py                 # Entry point: setup Flask, ekstensi, & registrasi router
extensions.py           # Instance ekstensi bersama (Flask-Limiter)
config.py               # Konfigurasi aplikasi (baca dari .env)

routes/                 # 1) TERIMA REQUEST — satu file per halaman/fitur
  public.py                # Halaman publik: beranda, budaya, wisata, search
  api.py                     # API chatbot RAG & pengiriman rating
  admin_auth.py                # Login/logout admin
  admin_dashboard.py             # Dashboard ringkasan
  admin_budaya.py                  # CRUD artikel budaya
  admin_wisata.py                    # CRUD destinasi wisata
  admin_ratings.py                     # Moderasi ulasan/rating
  admin_knowledge.py                     # Kelola dokumen & sinkronisasi RAG
  errors.py                                # Error handler (404, 429)

models/                 # 2) OLAH DATA — satu file per tabel/entitas
  budaya.py, wisata.py, ratings.py, admins.py, knowledge.py

utils/                  # 3) HELPER GENERIK — tidak menyentuh database
  pagination.py, uploads.py, coordinates.py, validators.py

core/                   # Infrastruktur inti (jarang disentuh)
  db.py                    # Koneksi & helper query MySQL (PyMySQL)
  auth.py                   # Guard @admin_required (session-based)
  security.py                # Fingerprint anti-spam & filter kata kasar
  content.py                   # Sanitasi HTML dari editor WYSIWYG
  template_helpers.py            # Context processor & filter Jinja global
  rag_engine.py                    # Engine chatbot RAG (retrieval + LLM)
  sync_engine.py                     # Pipeline sinkronisasi vector DB (ChromaDB)

templates/              # Tampilan — template Jinja2 (public/ & admin/)
static/                 # Aset statis (CSS, JS, gambar, hasil upload)
```

### Alur satu request

1. **`routes/`** ambil input dari `request`, panggil satu/dua fungsi di
   `models/` (kadang dibantu `utils/`), lalu `render_template(...)` atau
   `jsonify(...)`. **Jangan** tulis query SQL di sini.
2. **`models/`** eksekusi query ke MySQL lewat `core/db.py`, sekaligus
   menyimpan aturan yang menempel ke data itu (mis. "hapus berkas gambar
   lama saat record dihapus"). **Jangan** taruh kode yang berurusan dengan
   `request`/`render_template` di sini.
3. **`utils/`** cuma dipanggil kalau butuh — isinya fungsi generik yang tidak
   tahu apa itu "budaya"/"wisata" dan tidak menyentuh database sama sekali.
4. **`templates/`** murni presentasi, menerima data yang sudah siap pakai.

### Contoh: nambah fitur baru cukup 2 langkah

Misal mau nambah fitur "filter budaya berdasarkan tahun":

1. Tambah fungsi query baru di `models/budaya.py` (mis. `list_by_tahun(...)`).
2. Panggil fungsi itu dari `routes/public.py`.

Selesai — tidak perlu bikin file baru di layer lain untuk fitur sekecil ini.

Seluruh nama rute, method HTTP, dan `url_for()` di template tetap sama seperti
sebelumnya — penataan ulang ini tidak mengubah perilaku aplikasi.

## Checklist Keamanan untuk Kontributor Baru

Struktur di atas dibuat sesederhana mungkin, tapi celah keamanan **tidak boleh
ikut disederhanakan**. Selalu ikuti aturan berikut saat menambah kode baru:

| Risiko | Aturan | Sudah dijaga di |
| --- | --- | --- |
| **SQL Injection** | Selalu pakai placeholder `%s` + tuple parameter lewat `dbcore.query_*`/`dbcore.execute`. **Jangan pernah** menyambung input user ke string SQL pakai f-string atau `+`. | `core/db.py`, semua `models/*.py` |
| **XSS (stored)** | Field HTML panjang (WYSIWYG) wajib lewat `sanitize_content_html()` sebelum disimpan. | `core/content.py`, dipanggil di `models/budaya.py` & `models/wisata.py` |
| **CSRF** | Semua form POST admin wajib menyertakan `{{ csrf_token() }}` (form biasa) atau header `X-CSRFToken` (fetch/AJAX). Ini sudah aktif otomatis lewat `CSRFProtect` di `app.py` — jangan di-nonaktifkan per-route. | `app.py`, `templates/admin/*.html` |
| **Upload file berbahaya** | Selalu lewat `utils/uploads.py` (validasi ekstensi via allow-list + nama file di-random pakai timestamp). Jangan simpan file pakai nama asli dari user. | `utils/uploads.py` |
| **Akses admin tanpa login** | Setiap rute `/admin/*` wajib pakai dekorator `@admin_required` dari `core/auth.py` di baris paling atas fungsinya. | `routes/admin_*.py` |
| **Penyalahgunaan API publik** | `/api/chat` & `/api/rating` sudah dibatasi lewat `@limiter.limit(...)` (lihat `routes/api.py`) — jangan dihapus saat refactor. | `extensions.py`, `routes/api.py` |
| **Spam rating** | Rating baru difilter fingerprint IP+User-Agent & kata kasar sebelum disimpan. | `core/security.py`, `models/ratings.py` |

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
