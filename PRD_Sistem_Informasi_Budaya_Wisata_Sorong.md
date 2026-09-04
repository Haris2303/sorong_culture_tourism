# Product Requirement Document (PRD)

## Sistem Informasi Budaya & Wisata Sorong Raya Terintegrasi Chatbot AI, Admin Management, & Anti-Spam Rating System
**Proyek Tugas Akhir / Skripsi:** Perancangan Sistem Informasi dan Chatbot Sebagai Media Edukasi Budaya dan Tempat Wisata Sorong Raya Berbasis Website  
**Penyusun:** Virda Kristy (202255202064)  
**Institusi:** Program Studi Teknik Informatika, Fakultas Teknik, Universitas Muhammadiyah Sorong  
**Tahun:** 2026  
**Status Dokumen:** Approved / Baselines (Updated with Anti-Spam Rating System)  

---

## 1. Pendahuluan & Latar Belakang

### 1.1 Ringkasan Eksekutif
Kawasan Sorong Raya di Provinsi Papua Barat Daya (khususnya Kota Sorong dan Kabupaten Sorong) memiliki kekayaan destinasi wisata bahari, alam, serta nilai luhur kebudayaan suku asli Papua, salah satunya Suku Moi. Namun, informasi mengenai adat istiadat, tarian, bahasa daerah, serta potensi tempat wisata belum terpusat, belum terdokumentasi secara optimal dalam media digital interaktif, dan sering kali sulit diakses secara cepat oleh wisatawan maupun masyarakat.

Sistem ini dirancang sebagai platform web komprehensif yang mengintegrasikan:
1. Media edukasi publik interaktif mengenai budaya dan destinasi pariwisata.
2. Asisten virtual cerdas (*chatbot*) berbasis *Retrieval-Augmented Generation* (RAG) dan *Large Language Model* (LLM).
3. Fitur umpan balik dan penilaian kepuasan pengunjung (*Rating & Review*) yang dilengkapi mekanisme proteksi anti-spam berlapis (*Multi-Layer Anti-Spam Defense*).
4. Portal *Dashboard Admin* untuk manajemen data dinamis, moderasi ulasan, dan pembaruan berkala basis pengetahuan AI pada vector database.

### 1.2 Tujuan Produk
1. Membangun sistem informasi berbasis website yang menyajikan katalog edukasi budaya Suku Moi dan direktori tempat wisata di Kota dan Kabupaten Sorong secara terstruktur.
2. Mengintegrasikan asisten virtual chatbot interaktif yang mampu menjawab pertanyaan pengguna dengan akurat berdasarkan sumber dokumen terverifikasi (*grounded knowledge*) menggunakan pendekatan NLP, RAG, dan LLM.
3. Menyediakan fitur pemberian rating dan ulasan tempat wisata yang akuntabel dengan sistem proteksi pencegahan spamming/bot tanpa membebani pengunjung dengan keharusan login.
4. Menyediakan dashboard administrator yang memfasilitasi pengelolaan konten (*CMS*), moderasi ulasan publik, serta mekanisme pelatihan ulang / sinkronisasi (*re-indexing / re-training*) basis pengetahuan pada vector database (ChromaDB) secara berkala.

---

## 2. Ruang Lingkup & Batasan Sistem

### 2.1 Lingkup Wilayah & Konten
* **Cakupan Wilayah:** Dibatasi pada wilayah Kota Sorong dan Kabupaten Sorong (Papua Barat Daya).
* **Fokus Budaya:** Kebudayaan lokal Suku Moi (adat istiadat, tarian tradisional, upacara adat, seni ukir, dan kearifan lokal).
* **Fokus Wisata:** Objek wisata alam, pantai, bahari, dan kawasan konservasi di Kota dan Kabupaten Sorong (misal: Pantai Doom, Tanjung Batu, Saoka, dll.).

### 2.2 Batasan Teknis & Model Pengguna
* Platform beroperasi sebagai sistem berbasis web responsif (*desktop-friendly* dan *mobile-accessible*).
* Backend sistem dijalankan sepenuhnya menggunakan kerangka kerja Python Flask.
* Pengunjung publik tidak dibebani kewajiban registrasi akun (Zero-Friction Access).
* Chatbot menggunakan metode *in-context retrieval* (RAG) dengan memanfaatkan embedding lokal pada vector store (ChromaDB).

---

## 3. Aktor & Matriks Hak Akses (User Roles)

