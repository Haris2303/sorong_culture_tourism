# Sistem Informasi & Chatbot Budaya-Wisata Sorong Raya

Boilerplate Flask + MySQL (XAMPP) + ChromaDB + LangChain (Gemini) sesuai PRD skripsi.

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
