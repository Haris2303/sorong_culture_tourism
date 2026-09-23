"""Instance ekstensi Flask bersama.

Dibuat tanpa `app` di sini (baru di-`init_app` pada app.py) supaya modul rute
bisa mengimpor `limiter` langsung tanpa risiko circular import dengan app.py.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
