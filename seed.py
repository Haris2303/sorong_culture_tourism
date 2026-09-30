"""Seeder data untuk pengembangan lokal (Sorong Culture Tourism).

Berisi data budaya Suku Moi (Malamoi) dan destinasi wisata Kabupaten & Kota
Sorong, supaya tidak perlu isi manual satu-per-satu lewat form admin setiap
kali butuh database yang terisi (mis. setelah `schema.sql` baru diimpor).

Kolom `konten_lengkap` (budaya) dan `deskripsi` (wisata) berisi HTML sederhana
(p, h3, strong, em, ul/ol/li, blockquote) supaya tampil berformat di website,
sama seperti hasil editor rich text di form admin.

Aman dijalankan berkali-kali: data yang judul/namanya sudah ada otomatis
dilewati (tidak dobel).

Pemakaian:
    python seed.py                        # isi budaya + wisata
    python seed.py --only budaya           # hanya isi target tertentu
    python seed.py --reset                 # kosongkan dulu tabel yang di-seed, baru isi ulang
    python seed.py --reset --only wisata -y  # reset tanpa tanya konfirmasi

Menambah data baru:
    1. Salin satu blok dict(...) di BUDAYA_SEED / WISATA_SEED, lalu ubah isinya.
       Nama field salah ketik akan ditolak dengan pesan jelas saat seeding.
    2. `judul` (budaya) dan `nama_wisata` (wisata) harus unik, karena itu kunci
       pengecekan duplikat.
    3. Jalankan `python seed.py --only budaya` (atau wisata). Data lama dilewati,
       hanya data baru yang masuk.
"""
import argparse

from app import app
from core import db as dbcore
from models import budaya as budaya_model
from models import wisata as wisata_model