| Peran (Actor) | Deskripsi | Hak Akses Utama |
| :--- | :--- | :--- |
| **Pengunjung / Publik (User)** | Wisatawan, pelajar, akademisi, dan masyarakat umum (Tanpa Login). | <ul><li>Mengakses Landing Page, katalog budaya, direktori wisata.</li><li>Menggunakan fitur pencarian konten.</li><li>Melakukan percakapan tanya-jawab interaktif dengan Chatbot AI.</li><li>Memberikan rating (1–5 bintang) dan ulasan pada objek wisata (dibatasi 1x per destinasi).</li></ul> |
| **Administrator (Admin)** | Pengelola sistem dan data kebudayaan/pariwisata. | <ul><li>Autentikasi akun admin (Login / Logout).</li><li>Melihat ringkasan metrik konten, statistik rating, & status sistem pada dashboard.</li><li>Operasi CRUD (Create, Read, Update, Delete) data budaya dan tempat wisata.</li><li>Moderasi rating publik (menyetujui, menyembunyikan, atau menghapus ulasan spam/anomali).</li><li>Mengunggah dokumen referensi pengetahuan (PDF/TXT).</li><li>Memicu sinkronisasi / pelatihan ulang (*re-train / re-indexing*) vector database ChromaDB.</li></ul> |

---

## 4. Kebutuhan Fungsional (Functional Requirements)

### Modul A: Portal Edukasi Publik (Public Web)

* **FR-01: Landing Page (Halaman Beranda)**
  * Menampilkan *Hero Banner* edukatif dengan slogan eksplorasi budaya dan wisata Sorong Raya.
  * Menampilkan *Quick Navigation* menuju modul Budaya, Wisata, dan Fitur Pencarian.
  * Menampilkan *Highlight Section* untuk artikel budaya Suku Moi terpopuler dan rekomendasi destinasi wisata unggulan (lengkap dengan rata-rata skor rating).
  * Menyematkan komponen widget floating chatbot di sudut kanan bawah antarmuka.

* **FR-02: Modul Katalog & Detail Budaya**
  * Menampilkan daftar kartu (*cards*) materi kebudayaan Suku Moi lengkap dengan kategori (Tarian, Alat Musik, Seni Ukir, Upacara Adat).
  * Halaman detail artikel menyajikan foto dokumentasi, kategori, dan deskripsi naratif mendalam sejarah serta nilai filosofisnya.

* **FR-03: Modul Direktori & Detail Destinasi Wisata**
  * Menampilkan katalog objek wisata dengan filter wilayah: Kota Sorong dan Kabupaten Sorong.
  * Halaman detail wisata menyajikan foto, deskripsi, fasilitas, jam operasional, tiket masuk, informasi rute/lokasi, agregat skor rating, serta daftar ulasan pengunjung yang telah disetujui.

* **FR-04: Fitur Pencarian Cepat (Global Search)**
  * Menyediakan bilah pencarian (*search bar*) berbasis kata kunci.
  * Sistem melakukan *query matching* ke basis data untuk menemukan artikel budaya maupun tempat wisata yang relevan.

---

### Modul B: Fitur Rating & Review dengan Proteksi Anti-Spam Berlapis (*Baru*)

* **FR-05: Input Penilaian Destinasi (Rating & Review Submission)**
  * Form input skor bintang (skala 1–5) dan kolom komentar ulasan opsional pada halaman detail destinasi wisata.
  * Pengunjung tidak perlu membuat akun/login untuk memberikan penilaian.

* **FR-06: Proteksi Anti-Spam & Anti-Bot Berlapis (Multi-Layer Defense System)**
  * **Layer 1 (Client-side Storage & Token Lock):** Browser menyimpan penanda token di `localStorage`. Jika pengguna sudah memberi rating untuk destinasi tertentu, form input terkunci otomatis.
  * **Layer 2 (Device & Network Fingerprinting):** Backend Flask membuat kode hash unik berbasis `SHA256(IP_Address + User_Agent)`. Database menerapkan aturan `UNIQUE KEY (wisata_id, ip_address_hash)`. Jika perangkat yang sama mencoba mengirimkan ulasan berulang untuk wisata yang sama, sistem basis data menolaknya secara permanen.
  * **Layer 3 (Rate Limiting via Flask-Limiter):** Rute API submit rating dibatasi maksimal 3 permintaan per jam per alamat IP (`@limiter.limit("3 per hour")`) guna mencegah *burst attacks*.
  * **Layer 4 (CAPTCHA Validasi Ringan):** Validasi bot tak kasat mata (*invisible*) via Google reCAPTCHA v3 atau Cloudflare Turnstile saat form dikirimkan.
  * **Layer 5 (Badword Filtering):** Pengecekan otomatis terhadap kata-kata kasar/sara pada teks komentar; jika terdeteksi, ulasan dialihkan ke status `pending` untuk dimoderasi admin.

