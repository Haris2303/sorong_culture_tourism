-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Sep 23, 2026 at 06:56 AM
-- Server version: 9.6.0-commercial
-- PHP Version: 8.3.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `sorong_culture_tourism`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int NOT NULL,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nama_lengkap` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `username`, `password_hash`, `nama_lengkap`, `created_at`) VALUES
(1, 'admin', 'scrypt:32768:8:1$Im0SPqJqCdMevWsc$2c9d43ee9f2c9734cc92bcdf851620907b7174528c9211aca5fd0264b8bf345bfe844c6256f7ead04172fc3ed894ceda2f54097ef0c16717ec4eedeaa65b193e', 'Administrator Sorong Raya', '2026-09-04 13:26:12');

-- --------------------------------------------------------

--
-- Table structure for table `budaya`
--

CREATE TABLE `budaya` (
  `id` int NOT NULL,
  `judul` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `kategori` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ringkasan` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `konten_lengkap` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `gambar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `budaya`
--

INSERT INTO `budaya` (`id`, `judul`, `kategori`, `ringkasan`, `konten_lengkap`, `gambar`, `created_at`, `updated_at`) VALUES
(1, 'Tari Tumbu Tanah', 'Tarian Tradisional', 'Tarian penyambutan khas Suku Moi yang menggambarkan kegembiraan dan penghormatan kepada tamu.', 'Tari Tumbu Tanah merupakan tarian adat Suku Moi yang biasa ditampilkan pada acara penyambutan tamu kehormatan maupun upacara adat. Gerakannya menggambarkan hentakan kaki ke tanah sebagai simbol penghormatan terhadap alam dan leluhur. Tarian ini diiringi tifa dan nyanyian dalam bahasa Moi.', NULL, '2026-09-04 13:26:12', '2026-09-04 13:26:12'),
(2, 'Seni Ukir Suku Moi', 'Seni Ukir', 'Ukiran kayu bermotif flora dan fauna khas hutan Papua yang sarat makna filosofis.', 'Seni ukir Suku Moi umumnya diaplikasikan pada perisai, tifa, dan perahu. Motif yang digunakan terinspirasi dari alam sekitar seperti burung cenderawasih dan motif akar pohon, melambangkan hubungan erat masyarakat dengan hutan sebagai sumber kehidupan.', NULL, '2026-09-04 13:26:12', '2026-09-04 13:26:12'),
(3, 'Upacara Adat Injambik', 'Upacara Adat', 'Ritual adat Suku Moi terkait siklus kehidupan dan penghormatan terhadap leluhur.', 'Upacara adat Suku Moi dilaksanakan dalam berbagai momen penting seperti pernikahan adat, penyambutan panen, maupun peringatan leluhur. Upacara ini dipimpin oleh kepala adat dan melibatkan seluruh anggota kampung sebagai bentuk solidaritas sosial.', NULL, '2026-09-04 13:26:12', '2026-09-04 13:26:12'),
(4, 'Tari Uji Coba Galeri', 'Tarian Tradisional', 'Entri uji coba untuk fitur galeri multi-gambar.', '<p>Konten uji coba untuk memverifikasi fitur galeri foto dan slider Swiper pada halaman budaya.</p>', '1789940337.168663_hero.jpg', '2026-09-21 06:38:57', '2026-09-21 06:38:57');

-- --------------------------------------------------------

--
-- Table structure for table `budaya_galeri`
--

CREATE TABLE `budaya_galeri` (
  `id` int NOT NULL,
  `budaya_id` int NOT NULL,
  `gambar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `budaya_galeri`
--

INSERT INTO `budaya_galeri` (`id`, `budaya_id`, `gambar`, `created_at`) VALUES
(1, 4, '1789940337.170751_wisata.jpg', '2026-09-21 06:38:57'),
(2, 4, '1789940337.170751_hero.jpg', '2026-09-21 06:38:57');

-- --------------------------------------------------------

--
-- Table structure for table `knowledge_docs`
--