# ---------------------------------------------------------------------------
# BUDAYA (Suku Moi / Malamoi)
# konten_lengkap = HTML. Tiap baris string di bawah otomatis disambung jadi satu.
# ---------------------------------------------------------------------------
BUDAYA_SEED = [
    dict(
        judul="Malamoi: Tanah, Gunung, dan Asal Usul Suku Moi",
        kategori="Sejarah & Identitas",
        ringkasan="Malamoi adalah negeri asal Suku Moi, tempat dua kekuatan keramat, Tamrau dan Maladofok, dipercaya melahirkan peradaban yang kemudian menyebar hingga pesisir dan kepulauan.",
        konten_lengkap=(
            "<p>Dalam bahasa Moi, <em>Mala</em> merujuk pada gunung atau daratan luas. Dari kata itulah lahir nama <strong>Malamoi</strong>, tanah asal salah satu suku terbesar di Papua Barat Daya.</p>"
            "<blockquote>Legenda tua menyebut peradaban awal Moi berakar pada dua kekuatan keramat: <strong>Tamrau</strong> (kekuatan laki-laki) dan <strong>Maladofok</strong> (kekuatan perempuan).</blockquote>"
            "<p>Dari pegunungan itu, orang Moi bergerak turun ke dataran rendah, pesisir, hingga pulau-pulau.</p>"
            "<h3>Di Mana Orang Moi Tinggal</h3>"
            "<ul>"
            "<li>Kota Sorong (dalam tuturan adat disebut <em>Maladum</em>, “dataran luas tempat tumbuhnya dum”)</li>"
            "<li>Kabupaten Sorong</li>"
            "<li>Kabupaten Sorong Selatan</li>"
            "<li>Kabupaten Raja Ampat</li>"
            "<li>Bagian barat Kabupaten Tambrauw</li>"
            "</ul>"
            "<h3>Sembilan Sub-Suku</h3>"
            "<p>Moi Kelin, Klabra, Karon, Lamas, Legin, Maya, Moraid, Salkma, dan Segin. Mata pencarian utama mereka adalah berkebun dan mengelola hutan, dan para pemuda dahulu ditempa di rumah adat bernama <strong>Kambik</strong>.</p>"
        ),
    ),
    dict(
        judul="Neulig dan Nesaf: Cara Suku Moi Modern Terbentuk",
        kategori="Sejarah & Identitas",
        ringkasan="Suku Moi modern lahir dari perjumpaan \"tuan tanah\" asli dengan para pendatang pesisir, dua kelompok yang memilih untuk saling membuka diri.",
        konten_lengkap=(
            "<p>Kisah asal-usul Suku Moi bermula dari <strong>Klawelem di Makbon</strong>. Penduduk pertamanya disebut <em>neulig</em>, “tuan tanah”. Belakangan datang kelompok lain, <em>nesaf</em>, yang terutama menetap di wilayah pesisir.</p>"
            "<p>Kedua kelompok tidak saling menutup diri. Mereka berbaur dan kawin campur, dan dari percampuran itulah <strong>Suku Moi modern</strong> lahir.</p>"
            "<h3>Jejak dalam Nama Marga (Gelet)</h3>"
            "<ul>"
            "<li>Manggapraw menjadi <strong>Manggablaw</strong></li>"
            "<li>Arfayan menjadi <strong>Arfan</strong></li>"
            "</ul>"
            "<blockquote>Sejarah Moi, dengan kata lain, adalah sejarah keterbukaan.</blockquote>"
        ),
    ),
    dict(
        judul="Fun Mo dan Kerajaan Sailolof",
        kategori="Sejarah & Identitas",
        ringkasan="Kisah lisan tentang fun Mo, \"raja orang Moi\" yang lahir dari telur baykole dan mendirikan Kerajaan Sailolof di Raja Ampat.",
        konten_lengkap=(
            "<p>Tidak semua kerajaan di Raja Ampat berasal dari garis raja Waigeo, Salawati, atau Misool. <strong>Sailolof</strong> didirikan oleh tokoh Moi bernama <strong>fun (raja) Mo</strong>.</p>"
            "<h3>Kisah Lisan</h3>"
            "<ol>"
            "<li>Ia berasal dari sekitar sungai <em>Malyat</em>, lahir dari telur <em>baykole</em>, dan dibesarkan dengan air tebu, sehingga dinamai <strong>Ulbisi</strong>.</li>"
            "<li>Ia diangkat dengan gelar <strong>fun Mo</strong>, “raja orang Moi”, di pulau Sabba.</li>"
            "<li>Ia menikahi <em>Pinfun Libit</em>, putri raja Waigeo yang terdampar di dekat Sabba bersama dua pembantunya.</li>"
            "<li>Ia pindah ke selatan Pulau Salawati, ke tempat yang kemudian disebut <strong>Sailolof</strong>.</li>"
            "</ol>"
            "<blockquote>Keturunannya memerintah Sailolof dan menyandang gelar Kapita-laut atau Kapatla, gelar yang diperoleh dari hubungan perdagangan dengan Kesultanan Tidore.</blockquote>"
        ),
    ),
    dict(
        judul="Enso-Enso: Pemuda Moi dalam Operasi Trikora",
        kategori="Sejarah & Identitas",
        ringkasan="Pemuda-pemuda Moi ikut menyuplai kantong gerilya di sekitar Sorong bagi pasukan infiltran Trikora, yang dalam bahasa Moi disebut Enso-Enso.",
        konten_lengkap=(
            "<p>Di balik Operasi Trikora di sekitar Sorong, ada peran senyap para <strong>pemuda Moi</strong>. Bersama <em>Simon Randa</em>, seorang Toraja pegawai pemerintah Belanda, mereka menyuplai kantong-kantong gerilya yang dihuni pasukan infiltran Trikora, yang dalam bahasa Moi disebut <strong>Enso-Enso</strong>.</p>"
            "<ul>"
            "<li>Nama-nama mereka tercatat, dari keluarga <strong>Osok</strong>, <strong>Malibela</strong>, dan <strong>Kalaibin</strong>, hingga Jonas Satisa dan Hermanus Mili.</li>"
            "<li>Peninggalan perjuangan itu berupa sebuah rumah di <strong>km 12 Klasaman, Sorong</strong>.</li>"
            "</ul>"
        ),
    ),
    dict(
        judul="Peta Sub-Suku dan Wilayah Adat Moi",
        kategori="Sejarah & Identitas",
        ringkasan="Sembilan sub-suku Moi tersebar dari pegunungan Tambrauw hingga pulau-pulau Raja Ampat, dibedakan oleh dialek dan corak geografis.",
        konten_lengkap=(
            "<p>Bagi orang Moi, tanah adalah <strong>hak ulayat yang bersifat komunal</strong>, walaupun pemanfaatannya bisa individual atau bersama: untuk beternak, pasar, dusun adat, hingga tanah membangun kampung (<em>iik fagu</em>).</p>"
            "<h3>Kabupaten Sorong</h3>"
            "<ul>"
            "<li><strong>Moi Klabra:</strong> bagian selatan dan tengah</li>"
            "<li><strong>Moi Segin:</strong> selatan, berbatasan dengan Sorong Selatan</li>"
            "<li><strong>Moi Moraid:</strong> pesisir utara (sekitar Makbon)</li>"
            "<li><strong>Moi Madik / Moi Salkma:</strong> utara hingga timur, berbatasan dengan Tambrauw</li>"
            "<li><strong>Moi Seget dan Moi Lemas:</strong> barat daya (Distrik Seget dan sekitarnya)</li>"
            "</ul>"
            "<h3>Wilayah Lain</h3>"
            "<ul>"
            "<li><strong>Kota Sorong:</strong> Moi Kelin (Sorong Timur, Barat, Utara, Kota, Manoi, Maladummes, dan sekitarnya)</li>"
            "<li><strong>Raja Ampat:</strong> Suku Matbat di Pulau Misool bagian selatan, timur, dan utara; serta Moi Maya, yang kini sering dipandang sebagai suku tersendiri dengan marga maritimnya</li>"
            "<li><strong>Tambrauw bagian barat:</strong> Moi Abun, Moi Karon, dan Moi Salkma</li>"
            "<li><strong>Sorong Selatan:</strong> Moi Segin dan sebagian Moi Klabra, hingga berbatasan dengan wilayah adat Imeko/Inanwatan</li>"
            "</ul>"
            "<p>Moi Segin menghuni zona perbatasan yang sebagian besar berupa hutan tropis pedalaman dan aliran muara sungai.</p>"
            "<blockquote>Para ahli adat mengenali sekitar 7 sampai 10 sub-suku besar, dibedakan oleh dialek dan kondisi geografis: Moi pesisir/bahari seperti Maya dan Moraid, serta Moi darat/hutan seperti Klabra dan Abun.</blockquote>"
        ),
    ),
    dict(
        judul="Bahasa Moi, Matbat, dan Segin: Satu Wilayah, Banyak Suara",
        kategori="Sejarah & Identitas",
        ringkasan="Bahasa di wilayah Moi terbelah dua rumpun besar, dan penuturnya tidak selalu saling memahami.",
        konten_lengkap=(
            "<p>Peta bahasa di Malamoi ternyata lebih rumit daripada peta wilayahnya. Bahasa di sini terbelah menjadi <strong>dua rumpun besar</strong>.</p>"
            "<h3>Rumpun Austronesia: Bahasa Matbat</h3>"
            "<ul>"
            "<li>Dituturkan penduduk asli Pulau Misool, Raja Ampat.</li>"
            "<li>Punya <strong>sistem nada</strong>: makna kata bisa berubah total bergantung tinggi-rendah intonasi.</li>"
            "<li>Tidak dapat dipahami penutur dari daratan Sorong.</li>"
            "</ul>"
            "<h3>Rumpun Non-Austronesia: Moi Klabra dan Moi Segin</h3>"
            "<ul>"
            "<li>Termasuk keluarga bahasa <em>Kepala Burung Barat (West Bird's Head)</em>.</li>"
            "<li><strong>Moi Klabra</strong> adalah ragam dari bahasa besar Moi. Penuturnya masih memahami sebagian besar kosakata Moi Kelin di Kota Sorong.</li>"
            "<li><strong>Moi Segin</strong> berkembang menjadi isolek mandiri. Karena terpencil di pedalaman selatan perbatasan Sorong Selatan, kosakatanya cukup jauh berbeda dari ragam Moi perkotaan.</li>"
            "</ul>"
        ),
    ),
    dict(
        judul="Golongan dan Tokoh Adat Suku Moi",
        kategori="Struktur & Hukum Adat",
        ringkasan="Masyarakat Moi mengikuti garis patrilineal dan mengenal empat peran tokoh adat: penjaga sejarah, dukun, juru bicara, dan orang terhormat.",
        konten_lengkap=(
            "<p>Masyarakat Moi mengikuti <strong>garis keturunan pihak ayah (patrilineal)</strong>. Secara tradisional mereka terbagi menjadi tiga golongan.</p>"
            "<ol>"
            "<li><em>Ne folus</em>, orang yang berpengetahuan</li>"
            "<li>Golongan menengah, dengan pengetahuan terbatas</li>"
            "<li>Golongan yang dalam struktur lama ditempati kaum perempuan</li>"
            "</ol>"
            "<p>Hak-hak khusus, seperti menjabat tetua adat dan memiliki tanah, melekat pada laki-laki. Pengecualiannya adalah <strong>Moi Ma'ya</strong>, yang strukturnya lebih sejajar antara perempuan dan laki-laki karena pengaruh Suku Ma'ya.</p>"
            "<h3>Empat Peran Tokoh Adat</h3>"
            "<ul>"
            "<li><strong>Ne fulus:</strong> penjaga pengetahuan sejarah</li>"
            "<li><strong>Ne foos:</strong> orang berkekuatan gaib (dukun)</li>"
            "<li><strong>Ne ligin:</strong> sang pembicara</li>"
            "<li><strong>Ne kook:</strong> orang kaya yang terhormat</li>"
            "</ul>"
            "<blockquote>Meski struktur formalnya demikian, perempuan Moi tetap memegang peran penting dalam pengetahuan pangan dan obat-obatan tradisional.</blockquote>"
        ),
    ),
    dict(
        judul="Kambik: Sekolah Adat di Jantung Hutan",
        kategori="Upacara & Ritual Adat",
        ringkasan="Kambik adalah sekolah adat berjenjang tempat pemuda Moi belajar berburu, berkebun, mengobati, berperang, dan menjalankan hukum adat.",
        konten_lengkap=(
            "<p>Seorang anak laki-laki Moi (<em>nedla</em>) tidak otomatis dianggap pria dewasa. Ia harus lebih dulu menjadi siswa (<em>ulibi</em>) di rumah <strong>Kambik</strong>, sekolah adat berjenjang seperti pendidikan formal.</p>"
            "<h3>Jenjang Pendidikan</h3>"
            "<ol>"
            "<li><strong>Ulibi</strong> (setingkat SD): gelar <em>unsulu</em>. Lama 6 sampai 12 bulan.</li>"
            "<li><strong>Unsmas</strong> (setingkat SMP dan SMA): gelar <em>tulukma</em>. Lama 6 sampai 12 bulan.</li>"
            "<li><strong>Untlan / kmabiek</strong> (setara perguruan tinggi): gelar <em>wariek</em>, <em>sukmin</em>, dan <em>tukan</em> (untuk menjadi guru Kambik). Bisa sampai 18 bulan.</li>"
            "</ol>"
            "<h3>Tiga Jalan Menjadi Siswa</h3>"
            "<ul>"
            "<li>Dicuri (lalu dikembalikan ke keluarga setelah selesai)</li>"
            "<li>Dipilih secara adat, biasanya anak sulung</li>"
            "<li>Menjadi perwakilan, saat anak dititipkan ke marga lain dengan pembayaran kain timur</li>"
            "</ul>"
            "<h3>Yang Diajarkan</h3>"
            "<ul>"
            "<li><strong>Berburu:</strong> membaca arah angin, jenis dan lokasi hewan</li>"
            "<li><strong>Bercocok tanam:</strong> menebang dan mengawetkan sagu dengan tanah dan mantra</li>"
            "<li><strong>Kesehatan:</strong> obat dari dedaunan, kulit kayu, buah, dan bara api</li>"
            "<li><strong>Berperang:</strong> membuat tameng (<em>gili</em>) dan tombak (<em>sawiyek</em>)</li>"
            "<li><strong>Hukum adat:</strong> sistem perkawinan dan pembayaran adat bagi orang yang meninggal</li>"
            "</ul>"
            "<blockquote>Kambik adalah ruang sakral yang hanya boleh diikuti laki-laki. Tradisi ini meredup karena masuknya Belanda (lapangan kerja seperti NNGPM bagi para pemuda), ajaran Kristen, dan Perang Dunia II. Upaya menghidupkannya kembali difasilitasi LMA Moi di Maladofok, tempat sakral Suku Moi.</blockquote>"
        ),
    ),
    dict(
        judul="Sagu, Hutan, dan Meja Makan Orang Moi",
        kategori="Kearifan Lokal & Lingkungan",
        ringkasan="Budaya pangan Moi bertumpu pada sagu dan hasil hutan, dan kini tergerus oleh alih fungsi lahan serta pergeseran ke nasi dan mi instan.",
        konten_lengkap=(
            "<p>Meja makan orang Moi adalah <strong>cermin hutannya</strong>. Sagu menjadi makanan pokok, ditemani pisang, kasbi, keladi, sayur gedi, dan pakis. Semua berasal dari dusun, kebun, dan hutan adat yang bagi mereka bukan sekadar sumber pangan, melainkan bagian dari identitas.</p>"
            "<p>Perempuan Moi memegang peran kunci: meramu, berkebun, dan mengolah hasil hutan menjadi makanan sekaligus obat tradisional.</p>"
            "<h3>Tekanan pada Budaya Pangan</h3>"
            "<ul>"
            "<li>Perkebunan sawit dan pertambangan menggerus dusun sagu, ruang berburu, dan ruang hidup.</li>"
            "<li>Konsumsi sagu perlahan digantikan <strong>nasi dan mi instan</strong>, terutama di kalangan anak muda.</li>"
            "<li>Perempuan, penjaga budaya pangan, kerap tidak dilibatkan dalam keputusan pelepasan tanah adat kepada perusahaan.</li>"
            "</ul>"
            "<h3>Suara dari Diskusi Riset</h3>"
            "<p>Dalam diskusi hasil riset <em>Malamoi: Budaya Pangan, Tanah, dan Identitas</em> di Sorong pada <strong>17 Oktober 2025</strong>, perwakilan masyarakat adat Moi Kelim, <em>Ayub R. Paa</em>, menegaskan bahwa kehilangan tanah adat berarti kehilangan marga, budaya, dan identitas, meski Perda Kabupaten Sorong Nomor 10 Tahun 2017 telah mengakui dan melindungi masyarakat hukum adat.</p>"
            "<blockquote>Peneliti Zuhdi Siswanto menyebut putusnya relasi manusia adat dengan lingkungannya sebagai “keretakan metabolik”.</blockquote>"
        ),
    ),
    dict(
        judul="Lemek: Alat Pangkur Sagu yang Jadi Simbol",
        kategori="Pakaian & Kerajinan Adat",
        ringkasan="Lemek, atau Nani, adalah alat penokok isi batang sagu yang bagi Moi Kelim melambangkan kemandirian pangan dan kerja keras.",
        konten_lengkap=(
            "<p>Setelah pohon sagu ditebang dan dibelah kaum laki-laki, empulur batangnya masih keras dan harus dihancurkan. Untuk itulah <strong>Lemek</strong> (juga disebut <em>Nani</em>) dipakai: alat yang memahat isi batang hingga menjadi serbuk kasar yang siap diperas dan disaring untuk diambil patinya.</p>"
            "<h3>Ciri Alat</h3>"
            "<ul>"
            "<li>Panjang sekitar <strong>50 sentimeter</strong>.</li>"
            "<li>Gagang kayu bersudut lancip, mirip cangkul kecil.</li>"
            "<li>Ujung penokok dipasangi besi berbentuk lingkaran tajam dengan pengait khusus.</li>"
            "</ul>"
            "<h3>Lebih dari Alat Kerja</h3>"
            "<p>Bagi sub-suku <strong>Moi Kelim</strong>, bentuk Lemek kerap diabadikan sebagai motif kerajinan tangan yang melambangkan kemandirian pangan, kerja keras, dan kelestarian tanah ulayat.</p>"
            "<blockquote>Penokokan biasanya dilakukan bergotong royong di dusun sagu: laki-laki menokok, perempuan memeras dan mengendapkan tepung sagunya.</blockquote>"
        ),
    ),
    dict(
        judul="Tifa dan Gong Adat: Dua Denyut Musik Moi",
        kategori="Tarian & Musik Tradisional",
        ringkasan="Tifa berukir dan gong perunggu hasil barter kuno menjadi instrumen utama yang mengiringi tarian dan arak-arakan adat Suku Moi.",
        konten_lengkap=(
            "<p>Musik Moi bertumpu pada dua instrumen utama.</p>"
            "<h3>Tifa</h3>"
            "<p>Gendang kecil khas Papua yang badannya biasa dihiasi <strong>ukiran</strong> geometris atau motif flora dan fauna hutan, cermin kedekatan mereka dengan alam. Dimainkan kaum laki-laki sambil menari dalam upacara besar seperti Tari <em>Aluyen</em> dan Tari <em>Wutukala</em>.</p>"
            "<h3>Gong Adat</h3>"
            "<p>Gong perunggu kuno bukan alat musik bentukan lokal: ia diperoleh lewat barter zaman dahulu dengan pelaut Nusantara barat. Kedudukannya <strong>tinggi dan sakral</strong>. Gong wajib ditabuh berulang-ulang untuk mengiringi arak-arakan pengantin yang mengantar harta adat.</p>"
            "<blockquote>Dalam pertunjukan yang lebih santai atau ritual pembersihan, potongan bilah bambu kering kadang diketuk sebagai pelengkap irama. Tetangga Moi, Suku Tehit di Sorong Selatan, terkenal dengan alat musik bambu petik <em>Krombi</em>, tetapi bagi Moi, tifa dan gong tetap yang utama.</blockquote>"
        ),
    ),
    dict(
        judul="Tari Aluyen (Alen): Tarian Selamat Datang di Tanah Malamoi",
        kategori="Tarian & Musik Tradisional",
        ringkasan="Tarian sakral penyambutan tamu agung yang melambangkan keramahan, penghormatan, dan sukacita masyarakat adat Moi.",
        konten_lengkap=(
            "<p>Siapa pun yang pertama kali menginjak tanah Malamoi sebagai tamu kehormatan biasanya disambut <strong>Tari Aluyen</strong>, atau <em>Alen</em>. Tarian sakral ini menyimbolkan keramahan, penghormatan, dan sukacita masyarakat adat menyambut orang luar ke tanah mereka.</p>"
            "<h3>Kapan Ditampilkan</h3>"
            "<ul>"
            "<li>Menyambut tamu agung dan pejabat</li>"
            "<li>Upacara mendirikan rumah adat</li>"
            "<li>Membuka kebun baru</li>"
            "</ul>"
            "<blockquote>Di kampung adat seperti Malasigi, tamu disambut dengan tarian ini.</blockquote>"
        ),
    ),
    dict(
        judul="Tari Wutukala: Syukur dari Laut",
        kategori="Tarian & Musik Tradisional",
        ringkasan="Tarian pesisir yang menggambarkan perburuan ikan bersama, wujud syukur atas hasil laut sekaligus semangat gotong royong.",
        konten_lengkap=(
            "<p><strong>Tari Wutukala</strong> membawa laut ke atas panggung. Tarian tradisional ini menceritakan aktivitas perburuan ikan oleh masyarakat pesisir Moi.</p>"
            "<h3>Gerak dan Atribut</h3>"
            "<ul>"
            "<li><strong>Penari pria</strong> memeragakan gerakan menombak ikan dengan tombak atau panah (<em>kalawai</em>).</li>"
            "<li><strong>Penari wanita</strong> mengumpulkan hasil tangkapan ke dalam <em>noken</em>, tas rajut khas Papua.</li>"
            "<li>Iringan <strong>tifa</strong> ditabuh penari laki-laki.</li>"
            "</ul>"
            "<blockquote>Maknanya: rasa syukur kepada Tuhan atas hasil laut yang melimpah, sekaligus semangat gotong royong.</blockquote>"
        ),
    ),
    dict(
        judul="Busana dan Atribut Penari Moi",
        kategori="Pakaian & Kerajinan Adat",
        ringkasan="Serat kayu, manik-manik, bulu burung, dan lukisan tubuh dari kapur sirih dan tanah merah menyusun busana tari Moi.",
        konten_lengkap=(
            "<p>Busana penari Moi seluruhnya berbicara tentang alam.</p>"
            "<h3>Busana Utama</h3>"
            "<ul>"
            "<li><strong>Kain terfo:</strong> tenunan serat kulit kayu atau daun anyaman. Perempuan memakainya sebagai rok rumbai, laki-laki sebagai cawat atau celana adat.</li>"
            "<li><strong>Manik-manik (akes):</strong> untaian hiasan dada, dipakai penari perempuan maupun laki-laki.</li>"
            "</ul>"
            "<h3>Hiasan dan Properti</h3>"
            "<ul>"
            "<li><strong>Topi bulu burung</strong> (cenderawasih, kasuari, atau nuri): melambangkan kegagahan dan keindahan alam Papua.</li>"
            "<li><strong>Lukisan tubuh</strong> putih dan merah dari campuran kapur sirih dan arang atau tanah merah, di tubuh, wajah, tangan, dan kaki.</li>"
            "<li><strong>Tifa</strong> untuk penari laki-laki, <strong>noken</strong> untuk penari perempuan, <strong>tombak atau kalawai</strong> untuk peragaan berburu ikan.</li>"
            "</ul>"
        ),
    ),
    dict(
        judul="Kain Timur dan Kain Merah: Dua Kain, Dua Kekuatan Adat",
        kategori="Pakaian & Kerajinan Adat",
        ringkasan="Kain Timur adalah harta pusaka penentu martabat dan mas kawin, sedangkan Kain Merah adalah penanda larangan adat yang sakral.",
        konten_lengkap=(
            "<h3>Kain Timur</h3>"
            "<p>Tenun ikat prestisius yang diperoleh leluhur Moi berabad-abad lalu lewat barter lintas samudera dengan pelaut dari Maluku dan Nusa Tenggara Timur. Nilainya sangat tinggi dan dianggap <strong>harta pusaka</strong>.</p>"
            "<ul>"
            "<li>Wajib hadir sebagai <strong>mas kawin</strong> dalam pernikahan adat.</li>"
            "<li>Alat penyelesaian denda adat.</li>"
            "<li>Simbol martabat dan harga diri perempuan Moi.</li>"
            "<li>Pada penari perempuan, biasanya dililitkan di dada.</li>"
            "</ul>"
            "<h3>Kain Merah Sakral</h3>"
            "<p>Dipakai laki-laki sebagai cawat, bawahan selutut, atau selendang silang di dada. Maknanya adalah <strong>hukum</strong>:</p>"
            "<ul>"
            "<li>Diikat pada pohon di hutan: tanda larangan berburu atau mengambil hasil alam (<em>egek</em>).</li>"
            "<li>Dipasang di pintu bangunan: protes keras berupa pemalangan tanah ulayat, yang harus diselesaikan lewat hukum adat.</li>"
            "</ul>"
            "<blockquote>Selain keduanya, Moi memanfaatkan serat kulit kayu pohon Malo yang dipukul hingga tipis dan lembut untuk rok rumbai atau pakaian pelapis.</blockquote>"
        ),
    ),
    dict(
        judul="Lima Babak Pernikahan Adat Moi",
        kategori="Upacara & Ritual Adat",
        ringkasan="Pernikahan adat Moi wajib di luar marga dan berlangsung melalui lima tahap, dari peminangan hingga ritual Busbak yang mengesahkan ikatan.",
        konten_lengkap=(
            "<p>Pernikahan adat Moi diatur dengan ketat dan dipandu para tetua. Aturan dasarnya: menikah harus <strong>di luar klan (eksogami)</strong>. Prosesnya berlangsung dalam lima babak.</p>"
            "<ol>"
            "<li><strong>Peminangan (<em>Kamwafe</em>).</strong> Keluarga perempuan menyampaikan jumlah mas kawin yang harus disiapkan pihak laki-laki, dan angkanya dimusyawarahkan antar-marga sampai sepakat.</li>"
            "<li><strong>Penghiasan pengantin perempuan.</strong> Ia dimandikan kedua orang tuanya, menerima nasihat pra-nikah dari Ibu Kepala Suku, lalu dihias dengan Kain Timur, manik-manik, gelang, dan mahkota bulu burung, sementara keluarga menyanyikan lagu rakyat tentang asal-usul kedua marga.</li>"
            "<li><strong>Mengantar pengantin.</strong> Ia diantar berjalan kaki oleh saudara laki-lakinya ke rumah pihak laki-laki, diiringi tabuhan gong dan lagu pengantin sakral.</li>"
            "<li><strong>Penyerahan harta adat.</strong> Berlangsung satu sampai tiga hari untuk memeriksa kelengkapan mas kawin.</li>"
            "<li><strong>Busbak (gulung rokok).</strong> Puncak dan penutup seluruh rangkaian upacara.</li>"
            "</ol>"
            "<h3>Harta Adat yang Diserahkan</h3>"
            "<ul>"
            "<li><strong>Kain Timur:</strong> puluhan hingga ratusan lembar, sesuai kesepakatan status adat</li>"
            "<li><strong>Piring adat besar (piring batu)</strong></li>"
            "<li><strong>Noken dan tikar:</strong> dibawa pengantin perempuan untuk membina rumah tangga baru</li>"
            "</ul>"
            "<blockquote>Dalam Busbak, rokok dibakar, diisap, atau dirusak oleh pengantin perempuan, diberikan kepada pengantin pria, lalu diisap bergiliran oleh saudara perempuan mempelai pria, disertai janji adat di hadapan para tetua. Setelah itu, pernikahan sah menurut hukum adat dan ikatan kedua pihak tidak boleh dilanggar lagi.</blockquote>"
        ),
    ),
    dict(
        judul="Sanksi Adat bagi Pelanggar Janji Pernikahan",
        kategori="Struktur & Hukum Adat",
        ringkasan="Pelanggaran janji nikah diputus sidang dewan adat lewat denda harta adat, aturan mas kawin, dan sanksi sosial.",
        konten_lengkap=(
            "<p>Bagi Suku Moi, pernikahan adalah <strong>ikatan sakral antar-marga</strong>. Perselingkuhan, kekerasan dalam rumah tangga, penelantaran, atau perceraian sepihak dianggap mengacaukan keseimbangan sosial dan mencoreng harga diri keluarga, sehingga perkaranya dibawa ke sidang dewan adat.</p>"
            "<h3>Denda Harta Adat</h3>"
            "<p>Untuk memulihkan nama baik keluarga yang dirugikan. Jumlahnya ditentukan kepala adat dan korban.</p>"
            "<ul>"
            "<li>Piring gantung (piring batu)</li>"
            "<li>Kain adat</li>"
            "<li>Guci adat</li>"
            "<li>Babi, untuk upacara perdamaian</li>"
            "<li>Uang tunai, sebagai pelengkap</li>"
            "</ul>"
            "<h3>Aturan Mas Kawin</h3>"
            "<ul>"
            "<li><strong>Istri bersalah:</strong> keluarga perempuan wajib mengembalikan seluruh mas kawin yang dulu diberikan pihak laki-laki.</li>"
            "<li><strong>Suami bersalah:</strong> mas kawin dianggap hangus, dan ia sering dikenai denda tambahan untuk membiayai kepulangan istri ke rumah orang tua.</li>"
            "</ul>"
            "<h3>Sanksi Sosial dan Moral</h3>"
            "<ul>"
            "<li><strong>Pengucilan sementara:</strong> kehilangan hak berbicara dan dihormati dalam pertemuan adat sampai denda lunas.</li>"
            "<li><strong>Permohonan maaf terbuka</strong> di hadapan tetua kedua marga untuk membersihkan nama baik.</li>"
            "</ul>"
        ),
    ),
    dict(
        judul="Sidang Adat Moi: Keadilan yang Memulihkan",
        kategori="Struktur & Hukum Adat",
        ringkasan="Sidang adat yang dipimpin LMA Malamoi mengutamakan pemulihan hubungan antar-marga lewat lima tahap, dari pengaduan hingga sumpah adat Nalmsan.",
        konten_lengkap=(
            "<p>Berbeda dengan peradilan negara yang berfokus menghukum pelaku, sidang adat Moi mengutamakan <strong>pemulihan hubungan sosial</strong> dan pembersihan spiritual bagi marga yang bertikai, prinsip yang hari ini dikenal sebagai <em>restorative justice</em>. Sidang dipimpin fungsionaris adat dari <strong>Lembaga Masyarakat Adat (LMA) Malamoi</strong>.</p>"
            "<h3>Lima Tahap Sidang</h3>"
            "<ol>"
            "<li><strong>Pelaporan.</strong> Sidang tidak digelar tanpa aduan resmi ke tokoh adat atau pengurus LMA Malamoi.</li>"
            "<li><strong>Pemanggilan</strong> pelapor, terlapor, dan para saksi.</li>"
            "<li><strong>Musyawarah</strong> (<em>Kalak Foo</em> atau <em>Teh Bless</em>). Digelar di rumah adat atau balai terbuka, dipimpin Kepala Suku atau Dewan Adat. Kedua pihak menyampaikan kronologi bergantian, lalu para tetua bermusyawarah mencapai mufakat.</li>"
            "<li><strong>Putusan adat.</strong> Pelaku yang terbukti bersalah membayar denda adat (Kain Timur, piring gantung, babi, atau uang tunai) sesuai tenggat yang disepakati.</li>"
            "<li><strong>Sumpah Adat Nalmsan</strong> dan pemulihan. Pihak yang bertikai bersalaman, berpelukan, atau makan bersama sebagai tanda persaudaraan telah pulih.</li>"
            "</ol>"
            "<blockquote>Sumpah Nalmsan mengikat secara spiritual: keputusan yang dilanggar setelah sumpah dipercaya mendatangkan sanksi gaib dari leluhur.</blockquote>"
            "<h3>Hubungan dengan Hukum Negara</h3>"
            "<p>Di Sorong, hukum adat Moi diakui kuat oleh aparat. Kasus rumah tangga atau pidana yang melibatkan masyarakat asli diselesaikan secara adat terlebih dahulu, dan baru diteruskan ke jalur pidana negara bila pelaku menolak membayar denda adat.</p>"
        ),
    ),
    dict(
        judul="Kepala Adat: Hakim, Penjaga Tanah, dan Jembatan",
        kategori="Struktur & Hukum Adat",
        ringkasan="Kepala adat Moi adalah \"bapak masyarakat\" yang menjadi hakim, pelindung hak ulayat, penjaga ritual, dan penghubung dengan hukum negara.",
        konten_lengkap=(
            "<p>Dalam tatanan Malamoi, kepala adat dipandang sebagai <strong>“bapak masyarakat”</strong> yang mengayomi marga-marga di bawahnya. Perannya lima lapis:</p>"
            "<ol>"
            "<li><strong>Hakim dan pemutus peradilan adat.</strong> Memimpin sidang, mendengar kedua pihak, menentukan tingkat kesalahan berdasarkan hukum adat leluhur, dan menjatuhkan denda demi memulihkan keseimbangan sosial.</li>"
            "<li><strong>Pelindung hak ulayat.</strong> Mengawasi tanah dan hutan adat dari eksploitasi luar. Pelepasan tanah adat wajib diketahui dan disetujui langsung olehnya, dan ia memimpin sidang untuk menolak proyek yang mengancam lingkungan dan ruang hidup masyarakat.</li>"
            "<li><strong>Pengatur urusan pernikahan marga.</strong> Memastikan tidak ada pelanggaran larangan kawin satu marga, dan menjadi penengah atau saksi dalam tawar-menawar mas kawin.</li>"
            "<li><strong>Penjaga tradisi dan ritual.</strong> Memimpin ritual sakral, mengesahkan sumpah adat Nalmsan, dan memberlakukan Egek.</li>"
            "<li><strong>Jembatan dengan hukum negara.</strong> Bersama LMA Malamoi, menyuarakan aspirasi masyarakat asli ke pemerintah daerah dan pusat, serta bermitra dengan kepolisian dalam penyelesaian restorative justice.</li>"
            "</ol>"
        ),
    ),
    dict(
        judul="Pantangan Adat: Yang Tak Boleh Dilanggar Orang Moi",
        kategori="Upacara & Ritual Adat",
        ringkasan="Empat kelompok pantangan menjaga keseimbangan spiritual, kelestarian alam, dan tatanan sosial antar-marga.",
        konten_lengkap=(
            "<p>Orang Moi memegang <strong>pantangan</strong> (larangan adat) demi menjaga keseimbangan spiritual, alam, dan hubungan antar-marga. Melanggarnya dipercaya mendatangkan musibah, penyakit, atau sanksi adat yang berat.</p>"
            "<h3>Makanan bagi Perempuan</h3>"
            "<ul>"
            "<li>Perempuan dilarang makan <strong>tikus tanah</strong> dan jenis <strong>kuskus pohon</strong> tertentu, berdasarkan kepercayaan kuno tentang kesehatan reproduksi dan perlindungan spiritual.</li>"
            "</ul>"
            "<h3>Konservasi Alam (Egek)</h3>"
            "<ul>"
            "<li>Ketika tanda Egek terpasang, tak seorang pun boleh mengambil sagu, ikan, lobster, atau kayu di lokasi itu sampai upacara buka Egek.</li>"
            "<li>Merusak hutan atau menjual tanah ulayat tanpa persetujuan para tetua marga dan kepala suku dilarang keras.</li>"
            "</ul>"
            "<h3>Hubungan Sosial dan Pernikahan</h3>"
            "<ul>"
            "<li>Laki-laki dan perempuan dari satu <em>gelet</em> (marga) <strong>dilarang menikah</strong>. Pernikahan wajib di luar marga (eksogami).</li>"
            "<li>Perselingkuhan, penelantaran keluarga, dan KDRT dianggap tabu berat dan diseret ke sidang adat dengan denda yang sangat besar.</li>"
            "</ul>"
            "<h3>Ritual Sakral</h3>"
            "<ul>"
            "<li>Perempuan pantang mendekati lokasi, melihat prosesi, atau mengetahui materi rahasia <strong>pendidikan Kambik</strong>.</li>"
            "<li>Perwakilan dalam ritual rekonsiliasi seperti <em>Teh Bless</em> pantang ikut bila masih menyimpan dendam atau amarah. Hati harus bersih agar ritual berjalan sakral.</li>"
            "</ul>"
        ),
    ),
    dict(
        judul="Ketika Leluhur Menegur: Sanksi Gaib dalam Kepercayaan Moi",
        kategori="Upacara & Ritual Adat",
        ringkasan="Dalam kepercayaan Malamoi, pelanggaran adat tidak hanya berujung denda, tetapi juga sanksi gaib dari leluhur dan alam yang bekerja secara otomatis.",
        konten_lengkap=(
            "<p>Bagi orang Moi, hukum adat bukan hanya urusan manusia. Ia dilindungi <strong>leluhur (spirit) dan kekuatan alam</strong>, sehingga pelanggaran dipercaya membawa konsekuensi spiritual yang nyata dan bekerja secara otomatis.</p>"
            "<h3>Bentuk Sanksi Gaib</h3>"
            "<ul>"
            "<li><strong>Melanggar pantangan makanan perempuan:</strong> gangguan kesehatan reproduksi (kesulitan melahirkan, pendarahan hebat) dan dampak pada keturunan.</li>"
            "<li><strong>Mengingkari sumpah Nalmsan:</strong> penyakit misterius yang tak tersembuhkan medis, bahkan kematian mendadak, atau kemalangan beruntun (<em>kena sasi</em>).</li>"
            "<li><strong>Melanggar Egek:</strong> tersesat di hutan, gigitan hewan berbisa, tenggelam misterius saat melaut, atau hilangnya rezeki karena roh penjaga alam menyembunyikan hasil bumi.</li>"
            "<li><strong>Menikah satu marga (gelet):</strong> tabu terbesar. Sanksinya dipercaya menimpa seluruh kampung: gagal panen massal (dusun sagu rusak), wabah penyakit, serta pasangan yang mandul atau melahirkan keturunan yang memikul kutukan.</li>"
            "</ul>"
            "<blockquote>Keyakinan inilah yang membuat masyarakat adat Moi sangat patuh pada aturan tetua: hukum adat mereka percaya dijaga kekuatan yang jauh lebih besar dari sekadar hukum manusia.</blockquote>"
        ),
    ),
    dict(
        judul="Tam Sini: Hutan adalah Ibu Kandung",
        kategori="Kearifan Lokal & Lingkungan",
        ringkasan="Filosofi Tam Sini memandang hutan sebagai ibu yang menyusui dan alam sebagai kerabat, dengan prinsip mengambil secukupnya.",
        konten_lengkap=(
            "<p>Bagi Suku Moi, alam bukan komoditas dan bukan sekadar latar. Ia kerabat dan ruang hidup yang sakral. Inti filosofinya terangkum dalam dua kata: <strong>Tam Sini</strong>, “hutan adalah ibu kandung”.</p>"
            "<h3>Hutan sebagai Ibu yang Menyusui</h3>"
            "<ul>"
            "<li><strong>Pangan dan air:</strong> sagu, buah hutan, air bersih</li>"
            "<li><strong>Obat-obatan:</strong> tanaman herbal yang diracik perempuan Moi</li>"
            "<li><strong>Sandang dan papan:</strong> serat kulit kayu untuk noken dan pakaian, kayu untuk rumah</li>"
            "</ul>"
            "<blockquote>Menjual atau merusak hutan sama saja dengan menjual atau melukai tubuh mama kandung sendiri. Kehilangan hutan berarti kehilangan identitas, marga, dan budaya.</blockquote>"
            "<h3>Alam sebagai Kerabat</h3>"
            "<p>Manusia tidak berada di atas alam, melainkan hidup berdampingan setara dengan makhluk lain. Orang Moi membaca arah angin sebagai penanda pergantian musim, dan suara burung tertentu sebagai isyarat keberadaan hewan atau kondisi hutan.</p>"
            "<h3>Mengambil Secukupnya</h3>"
            "<p>Ambil yang dibutuhkan, bukan yang diinginkan, dan pantang menghabiskan semuanya agar generasi mendatang menikmati kelimpahan yang sama.</p>"
            "<p><strong>Ko jaga alam, alam jaga ko.</strong> Pesan kearifan ini ditutup dengan ajakan menjaga Sorong, karena <em>Sorong itu sinagi</em> (kasih).</p>"
        ),
    ),
    dict(
        judul="Egek: Sasi Adat Penjaga Hutan dan Laut",
        kategori="Kearifan Lokal & Lingkungan",
        ringkasan="Egek atau yegek adalah sistem sasi Moi: menutup sementara wilayah hutan dan laut agar alam sempat pulih sebelum dipanen bersama.",
        konten_lengkap=(
            "<p>Filosofi Tam Sini tidak berhenti sebagai konsep. Ia dijalankan lewat <strong>Egek</strong> (juga ditulis <em>yegek</em>), tradisi sasi yang melarang pengambilan hasil hutan dan laut secara berlebihan.</p>"
            "<h3>Zonasi Wilayah Adat</h3>"
            "<ul>"
            "<li><strong>Zona inti (Soo atau Kofok):</strong> kawasan sakral yang pantang disentuh sama sekali.</li>"
            "<li><strong>Zona Egek:</strong> wilayah yang ditutup berkala, misalnya laut atau dusun sagu, agar flora dan fauna punya waktu bertumbuh sebelum dipanen bersama.</li>"
            "</ul>"
            "<h3>Tanda Larangan</h3>"
            "<p>Penandanya kasatmata: <strong>kain merah</strong> atau <strong>janur khusus</strong> yang dipasang di lokasi. Selama tanda itu terpasang, tak seorang pun boleh mengambil hasil alam di sana.</p>"
            "<blockquote>Pemanfaatan baru dibuka massal pada upacara buka Egek. Karena praktik inilah Suku Moi dikenal sebagai salah satu penjaga garis depan hutan hujan tropis dan kekayaan maritim tanah Papua.</blockquote>"
        ),
    ),
]

