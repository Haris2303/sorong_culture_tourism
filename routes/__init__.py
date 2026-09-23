"""Registrasi seluruh router aplikasi ke instance Flask."""
from routes import (
    admin_auth,
    admin_budaya,
    admin_dashboard,
    admin_knowledge,
    admin_ratings,
    admin_wisata,
    api,
    errors,
    public,
)


def register_routes(app):
    public.register(app)
    api.register(app)
    admin_auth.register(app)
    admin_dashboard.register(app)
    admin_budaya.register(app)
    admin_wisata.register(app)
    admin_ratings.register(app)
    admin_knowledge.register(app)
    errors.register(app)