CREATE TABLE `knowledge_docs` (
  `id` int NOT NULL,
  `nama_file` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipe_file` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `path_file` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status_indexed` tinyint(1) DEFAULT '0',
  `uploaded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `knowledge_docs`
--

INSERT INTO `knowledge_docs` (`id`, `nama_file`, `tipe_file`, `path_file`, `status_indexed`, `uploaded_at`) VALUES
(2, 'untukchtbot.pdf', 'pdf', '1789886742_untukchtbot.pdf', 1, '2026-09-20 15:45:42');

-- --------------------------------------------------------

--
-- Table structure for table `ratings`
--

CREATE TABLE `ratings` (
  `id` int NOT NULL,
  `wisata_id` int NOT NULL,
  `skor_bintang` tinyint NOT NULL,
  `komentar` text COLLATE utf8mb4_unicode_ci,
  `ip_address_hash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status_tampil` enum('approved','pending','rejected') COLLATE utf8mb4_unicode_ci DEFAULT 'approved',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ;

--
-- Dumping data for table `ratings`
--

INSERT INTO `ratings` (`id`, `wisata_id`, `skor_bintang`, `komentar`, `ip_address_hash`, `status_tampil`, `created_at`) VALUES
(5, 9, 5, 'wisata ini sangat bagus untuk liburan', '923aaa05bc8579d553974db687c3efdbddf4d204860ae5a376219a991bb5f4aa', 'approved', '2026-09-21 09:24:17'),
(6, 12, 5, 'bagus sekali ini', '923aaa05bc8579d553974db687c3efdbddf4d204860ae5a376219a991bb5f4aa', 'approved', '2026-09-21 10:07:33');

-- --------------------------------------------------------

--
-- Table structure for table `wisata`
--

CREATE TABLE `wisata` (
  `id` int NOT NULL,
  `nama_wisata` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `wilayah` enum('Kota Sorong','Kabupaten Sorong') COLLATE utf8mb4_unicode_ci NOT NULL,
  `deskripsi` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fasilitas` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `alamat` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tiket_masuk` text COLLATE utf8mb4_unicode_ci,
  `jam_operasional` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT 'Setiap Hari',
  `gambar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `latitude` decimal(10,7) DEFAULT NULL,
  `longitude` decimal(10,7) DEFAULT NULL,
  `sosmed_email` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sosmed_facebook` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sosmed_instagram` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sosmed_youtube` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `wisata`
--

INSERT INTO `wisata` (`id`, `nama_wisata`, `wilayah`, `deskripsi`, `fasilitas`, `alamat`, `tiket_masuk`, `jam_operasional`, `gambar`, `latitude`, `longitude`, `sosmed_email`, `sosmed_facebook`, `sosmed_instagram`, `sosmed_youtube`, `created_at`, `updated_at`) VALUES
(1, 'Tanjung Batu', 'Kabupaten Sorong', 'Kawasan tebing batu karang yang menjorok ke laut dengan pemandangan matahari terbenam yang memukau.', 'Area parkir, warung makan, gazebo, spot foto', 'Distrik Makbon, Kabupaten Sorong', 'Rp 10.000', '08.00 - 18.00 WIT', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-09-04 13:26:12', '2026-09-04 13:26:12'),
(8, 'Pulau Um', 'Kabupaten Sorong', '<p>Pulau Um adalah destinasi wisata eksotis di kawasan <strong>Kabupaten Sorong</strong> yang menawarkan panorama laut jernih dan pasir putih.</p><p>Cocok untuk kegiatan:</p><ul><li>Snorkeling di sekitar terumbu karang</li><li>Bersantai di dermaga kayu</li><li>Fotografi lanskap pulau</li></ul><p>Akses menuju pulau ditempuh dengan perahu dari dermaga terdekat.</p>', 'Snorkeling, dermaga', 'Distrik Mayamuk, Kabupaten Sorong', 'Gratis / Menyesuaikan', 'Setiap Hari', '1789928238.41312_pulau_um_1.jpg', -0.7365560, 131.5836390, NULL, NULL, NULL, NULL, '2026-09-20 16:32:47', '2026-09-22 15:12:10'),
(9, 'Pulau Yerusel', 'Kabupaten Sorong', 'Pulau dengan hutan mangrove dan pantai pasir putih yang cocok untuk snorkeling, berenang, dan berjemur. Perairan di sekitar pulau ini menjadi habitat ikan badut yang cantik, menjadikannya destinasi favorit island hopping singkat dari Aimas.', 'Gazebo, kursi panjang yang bisa disewa, warung makan warga Kampung Arar, toilet.', 'Distrik Mayamuk, Kabupaten Sorong (±30 menit dari Aimas ke Pelabuhan ASDP, lalu menyeberang ±10 menit dengan perahu)', 'Rp30.000/orang (perahu dari Dermaga ASDP) + Rp5.000/orang (tiket masuk pulau)', 'Setiap Hari', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-09-20 16:32:47', '2026-09-20 16:32:47'),
(10, 'Pulau Sisi', 'Kabupaten Sorong', 'Destinasi camping ground di sebuah pulau kecil yang menawarkan pengalaman berkemah nyaman di tengah keindahan alam, lengkap dengan kuliner khas yang jarang dijumpai di wilayah Sorong lainnya.', 'Puluhan tenda (kapasitas 3 orang/tenda), layanan antar-jemput oleh pengelola, paket makanan & camilan.', 'Warmon, Kec. Aimas, Kabupaten Sorong, Papua Barat Daya', 'Paket berkemah Rp250.000 atau Rp500.000/paket (min. 10 orang, termasuk tenda & makan)', 'Setiap Hari', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-09-20 16:32:47', '2026-09-20 16:32:47'),
(11, 'Pulau Raam (Pulau Buaya)', 'Kota Sorong', 'Pulau kelurahan yang dijuluki Pulau Buaya karena bentuknya menyerupai seekor buaya jika dilihat dari udara. Hanya berjarak sekitar 2 km dari daratan Kota Sorong, pulau berpenghuni ini menawarkan pantai pasir putih dengan air laut jernih bergradasi hijau toska dan ombak tenang yang aman untuk berenang dan piknik keluarga.', 'Banana boat, donut boat, perahu karet dayung, flying fish, sewa alat snorkeling & diving, outbound & paintball, sewa ATV, gazebo, cottage (termasuk water cottage), kafe/kedai makan, dermaga tambatan perahu, musala, toilet.', 'Distrik Sorong Kepulauan, Kota Sorong (naik perahu taksi laut/jonson dari Pelabuhan Rakyat Sorong atau Dermaga Tradisional Rufei, ±10-15 menit)', 'Gratis masuk; sewa gazebo Rp50rb-100rb; wahana air Rp25rb-35rb/orang; ATV Rp50rb-100rb', 'Setiap Hari', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-09-20 16:32:47', '2026-09-20 16:32:47'),
(12, 'Pulau Soop', 'Kota Sorong', 'Pulau eksotis seluas sekitar 2,6 km² yang populer untuk island hopping atau one day trip. Dikelilingi pasir putih dan laut biru kehijauan yang jernih, pulau ini juga menyimpan jejak sejarah tersembunyi berupa situs goa pertahanan Jepang, sumur peninggalan Belanda, dan kawasan Tanjung Lampu.', 'Gazebo dan toilet umum yang dikelola swadaya oleh warga setempat.', 'Distrik Sorong Kepulauan, Kota Sorong (naik perahu dari dermaga tradisional daratan Sorong atau dekat Halte Doom, ±15-30 menit)', 'Gratis masuk; penyeberangan Rp15rb-20rb/orang; charter satu kapal PP Rp250rb-400rb', 'Setiap Hari', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-09-20 16:32:47', '2026-09-20 16:32:47');

-- --------------------------------------------------------

--
-- Table structure for table `wisata_galeri`
--

CREATE TABLE `wisata_galeri` (
  `id` int NOT NULL,
  `wisata_id` int NOT NULL,
  `gambar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `wisata_galeri`
--

INSERT INTO `wisata_galeri` (`id`, `wisata_id`, `gambar`, `created_at`) VALUES
(1, 8, '1789928238.41312_pulau_um_3.jpg', '2026-09-21 03:17:18'),
(2, 8, '1789928238.41312_pulau_um_2.jpg', '2026-09-21 03:17:18');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `budaya`
--
ALTER TABLE `budaya`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `budaya_galeri`
--
ALTER TABLE `budaya_galeri`
  ADD PRIMARY KEY (`id`),
  ADD KEY `budaya_id` (`budaya_id`);

--
-- Indexes for table `knowledge_docs`
--
ALTER TABLE `knowledge_docs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `ratings`
--
ALTER TABLE `ratings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_user_wisata_rating` (`wisata_id`,`ip_address_hash`);

--
-- Indexes for table `wisata`
--
ALTER TABLE `wisata`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `wisata_galeri`
--
ALTER TABLE `wisata_galeri`
  ADD PRIMARY KEY (`id`),
  ADD KEY `wisata_id` (`wisata_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `budaya`
--
ALTER TABLE `budaya`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `budaya_galeri`
--
ALTER TABLE `budaya_galeri`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `knowledge_docs`
--
ALTER TABLE `knowledge_docs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `ratings`
--
ALTER TABLE `ratings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `wisata`
--
ALTER TABLE `wisata`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `wisata_galeri`
--
ALTER TABLE `wisata_galeri`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `budaya_galeri`
--
ALTER TABLE `budaya_galeri`
  ADD CONSTRAINT `budaya_galeri_ibfk_1` FOREIGN KEY (`budaya_id`) REFERENCES `budaya` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `ratings`
--
ALTER TABLE `ratings`
  ADD CONSTRAINT `ratings_ibfk_1` FOREIGN KEY (`wisata_id`) REFERENCES `wisata` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `wisata_galeri`
--
ALTER TABLE `wisata_galeri`
  ADD CONSTRAINT `wisata_galeri_ibfk_1` FOREIGN KEY (`wisata_id`) REFERENCES `wisata` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