# ---------------------------------------------------------------------------
# WISATA (Kabupaten Sorong & Kota Sorong)
# deskripsi = HTML. Field sosmed_* boleh dihilangkan bila tidak ada
# (otomatis diisi None lewat WISATA_DEFAULTS).
# ---------------------------------------------------------------------------
WISATA_SEED = [
    # --- Kabupaten Sorong - Wisata Alam ---
    dict(
        nama_wisata="Pulau Um",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p><strong>Sepuluh menit di atas perahu kecil</strong> dari Pantai Malaumkarta, suasana berubah: pasir bersih, air laut jernih, dan kesan <em>private island</em> yang seolah hanya milik Anda. Pulau Um juga rumah asli kelelawar, burung camar, dan penyu. Pagi dan sore hari menjadi waktu pergantian jaga antara kelelawar dan camar.</p>"
            "<h3>Yang Bisa Dinikmati</h3>"
            "<ul>"
            "<li><strong>Penyu bertelur:</strong> penyu kembali ke pulau pada <strong>April</strong>, dan telur menetas pada <strong>Mei</strong>.</li>"
            "<li><strong>Snorkeling:</strong> terumbu karang indah dan bangkai pesawat Perang Dunia II di perairan sekitar.</li>"
            "<li><strong>Dugong:</strong> bila beruntung, satwa ini terlihat di perairan Pulau Um.</li>"
            "</ul>"
            "<blockquote>Selepas musim bertelur, Kelompok Pelestarian Alam Malaumkarta Raya memasang pagar alam dan tanda di sekitar sarang agar telur aman dari predator sampai menetas.</blockquote>"
            "<h3>Cara Menuju</h3>"
            "<ol>"
            "<li>Berkendara sekitar 1 sampai 1,5 jam dari Alun-Alun Aimas lewat Jalan Osok ke Pantai Malaumkarta.</li>"
            "<li>Bayar masuk kawasan: Rp 50.000/mobil atau Rp 10.000/motor.</li>"
            "<li>Hubungi pemilik perahu untuk mengatur waktu jemput. Satu perahu memuat maksimal 12 penumpang.</li>"
            "<li>Menyeberang sekitar 10 menit. Tarif Rp 300.000 pulang-pergi.</li>"
            "</ol>"
        ),
        fasilitas="Perahu penyeberangan warga, area snorkeling, pagar alam sarang penyu",
        alamat="Kampung Malaumkarta, Distrik Makbon, Kabupaten Sorong",
        tiket_masuk="Rp 50.000/mobil, Rp 10.000/motor; perahu Rp 300.000 PP",
        jam_operasional="Fleksibel (sesuai jadwal perahu)",
        sosmed_instagram="@malaukarta.id",
    ),
    dict(
        nama_wisata="Pulau Yerusel",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Dua wajah pantai dalam satu pulau: <strong>hutan mangrove</strong> yang rimbun di satu sisi, <strong>pantai pasir putih</strong> di sisi lain. Di perairan sekitarnya hidup banyak <em>ikan badut</em> yang cantik.</p>"
            "<h3>Aktivitas</h3>"
            "<ul>"
            "<li>Snorkeling</li>"
            "<li>Berenang</li>"
            "<li>Berjemur di tepi pantai</li>"
            "</ul>"
            "<h3>Cara Menuju</h3>"
            "<ol>"
            "<li>Dari Aimas, berkendara sekitar 30 menit ke pelabuhan ASDP di Distrik Mayamuk.</li>"
            "<li>Menyeberang dengan perahu sekitar 10 menit (Rp 30.000/orang).</li>"
            "<li>Bayar tarif masuk pulau Rp 5.000/orang.</li>"
            "</ol>"
            "<blockquote>Gazebo dan kursi panjang bisa disewa. Lapar? Mama-mama dari Kampung Arar berjualan di warung-warung pulau.</blockquote>"
        ),
        fasilitas="Gazebo, kursi sewa, warung mama-mama Kampung Arar, toilet",
        alamat="Distrik Mayamuk, Kabupaten Sorong",
        tiket_masuk="Rp 5.000/orang; perahu Rp 30.000/orang",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pantai Batu Lubang",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Garis pantai panjang, <strong>bebatuan estetik</strong> di banyak titik, dan panorama yang menuntut kamera siap. Pantai Batu Lubang sebenarnya rangkaian pantai: <em>Klasonik</em>, <em>Pasir Pendek</em>, <em>Bainggik</em>, <em>Bainggik Tengah</em>, dan <em>Kaladimala</em>.</p>"
            "<h3>Sorotan</h3>"
            "<ul>"
            "<li><strong>Batu berlubang</strong> menyerupai gua, ikon tempat ini. Dicapai dengan longboat sewaan sekitar 10 menit.</li>"
            "<li><strong>Jembatan kayu</strong> menuju <em>Bukit Doa</em> dengan panorama 360° (kampung, hutan, pantai, laut, dan bebatuan).</li>"
            "<li><strong>Matahari terbenam</strong> yang indah dari atas bukit.</li>"
            "<li>Jembatan kayu yang mengelilingi bebatuan, dengan pemandangan laut dan gua.</li>"
            "</ul>"
            "<blockquote>Sekitar 1 jam lewat jalur darat dari Alun-Alun Kota Baru Aimas. Tersedia gazebo, toilet, parkir luas, penginapan, dan pusat oleh-oleh hasil tangan warga.</blockquote>"
        ),
        fasilitas="Gazebo, toilet, parkir luas, penginapan, pusat oleh-oleh, sewa longboat, jembatan kayu",
        alamat="Distrik Makbon, Kabupaten Sorong",
        tiket_masuk="Rp 50.000/mobil, Rp 10.000/motor",
        jam_operasional="Tidak dicantumkan",
        sosmed_email="disparporakabsorong@gmail.com",
    ),
    dict(
        nama_wisata="Kali Klawak",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p><strong>Suara arus terdengar lebih dulu</strong> sebelum sungainya tampak. Kali Klawak di Kampung Wilti mengalir deras dan mengundang pengunjung <strong>berenang dari jembatan</strong> yang disediakan.</p>"
            "<ul>"
            "<li>Gazebo berjajar di sepanjang tepi sungai.</li>"
            "<li>Parkir: Rp 20.000 (motor), Rp 50.000 (mobil).</li>"
            "</ul>"
            "<blockquote>Jarak tempuh sekitar 2 jam dari Kota Baru Aimas atau 2,5 jam dari Bandara DEO Kota Sorong.</blockquote>"
            "<p><strong>Kontak:</strong> 081343132489</p>"
        ),
        fasilitas="Jembatan untuk berenang, gazebo tepi sungai, area parkir",
        alamat="Kampung Wilti, Distrik Klawak, Kabupaten Sorong",
        tiket_masuk="Parkir Rp 20.000/motor, Rp 50.000/mobil",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Air Terjun Asbaken",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Air terjun yang <strong>langsung menghadap ke laut</strong>, pemandangan yang jarang ditemui. Karena letaknya itu, Asbaken hanya bisa dicapai dengan <em>longboat</em> atau perahu.</p>"
            "<ul>"
            "<li>Perjalanan laut sekitar <strong>2 jam</strong>.</li>"
            "<li>Sepanjang jalan, pengunjung disuguhi udara segar dari dalam hutan dan pemandangan laut.</li>"
            "</ul>"
            "<blockquote>Destinasi bagi yang menganggap perjalanan sama berharganya dengan tujuan.</blockquote>"
        ),
        fasilitas="Tidak dicantumkan",
        alamat="Kampung Asbaken, Distrik Makbon, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan (akses longboat/perahu)",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pantai Mangrove Jeflio",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Pantai yang tenang berpadu dengan <strong>hutan mangrove</strong> kampung yang menjadi rumah berbagai jenis <em>burung mangrove</em>.</p>"
            "<ul>"
            "<li>Belum ada retribusi masuk.</li>"
            "<li>Parkir dikelola masyarakat: Rp 10.000 (motor), Rp 20.000 (mobil).</li>"
            "</ul>"
            "<blockquote>Sekitar 30 menit dari ibukota kabupaten dan sekitar 1 jam dari Bandara Kota Sorong.</blockquote>"
            "<p><strong>Kontak:</strong> 0822402653617</p>"
        ),
        fasilitas="Parkir dikelola warga, hutan mangrove untuk pengamatan burung",
        alamat="Kampung Jeflio, Distrik Mayamuk, Kabupaten Sorong",
        tiket_masuk="Gratis; parkir Rp 10.000/motor, Rp 20.000/mobil",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Kali Klabot",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Air <strong>bening kebiruan seperti kaca</strong> dan mata air yang deras. Kali Klabot dinilai layak menjadi destinasi wisata, sekaligus berpotensi menjadi sumber pembangkit listrik.</p>"
            "<ul>"
            "<li>Gazebo untuk bersantai.</li>"
            "<li>Perahu sewa dari masyarakat setempat untuk menyusuri kali.</li>"
            "</ul>"
            "<blockquote>Sekitar 48 km dari Aimas dengan waktu tempuh kurang lebih 2,5 jam.</blockquote>"
        ),
        fasilitas="Gazebo, perahu sewa dari masyarakat setempat",
        alamat="Distrik Klabot, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pantai Walio",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Hamparan pantai yang <strong>panjang dan padat</strong>. Saat air surut, kendaraan bisa menyisir sepanjang pantai. Pohon <em>pinus</em> berjajar di tepinya, membuat suasana terasa lebih sejuk.</p>"
            "<ul>"
            "<li>Pemandangan <strong>matahari terbenam</strong> yang sangat direkomendasikan bagi pecinta pantai dan sunset.</li>"
            "</ul>"
            "<blockquote>Sekitar 20 km dari pusat Kota Aimas atau kurang lebih 40 km dari Bandara DEO Kota Sorong.</blockquote>"
        ),
        fasilitas="Tidak dicantumkan",
        alamat="Distrik Seget, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Air Panas Klayili",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Di Kampung Wisata Adat Malasigi, bumi mengeluarkan <strong>air hangat</strong>. Air panas Klayili bersumber dari <em>geotermal</em> alami: air tanah yang bersentuhan dengan magma naik ke permukaan. Kawasan ini bagian dari wilayah geotermal dan vulkanik aktif Cincin Api Pasifik.</p>"
            "<h3>Selain Berendam</h3>"
            "<ul>"
            "<li>Telusur goa</li>"
            "<li>Tontonan burung cendrawasih</li>"
            "<li>Flora dan fauna unik lainnya</li>"
            "<li>Penyambutan tarian tradisional oleh masyarakat setempat</li>"
            "</ul>"
            "<blockquote>Tersedia homestay dan camping ground yang bisa disewa untuk menginap di kampung.</blockquote>"
        ),
        fasilitas="Homestay, camping ground",
        alamat="Kampung Malasigi, Distrik Klayili, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
        sosmed_instagram="@kampungwisataadatmalasigi",
    ),
    dict(
        nama_wisata="Pulau Sisi",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p><strong>Berkemah tanpa repot.</strong> Di Pulau Sisi, puluhan tenda berkapasitas tiga orang sudah siap, cocok untuk keluarga maupun rombongan.</p>"
            "<h3>Pilihan Paket</h3>"
            "<ul>"
            "<li>Paket <strong>Rp 250.000</strong></li>"
            "<li>Paket <strong>Rp 500.000</strong></li>"
            "</ul>"
            "<p>Minimal untuk 10 orang, sudah termasuk tenda, makanan, dan camilan.</p>"
            "<blockquote>Pengelola menyediakan layanan antar-jemput. Camping ground ini juga dikenal dengan kuliner khas yang jarang dijumpai di wilayah Sorong.</blockquote>"
            "<p><strong>Kontak:</strong> 085244213655</p>"
        ),
        fasilitas="Tenda (3 orang/tenda), makanan dan camilan, antar-jemput",
        alamat="Warmon, Kecamatan Aimas, Kabupaten Sorong",
        tiket_masuk="Paket Rp 250.000 / Rp 500.000 (min. 10 orang)",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Air Terjun Malawor",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p><strong>Dua air terjun dalam satu spot</strong>, berjarak sekitar 15 meter satu sama lain, dengan tinggi kira-kira 15 dan 30 meter. Airnya langsung dari <em>mata air pegunungan</em>.</p>"
            "<h3>Yang Bisa Dilakukan</h3>"
            "<ul>"
            "<li>Berenang atau berendam kaki. Ramah untuk anak di atas 10 tahun, tetap perlu pengawasan.</li>"
            "<li>Berfoto di batu-batu besar di sekitar air terjun.</li>"
            "<li>Menikmati suasana hutan yang tenang.</li>"
            "</ul>"
            "<h3>Menuju Lokasi</h3>"
            "<ol>"
            "<li>Dari Alun-Alun Aimas lewat Jalan Osok lalu Jalan Makbon, sekitar 45 sampai 50 menit.</li>"
            "<li>Dari Jalan Poros Malawor-Makbon, jalan kaki 15 sampai 20 menit lewat jalur setapak tanah yang tidak curam.</li>"
            "</ol>"
            "<blockquote>Sebaiknya hindari musim hujan: jalur tanah menjadi licin dan becek.</blockquote>"
        ),
        fasilitas="Jalur setapak tanah menuju air terjun",
        alamat="Batu Lobang, Kecamatan Makbon, Kabupaten Sorong (6FGF+JC)",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pantai Mibi",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Saat Batu Lubang dan Malaumkarta ramai, <strong>Pantai Mibi masih sepi</strong>. Pantainya asri dan dikelilingi hutan, cocok bagi yang ingin menikmati pantai lebih tenang.</p>"
            "<h3>Fasilitas</h3>"
            "<ul>"
            "<li>Kamar mandi dan toilet, parkir memadai untuk kendaraan roda 4.</li>"
            "<li>Homestay bersih dengan 4 kamar (2 kecil, 2 besar), kamar mandi di luar.</li>"
            "</ul>"
            "<h3>Akses</h3>"
            "<ul>"
            "<li>Sekitar 15 menit dari Pantai Malaumkarta</li>"
            "<li>1 sampai 1,5 jam dari Alun-Alun Kota Baru Aimas</li>"
            "<li>1 jam 2 menit (41,7 km) dari Bandara DEO</li>"
            "</ul>"
            "<blockquote>Pemesanan homestay lewat Instagram <em>@disparporakabsorong</em>.</blockquote>"
        ),
        fasilitas="Kamar mandi, toilet, parkir, homestay 4 kamar",
        alamat="Kampung Mibi, Distrik Makbon, Kabupaten Sorong (6HM5+H6)",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
        sosmed_instagram="@disparporakabsorong",
    ),

    # --- Kabupaten Sorong - Wisata Budaya dan Kampung Adat ---
    dict(
        nama_wisata="Rumah Etnik Papua",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Satu tempat untuk <strong>mengenal Papua</strong>: rumah tradisional, tarian, pakaian, makanan, dan suvenir khas. Pengunjung bisa menyewa <strong>busana adat lengkap</strong> dengan aksesori dan ukiran badan khas Papua untuk berfoto. Jasa fotografer tersedia untuk hasil yang lebih profesional.</p>"
            "<blockquote>Setiap <strong>Minggu sore</strong>, tarian tradisional dipentaskan dan bisa disaksikan langsung.</blockquote>"
            "<h3>Tiga Paket Pengalaman</h3>"
            "<ol>"
            "<li><strong>Marasrisen (Rp 220.000/orang):</strong> kostum Papua lengkap dengan ukiran, foto sepuasnya di rumah tradisional, dan tarian <em>Yospan</em> bersama masyarakat setempat.</li>"
            "<li><strong>Saswar (Rp 300.000/orang):</strong> penyambutan tari pengalungan kalung kerang (dibawa pulang), menyaksikan tarian tradisional dan pembuatan <em>sinole</em> dan <em>sagu forno</em>, tarian Yospan, serta jamuan teh, kopi, kasbi goreng, dan pisang keju.</li>"
            "<li><strong>Sopendo (Rp 420.000/orang):</strong> penyambutan tarian dan adat <em>Mansorandak</em> (injak piring), noken kecil yang dibawa pulang, menyaksikan sagu diolah menjadi papeda, dan makan makanan tradisional Papua sepuasnya.</li>"
            "</ol>"
            "<h3>Informasi</h3>"
            "<ul>"
            "<li>Tiket masuk <strong>Rp 25.000/orang</strong>; sewa kostum Papua Rp 60.000/orang.</li>"
            "<li>Tersedia museum mini, homestay bernuansa tradisional Papua, dan meeting room.</li>"
            "<li>Pemesanan paket maksimal <strong>2 hari sebelumnya</strong> dengan DP 40%. Biaya bisa dikurangi bila membawa kamera sendiri.</li>"
            "</ul>"
            "<p><strong>Kontak:</strong> 081248415096</p>"
        ),
        fasilitas="Museum mini, homestay, meeting room, sewa kostum adat, jasa fotografer",
        alamat="Jl. Klamono KM 21, Aimas, Kabupaten Sorong",
        tiket_masuk="Rp 25.000/orang; paket Rp 220.000 - 420.000",
        jam_operasional="Pentas tari: Minggu sore",
        sosmed_instagram="@rumah_etnik_papua",
    ),
    dict(
        nama_wisata="Kampung Malasigi",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Kampung adat di sisi timur Kabupaten Sorong yang menyambut tamu dengan <strong>Tari Alen</strong> khas suku asli Moi. Penduduknya tidak terlalu banyak, sehingga suasana pedesaan yang berbudaya, dengan kearifan lokal dan adat istiadat yang kental, terasa nyaman.</p>"
            "<h3>Pengamatan Burung Liar</h3>"
            "<ul>"
            "<li><strong>Cendrawasih:</strong> kuning-kecil, raja, belah rotan, dan 12 antena.</li>"
            "<li><strong>Burung lainnya:</strong> kasuari, <em>Papuan Frogmouth</em>, <em>Red-breasted Paradise-kingfisher</em>, <em>Red-bellied Pitta</em>, dan kakatua jambul kuning.</li>"
            "</ul>"
            "<blockquote>Selain burung, kampung ini memiliki sumber air panas. Perjalanan sekitar 1 sampai 2 jam dari ibukota Kabupaten Sorong.</blockquote>"
        ),
        fasilitas="Sumber air panas, pengamatan burung, homestay, camping ground",
        alamat="Distrik Klayili, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
        sosmed_email="pbdmalasigiphd@gmail.com",
    ),
    dict(
        nama_wisata="Desa Wisata Malaumkarta",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Gerbang menuju <strong>Pulau Um</strong>: kampung di Distrik Makbon, di tepi <em>Teluk Dore</em>, di utara Kota Sorong.</p>"
            "<ul>"
            "<li>Pantai Malaumkarta menjadi titik berangkat perahu warga ke Pulau Um.</li>"
            "<li>Pelestarian digerakkan masyarakat lewat <em>Kelompok Pelestarian Alam Malaumkarta Raya</em>, yang menjaga sarang penyu di Pulau Um.</li>"
            "</ul>"
            "<blockquote>Wisata di sini bukan sekadar bermain di pantai. Anda juga melihat bagaimana warga hidup berdampingan dengan alamnya.</blockquote>"
        ),
        fasilitas="Akses ke Pantai Malaumkarta dan Pulau Um, perahu warga",
        alamat="Malaumkarta, Kecamatan Makbon, Kabupaten Sorong",
        tiket_masuk="Rp 50.000/mobil, Rp 10.000/motor",
        jam_operasional="Tidak dicantumkan",
        sosmed_instagram="@Malaumkarta14pgm",
    ),
    dict(
        nama_wisata="Kampung Ekowisata Malagufuk",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Salah satu tujuan <strong>pengamatan burung</strong> di dunia. Burung endemik Papua Barat mencari makan, minum, beristirahat, dan berkembang biak di hutan kampung ini.</p>"
            "<h3>Burung yang Bisa Dijumpai</h3>"
            "<ul>"
            "<li>Lesser Bird of Paradise</li>"
            "<li>Northern Cassowary</li>"
            "<li>Twelve-wired Bird of Paradise</li>"
            "<li>King Bird of Paradise</li>"
            "<li>Red-breasted Paradise Kingfisher</li>"
            "<li>Magnificent Riflebird</li>"
            "</ul>"
            "<blockquote>Musim tersibuk: <strong>Agustus sampai Desember</strong>, bertepatan dengan musim kawin burung.</blockquote>"
            "<h3>Jembatan Kayu Terpanjang di Indonesia</h3>"
            "<p>Jembatan sepanjang <strong>3,305 kilometer</strong> membelah belantara dan tercatat di Museum Rekor Dunia Indonesia (MURI). Diresmikan Bupati Sorong John Kamuru pada 2 Juli 2021 agar wisatawan lebih mudah melihat burung-burung endemik.</p>"
            "<h3>Menginap di Pondok Wisata Eco Village</h3>"
            "<ul>"
            "<li><strong>Rp 688.500</strong> per orang per malam, termasuk sarapan.</li>"
            "<li>Kamar mandi pribadi dengan shower dan handuk, kipas angin, keamanan 24 jam.</li>"
            "<li>Restoran dan layanan makanan minuman. Tur budaya dan tur jalan kaki tersedia dengan biaya tambahan.</li>"
            "<li>Tidak tersedia koneksi internet dan tempat parkir.</li>"
            "</ul>"
            "<blockquote>Sekitar 2 jam dari Bandara DEO Kota Sorong.</blockquote>"
            "<p><strong>Kontak:</strong> 081343365573</p>"
        ),
        fasilitas="Homestay Eco Village, restoran, tur budaya dan jalan kaki, jembatan kayu 3,3 km",
        alamat="Distrik Makbon, Kabupaten Sorong",
        tiket_masuk="Menginap Rp 688.500/orang/malam (sarapan)",
        jam_operasional="Ramai Agustus - Desember",
        sosmed_instagram="malagufuk.id",
    ),

    # --- Kabupaten Sorong - Wisata Buatan ---
    dict(
        nama_wisata="Tirta Istianah Indah Waterpark",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Waterpark keluarga yang <strong>lengkap dan dekat</strong> dari pusat kota: 8 menit dari Alun-Alun Kota Baru Aimas (3,9 km) dan 35 menit (16 km) dari Bandara DEO.</p>"
            "<h3>Pilihan Kolam</h3>"
            "<ul>"
            "<li>Kolam khusus anak-anak</li>"
            "<li>Kolam dewasa (bisa untuk latihan renang)</li>"
            "<li>Kolam arus</li>"
            "<li>Kolam dengan <em>water slide</em> dan seluncur air</li>"
            "</ul>"
            "<h3>Harga dan Jam Buka</h3>"
            "<ul>"
            "<li><strong>Rp 50.000/orang</strong>, sama di hari kerja dan akhir pekan, sudah termasuk parkir dan gazebo.</li>"
            "<li>Buka <strong>09.00 sampai 17.00 WIT</strong> setiap hari.</li>"
            "<li>Sewa ban pelampung: Rp 50.000/jam (besar) atau Rp 50.000/2 jam (kecil).</li>"
            "</ul>"
            "<blockquote>Ingin belajar berenang? Tersedia kursus renang bersama tenaga profesional. Panggungnya juga bisa disewa untuk perpisahan sekolah, ulang tahun, atau rapat.</blockquote>"
            "<p><strong>Kontak:</strong> 081344641910</p>"
        ),
        fasilitas="Kolam anak/dewasa/arus, water slide, sewa ban, foodcourt, toilet, kamar ganti, kursus renang",
        alamat="Jl. Seledri, Malawele, Aimas, Kabupaten Sorong",
        tiket_masuk="Rp 50.000/orang",
        jam_operasional="09.00 - 17.00 WIT",
        sosmed_email="disparporakabsorong@gmail.com",
        sosmed_instagram="@istianah_swimclubsorong",
    ),
    dict(
        nama_wisata="Kolam Pancing Mariat",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Dulu bernama <em>Wisata Agro Mina</em>, kini Kolam Pancing Mariat mengusung <strong>konsep wisata taman</strong>: memancing dalam suasana santai.</p>"
            "<h3>Biaya</h3>"
            "<ul>"
            "<li>Masuk <strong>gratis</strong>.</li>"
            "<li>Memancing dengan alat sendiri: Rp 15.000.</li>"
            "<li>Sewa pancing Rp 20.000, pelet Rp 10.000/200 gram, keranjang ikan gratis.</li>"
            "<li>Ikan (nila, bawal, lele, gabus, patin, emas, gurame): Rp 70.000 sampai Rp 125.000/kg.</li>"
            "<li>Ingin langsung disantap? Jasa memasak Rp 25.000/kg.</li>"
            "</ul>"
            "<blockquote>Buka Senin sampai Sabtu pukul 09.00, Minggu pukul 10.00, tutup 19.00 WIT. Gazebo Rp 50.000 tersedia untuk meeting kantor, ulang tahun, atau arisan.</blockquote>"
            "<p>Lokasi 5,6 km (sekitar 9 menit) dari Alun-Alun Kota Baru Aimas dan 17,5 km (sekitar 32 menit) dari Bandara DEO.</p>"
            "<p><strong>Kontak:</strong> 08114819966</p>"
        ),
        fasilitas="Gazebo, minimarket, restoran, toilet, parkir luas",
        alamat="Jl. Baru, pertigaan Pasar Induk Aimas, Kabupaten Sorong",
        tiket_masuk="Gratis; memancing Rp 15.000",
        jam_operasional="Sen - Sab 09.00, Min 10.00 - 19.00 WIT",
        sosmed_email="disparporakabsorong@gmail.com",
        sosmed_facebook="@kolampancingmariat",
        sosmed_instagram="@kolampancingmariat",
    ),
    dict(
        nama_wisata="Taman Rainbow Katapop",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Taman baru yang sedang <strong>naik daun</strong> di kalangan warga Kota dan Kabupaten Sorong, dengan spot foto <em>instagramable</em>.</p>"
            "<ul>"
            "<li>Kincir angin</li>"
            "<li>Pondok</li>"
            "<li>Miniatur rumah</li>"
            "</ul>"
            "<blockquote>Tiket <strong>Rp 25.000</strong> untuk dewasa, anak-anak <strong>gratis</strong>. Lokasi di Katapop 1, Majener, Salawati, dekat SD Inpres 32.</blockquote>"
        ),
        fasilitas="Spot foto kincir angin, pondok, miniatur rumah",
        alamat="Jl. Trunojoyo, Katapop 1, Majener, Salawati, Kabupaten Sorong",
        tiket_masuk="Rp 25.000 (dewasa); anak gratis",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Telaga Syafa'at",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Pilihan tepat untuk <strong>liburan santai</strong> bersama keluarga atau teman.</p>"
            "<ul>"
            "<li>Kolam renang yang bersih</li>"
            "<li>Gazebo nyaman untuk bersantai</li>"
            "<li>Ayunan, favorit anak-anak</li>"
            "<li>Warung <em>Adem Ayam</em> dengan aneka menu khas lokal</li>"
            "<li>Ruang karaoke</li>"
            "<li>Musala yang bersih dan nyaman</li>"
            "</ul>"
            "<blockquote>Berjarak 19,4 km dari Bandara DEO Kota Sorong, sekitar 33 menit berkendara.</blockquote>"
            "<p><strong>Kontak:</strong> 081248955463</p>"
        ),
        fasilitas="Kolam renang, gazebo, ayunan, Warung Adem Ayam, karaoke, musala",
        alamat="Distrik Mariat, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Taman Sari Garden",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Berenang, ngopi, lalu bermain, semuanya di satu tempat.</p>"
            "<ol>"
            "<li><strong>Berenang</strong> di kolam luas untuk anak-anak dan dewasa.</li>"
            "<li><strong>Bersantai</strong> di kafe dengan menu dari makanan ringan sampai hidangan utama.</li>"
            "<li><strong>Bermain</strong> di taman hiburan dengan wahana permainan seru.</li>"
            "</ol>"
            "<blockquote>Sekitar 19 km atau 30 menit berkendara dari Bandara DEO Kota Sorong.</blockquote>"
            "<p><strong>Kontak:</strong> 081247776434</p>"
        ),
        fasilitas="Kolam renang, kafe, taman hiburan dan wahana",
        alamat="Mariat Pantai, Kecamatan Aimas, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
        sosmed_facebook="@tamansarigarden",
        sosmed_instagram="@tamansarigarden.soq",
    ),
    dict(
        nama_wisata="Bumi Cendrawasih Agrowisata",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Destinasi wisata buatan <strong>pertama di Kabupaten Sorong</strong>, dengan <em>melon hidroponik</em> sebagai atraksi utama. Anak-anak diajak belajar dari penanaman sampai panen dan ikut memeriksa tingkat kemanisan melon, jadi cocok sebagai wisata edukasi.</p>"
            "<h3>Varietas Melon</h3>"
            "<ul>"
            "<li><strong>Dalmatian</strong>: impor Korea, manis, berair, harum</li>"
            "<li><strong>Inthanon</strong>: varietas unggulan asal Belanda</li>"
            "<li><strong>Sweet Lavender</strong>: sangat manis dan renyah</li>"
            "<li><strong>Rangipo</strong>: daging oranye, manis, juicy, renyah</li>"
            "<li><strong>Sky Rocket</strong></li>"
            "</ul>"
            "<h3>Informasi Kunjungan</h3>"
            "<ul>"
            "<li>Buka setiap hari: <strong>08.00 sampai 10.00</strong> dan <strong>15.00 sampai 18.30 WIT</strong>.</li>"
            "<li>Tiket hari biasa gratis. Melon mulai <strong>Rp 25.000/kg</strong>.</li>"
            "<li>Wisata petik langsung dari pohon mengikuti jadwal tanam yang diumumkan pengelola di media sosial.</li>"
            "<li>Tersedia juga sayuran hidroponik segar seperti selada dan pakcoi.</li>"
            "</ul>"
            "<blockquote>Hanya 800 meter (sekitar 3 menit) dari Alun-Alun Kota Baru Aimas dan 12,5 km (sekitar 25 menit) dari Bandara DEO.</blockquote>"
            "<p><strong>Kontak:</strong> 0813-8519-8410 (WhatsApp 0852-6830-4666)</p>"
        ),
        fasilitas="Kebun melon hidroponik, sayuran hidroponik, parkir dan toilet gratis",
        alamat="Jl. Enau (depan Polres Aimas), Aimas, Kabupaten Sorong",
        tiket_masuk="Gratis (melon mulai Rp 25.000/kg)",
        jam_operasional="08.00 - 10.00 & 15.00 - 18.30 WIT",
        sosmed_facebook="fransoktiz_papilaya",
        sosmed_instagram="fransoktiz_papilaya",
    ),
    dict(
        nama_wisata="Nancy Swimming Pool Aimas Hotel",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Kolam renang di <strong>Aimas Hotel and Convention Centre</strong> yang terbuka untuk umum.</p>"
            "<ul>"
            "<li>Buka <strong>06.00 sampai 18.00 WIT</strong> setiap hari.</li>"
            "<li><strong>Rp 50.000</strong>: berenang sepuasnya, sudah termasuk parkir.</li>"
            "<li><strong>Rp 75.000</strong>: sudah termasuk nasi goreng dan es teh.</li>"
            "<li>Fasilitas: toilet, musala, minimarket, dan restoran di sebelah kolam (di luar biaya masuk).</li>"
            "</ul>"
            "<blockquote>Bisa juga menginap di hotel (biaya terpisah) atau mengadakan gathering. Lokasi 3,7 km (6 menit) dari Alun-Alun Kota Baru Aimas dan 15,6 km (29 menit) dari Bandara DEO.</blockquote>"
            "<p><strong>Kontak:</strong> 08114887778</p>"
        ),
        fasilitas="Toilet, musala, minimarket, restoran, parkir",
        alamat="Aimas Hotel and Convention Centre, Klamasen, Distrik Mariat, Kabupaten Sorong",
        tiket_masuk="Rp 50.000/orang",
        jam_operasional="06.00 - 18.00 WIT",
    ),
    dict(
        nama_wisata="Podomoro Pemancingan dan Kolam Renang",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Dua kesenangan akhir pekan sekaligus: <strong>memancing</strong> dan <strong>berenang</strong>. Beroperasi sejak <em>2023</em>.</p>"
            "<ul>"
            "<li>Kolam renang <strong>Rp 10.000/orang</strong>, dilengkapi perosotan.</li>"
            "<li>Kolam pemancingan <strong>gratis</strong>. Ikan nila hasil pancingan Rp 50.000/kg.</li>"
            "</ul>"
            "<blockquote>Alat pancing tidak disewakan, jadi bawa sendiri. Buka 08.00 sampai 17.00 WIT hanya pada Sabtu, Minggu, dan hari libur.</blockquote>"
            "<p>Lokasi 17 km (sekitar 26 menit) dari Alun-Alun Kota Baru Aimas dan 28,9 km (sekitar 49 menit) dari Bandara DEO.</p>"
            "<p><strong>Kontak:</strong> 082239010520</p>"
        ),
        fasilitas="Kolam renang berperosotan, kolam pemancingan nila, toilet, musala, parkir",
        alamat="SP 4, Jl. Poros TSM, Makbalim, Mayamuk, Kabupaten Sorong",
        tiket_masuk="Kolam renang Rp 10.000; pemancingan gratis",
        jam_operasional="Sab, Min, hari libur 08.00 - 17.00 WIT",
    ),
    dict(
        nama_wisata="Bendungan SP 1",
        wilayah="Kabupaten Sorong",
        deskripsi=(
            "<p>Bendungan pengairan yang berubah menjadi <strong>ruang rekreasi favorit</strong> warga lokal. Sorotan utamanya adalah <strong>panorama senja</strong>: sinar keemasan memantul di permukaan air dan menciptakan siluet pepohonan yang menawan.</p>"
            "<h3>Aktivitas</h3>"
            "<ul>"
            "<li>Piknik keluarga di area terbuka yang teduh</li>"
            "<li>Memancing</li>"
            "<li>Bersepeda dan jalan santai pagi atau sore hari</li>"
            "<li>Wisata kuliner di <em>Lesehan K'waduk</em> dengan saung-saung, cocok untuk gathering, rapat, ulang tahun, atau arisan</li>"
            "</ul>"
            "<blockquote>Lokasi 7 km (13 menit) dari Alun-Alun Kota Baru Aimas dan 13 km (39 menit) dari Bandara DEO.</blockquote>"
        ),
        fasilitas="Area piknik, Lesehan K'waduk, toilet, parkir, musala",
        alamat="Jl. Cianjur, Klamalu, Distrik Mariat, Kabupaten Sorong",
        tiket_masuk="Tidak dicantumkan",
        jam_operasional="Tidak dicantumkan",
    ),

    # --- Kota Sorong - Wisata Sejarah ---
    dict(
        nama_wisata="Pulau Doom",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Kurang dari <strong>10 menit</strong> naik perahu mesin dari daratan besar Kota Sorong, dan Anda tiba di bekas <strong>pusat pemerintahan Belanda</strong> di wilayah timur Indonesia pada masa Perang Dunia II. Perahu bersandar di <em>Halte Doom</em>, yang bukan tempat menunggu bus melainkan dermaga kecil.</p>"
            "<h3>Jejak Sejarah</h3>"
            "<ul>"
            "<li>Rumah-rumah tua peninggalan Belanda yang masih berdiri kokoh.</li>"
            "<li>Terowongan <em>Gua Jepang</em> berdiameter sekitar 1 meter, sehingga pengunjung harus membungkuk.</li>"
            "<li>Bunker pasukan Jepang dengan tiga lubang moncong senapan.</li>"
            "</ul>"
            "<blockquote>Panorama terbaik ada di puncak bukit, di Gereja Jemaat Bethel Doom: laut lepas dengan Pulau Raam, Soop, dan Dofior sebagai latar.</blockquote>"
        ),
        fasilitas="Rumah tua Belanda, Gua Jepang, bunker, Gereja Jemaat Bethel Doom",
        alamat="Pulau Doom, Kota Sorong (dermaga Halte Doom)",
        tiket_masuk="Perahu sekitar Rp 10.000 PP",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Goa Jepang Pulau Doom",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Jejak <strong>pertahanan Jepang</strong> di Pulau Doom yang bisa dijangkau dengan cepat, karena luas pulau hanya sekitar 5 kilometer persegi.</p>"
            "<h3>Dari Halte Doom, Pilih Salah Satu</h3>"
            "<ul>"
            "<li><strong>Becak atau ojek:</strong> 2 sampai 5 menit (becak sekitar Rp 5.000/orang).</li>"
            "<li><strong>Jalan kaki:</strong> 7 sampai 10 menit menyusuri kota tua.</li>"
            "</ul>"
            "<h3>Perlu Diketahui</h3>"
            "<ul>"
            "<li><strong>Gratis masuk</strong>, karena ini situs sejarah terbuka. Perahu ke pulau sekitar Rp 10.000 pulang-pergi.</li>"
            "<li>Tidak ada penerangan di dalam goa.</li>"
            "</ul>"
            "<blockquote>Bawa senter sendiri, atau beri uang sukarela kepada warga bila memerlukan pemandu atau penerangan tambahan. Pengelola: Dinas Pariwisata Kota Sorong.</blockquote>"
        ),
        fasilitas="Terowongan dan bunker Jepang, becak dan ojek dari dermaga",
        alamat="Pulau Doom, Kota Sorong",
        tiket_masuk="Gratis (perahu sekitar Rp 10.000 PP)",
        jam_operasional="Situs terbuka",
    ),

    # --- Kota Sorong - Wisata Alam ---
    dict(
        nama_wisata="Taman Wisata Mangrove Klawalu",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Hamparan <strong>hijau bakau</strong> yang dibelah <strong>jembatan kayu warna-warni</strong>, jalur tracking yang ramah pejalan kaki sekaligus spot foto favorit.</p>"
            "<h3>Yang Bisa Dilakukan</h3>"
            "<ul>"
            "<li>Naik menara pandang untuk melihat hutan bakau dari ketinggian.</li>"
            "<li>Mengenal jenis bakau seperti <em>Rhizophora stylosa</em> dan <em>Sonneratia caseolaris</em>.</li>"
            "<li>Mengamati burung liar (birdwatching).</li>"
            "<li>Menyewa perahu wisata atau speed kaca menyusuri pesisir.</li>"
            "</ul>"
            "<blockquote>Buka 08.00 sampai 18.00 WIT setiap hari. Tiket Rp 10.000 (dewasa) dan Rp 5.000 (anak-anak). Sekitar 18 menit dari Bandara DEO.</blockquote>"
        ),
        fasilitas="Menara pandang, jembatan kayu warna-warni, sewa perahu dan speed kaca",
        alamat="Klawalu, Kota Sorong",
        tiket_masuk="Rp 10.000 (dewasa), Rp 5.000 (anak)",
        jam_operasional="08.00 - 18.00 WIT",
    ),
    dict(
        nama_wisata="Bukit Cinta (Bambu Kuning)",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Perbukitan asri dengan <strong>jembatan kayu panjang</strong> yang membelah bukit, sekaligus salah satu spot terbaik menikmati <strong>sunset</strong> dan pemandangan sebagian wilayah Kota Sorong dari ketinggian.</p>"
            "<ul>"
            "<li>Menara pandang setinggi kurang lebih 12 meter.</li>"
            "<li>Gazebo dan saung di sepanjang jalur untuk bersantai.</li>"
            "<li>Pagi hari: udara segar ditemani kicau burung liar.</li>"
            "</ul>"
            "<blockquote>Tiket Rp 10.000/orang. Terletak di pinggir jalan Trans Papua segmen Sorong-Makbon-Tambrauw, sekitar 13 menit dari Bandara DEO lewat Jl. Basuki Rahmat. Bisa dengan motor maupun mobil.</blockquote>"
        ),
        fasilitas="Jembatan kayu, menara pandang 12 m, gazebo",
        alamat="Jl. Sorong - Makbon, Kelurahan Giwu, Sorong Timur, Kota Sorong",
        tiket_masuk="Rp 10.000/orang",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pantai Tanjung Kasuari",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Dinamai <em>Tanjung Kasuari</em> karena daratannya menonjol ke laut lepas dan, bila dilihat dari atas, menyerupai <strong>kepala burung kasuari</strong>. Bagi warga Sorong, inilah oase pelarian dari penatnya kota.</p>"
            "<h3>Daya Tarik</h3>"
            "<ul>"
            "<li>Pasir putih bersih dan halus</li>"
            "<li>Pepohonan rindang di sepanjang bibir pantai</li>"
            "<li>Air jernih dengan ombak teluk yang relatif tenang, aman untuk berenang</li>"
            "<li>Piknik sambil menikmati kelapa muda</li>"
            "</ul>"
            "<h3>Perkiraan Biaya</h3>"
            "<ul>"
            "<li>Parkir sekitar Rp 20.000/motor</li>"
            "<li>Pondok atau gazebo Rp 50.000 sampai Rp 100.000, sepuasnya</li>"
            "<li>Toilet dan bilas: sukarela sekitar Rp 5.000</li>"
            "</ul>"
            "<blockquote>Fasilitas dikelola swadaya oleh warga pemilik hak ulayat. Dari Bandara DEO sekitar 30 sampai 35 menit lewat Jl. Basuki Rahmat, Jl. Ahmad Yani, dan Jl. Rufei.</blockquote>"
        ),
        fasilitas="Gazebo sewa, warung, sewa ban renang, toilet dan bilas, parkir luas",
        alamat="Jl. Tj. Kasuari, Kelurahan Malaingkedi, Sorong Utara, Kota Sorong",
        tiket_masuk="Parkir sekitar Rp 20.000/motor",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pantai Alinda",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Bertetangga hanya <strong>650 meter</strong> dari Tanjung Kasuari, tetapi suasananya lebih <strong>aktif dan penuh hiburan</strong>.</p>"
            "<h3>Wahana dan Hiburan</h3>"
            "<ul>"
            "<li><em>Banana boat</em> dan <em>donut boat</em>, sekitar Rp 25.000/orang (ramai di hari Minggu)</li>"
            "<li>Kolam renang air tawar</li>"
            "<li>Panggung karaoke gratis</li>"
            "<li>Area bermain anak</li>"
            "</ul>"
            "<h3>Informasi</h3>"
            "<ul>"
            "<li>Buka <strong>24 jam</strong>.</li>"
            "<li>Tiket Rp 25.000 (dewasa) dan Rp 5.000 (anak-anak).</li>"
            "<li>Tersedia cottage untuk menginap, gazebo, musala, toilet, kamar bilas, warung makan, dan parkir luas.</li>"
            "</ul>"
            "<blockquote>Sekitar 30 sampai 35 menit dari Bandara DEO, dengan rute yang hampir sama dengan Tanjung Kasuari.</blockquote>"
        ),
        fasilitas="Banana boat, kolam air tawar, karaoke, gazebo, musala, cottage, parkir",
        alamat="Kawasan Tanjung Kasuari, Sorong Barat, Kota Sorong",
        tiket_masuk="Rp 25.000 (dewasa), Rp 5.000 (anak)",
        jam_operasional="24 jam",
    ),
    dict(
        nama_wisata="Pantai Kaisarea",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Pantai yang lahir dari tekad seorang warga. Pada <strong>Agustus 2023</strong>, tokoh masyarakat <em>Hendrik Rumsau</em> merintisnya sendiri, memakai pengalamannya bekerja di sebuah resor wisata Raja Ampat untuk mengubah lahan keluarganya menjadi pantai yang bersih dan nyaman.</p>"
            "<h3>Daya Tarik</h3>"
            "<ul>"
            "<li>Ombak tenang, aman untuk berenang.</li>"
            "<li>Spot berburu <strong>sunset</strong>, menghadap gugusan pulau di perairan Sorong.</li>"
            "<li>Cocok untuk berkumpul dan membakar ikan.</li>"
            "<li>Sekitar 10 pondok kayu, spot swafoto, ayunan pantai, dan toilet umum.</li>"
            "</ul>"
            "<h3>Tarif per Kendaraan</h3>"
            "<ul>"
            "<li>Motor: Rp 20.000</li>"
            "<li>Mobil: Rp 50.000</li>"
            "<li>Bus atau truk pariwisata: Rp 100.000</li>"
            "</ul>"
            "<blockquote>Tarif dihitung per kendaraan, bukan per orang. Lokasi sekitar 10 km dari pusat kota, 20 menit lewat jalan beraspal mulus.</blockquote>"
        ),
        fasilitas="10 pondok kayu, spot swafoto, ayunan, toilet umum",
        alamat="Kampung Suprau, Distrik Maladumes, Kota Sorong",
        tiket_masuk="Motor Rp 20.000, mobil Rp 50.000, bus Rp 100.000",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Taman Wisata Alam Sorong (Arboretum Anggrek)",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Kawasan hutan lindung seluas <strong>945,9 hektare</strong> yang kerap disebut <em>paru-paru Kota Sorong</em>, dikelola langsung oleh BBKSDA Papua Barat.</p>"
            "<h3>Daya Tarik Utama</h3>"
            "<ul>"
            "<li><strong>Arboretum Anggrek:</strong> lebih dari 84 jenis anggrek asli Papua, 36 di antaranya endemik.</li>"
            "<li><strong>Birdwatching:</strong> hutan lebat menjadi surga pengamat burung, terutama saat pagi.</li>"
            "<li><strong>Kandang penyelamatan satwa:</strong> kakatua, nuri, dan kasuari dirawat sebelum dilepasliarkan.</li>"
            "<li>Sungai jernih dan air terjun mini di jalur tracking.</li>"
            "<li>Jembatan gantung dan spot foto berlatar hutan lebat.</li>"
            "</ul>"
            "<h3>Biaya</h3>"
            "<ul>"
            "<li>Tiket mulai Rp 20.000 (wisatawan domestik, hari biasa)</li>"
            "<li>Parkir: Rp 5.000 (motor), Rp 10.000 sampai Rp 20.000 (mobil)</li>"
            "</ul>"
            "<blockquote>Lokasi di KM 14, sekitar 15 sampai 20 menit dari Bandara DEO. Tarif bisa berubah mengikuti kebijakan BBKSDA.</blockquote>"
        ),
        fasilitas="Arboretum Anggrek, kandang penyelamatan satwa, jalur tracking, gazebo, aula, toilet, parkir",
        alamat="KM 14, Kelurahan Klamana, Sorong Timur, Kota Sorong",
        tiket_masuk="Mulai Rp 20.000 (+ parkir)",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pulau Raam (Pulau Buaya)",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Warga Sorong menyebutnya <strong>Pulau Buaya</strong> karena dari ketinggian bentuknya menyerupai seekor buaya yang mengapung di laut. Pulau berpenghuni ini hanya sekitar 2 km dari daratan Sorong, dengan pantai pasir putih dan air jernih bergradasi hijau toska.</p>"
            "<h3>Aktivitas dan Perkiraan Tarif</h3>"
            "<ul>"
            "<li><em>Banana boat</em> dan <em>donut boat</em>: Rp 25.000 sampai Rp 35.000/orang</li>"
            "<li>Sewa ATV: Rp 50.000 sampai Rp 100.000</li>"
            "<li>Gazebo: Rp 50.000 sampai Rp 100.000</li>"
            "<li>Snorkeling dan diving, outbound, paintball, perahu karet, dan flying fish</li>"
            "</ul>"
            "<h3>Cara Menuju</h3>"
            "<ol>"
            "<li>Menuju Pelabuhan Rakyat (Pelra) Sorong atau Dermaga Tradisional Rufei (yang terdekat).</li>"
            "<li>Naik perahu taksi laut (jonson) melintasi Selat Dom, sekitar 10 sampai 15 menit.</li>"
            "<li>Merapat di dermaga atau pantai pasir putih pulau.</li>"
            "</ol>"
            "<blockquote>Masuk pulau gratis. Bermalam bisa di cottage, termasuk water cottage di atas laut.</blockquote>"
        ),
        fasilitas="Wahana air, sewa snorkeling/diving dan ATV, gazebo, cottage, kedai seafood, dermaga",
        alamat="Kelurahan Raam, Distrik Sorong Kepulauan, Kota Sorong",
        tiket_masuk="Gratis (sewa fasilitas terpisah)",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pulau Soop",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Pulau seluas sekitar <strong>2,6 km²</strong> yang kian populer sebagai destinasi <em>island hopping</em> atau <em>one day trip</em> bagi warga Sorong.</p>"
            "<h3>Yang Menarik</h3>"
            "<ul>"
            "<li>Pasir putih bersih, kelapa rindang, air biru kehijauan.</li>"
            "<li>Batu karang dan bintang laut terlihat jelas dari atas perahu.</li>"
            "<li>Jejak sejarah: goa pertahanan Jepang, sumur peninggalan Belanda, dan kawasan Tanjung Lampu.</li>"
            "</ul>"
            "<h3>Biaya dan Waktu</h3>"
            "<ul>"
            "<li>Masuk pulau <strong>gratis</strong>.</li>"
            "<li>Perahu jonson Rp 15.000 sampai Rp 20.000/orang sekali jalan, 15 sampai 30 menit.</li>"
            "<li>Sewa perahu pulang-pergi Rp 250.000 sampai Rp 400.000 untuk rombongan.</li>"
            "<li>Toilet dan gazebo swadaya warga: sukarela Rp 5.000 sampai Rp 10.000.</li>"
            "</ul>"
        ),
        fasilitas="Gazebo dan toilet swadaya warga, akses perahu jonson",
        alamat="Distrik Sorong Kepulauan, Kota Sorong",
        tiket_masuk="Gratis (perahu Rp 15.000 - 20.000)",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Pantai Indah Suprauw",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Bertetangga dengan Pantai Kaisarea, Pantai Indah membentuk klaster wisata pantai baru yang ramai. Ikonnya adalah <strong>ayunan kayu romantis</strong> yang menghadap langsung ke laut, tempat pasangan muda dan keluarga antre berfoto.</p>"
            "<ul>"
            "<li>Meja dan kursi berpayung kain warna-warni di tepi pantai.</li>"
            "<li>Lanskap tenang, bersih, dan rindang.</li>"
            "</ul>"
            "<blockquote>Tarif per kendaraan: Rp 20.000 (motor) dan Rp 50.000 (mobil). Dari arah pusat kota, lokasinya ada di sisi kiri sebelum area Tanjung Kasuari, sekitar 25 sampai 30 menit dari Bandara DEO.</blockquote>"
        ),
        fasilitas="Ayunan kayu, meja-kursi berpayung warna-warni",
        alamat="Kampung Suprau, Distrik Maladumes, Kota Sorong",
        tiket_masuk="Motor Rp 20.000, mobil Rp 50.000",
        jam_operasional="Tidak dicantumkan",
    ),
    dict(
        nama_wisata="Taman Chika",
        wilayah="Kota Sorong",
        deskripsi=(
            "<p>Tempat berburu foto di garis pantai Tanjung Kasuari, dengan <strong>spot swafoto buatan</strong> yang menghadap laut lepas.</p>"
            "<h3>Spot dan Fasilitas</h3>"
            "<ul>"
            "<li>Dekorasi berbentuk hati dan gerbang bunga</li>"
            "<li>Jembatan kayu yang dicat rapi</li>"
            "<li><strong>Ayunan tepi pantai</strong>, favorit untuk menikmati sunset</li>"
            "<li>Gazebo, warung jajanan, dan toilet sederhana</li>"
            "</ul>"
            "<blockquote>Tarif per kendaraan: Rp 20.000 (motor) dan Rp 50.000 (mobil), berlaku untuk seluruh rombongan dalam kendaraan. Sekitar 30 sampai 35 menit dari Bandara DEO.</blockquote>"
        ),
        fasilitas="Spot foto, ayunan tepi pantai, gazebo, warung, toilet",
        alamat="Kawasan Tanjung Kasuari, Kota Sorong",
        tiket_masuk="Motor Rp 20.000, mobil Rp 50.000",
        jam_operasional="Tidak dicantumkan",
    ),
]

