"""Seeder data dummy untuk pengembangan lokal.

Menambahkan beberapa contoh data budaya, wisata, & rating lewat satu perintah
saja, supaya tidak perlu isi manual satu-per-satu lewat form admin setiap kali
butuh database yang terisi (mis. setelah `schema.sql` baru diimpor).

Aman dijalankan berkali-kali: data yang judul/namanya sudah ada otomatis
dilewati (tidak dobel).

Pemakaian:
    python seed.py                        # isi admin + budaya + wisata + ratings
    python seed.py --only budaya wisata    # hanya isi target tertentu
    python seed.py --reset                 # kosongkan dulu tabel yang di-seed, baru isi ulang
    python seed.py --reset --only wisata -y  # reset tanpa tanya konfirmasi
"""
import argparse

from werkzeug.security import generate_password_hash

from app import app
from core import db as dbcore
from core.security import generate_fingerprint
from models import admins as admin_model
from models import budaya as budaya_model
from models import ratings as ratings_model
from models import wisata as wisata_model

ADMIN_SEED = {
    "username": "admin",
    "password": "admin123",
    "nama_lengkap": "Administrator Sorong Raya",
}

BUDAYA_SEED = [
    dict(
        judul="Tari Suanggi",
        kategori="Tarian Tradisional",
        ringkasan="Tarian mistis Suku Moi yang menggambarkan kisah roh leluhur dan kekuatan alam gaib.",
        konten_lengkap=(
            "Tari Suanggi merupakan tarian sakral yang dipentaskan dalam upacara adat tertentu Suku Moi. "
            "Gerakannya lambat dan penuh penghayatan, melambangkan komunikasi antara dunia manusia dan "
            "roh leluhur. Penari biasanya mengenakan atribut adat berupa daun sagu dan aksesori dari bulu "
            "burung sebagai simbol penghormatan terhadap alam."
        ),
    ),
    dict(
        judul="Anyaman Noken Khas Moi",
        kategori="Kerajinan Tangan",
        ringkasan="Tas rajut tradisional dari serat kulit kayu yang menjadi identitas budaya masyarakat Papua.",
        konten_lengkap=(
            "Noken dibuat dari serat kulit kayu yang dipintal manual lalu dianyam menjadi tas serbaguna. "
            "Bagi Suku Moi, noken bukan sekadar wadah barang, tapi juga simbol kedewasaan perempuan dan "
            "kemandirian ekonomi keluarga. Motif dan ukuran noken bisa menunjukkan status sosial pemakainya."
        ),
    ),
    dict(
        judul="Musik Tifa dan Nyanyian Adat",
        kategori="Musik Tradisional",
        ringkasan="Alat musik pukul khas Papua yang mengiringi hampir seluruh upacara adat dan tarian Suku Moi.",
        konten_lengkap=(
            "Tifa terbuat dari batang kayu berongga yang salah satu ujungnya dilapisi kulit hewan sebagai "
            "membran. Irama tifa dipadukan dengan nyanyian adat berbahasa Moi, biasa dimainkan saat "
            "penyambutan tamu, pesta panen, maupun ritual keagamaan tradisional."
        ),
    ),
    dict(
        judul="Upacara Watani Kambik",
        kategori="Upacara Adat",
        ringkasan="Ritual pembayaran mas kawin adat yang menjadi syarat sahnya pernikahan menurut hukum adat Suku Moi.",
        konten_lengkap=(
            "Watani Kambik adalah prosesi penyerahan mas kawin berupa barang adat (seperti piring antik, "
            "manik-manik, dan kain timur) dari keluarga mempelai pria kepada keluarga mempelai wanita. "
            "Upacara ini disaksikan oleh kepala adat dan tetua kampung sebagai bentuk pengesahan sosial."
        ),
    ),
    dict(
        judul="Bahasa Moi dan Tradisi Lisan",
        kategori="Bahasa & Sastra Lisan",
        ringkasan="Bahasa asli Suku Moi yang diwariskan turun-temurun lewat cerita rakyat dan pantun adat.",
        konten_lengkap=(
            "Bahasa Moi termasuk rumpun bahasa Papua Barat yang penuturnya tersebar di wilayah Sorong Raya. "
            "Tradisi lisan seperti dongeng asal-usul kampung dan pantun adat menjadi media utama pewarisan "
            "nilai budaya karena sebagian besar sejarah Suku Moi belum dituliskan secara formal."
        ),
    ),
    dict(
        judul="Papeda dan Kuliner Khas Sorong",
        kategori="Kuliner Tradisional",
        ringkasan="Makanan pokok berbahan sagu yang menjadi hidangan khas masyarakat Papua, termasuk Sorong Raya.",
        konten_lengkap=(
            "Papeda dibuat dari pati sagu yang dimasak hingga bertekstur kenyal seperti lem, biasa disantap "
            "bersama kuah ikan kuning berbumbu kunyit. Hidangan ini mencerminkan kedekatan masyarakat "
            "Sorong dengan hutan sagu dan hasil laut sebagai dua sumber pangan utama."
        ),
    ),
]

