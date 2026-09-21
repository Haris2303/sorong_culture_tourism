"""Sanitasi & konversi HTML hasil editor WYSIWYG (Quill) pada field konten panjang."""
import html as html_module
import re

import nh3

_ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "strike",
    "blockquote", "ol", "ul", "li", "h2", "h3", "a",
}
_ALLOWED_ATTRIBUTES = {"a": {"href"}}
_ALLOWED_SCHEMES = {"http", "https", "mailto"}

_BLOCK_BREAK_RE = re.compile(r"</(p|li|ul|ol|blockquote|h[1-6])>|<br\s*/?>", re.IGNORECASE)


def sanitize_content_html(value: str) -> str:
    """Bersihkan HTML dari editor WYSIWYG sebelum disimpan (cegah stored XSS)."""
    return nh3.clean(
        value or "",
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_SCHEMES,
        link_rel="noopener noreferrer nofollow",
    )


def html_to_plain_text(value: str) -> str:
    """Ubah HTML konten menjadi teks polos, pertahankan jeda antar paragraf/list (untuk konteks RAG)."""
    if not value:
        return ""
    with_breaks = _BLOCK_BREAK_RE.sub("\n", value)
    stripped = nh3.clean(with_breaks, tags=set())
    unescaped = html_module.unescape(stripped)
    lines = [line.strip() for line in unescaped.splitlines()]
    return "\n".join(line for line in lines if line)