WISATA_DEFAULTS = {
    "gambar": None,
    "latitude": None,
    "longitude": None,
    "sosmed_email": None,
    "sosmed_facebook": None,
    "sosmed_instagram": None,
    "sosmed_youtube": None,
}

BUDAYA_WAJIB = {"judul", "kategori", "ringkasan", "konten_lengkap"}
WISATA_WAJIB = {
    "nama_wisata", "wilayah", "deskripsi", "fasilitas",
    "alamat", "tiket_masuk", "jam_operasional",
}


def _cek_field(label, item, wajib, opsional=()):
    """Tolak data yang field-nya kurang atau salah ketik, supaya ketahuan sebelum masuk DB."""
    kurang = set(wajib) - set(item)
    asing = set(item) - set(wajib) - set(opsional)
    if kurang or asing:
        raise ValueError(
            f"Data '{label}' bermasalah: field kurang {sorted(kurang)}, "
            f"field tidak dikenal {sorted(asing)}"
        )


def seed_budaya():
    for item in BUDAYA_SEED:
        _cek_field(item.get("judul", "?"), item, BUDAYA_WAJIB)
        existing = dbcore.query_one("SELECT id FROM budaya WHERE judul = %s", (item["judul"],))
        if existing:
            print(f"  - budaya '{item['judul']}' sudah ada, dilewati")
            continue
        budaya_model.create(item["judul"], item["kategori"], item["ringkasan"], item["konten_lengkap"], None)
        print(f"  + budaya '{item['judul']}' ditambahkan")