WISATA_SEED = [
    dict(
        nama_wisata="Pulau Um",
        wilayah="Kabupaten Sorong",
        deskripsi="Pulau kecil berpasir putih dengan air laut jernih, populer untuk snorkeling dan memancing.",
        fasilitas="Perahu sewa, gazebo, area snorkeling",
        alamat="Perairan Distrik Moisegen, Kabupaten Sorong",
        tiket_masuk="Rp 15.000",
        jam_operasional="07.00 - 17.00 WIT",
    ),
    dict(
        nama_wisata="Malaumkarta",
        wilayah="Kabupaten Sorong",
        deskripsi="Kampung wisata budaya di tepi Teluk Doreri dengan rumah panggung khas dan aktivitas nelayan tradisional.",
        fasilitas="Homestay, perahu wisata, pemandu lokal",
        alamat="Distrik Makbon, Kabupaten Sorong",
        tiket_masuk="Gratis / Menyesuaikan",
        jam_operasional="Setiap Hari",
    ),
    dict(
        nama_wisata="Klasabi Waterpark",
        wilayah="Kota Sorong",
        deskripsi="Taman rekreasi air keluarga dengan kolam renang dan wahana permainan anak.",
        fasilitas="Kolam renang, wahana air, kantin, mushola",
        alamat="Klasabi, Kota Sorong",
        tiket_masuk="Rp 25.000",
        jam_operasional="08.00 - 18.00 WIT",
    ),
    dict(
        nama_wisata="Tugu Kilometer Nol",
        wilayah="Kota Sorong",
        deskripsi="Monumen penanda titik nol jalan Trans Papua Barat, jadi lokasi favorit warga untuk berfoto dan bersantai.",
        fasilitas="Area parkir, pedagang kaki lima, spot foto",
        alamat="Pusat Kota Sorong",
        tiket_masuk="Gratis",
        jam_operasional="Setiap Hari",
    ),
    dict(
        nama_wisata="Pulau Buaya",
        wilayah="Kabupaten Sorong",
        deskripsi="Pulau eksotis dengan hamparan terumbu karang yang cocok untuk snorkeling maupun diving.",
        fasilitas="Perahu sewa, spot diving, camping ground",
        alamat="Perairan Kabupaten Sorong",
        tiket_masuk="Rp 20.000",
        jam_operasional="07.00 - 17.00 WIT",
    ),
    dict(
        nama_wisata="Pantai Tembok Berlin",
        wilayah="Kota Sorong",
        deskripsi="Pantai kecil dengan tanggul pemecah ombak yang jadi lokasi favorit menikmati matahari terbenam.",
        fasilitas="Warung kuliner, area duduk santai, spot foto",
        alamat="Kelurahan Tanjung Kasuari, Kota Sorong",
        tiket_masuk="Gratis / Menyesuaikan",
        jam_operasional="Setiap Hari",
    ),
]

