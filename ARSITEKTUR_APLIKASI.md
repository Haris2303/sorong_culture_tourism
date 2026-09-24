# Panduan Arsitektur Aplikasi (Versi Gampang Dipahami)

> Dokumen ini ditulis untuk siapa saja — termasuk yang **belum paham
> pemrograman** — supaya bisa mengerti aplikasi ini secara garis besar: apa
> isinya, bagaimana cara menjalankannya, dan folder mana yang ngapain.
> Tidak ada kode yang perlu dihafal, cukup ikuti analogi & langkah di bawah.

---

## Daftar Isi

1. [Aplikasi Ini Sebenarnya Apa?](#1-aplikasi-ini-sebenarnya-apa)
2. [Cara Menjalankan Aplikasi dari Nol](#2-cara-menjalankan-aplikasi-dari-nol)
3. [Gambaran Besar: Bagaimana Semua Bagian Terhubung](#3-gambaran-besar-bagaimana-semua-bagian-terhubung)
4. [Peta Semua Folder & File](#4-peta-semua-folder--file)
5. [Penjelasan Tiap Folder Satu per Satu](#5-penjelasan-tiap-folder-satu-per-satu)
6. [Contoh Nyata: Mengikuti Satu Klik dari Awal sampai Akhir](#6-contoh-nyata-mengikuti-satu-klik-dari-awal-sampai-akhir)
7. [Bagaimana Chatbot AI-nya Bekerja](#7-bagaimana-chatbot-ai-nya-bekerja)
8. [Peta Semua Halaman (Sitemap)](#8-peta-semua-halaman-sitemap)
9. [Keamanan yang Sudah Dijaga Otomatis](#9-keamanan-yang-sudah-dijaga-otomatis)
10. [Pertanyaan Umum & Solusi Cepat](#10-pertanyaan-umum--solusi-cepat)
11. [Kamus Istilah Teknis (Bahasa Awam)](#11-kamus-istilah-teknis-bahasa-awam)

---

## 1. Aplikasi Ini Sebenarnya Apa?

Ini adalah **website informasi Budaya & Wisata Sorong Raya**, lengkap dengan
**chatbot AI** yang bisa menjawab pertanyaan pengunjung tentang budaya Suku
Moi dan destinasi wisata di sana.

Ada dua "sisi" pengguna:

| Sisi | Siapa | Bisa ngapain |
| --- | --- | --- |
| **Publik** | Pengunjung website biasa (siapa saja) | Baca artikel budaya, lihat daftar & detail wisata, cari sesuatu, kasih rating/ulasan wisata, tanya-jawab dengan chatbot |
| **Admin** | Pengelola konten (petugas dinas/pengelola situs) | Login, tambah/edit/hapus artikel budaya & wisata, moderasi ulasan (setujui/tolak), unggah dokumen pengetahuan & "melatih ulang" chatbot |

Semua ditulis dengan bahasa pemrograman **Python**, memakai kerangka kerja
(_framework_) bernama **Flask** — anggap saja Flask itu "mesin" yang mengatur
lalu-lintas antara browser pengunjung dan data di server.

---

## 2. Cara Menjalankan Aplikasi dari Nol

Anggap komputer Anda masih kosong sama sekali. Berikut langkah lengkapnya.

### Yang perlu disiapkan dulu

1. **Python** (bahasa pemrogramannya) — download di [python.org](https://www.python.org/downloads/).
2. **XAMPP** — paket yang menyediakan database MySQL. Download di
   [apachefriends.org](https://www.apachefriends.org/).
3. **API Key Gemini** (gratis) dari [Google AI Studio](https://aistudio.google.com/app/apikey)
   — dipakai untuk "mengindeks" pengetahuan chatbot.
4. **API Key OpenRouter** (gratis) dari [openrouter.ai/keys](https://openrouter.ai/keys)
   — dipakai supaya chatbot bisa "berbicara"/menjawab.

### Langkah demi langkah

**Langkah 1 — Siapkan "ruang kerja" Python (virtual environment)**

```bash
python -m venv venv
venv\Scripts\activate
```

Perintah ini membuat folder terpisah bernama `venv` supaya pustaka/library
Python untuk proyek ini tidak bercampur dengan proyek lain di komputer Anda.

**Langkah 2 — Install semua "bahan" yang dibutuhkan aplikasi**

```bash
pip install -r requirements.txt
```

File `requirements.txt` itu semacam daftar belanja — isinya nama-nama
pustaka (Flask, MySQL connector, LangChain, dll) yang otomatis diunduh &
dipasang.

**Langkah 3 — Salin file pengaturan rahasia**

```bash
copy .env.example .env
```

Lalu buka file `.env` dengan text editor, isi:
- `GEMINI_API_KEY` → API key dari Google AI Studio.
- `OPENROUTER_API_KEY` → API key dari OpenRouter.
- Data MySQL (`DB_USER`, `DB_PASSWORD`, dll) — default XAMPP biasanya
  `root` tanpa password, jadi kalau belum pernah diubah tidak perlu disentuh.

**Langkah 4 — Nyalakan database**

1. Buka **XAMPP Control Panel**, klik **Start** pada baris **Apache** dan **MySQL**.
2. Buka `http://localhost/phpmyadmin` di browser.
3. Buat database baru (atau import langsung file `schema.sql` yang ada di
   folder proyek ini) — ini akan otomatis membuat semua "rak data" (tabel)
   yang dibutuhkan aplikasi.

**Langkah 5 — Jalankan aplikasinya**

```bash
python app.py
```

Kalau berhasil, akan muncul tulisan bahwa server berjalan. Buka browser lalu
kunjungi:

```
http://localhost:5000
```

**Langkah 6 — Login sebagai admin**

- URL: `http://localhost:5000/admin/login`
- Username: `admin`
- Password: `admin123`

> ⚠️ Ganti password ini setelah login pertama kali di lingkungan produksi
> (lihat README.md bagian "Login Admin" untuk caranya).

**Langkah 7 — "Latih" chatbot supaya bisa menjawab**

1. Masuk ke menu **Dashboard Admin → Knowledge Base**.
2. Unggah dokumen (PDF/TXT/MD) berisi informasi budaya & wisata.
3. Klik tombol **"Sinkronkan & Latih Ulang Vector DB"**.
4. Tunggu sampai selesai — chatbot di halaman utama sekarang siap menjawab
   berdasarkan dokumen yang baru diunggah.

---

## 3. Gambaran Besar: Bagaimana Semua Bagian Terhubung

Bayangkan aplikasi ini seperti **restoran**:

```
   Pengunjung (Browser)
          |
          |  1. "Saya mau lihat menu wisata"
          v
   +--------------+        2. "Tolong ambilkan       +----------------+
   |   routes/    |  --->     data wisata dari        |    models/     |
   |  (PELAYAN)   |           gudang"                 |    (DAPUR)     |
   +--------------+  <---------------------------     +----------------+
          |              3. Data mentah dikirim               |
          |                 balik ke pelayan                  |
          |                                          4. Dapur ambil bahan
          |                                             dari gudang besar
          v                                             (database MySQL)
   +--------------+
   | templates/   |   5. Pelayan taruh data di "piring"
   | (PIRING SAJI)|      (halaman HTML) yang cantik
   +--------------+
          |
          v
   Pengunjung melihat halaman jadi di browser
```

Tabel peran singkatnya:

| Folder | Peran di restoran | Tugas sebenarnya |
| --- | --- | --- |
| `routes/` | **Pelayan** | Menerima "pesanan" (request dari browser), teruskan ke dapur, antar hasilnya kembali. Pelayan **tidak masak sendiri**. |
| `models/` | **Dapur** | Tempat data benar-benar diolah & disimpan/diambil dari "gudang besar" (database MySQL). |
| `utils/` | **Alat dapur generik** | Perkakas kecil yang dipakai di banyak resep tapi tidak spesifik ke satu menu (contoh: menghitung halaman/pagination, menyimpan file upload). |
| `templates/` | **Piring saji** | Bagaimana data ditampilkan ke pengunjung (halaman HTML). |
| `core/` | **Ruang mesin & infrastruktur** | Bagian inti yang jarang disentuh: koneksi ke database, penjaga pintu login admin, "otak" chatbot AI. |
| `static/` | **Gudang aset visual** | Gambar, video, file CSS (gaya tampilan), dan JavaScript (interaktivitas tombol/animasi). |

Aturan emasnya: **pelayan (routes) tidak boleh masak sendiri** (tidak
menulis query database langsung), dan **dapur (models) tidak boleh
berurusan dengan pelanggan** (tidak tahu apa itu halaman HTML). Pemisahan
ini membuat kalau ada yang error, gampang dicari letaknya.

---

## 4. Peta Semua Folder & File

```
S-Virda/
│
├── app.py                  # "Saklar utama" — menyalakan seluruh aplikasi
├── config.py                # Semua pengaturan (dibaca dari file .env)
├── extensions.py             # Alat tambahan Flask yang dipakai bareng (pembatas jumlah request)
├── schema.sql                 # Cetak biru struktur database (dipakai saat setup awal)
├── sorong_culture_tourism.sql  # Cadangan/dump database berisi contoh data
├── requirements.txt             # Daftar belanja pustaka Python
├── .env.example                  # Contoh file pengaturan rahasia (API key, password DB)
│
├── routes/                  # 1) PINTU MASUK - terima permintaan dari browser
│   ├── public.py              # Halaman publik: beranda, budaya, wisata, pencarian
│   ├── api.py                   # API chatbot & pengiriman rating
│   ├── admin_auth.py              # Login / logout admin
│   ├── admin_dashboard.py           # Halaman ringkasan (dashboard) admin
│   ├── admin_budaya.py                # Kelola (tambah/edit/hapus) artikel budaya
│   ├── admin_wisata.py                  # Kelola destinasi wisata
│   ├── admin_ratings.py                   # Setujui/tolak/hapus ulasan pengunjung
│   ├── admin_knowledge.py                   # Kelola dokumen & "latih ulang" chatbot
│   └── errors.py                              # Halaman saat terjadi error (404, dll)
│
├── models/                  # 2) OLAH DATA - satu file per jenis data
│   ├── budaya.py               # Semua urusan data artikel budaya
│   ├── wisata.py                # Semua urusan data destinasi wisata
│   ├── ratings.py                 # Semua urusan data rating/ulasan
│   ├── admins.py                    # Data akun admin
│   └── knowledge.py                   # Data dokumen pengetahuan chatbot
│
├── utils/                   # 3) ALAT BANTU GENERIK - tidak menyentuh database
│   ├── pagination.py            # Membagi daftar panjang jadi beberapa halaman
│   ├── uploads.py                 # Menyimpan & menghapus file yang diunggah
│   ├── coordinates.py               # Membaca format koordinat lokasi wisata
│   └── validators.py                  # Memeriksa apakah input form valid
│
├── core/                     # INFRASTRUKTUR INTI - jarang perlu disentuh
│   ├── db.py                    # Jalur koneksi ke database MySQL
│   ├── auth.py                    # Penjaga pintu: cek admin sudah login atau belum
│   ├── security.py                  # Deteksi kata kasar & cegah spam ulasan
│   ├── content.py                     # Membersihkan HTML dari editor teks admin
│   ├── template_helpers.py              # Data global yang tersedia di semua halaman (mis. tahun berjalan)
│   ├── rag_engine.py                      # "Otak" chatbot: cari jawaban + tanya AI
│   ├── sync_engine.py                       # Proses "melatih ulang" pengetahuan chatbot
│   └── chat_jobs.py                           # Menjaga jawaban chatbot tetap diproses meski pengunjung pindah halaman
│
├── templates/                # TAMPILAN - kerangka halaman HTML
│   ├── public/                  # Halaman yang dilihat pengunjung umum
│   └── admin/                     # Halaman panel admin
│
├── static/                    # ASET STATIS (tidak berubah-ubah oleh server)
│   ├── css/                       # Berkas gaya tampilan (warna, tata letak)
│   ├── js/                          # Berkas interaktivitas (klik tombol, animasi, dsb)
│   ├── images/                        # Gambar bawaan situs
│   ├── assets/                          # Gambar dekoratif (motif, ikon, header)
│   ├── video/                              # Video latar (hero)
│   └── uploads/                              # Gambar yang diunggah admin lewat panel
│
├── data_store/                # "OTAK" CHATBOT tersimpan di sini
│   ├── chroma_db/                # Database vektor (hasil "pemahaman" AI atas dokumen)
│   └── knowledge_docs/             # Dokumen asli (PDF/TXT/MD) yang pernah diunggah admin
│
└── docs/
    └── knowledge_base.pdf      # Contoh dokumen pengetahuan bawaan untuk chatbot
```

---

## 5. Penjelasan Tiap Folder Satu per Satu

### 5.1 File-file di folder utama (root)

| File | Analoginya | Penjelasan sederhana |
| --- | --- | --- |
| `app.py` | Saklar listrik utama gedung | Ini yang dijalankan pertama kali (`python app.py`). Tugasnya: menyalakan Flask, menyambungkan ke database, memasang semua "pintu masuk" (routes), lalu menyalakan server di `http://localhost:5000`. |
| `config.py` | Buku catatan pengaturan | Semua nilai yang bisa berubah-ubah (alamat database, API key, ukuran maksimal upload) disimpan di sini, dan sebagian besar nilainya sebenarnya dibaca dari file `.env`. |
| `extensions.py` | Alat tambahan bersama | Menyiapkan "pembatas kecepatan" (rate limiter) supaya satu orang tidak bisa spam kirim request ratusan kali per detik. |
| `.env` / `.env.example` | Brankas kata sandi | Tempat menyimpan data rahasia: password database, API key Gemini & OpenRouter. `.env.example` adalah contoh kosongnya (aman dibagikan), sedangkan `.env` yang asli **tidak boleh** dibagikan ke publik. |
| `requirements.txt` | Daftar belanja | Daftar semua pustaka pihak ketiga yang dipakai aplikasi ini, supaya orang lain bisa install versi yang sama persis. |
| `schema.sql` | Cetak biru gudang | Berisi perintah untuk membuat semua tabel database dari nol (kosong, tanpa isi). |
| `sorong_culture_tourism.sql` | Gudang yang sudah ada isinya | Sama seperti `schema.sql` tapi sudah termasuk contoh data, cocok untuk demo. |

### 5.2 `routes/` — Pelayan (pintu masuk semua permintaan)

Setiap file di sini menangani **satu kelompok halaman**. Tugasnya cuma 3
langkah: (1) baca apa yang diminta browser, (2) minta data ke `models/`,
(3) kirim balik halaman atau data JSON.

| File | Menangani halaman/fitur apa |
| --- | --- |
| `public.py` | Beranda, daftar & detail artikel budaya, daftar & detail wisata, pencarian |
| `api.py` | Percakapan dengan chatbot (`/api/chat`) & pengiriman rating wisata (`/api/rating`) |
| `admin_auth.py` | Login & logout admin |
| `admin_dashboard.py` | Halaman ringkasan/statistik setelah admin login |
| `admin_budaya.py` | Tambah, edit, hapus artikel budaya beserta galeri fotonya |
| `admin_wisata.py` | Tambah, edit, hapus destinasi wisata beserta galeri fotonya |
| `admin_ratings.py` | Menyetujui, menolak, atau menghapus ulasan pengunjung |
| `admin_knowledge.py` | Unggah/hapus dokumen pengetahuan & memicu "latih ulang" chatbot |
| `errors.py` | Menentukan tampilan saat halaman tidak ditemukan (404) atau terlalu banyak request (429) |

### 5.3 `models/` — Dapur (semua urusan data)

Satu file untuk satu jenis data ("entitas"). Isinya perintah-perintah untuk
mengambil, menyimpan, mengubah, atau menghapus data di database MySQL.

| File | Data yang diurus |
| --- | --- |
| `budaya.py` | Artikel budaya & galeri fotonya |
| `wisata.py` | Destinasi wisata & galeri fotonya |
| `ratings.py` | Rating/ulasan wisata dari pengunjung |
| `admins.py` | Akun admin (untuk proses login) |
| `knowledge.py` | Daftar dokumen pengetahuan yang pernah diunggah |

### 5.4 `utils/` — Kotak Perkakas Umum

Fungsi-fungsi kecil yang **tidak tahu-menahu soal budaya/wisata** dan
**tidak menyentuh database** — jadi bisa dipakai di mana saja.

| File | Kegunaan |
| --- | --- |
| `pagination.py` | Memecah daftar panjang (misal 100 artikel) jadi beberapa halaman kecil |
| `uploads.py` | Menyimpan file gambar/dokumen yang diunggah dengan aman (nama file diacak, ekstensi diperiksa) |
| `coordinates.py` | Membaca lokasi wisata baik dalam format angka desimal maupun format derajat-menit-detik |
| `validators.py` | Memeriksa apakah isian form (misalnya email) sudah benar formatnya |

### 5.5 `core/` — Ruang Mesin (Infrastruktur Inti)

Bagian paling "dalam" dari aplikasi. Biasanya **tidak perlu diubah** kecuali
memang sedang mengerjakan hal inti seperti keamanan atau chatbot.

| File | Fungsinya |
| --- | --- |
| `db.py` | Membuka & mengelola koneksi ke database MySQL |
| `auth.py` | "Satpam" — memeriksa apakah seseorang sudah login sebagai admin sebelum boleh mengakses halaman `/admin/*` |
| `security.py` | Mendeteksi kata kasar di ulasan & mencegah satu orang mengulas berkali-kali (anti-spam) |
| `content.py` | Membersihkan kode HTML dari editor teks admin supaya tidak disusupi kode berbahaya (XSS) |
| `template_helpers.py` | Menyediakan data yang bisa dipakai di semua halaman, misalnya tahun berjalan untuk teks hak cipta di footer |
| `rag_engine.py` | "Otak" chatbot — mencari potongan dokumen yang relevan lalu bertanya ke AI (LLM) untuk menyusun jawaban |
| `sync_engine.py` | Proses "pelatihan ulang": membaca semua dokumen & artikel, memecahnya jadi potongan kecil, lalu menyimpannya ke database khusus AI (ChromaDB) |
| `chat_jobs.py` | Menjaga agar jawaban chatbot tetap diproses di latar belakang walau pengunjung sudah pindah ke halaman lain, supaya jawabannya tidak hilang percuma |

### 5.6 `templates/` — Piring Saji (Tampilan Halaman)

Berisi kerangka HTML yang diisi otomatis dengan data oleh `routes/`. Dibuat
dengan Jinja2 — cara menulis HTML biasa yang bisa disisipi data dinamis
(contoh: `{{ nama_wisata }}`).

- **`templates/public/`** — halaman yang dilihat pengunjung umum: beranda
  (`index.html`), daftar & detail budaya, daftar & detail wisata, hasil
  pencarian, halaman 404, dan widget kotak chat (`_chat_widget.html`).
- **`templates/admin/`** — halaman panel admin: login, dashboard, kelola
  budaya, kelola wisata, moderasi ulasan, sinkronisasi pengetahuan chatbot.
- File yang diawali garis bawah (`_chat_widget.html`, `_budaya_table.html`,
  `_wisata_table.html`) adalah "potongan" HTML kecil yang dipakai berulang
  di beberapa halaman (supaya tidak menulis kode yang sama dua kali).

### 5.7 `static/` — Gudang Aset Visual

Berkas yang **dikirim apa adanya** ke browser (tidak diproses server),
seperti gambar dan gaya tampilan.

| Subfolder | Isinya |
| --- | --- |
| `css/` | `style.css` (tampilan halaman publik) & `admin.css` (tampilan panel admin) |
| `js/` | `chat.js` (logika chatbot), `rating.js` (form ulasan), `hero-video.js` (video latar beranda), `admin.js` (interaktivitas panel admin) |
| `images/` | Gambar bawaan situs (gambar pengganti/fallback jika data belum punya foto) |
| `assets/` | Elemen dekoratif seperti motif Papua, ikon tifa & cendrawasih, gambar header |
| `video/` | Video latar untuk bagian hero di beranda |
| `uploads/` | Tempat gambar hasil unggahan admin (artikel budaya & wisata) disimpan |

### 5.8 `data_store/` — "Otak" & Ingatan Chatbot

Ini bukan kode, melainkan **tempat penyimpanan hasil kerja chatbot**:

- **`chroma_db/`** — database vektor. Setelah dokumen "dibaca" AI, isinya
  diubah jadi angka-angka (disebut *embedding*) yang mewakili makna teks,
  lalu disimpan di sini supaya chatbot bisa cepat mencari potongan teks
  yang relevan saat menjawab pertanyaan.
- **`knowledge_docs/`** — salinan asli dokumen (PDF/TXT/MD) yang pernah
  diunggah admin lewat menu Knowledge Base.

### 5.9 `docs/`

Folder ini **berbeda** dari dokumen arsitektur yang sedang Anda baca ini —
isinya adalah `knowledge_base.pdf`, salah satu contoh bahan bacaan/sumber
pengetahuan bawaan yang bisa dipakai untuk melatih chatbot.

---

## 6. Contoh Nyata: Mengikuti Satu Klik dari Awal sampai Akhir

### Contoh A — Pengunjung membuka detail sebuah destinasi wisata

1. Pengunjung klik salah satu kartu wisata di halaman `/wisata`, browser
   pergi ke alamat semacam `/wisata/5`.
2. **`routes/public.py`** menerima permintaan ini lewat fungsi
   `wisata_detail`, lalu bertanya ke **`models/wisata.py`**: "tolong
   ambilkan data wisata dengan id 5".
3. **`models/wisata.py`** menjalankan perintah ke database lewat
   **`core/db.py`**, mendapatkan data (nama, deskripsi, lokasi, foto), lalu
   mengembalikannya ke `routes/public.py`.
4. `routes/public.py` juga meminta ringkasan rating dari
   **`models/ratings.py`**.
5. Semua data itu dibungkus dan dikirim ke
   **`templates/public/wisata_detail.html`**, yang menyusunnya jadi halaman
   HTML lengkap dengan gaya dari **`static/css/style.css`**.
6. Browser menampilkan halaman jadi ke pengunjung.

### Contoh B — Admin mengunggah dokumen baru lalu "melatih ulang" chatbot

1. Admin membuka menu **Knowledge Base**, memilih file PDF, klik unggah.
2. **`routes/admin_knowledge.py`** menerima file itu, memvalidasinya lewat
   **`utils/uploads.py`** (cek ekstensi file & mengacak nama file demi
   keamanan), lalu menyimpan catatannya lewat **`models/knowledge.py`** dan
   file aslinya di **`data_store/knowledge_docs/`**.
3. Admin klik tombol **"Sinkronkan & Latih Ulang Vector DB"**.
4. **`core/sync_engine.py`** berjalan di latar belakang: membaca semua
   dokumen + artikel budaya/wisata di database, memotongnya jadi
   potongan-potongan kecil, mengubahnya jadi *embedding* lewat Gemini,
   lalu menyimpannya ke **`data_store/chroma_db/`**.
5. Setelah selesai, chatbot di beranda sudah "tahu" isi dokumen baru itu.

### Contoh C — Pengunjung bertanya ke chatbot

1. Pengunjung mengetik pertanyaan di kotak chat (`_chat_widget.html`,
   digerakkan oleh `static/js/chat.js`).
2. Pertanyaan dikirim ke **`routes/api.py`** (`/api/chat`), yang langsung
   menyerahkannya ke **`core/chat_jobs.py`** untuk diproses **di latar
   belakang** (supaya kalau pengunjung pindah halaman, jawabannya tidak
   hilang percuma) dan langsung membalas dengan sebuah "nomor tiket"
   (`job_id`).
3. `static/js/chat.js` terus bertanya secara berkala ("apakah jawaban untuk
   tiket ini sudah siap?") ke `/api/chat/status/<job_id>` sampai jawabannya
   selesai.
4. Di baliknya, **`core/rag_engine.py`** mencari potongan dokumen paling
   relevan dari `data_store/chroma_db/`, menyusunnya jadi konteks, lalu
   mengirimkannya ke AI (lewat OpenRouter) untuk disusun jadi jawaban yang
   enak dibaca.
5. Jawaban itu ditampilkan di kotak chat, dan tetap ada meski pengunjung
   sudah berpindah ke halaman lain (lihat riwayat commit "jawaban bertahan
   saat pindah halaman & badge notifikasi").

---

## 7. Bagaimana Chatbot AI-nya Bekerja

Teknik ini disebut **RAG** (*Retrieval-Augmented Generation*) — istilahnya
terdengar rumit, tapi konsepnya sederhana, seperti **mahasiswa ujian buka
buku**:

1. **Sebelum ujian** (proses sinkronisasi): semua dokumen & artikel dibaca
   lebih dulu, dipotong jadi bagian-bagian kecil, dan disimpan rapi di
   sebuah "rak catatan" khusus (`data_store/chroma_db/`) supaya gampang
   dicari lagi nanti.
2. **Saat ada pertanyaan**: chatbot tidak asal menjawab dari ingatannya
   sendiri. Ia dulu **mencari bagian catatan mana yang paling nyambung**
   dengan pertanyaan itu (langkah *Retrieval* — "mencari").
3. **Baru setelah itu** ia menyerahkan pertanyaan + catatan relevan tadi ke
   AI (LLM lewat OpenRouter) dan minta AI itu **menyusun jawaban yang
   enak dibaca** berdasarkan catatan tersebut (langkah *Generation* —
   "menyusun jawaban").

Keuntungannya: chatbot menjawab berdasarkan **dokumen yang benar-benar
diunggah admin**, bukan mengarang bebas, dan jawabannya bisa diperbarui
cukup dengan mengunggah dokumen baru lalu sinkronisasi ulang — tanpa perlu
mengubah kode sama sekali.

---

## 8. Peta Semua Halaman (Sitemap)

### Halaman Publik

| Alamat (URL) | Isinya |
| --- | --- |
| `/` | Beranda — sorotan budaya & wisata, statistik ringkas |
| `/budaya` | Daftar semua artikel budaya (bisa difilter per kategori) |
| `/budaya/<id>` | Detail satu artikel budaya |
| `/wisata` | Daftar semua destinasi wisata (bisa difilter per wilayah) |
| `/wisata/<id>` | Detail satu destinasi wisata + rating & ulasan |
| `/search?q=...` | Hasil pencarian budaya & wisata |
| `/api/chat` | (dipakai kotak chat) mengirim pertanyaan ke chatbot |
| `/api/rating` | (dipakai form ulasan) mengirim rating baru |

### Halaman Admin (wajib login lebih dulu)

| Alamat (URL) | Isinya |
| --- | --- |
| `/admin/login` | Halaman login admin |
| `/admin/dashboard` | Ringkasan/statistik setelah login |
| `/admin/budaya` | Kelola (tambah/edit/hapus) artikel budaya |
| `/admin/wisata` | Kelola destinasi wisata |
| `/admin/ratings` | Setujui/tolak/hapus ulasan pengunjung |
| `/admin/knowledge` | Unggah dokumen & jalankan "latih ulang" chatbot |

---

## 9. Keamanan yang Sudah Dijaga Otomatis

Aplikasi ini sudah dibuat sesederhana mungkin dari sisi struktur, tapi
sisi keamanannya **tidak ikut disederhanakan**. Beberapa contoh yang sudah
otomatis berjalan (detail lengkap ada di `README.md`):

- Semua pertanyaan ke database memakai cara aman (parameter terpisah),
  bukan menggabung teks mentah — mencegah **SQL Injection**.
- Isi artikel dari editor teks dibersihkan dulu sebelum disimpan —
  mencegah **kode berbahaya menyusup (XSS)**.
- Semua form admin dilindungi token keamanan (**CSRF protection**).
- File yang diunggah diperiksa jenisnya & namanya diacak — mencegah
  unggahan file berbahaya.
- Setiap halaman `/admin/*` wajib melewati "satpam" (`core/auth.py`) —
  tidak bisa diakses tanpa login.
- Chatbot & form rating dibatasi jumlah pemakaiannya per menit/jam supaya
  tidak disalahgunakan (spam).

---

## 10. Pertanyaan Umum & Solusi Cepat

**"Muncul error tidak bisa konek ke database."**
→ Pastikan **Apache** dan **MySQL** di XAMPP Control Panel sudah menyala
(tombol Start berwarna hijau), dan data di `.env` (`DB_USER`,
`DB_PASSWORD`, `DB_NAME`) sudah sesuai.

**"Chatbot tidak menjawab / muncul pesan error."**
→ Cek apakah `GEMINI_API_KEY` dan `OPENROUTER_API_KEY` di `.env` sudah
diisi dan masih berlaku. Model gratis di OpenRouter kadang penuh kuota —
aplikasi ini sudah otomatis mencoba beberapa model cadangan secara
berurutan (lihat `OPENROUTER_CHAT_MODEL_FALLBACKS` di `config.py`).

**"Chatbot menjawab tapi jawabannya kosong/tidak relevan."**
→ Kemungkinan belum ada dokumen yang disinkronkan. Masuk ke
**Dashboard Admin → Knowledge Base**, unggah dokumen, lalu klik
**Sinkronkan & Latih Ulang Vector DB**.

**"Port 5000 sudah dipakai aplikasi lain."**
→ Tutup aplikasi lain yang memakai port itu, atau ubah baris terakhir di
`app.py` (`app.run(..., port=5000, ...)`) ke angka port lain, misalnya `5050`.

**"Lupa password admin."**
→ Boilerplate ini belum punya fitur ganti password lewat tampilan, jadi
harus diubah manual lewat query ke tabel `admins` di phpMyAdmin (lihat
petunjuk di `README.md` bagian "Login Admin").

---

## 11. Kamus Istilah Teknis (Bahasa Awam)

| Istilah | Artinya secara sederhana |
| --- | --- |
| **Flask** | "Mesin" yang mengatur bagaimana aplikasi Python ini bisa diakses lewat browser sebagai website |
| **Route / URL rule** | Alamat halaman (contoh: `/wisata`) beserta aturan apa yang terjadi saat alamat itu dikunjungi |
| **Request** | Permintaan yang dikirim browser ke server, misalnya saat mengklik link atau mengirim form |
| **Response** | Balasan dari server ke browser — bisa berupa halaman HTML atau data mentah (JSON) |
| **Database (MySQL)** | "Gudang besar" tempat semua data (artikel, wisata, ulasan) disimpan permanen |
| **Query** | Perintah untuk mengambil/mengubah/menghapus data di database |
| **Template (Jinja2)** | Kerangka halaman HTML yang bisa diisi data secara otomatis |
| **Session** | "Gelang tangan" sementara yang menandai bahwa seseorang sudah login sebagai admin, disimpan lewat cookie di browser |
| **CSRF Token** | Kode rahasia kecil di setiap form untuk memastikan pengiriman form benar-benar berasal dari halaman aplikasi ini, bukan dari situs lain yang mencoba menipu |
| **API** | Cara program saling "berbicara" tanpa harus menampilkan halaman penuh — biasanya untuk fitur seperti chatbot yang butuh kirim-terima data cepat |
| **JSON** | Format teks sederhana untuk mengirim data terstruktur antar program (dipakai oleh `api.py`) |
| **RAG (Retrieval-Augmented Generation)** | Teknik chatbot AI: cari dulu catatan yang relevan, baru minta AI menyusun jawaban berdasarkan catatan itu |
| **Embedding** | Cara mengubah teks jadi kumpulan angka yang mewakili maknanya, supaya komputer bisa membandingkan "kemiripan makna" antar teks |
| **Vector Database (ChromaDB)** | Tempat penyimpanan khusus untuk data embedding, dirancang supaya pencarian "teks yang mirip makna" jadi cepat |
| **LLM (Large Language Model)** | Model AI yang bisa memahami & menyusun teks, seperti yang dipakai lewat OpenRouter untuk menjawab pertanyaan pengunjung |
| **Rate limiting** | Pembatasan jumlah permintaan yang boleh dikirim seseorang dalam waktu tertentu, supaya server tidak kebanjiran/disalahgunakan |
| **Environment variable (.env)** | Nilai pengaturan/rahasia yang disimpan di luar kode program, supaya tidak perlu mengubah kode saat pindah server atau mengganti kata sandi |
| **Virtual environment (venv)** | "Ruang kerja" Python yang terisolasi, supaya pustaka untuk proyek ini tidak bentrok dengan proyek Python lain di komputer yang sama |

---

*Dokumen ini melengkapi `README.md` (fokus ke setup cepat) dan `DESIGN.md`
(fokus ke sistem desain tampilan). Kalau ada bagian aplikasi yang berubah
signifikan, jangan lupa perbarui juga dokumen ini.*