---

### Modul C: Asisten Chatbot AI (NLP, RAG, & LLM Engine)

* **FR-07: Antarmuka Chatbot Interaktif (Floating Chat Widget)**
  * Widget obrolan melayang di sudut kanan bawah yang dapat dibuka-tutup tanpa me-*reload* halaman web.
  * Menyediakan riwayat sesi, status animasi *typing indicator*, dan tombol bantuan *quick-prompts*.

* **FR-08: Pemrosesan Bahasa Alami (NLP)**
  * Menerima input teks bebas dalam bahasa Indonesia percakapan sehari-hari.
  * Memproses input melalui tahapan tokenisasi, sanitasi teks, dan ekstraksi intensi konteks budaya atau destinasi wisata.

* **FR-09: Retrieval-Augmented Generation (RAG Context Retrieval)**
  * Menghitung vektor kemiripan (*similarity search*) antara pertanyaan pengguna dengan potongan dokumen (*chunks*) di ChromaDB.
  * Mengambil $k$ potongan teks paling relevan sebagai *context payload* ke dalam *prompt template* LLM.

* **FR-10: Respons Generatif Bersumber Terverifikasi (LLM Answering)**
  * Menghasilkan jawaban yang ramah, santun, dan berbasis murni pada data dokumen lokal yang terverifikasi untuk mengeliminasi halusinasi model.
  * Jika pertanyaan di luar konteks pengetahuan lokal, chatbot merespons secara sopan: *"Maaf, informasi mengenai hal tersebut belum tersedia dalam basis pengetahuan budaya dan wisata Sorong Raya kami."*

---

### Modul D: Dashboard Admin & Manajemen Pengetahuan AI

* **FR-11: Autentikasi & Otorisasi Admin**
  * Form masuk (*login*) khusus administrator dengan validasi kredensial (username & hashed password).
  * Proteksi sesi (*session-based auth*) pada seluruh rute backend berawalan `/admin/*`.

* **FR-12: Dashboard Metrik & Ringkasan Sistem**
  * Kartu statistik: Total artikel budaya, total destinasi wisata, rata-rata rating wisata, jumlah ulasan masuk, jumlah dokumen referensi, dan timestamp sinkronisasi RAG terakhir.

* **FR-13: Manajemen Data Budaya & Wisata (CRUD)**
  * Formulir tambah, sunting, dan hapus artikel budaya Suku Moi dan tempat wisata.
  * Fitur unggah gambar sampul/dokumentasi ke direktori server lokal.

* **FR-14: Panel Moderasi Rating & Ulasan (*Baru*)**
  * Daftar tabel ulasan masuk: Destinasi, skor bintang, komentar, timestamp, dan status (`approved`, `pending`, `rejected`).
  * Admin dapat menyetujui, menyembunyikan, atau menghapus ulasan yang dinilai sebagai anomali/pencemaran spam.

* **FR-15: Repositori Dokumen Pengetahuan (Knowledge Base Document Manager)**
  * Fitur unggah berkas sumber pengetahuan (PDF, TXT, MD) terkait naskah riset atau data budaya.
  * Tabel status dokumen (*Indexed / Pending*).

* **FR-16: Fitur Re-train / Re-indexing Vector Database Berkala**
  * Tombol aksi satu-klik: **"Sinkronisasi & Latih Ulang Vector DB"**.
  * Pipeline mengeksekusi *Document Loader*, *Text Chunking* (*RecursiveCharacterTextSplitter*), kalkulasi vektor embedding baru, dan pembaruan koleksi ChromaDB secara dinamis tanpa *downtime*.

---

## 5. Kebutuhan Non-Fungsional (Non-Functional Requirements)

### 5.1 Kinerja (Performance)
* Render halaman web publik berada di bawah 2 detik pada kondisi normal.
* Latensi pemrosesan kueri chatbot maksimal 3–5 detik.
* Perhitungan rata-rata rating destinasi wisata di-cache atau dihitung secara terindeks untuk mencegah *query bottleneck*.