# (nama_wisata, skor_bintang, komentar) - wisata harus sudah ada (lihat WISATA_SEED).
RATING_SEED = [
    ("Pulau Um", 5, "Airnya jernih banget, cocok buat snorkeling bareng keluarga."),
    ("Pulau Um", 4, "Bagus tapi perlu sewa perahu dari dermaga, agak jauh."),
    ("Klasabi Waterpark", 4, "Seru buat bawa anak-anak main air di akhir pekan."),
    ("Klasabi Waterpark", 5, "Wahana lengkap dan tempatnya bersih."),
    ("Malaumkarta", 5, "Suasana kampungnya masih sangat alami, warganya ramah."),
    ("Tugu Kilometer Nol", 4, "Spot foto ikonik, ramai kalau sore hari."),
    ("Pulau Buaya", 5, "Terumbu karangnya masih bagus, recommended buat diving."),
    ("Pantai Tembok Berlin", 3, "Pemandangan oke tapi agak kotor pas musim hujan."),
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


def seed_admin():
    if admin_model.find_by_username(ADMIN_SEED["username"]):
        print(f"  - admin '{ADMIN_SEED['username']}' sudah ada, dilewati")
        return
    dbcore.execute(
        "INSERT INTO admins (username, password_hash, nama_lengkap) VALUES (%s, %s, %s)",
        (
            ADMIN_SEED["username"],
            generate_password_hash(ADMIN_SEED["password"]),
            ADMIN_SEED["nama_lengkap"],
        ),
    )
    print(f"  + admin '{ADMIN_SEED['username']}' dibuat (password: {ADMIN_SEED['password']})")


def seed_budaya():
    for item in BUDAYA_SEED:
        existing = dbcore.query_one("SELECT id FROM budaya WHERE judul = %s", (item["judul"],))
        if existing:
            print(f"  - budaya '{item['judul']}' sudah ada, dilewati")
            continue
        budaya_model.create(item["judul"], item["kategori"], item["ringkasan"], item["konten_lengkap"], None)
        print(f"  + budaya '{item['judul']}' ditambahkan")


def seed_wisata():
    for item in WISATA_SEED:
        existing = dbcore.query_one("SELECT id FROM wisata WHERE nama_wisata = %s", (item["nama_wisata"],))
        if existing:
            print(f"  - wisata '{item['nama_wisata']}' sudah ada, dilewati")
            continue
        data = {**WISATA_DEFAULTS, **item}
        wisata_model.create(data)
        print(f"  + wisata '{item['nama_wisata']}' ditambahkan")


def seed_ratings():
    for idx, (nama_wisata, skor, komentar) in enumerate(RATING_SEED):
        wisata = dbcore.query_one("SELECT id FROM wisata WHERE nama_wisata = %s", (nama_wisata,))
        if not wisata:
            print(f"  - lewati rating untuk '{nama_wisata}' (wisata belum ada, jalankan --only wisata dulu)")
            continue
        fingerprint = generate_fingerprint(f"10.20.30.{idx}", "seed-script/1.0")
        _, error = ratings_model.create(wisata["id"], skor, komentar, fingerprint, "approved")
        if error:
            print(f"  - rating {skor}★ untuk '{nama_wisata}' sudah ada, dilewati")
        else:
            print(f"  + rating {skor}★ untuk '{nama_wisata}' ditambahkan")


SEEDERS = {
    "admin": seed_admin,
    "budaya": seed_budaya,
    "wisata": seed_wisata,
    "ratings": seed_ratings,
}


def reset_tables(targets):
    """Kosongkan tabel yang mau di-seed ulang. FK ON DELETE CASCADE otomatis
    membersihkan galeri (budaya_galeri/wisata_galeri) & rating terkait."""
    if "ratings" in targets:
        dbcore.execute("DELETE FROM ratings")
        print("  * tabel ratings dikosongkan")
    if "wisata" in targets:
        dbcore.execute("DELETE FROM wisata")
        dbcore.execute("ALTER TABLE wisata AUTO_INCREMENT = 1")
        print("  * tabel wisata (+ galeri & rating terkait) dikosongkan")
    if "budaya" in targets:
        dbcore.execute("DELETE FROM budaya")
        dbcore.execute("ALTER TABLE budaya AUTO_INCREMENT = 1")
        print("  * tabel budaya (+ galeri terkait) dikosongkan")


def parse_args():
    parser = argparse.ArgumentParser(description="Seeder data dummy Sorong Culture Tourism.")
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
        help="Kosongkan dulu tabel yang mau di-seed sebelum mengisi ulang (tidak berlaku untuk admin).",
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
            resettable = [t for t in targets if t != "admin"]
            if resettable:
                if not args.yes:
                    confirm = input(
                        f"Ini akan MENGHAPUS semua data di tabel {', '.join(resettable)} "
                        "(dan turunannya) sebelum mengisi ulang. Lanjutkan? [y/N] "
                    )
                    if confirm.strip().lower() != "y":
                        print("Dibatalkan.")
                        return
                reset_tables(resettable)

        for target in targets:
            print(f"{target.capitalize()}:")
            SEEDERS[target]()

        print("Selesai.")


if __name__ == "__main__":
    main()
