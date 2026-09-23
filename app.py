"""Sistem Informasi & Chatbot Budaya-Wisata Sorong Raya.

Entry point aplikasi: inisialisasi Flask & ekstensi, lalu registrasi seluruh
router (lihat paket `routes/`). Logika data ada di `models/`, logika bisnis
ada di `services/` & `core/`, dan tampilan ada di `templates/`.
"""
import os

from flask import Flask
from flask_wtf import CSRFProtect

from config import Config
from core import db as dbcore
from core.template_helpers import register as register_template_helpers
from extensions import limiter
from routes import register_routes

app = Flask(__name__)
app.config.from_object(Config)

dbcore.init_app(app)
CSRFProtect(app)
limiter.init_app(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["KNOWLEDGE_DOCS_DIR"], exist_ok=True)
os.makedirs(app.config["CHROMA_PERSIST_DIR"], exist_ok=True)

register_template_helpers(app)
register_routes(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"], threaded=True)