### 5.2 Keandalan & Integritas Data (Data Integrity & Outlier Handling)
* Menggunakan metode pembobotan atau pemotongan nilai ekstrem (*Trimmed Mean / Weighted Rating*) agar lonjakan ulasan bintang 1 yang tiba-tiba tidak langsung merusak kredibilitas rating destinasi sebelum dimoderasi.
* Chatbot memiliki *system prompt* pembatas (*guardrails*) agar fokus pada kebudayaan Sorong dan objek wisata lokal.

### 5.3 Keamanan (Security)
* Enkripsi kata sandi administrator menggunakan *hashing* satu arah (*Werkzeug / bcrypt*).
* Proteksi CSRF pada formulir input dan upload file.
* Pencegahan SQL Injection melalui *parameterized queries* / ORM.
* Rate Limiting aktif pada seluruh endpoint publik yang menerima masukan data (termasuk `/api/rating` dan `/api/chat`).

---

## 6. Arsitektur Data (Database Schema - MySQL)

```sql
-- 1. Tabel Administrator
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Budaya Suku Moi
CREATE TABLE budaya (
    id INT AUTO_INCREMENT PRIMARY KEY,
    judul VARCHAR(150) NOT NULL,
    kategori VARCHAR(50) NOT NULL,
    ringkasan TEXT NOT NULL,
    konten_lengkap LONGTEXT NOT NULL,
    gambar VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Tabel Tempat Wisata
CREATE TABLE wisata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_wisata VARCHAR(150) NOT NULL,
    wilayah ENUM('Kota Sorong', 'Kabupaten Sorong') NOT NULL,
    deskripsi LONGTEXT NOT NULL,
    fasilitas TEXT NOT NULL,
    lokasi VARCHAR(255) NOT NULL,
    tiket_masuk VARCHAR(100) DEFAULT 'Gratis / Menyesuaikan',
    jam_operasional VARCHAR(100) DEFAULT 'Setiap Hari',
    gambar VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. Tabel Metadata Dokumen RAG Chatbot
CREATE TABLE knowledge_docs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_file VARCHAR(255) NOT NULL,
    tipe_file VARCHAR(20) NOT NULL,
    path_file VARCHAR(255) NOT NULL,
    status_indexed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabel Rating & Ulasan Wisata (Dengan Proteksi Skema Anti-Spam)
CREATE TABLE ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    wisata_id INT NOT NULL,
    skor_bintang TINYINT NOT NULL CHECK (skor_bintang BETWEEN 1 AND 5),
    komentar TEXT NULL,
    ip_address_hash VARCHAR(64) NOT NULL, -- SHA256(IP + User Agent)
    status_tampil ENUM('approved', 'pending', 'rejected') DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wisata_id) REFERENCES wisata(id) ON DELETE CASCADE,
    -- Membatasi 1 entitas perangkat/IP unik hanya dapat memberi rating 1 kali per tempat wisata
    UNIQUE KEY unique_user_wisata_rating (wisata_id, ip_address_hash)
);
```

---

## 7. Desain Arsitektur Teknis & Struktur Proyek

### 7.1 Tech Stack Terpilih
* **Backend Web Framework:** Python (Flask, Flask-Limiter)
* **Frontend Web:** HTML5, CSS3, JavaScript (Fetch API Asynchronous)
* **Database Relasional:** MySQL (via XAMPP Environment)
* **Vector Store Engine:** ChromaDB
* **AI Orchestrator & LLM:** LangChain Framework + Model Embedding + Large Language Model
* **Tooling:** Visual Studio Code, Figma (UI/UX), Draw.io (UML)