def seed_wisata():
    for item in WISATA_SEED:
        _cek_field(item.get("nama_wisata", "?"), item, WISATA_WAJIB, WISATA_DEFAULTS)
        existing = dbcore.query_one("SELECT id FROM wisata WHERE nama_wisata = %s", (item["nama_wisata"],))
        if existing:
            print(f"  - wisata '{item['nama_wisata']}' sudah ada, dilewati")
            continue
        data = {**WISATA_DEFAULTS, **item}
        wisata_model.create(data)
        print(f"  + wisata '{item['nama_wisata']}' ditambahkan")


SEEDERS = {
    "budaya": seed_budaya,
    "wisata": seed_wisata,
}


def reset_tables(targets):
    """Kosongkan tabel yang mau di-seed ulang. FK ON DELETE CASCADE otomatis
    membersihkan galeri (budaya_galeri/wisata_galeri) & rating terkait."""
    if "wisata" in targets:
        dbcore.execute("DELETE FROM wisata")
        dbcore.execute("ALTER TABLE wisata AUTO_INCREMENT = 1")
        print("  * tabel wisata (+ galeri & rating terkait) dikosongkan")
    if "budaya" in targets:
        dbcore.execute("DELETE FROM budaya")
        dbcore.execute("ALTER TABLE budaya AUTO_INCREMENT = 1")
        print("  * tabel budaya (+ galeri terkait) dikosongkan")


def parse_args():
    parser = argparse.ArgumentParser(description="Seeder data Sorong Culture Tourism.")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(SEEDERS.keys()),
        default=list(SEEDERS.keys()),
        help="Hanya jalankan target tertentu (default: semua).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Kosongkan dulu tabel yang mau di-seed sebelum mengisi ulang.",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Lewati konfirmasi saat --reset.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    targets = args.only

    with app.app_context():
        if args.reset:
            if not args.yes:
                confirm = input(
                    f"Ini akan MENGHAPUS semua data di tabel {', '.join(targets)} "
                    "(dan turunannya) sebelum mengisi ulang. Lanjutkan? [y/N] "
                )
                if confirm.strip().lower() != "y":
                    print("Dibatalkan.")
                    return
            reset_tables(targets)

        for target in targets:
            print(f"{target.capitalize()}:")
            SEEDERS[target]()

        print("Selesai.")


if __name__ == "__main__":
    main()