"""Guard otentikasi admin berbasis session, dipakai oleh seluruh rute /admin/*."""
import functools

from flask import redirect, request, session, url_for


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped
