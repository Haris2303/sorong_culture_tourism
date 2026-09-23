"""Data access layer untuk entitas admin."""
from core import db as dbcore


def find_by_username(username):
    return dbcore.query_one("SELECT * FROM admins WHERE username = %s", (username,))
