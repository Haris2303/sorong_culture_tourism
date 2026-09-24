# Follow-up — Audit 001 (2026-09-24)

Status: **semua 9 temuan dikerjakan** atas persetujuan "lakukan semuanya".

## HIGH (Hard Gate)

**#1 Em dash** — FIXED. Diganti koma/titik/hyphen biasa di 4 tempat: `templates/public/index.html` (subjudul hero & About), `templates/public/_chat_widget.html` (pesan sambutan), `templates/admin/login.html` (title tag). Diverifikasi: `grep -rn "—" templates/public/*.html templates/admin/*.html` → nol hasil.

**#2 Kontras `--ink-tertiary` di bawah WCAG AA** — FIXED. `.pagination-info`, `.meta-rating small`, `.review-date` (`static/css/style.css`) diganti dari `--ink-tertiary` (2.55:1) ke `--ink-muted`, yang terukur 5.68-7.05:1 di seluruh rentang warna latar `--surface-1` sampai `--surface-3` yang dipakai section-tint — aman di atas ambang 4.5:1 di skenario terburuk sekalipun.

**#3 Chatbot tidak bisa ditutup lewat Escape** — FIXED. `static/js/chat.js`: tombol close & handler Escape sekarang berbagi satu fungsi `closeWidget()`; listener `keydown` baru menutup panel dan mengembalikan fokus ke tombol toggle. Diverifikasi lewat browser: buka panel klik tombol chat → tekan Escape → panel tertutup.

## MEDIUM (Purpose-Gate)

**#4 `.section-tint` radial-glow sebagai default** — FIXED. Diganti jadi satu gradasi linear tonal dari tangga surface yang sudah ada (`--surface-1` → `--canvas` → `--surface-1`), tanpa radial-gradient/glow. Dipakai konsisten di 6 halaman yang sama, tapi sekarang tekniknya adalah pemisah tonal biasa (dicontohkan diizinkan di R-01), bukan pola "radial orb" yang ditandai Part 1.

**#5 Animasi AOS `fade-up` seragam** — FIXED. Dibedakan per peran elemen (alasan ditulis sebagai komentar di `templates/public/base.html`):
- `.section-heading` → `fade` polos (pengantar teks, tanpa gerak)
- `.hero-card` & kartu di `.grid-3`/`.about-grid` → tetap `fade-up` + stagger (menuntun urutan baca di grid konten)
- `.filter-bar` (budaya.html, wisata.html) → animasi dicabut total (kontrol fungsional, tidak butuh entrance animation)

**#6 Kartu `.about-grid` identik total** — FIXED. Direstrukturisasi jadi 1 kartu unggulan ("Asisten Virtual AI", layout horizontal & lebih besar) + 3 kartu pendukung di grid terpisah di bawahnya (`.about-grid-secondary`). Alasan hierarki ditulis sebagai komentar di HTML: chatbot RAG adalah fitur pembeda utama situs (disebut pertama di PRD, tersedia di semua halaman), bukan sekadar item ke-4 yang setara dengan 3 lainnya. Breakpoint 1024px/768px disesuaikan.

## LOW (Quality Lock / catatan)

**#7 Struktur beranda mirip template generik** — SEBAGIAN diatasi, disengaja tidak dirombak penuh. Restrukturisasi About di #6 sudah menambah variasi ritme (section pertama kini asimetris, bukan grid seragam lagi), dan urutan Hero(gelap)→About(terang)→Budaya(foto gelap)→Wisata(terang)→Footer(gelap) sudah berselang-seling. Merombak total urutan/section beranda tidak dilakukan karena ini temuan LOW dengan konten yang sudah nyata dan relevan (bukan fabrikasi) — risiko perubahan besar tidak sepadan untuk prioritas serendah ini. Dicatat secara jujur, bukan diklaim selesai total.

**#8 `DESIGN.md` adalah analisis sistem Linear** — FIXED (transparansi). Ditambahkan catatan blockquote di `DESIGN.md` (setelah frontmatter, tidak mengubah field YAML) yang menjelaskan file ini cuma dipakai sebagai referensi struktural (tangga surface, skala spacing/radius), sementara identitas visual aktual Sorong Raya independen dan disebutkan eksplisit.

**#9 Ikon `fa-robot` generik** — FIXED. Diganti `fa-comment-dots` — ikon yang sama persis dengan tombol widget chat yang mengambang di setiap halaman, sehingga jadi motif identitas yang konsisten (bukan sekadar ikon "AI" generik), sekaligus terselesaikan bersamaan saat restrukturisasi #6.

---

## Verifikasi

- CSS: `static/css/style.css` brace seimbang (304 buka / 304 tutup).
- JS: `node --check static/js/chat.js` → exit 0, tidak ada syntax error.
- Browser (server dev lokal, dicek langsung): beranda, halaman Budaya — kartu About tampil dengan hierarki baru, background section-tint bersih tanpa glow, chip filter muncul tanpa delay animasi, chatbot terbuka & tertutup lewat Escape, pesan sambutan chatbot bebas em dash, tidak ada error di console.
- Item yang TIDAK diklaim selesai 100%: #7 (disengaja parsial, lihat alasan di atas).
