"""Helper koneksi & kueri MySQL menggunakan PyMySQL (dipakai via Flask `g`)."""
import pymysql
import pymysql.cursors
from flask import current_app, g


def get_db():
    """Mengembalikan koneksi MySQL yang di-cache pada konteks request Flask."""
    if "db" not in g:
        cfg = current_app.config
        g.db = pymysql.connect(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            database=cfg["DB_NAME"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def query_all(sql, params=None):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def query_one(sql, params=None):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql, params=None):
    """Jalankan INSERT/UPDATE/DELETE, commit, dan kembalikan lastrowid."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params or ())
    db.commit()
    return cur.lastrowid


def execute_unique_safe(sql, params=None):
    """Sama seperti execute, tapi menangkap pelanggaran UNIQUE KEY (IntegrityError 1062)."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(sql, params or ())
        db.commit()
        return cur.lastrowid, None
    except pymysql.err.IntegrityError as exc:
        db.rollback()
        return None, exc