### 7.2 Struktur Folder Proyek
```text
sorong_culture_tourism/
│
├── app.py                      # Router Utama (Public, Chatbot, Rating, Admin)
├── config.py                   # Konfigurasi Database, Secret Key, Limiter, API Keys
├── requirements.txt            # Daftar pustaka (Flask, chromadb, langchain, dll.)
│
├── core/
│   ├── __init__.py
│   ├── db.py                   # Koneksi MySQL & helper kueri
│   ├── security.py             # Fingerprint generator & badword filter
│   ├── rag_engine.py           # Inisialisasi LangChain, Retriever, & Prompt Generator
│   └── sync_engine.py          # Document Loader, Chunking, & ChromaDB Indexer
│
├── data_store/
│   ├── chroma_db/              # Direktori penyimpanan vektor ChromaDB lokal
│   └── knowledge_docs/         # Direktori berkas PDF/TXT sumber pengetahuan RAG
│
├── static/
│   ├── css/
│   │   ├── style.css           # Styling portal publik
│   │   └── admin.css           # Styling dashboard admin
│   ├── js/
│   │   ├── chat.js             # Logika floating chatbot
│   │   ├── rating.js           # AJAX rating submission & local lock
│   │   └── admin.js            # Interaksi panel admin & sync trigger
│   ├── images/                 # Aset grafis UI
│   └── uploads/                # Berkas gambar destinasi & budaya
│
└── templates/
    ├── public/                 # Tampilan Portal Publik
    │   ├── base.html           # Layout induk publik
    │   ├── index.html          # Halaman beranda
    │   ├── budaya.html         # Katalog budaya Suku Moi
    │   ├── budaya_detail.html  # Detail artikel budaya
    │   ├── wisata.html         # Direktori wisata
    │   └── wisata_detail.html  # Detail destinasi & section rating/review
    │
    └── admin/                  # Tampilan Dashboard Admin
        ├── base_admin.html     # Layout induk admin
        ├── login.html          # Form login admin
        ├── dashboard.html      # Panel metrik & ringkasan
        ├── budaya_manage.html  # CRUD artikel budaya
        ├── wisata_manage.html  # CRUD tempat wisata
        ├── rating_manage.html  # Moderasi ulasan & status rating
        └── knowledge_sync.html # Upload berkas RAG & tombol re-train
```

---

## 8. Alur Kerja (Workflow) Sistem Anti-Spam Rating

```
[Pengguna Membuka Halaman Detail Wisata]
                    │
                    ▼
[Cek LocalStorage Browser: Apakah Sudah Pernah Beri Rating?]
   ├──> [Ya] ──> Nonaktifkan Form Rating (Tampilkan "Anda sudah mengulas tempat ini")
   │
   └──> [Belum] ──> Aktifkan Form Bintang & Komentar
                          │
                          ▼
            [Pengguna Mengirimkan Ulasan]
                          │
                          ▼
             [POST /api/rating via AJAX]
                          │
                          ▼
     [Flask-Limiter: Cek Batas Frekuensi (Max 3/jam)]
        ├──> Melebihi Batas ──> Tolak (HTTP 429 Too Many Requests)
        │
        └──> Lolos Batas ──────> [Ekstraksi IP + User-Agent]
                                         │
                                         ▼
                               [Hitung Hash SHA256]
                                         │
                                         ▼
                 [Validasi Database: Cek UNIQUE KEY (wisata_id, ip_hash)]
                    ├──> Sudah Ada di DB ──> Tolak ("Perangkat ini sudah memberi ulasan")
                    │
                    └──> Belum Ada ───────> [Cek Badword Filter]
                                                 ├──> Terdeteksi Kata Kasar ──> Simpan Status 'pending'
                                                 │
                                                 └──> Teks Bersih ───────────> Simpan Status 'approved'
                                                                                      │
                                                                                      ▼
                                                                     [Perbarui Rata-rata Skor Wisata]
```

---

## 9. Rencana Pengujian (Testing Plan)

1. **Black Box Testing:**
   * Pengujian form autentikasi admin dan operasi CRUD data.
   * Pengujian form pencarian konten di portal publik.
   * Pengujian respon API chatbot (`/api/chat`) terhadap pertanyaan relevan dan out-of-scope.
   * **Pengujian Khusus Fitur Rating & Anti-Spam:**
     * Menyerang endpoint `/api/rating` dengan skrip loop/otomatis (memastikan *Rate Limiter* dan *Unique Constraint* memblokir spam).
     * Uji coba pemberian rating ganda dari peramban yang sama.
     * Uji coba input komentar mengandung kata kasar (memastikan moderasi status bekerja).
   * Pengujian tombol sinkronisasi re-training ChromaDB.

2. **System Usability Scale (SUS) Testing:**
   * Pengujian kenyamanan (*usability*) antarmuka web, kemudahan membaca edukasi budaya, serta interaksi responsif asisten chatbot AI.
   * Ditargetkan kepada 30+ responden dengan instrumen 10 pertanyaan baku skala Likert SUS.
   * Target pencapaian skor SUS: $\ge 70$ (Kategori *Good / Acceptable*).

---
*Dokumen ini merupakan acuan spesifikasi teknis dan perancangan fungsionalitas sistem sebelum proses pengkodean (coding) diimplementasikan.*
