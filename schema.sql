-- ============================================================
-- Sistem Informasi & Chatbot Budaya-Wisata Sorong Raya
-- Schema MySQL - jalankan di phpMyAdmin / mysql client (XAMPP)
-- ============================================================

CREATE DATABASE IF NOT EXISTS sorong_culture_tourism
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE sorong_culture_tourism;

-- 1. Tabel Administrator
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Tabel Budaya Suku Moi
CREATE TABLE IF NOT EXISTS budaya (
    id INT AUTO_INCREMENT PRIMARY KEY,
    judul VARCHAR(150) NOT NULL,
    kategori VARCHAR(50) NOT NULL,
    ringkasan TEXT NOT NULL,
    konten_lengkap LONGTEXT NOT NULL,
    gambar VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2b. Tabel Galeri Foto Tambahan Budaya (untuk slider di halaman detail)
CREATE TABLE IF NOT EXISTS budaya_galeri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    budaya_id INT NOT NULL,
    gambar VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (budaya_id) REFERENCES budaya(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Tabel Tempat Wisata
CREATE TABLE IF NOT EXISTS wisata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_wisata VARCHAR(150) NOT NULL,
    wilayah ENUM('Kota Sorong', 'Kabupaten Sorong') NOT NULL,
    deskripsi LONGTEXT NOT NULL,
    fasilitas TEXT NOT NULL,
    alamat VARCHAR(255) NOT NULL,
    tiket_masuk TEXT NULL,
    jam_operasional VARCHAR(100) DEFAULT 'Setiap Hari',
    gambar VARCHAR(255) NULL,
    latitude DECIMAL(10,7) NULL,
    longitude DECIMAL(10,7) NULL,
    sosmed_email VARCHAR(150) NULL,
    sosmed_facebook VARCHAR(255) NULL,
    sosmed_instagram VARCHAR(255) NULL,
    sosmed_youtube VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. Tabel Galeri Foto Tambahan Wisata (untuk slider di halaman detail)
CREATE TABLE IF NOT EXISTS wisata_galeri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    wisata_id INT NOT NULL,
    gambar VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wisata_id) REFERENCES wisata(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Tabel Metadata Dokumen RAG Chatbot
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_file VARCHAR(255) NOT NULL,
    tipe_file VARCHAR(20) NOT NULL,
    path_file VARCHAR(255) NOT NULL,
    status_indexed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 6. Tabel Rating & Ulasan Wisata (Proteksi Anti-Spam)
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    wisata_id INT NOT NULL,
    skor_bintang TINYINT NOT NULL CHECK (skor_bintang BETWEEN 1 AND 5),
    komentar TEXT NULL,
    ip_address_hash VARCHAR(64) NOT NULL,
    status_tampil ENUM('approved', 'pending', 'rejected') DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wisata_id) REFERENCES wisata(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_wisata_rating (wisata_id, ip_address_hash)
) ENGINE=InnoDB;

-- ============================================================
-- Dummy data admin (username: admin / password: admin123)
-- Hash dibuat dengan werkzeug.security.generate_password_hash
-- ============================================================
INSERT INTO admins (username, password_hash, nama_lengkap)
SELECT 'admin',
       'scrypt:32768:8:1$Im0SPqJqCdMevWsc$2c9d43ee9f2c9734cc92bcdf851620907b7174528c9211aca5fd0264b8bf345bfe844c6256f7ead04172fc3ed894ceda2f54097ef0c16717ec4eedeaa65b193e',
       'Administrator Sorong Raya'
WHERE NOT EXISTS (SELECT 1 FROM admins WHERE username = 'admin');

-- ============================================================
-- Dummy data budaya
-- ============================================================
INSERT INTO budaya (judul, kategori, ringkasan, konten_lengkap, gambar)
SELECT * FROM (SELECT
  'Tari Tumbu Tanah' AS judul,
  'Tarian Tradisional' AS kategori,
  'Tarian penyambutan khas Suku Moi yang menggambarkan kegembiraan dan penghormatan kepada tamu.' AS ringkasan,
  'Tari Tumbu Tanah merupakan tarian adat Suku Moi yang biasa ditampilkan pada acara penyambutan tamu kehormatan maupun upacara adat. Gerakannya menggambarkan hentakan kaki ke tanah sebagai simbol penghormatan terhadap alam dan leluhur. Tarian ini diiringi tifa dan nyanyian dalam bahasa Moi.' AS konten_lengkap,
  NULL AS gambar
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM budaya WHERE judul = 'Tari Tumbu Tanah');

INSERT INTO budaya (judul, kategori, ringkasan, konten_lengkap, gambar)
SELECT * FROM (SELECT
  'Seni Ukir Suku Moi' AS judul,
  'Seni Ukir' AS kategori,
  'Ukiran kayu bermotif flora dan fauna khas hutan Papua yang sarat makna filosofis.' AS ringkasan,
  'Seni ukir Suku Moi umumnya diaplikasikan pada perisai, tifa, dan perahu. Motif yang digunakan terinspirasi dari alam sekitar seperti burung cenderawasih dan motif akar pohon, melambangkan hubungan erat masyarakat dengan hutan sebagai sumber kehidupan.' AS konten_lengkap,
  NULL AS gambar
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM budaya WHERE judul = 'Seni Ukir Suku Moi');

INSERT INTO budaya (judul, kategori, ringkasan, konten_lengkap, gambar)
SELECT * FROM (SELECT
  'Upacara Adat Injambik' AS judul,
  'Upacara Adat' AS kategori,
  'Ritual adat Suku Moi terkait siklus kehidupan dan penghormatan terhadap leluhur.' AS ringkasan,
  'Upacara adat Suku Moi dilaksanakan dalam berbagai momen penting seperti pernikahan adat, penyambutan panen, maupun peringatan leluhur. Upacara ini dipimpin oleh kepala adat dan melibatkan seluruh anggota kampung sebagai bentuk solidaritas sosial.' AS konten_lengkap,
  NULL AS gambar
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM budaya WHERE judul = 'Upacara Adat Injambik');

-- ============================================================
-- Dummy data wisata
-- ============================================================
INSERT INTO wisata (nama_wisata, wilayah, deskripsi, fasilitas, alamat, tiket_masuk, jam_operasional, gambar)
SELECT * FROM (SELECT
  'Tanjung Batu' AS nama_wisata,
  'Kabupaten Sorong' AS wilayah,
  'Kawasan tebing batu karang yang menjorok ke laut dengan pemandangan matahari terbenam yang memukau.' AS deskripsi,
  'Area parkir, warung makan, gazebo, spot foto' AS fasilitas,
  'Distrik Makbon, Kabupaten Sorong' AS alamat,
  'Rp 10.000' AS tiket_masuk,
  '08.00 - 18.00 WIT' AS jam_operasional,
  NULL AS gambar
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM wisata WHERE nama_wisata = 'Tanjung Batu');

INSERT INTO wisata (nama_wisata, wilayah, deskripsi, fasilitas, alamat, tiket_masuk, jam_operasional, gambar)
SELECT * FROM (SELECT
  'Pantai Doom' AS nama_wisata,
  'Kota Sorong' AS wilayah,
  'Pantai bersejarah peninggalan masa kolonial yang kini menjadi destinasi rekreasi keluarga favorit warga Kota Sorong.' AS deskripsi,
  'Area parkir, kios kuliner, dermaga, kolam renang anak' AS fasilitas,
  'Kelurahan Klawuyuk, Kota Sorong' AS alamat,
  'Rp 5.000' AS tiket_masuk,
  '07.00 - 21.00 WIT' AS jam_operasional,
  NULL AS gambar
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM wisata WHERE nama_wisata = 'Pantai Doom');

INSERT INTO wisata (nama_wisata, wilayah, deskripsi, fasilitas, alamat, tiket_masuk, jam_operasional, gambar)
SELECT * FROM (SELECT
  'Saoka' AS nama_wisata,
  'Kota Sorong' AS wilayah,
  'Kawasan mangrove dan pantai alami yang masih asri, cocok untuk wisata edukasi konservasi.' AS deskripsi,
  'Jalur tracking mangrove, gazebo, area piknik' AS fasilitas,
  'Kelurahan Klasaman, Kota Sorong' AS alamat,
  'Gratis / Menyesuaikan' AS tiket_masuk,
  '08.00 - 17.00 WIT' AS jam_operasional,
  NULL AS gambar
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM wisata WHERE nama_wisata = 'Saoka');
