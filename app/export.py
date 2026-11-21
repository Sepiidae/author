"""Export a book to TXT, Markdown, HTML, EPUB or Amazon (KDP) formats.

All source text is markdown. We render it to the requested format using a
small, dependency-light pipeline (``markdown`` for HTML, ``ebooklib`` for
EPUB). The Amazon export produces a KDP-friendly HTML file that can be
imported directly into Kindle Create / KDP.
"""
from __future__ import annotations

import html
import io

import markdown as md_module

from .models import Book, Chapter


def _md_to_html(md: str) -> str:
    return md_module.markdown(
        md,
        extensions=["extra", "sane_lists", "toc"],
        output_format="html5",
    )


def _collect_chapters(book: Book) -> list[Chapter]:
    return sorted(book.chapters, key=lambda c: (c.order, c.created_at))


def render_txt(book: Book) -> tuple[str, str]:
    lines: list[str] = [f"# {book.title}", ""]
    if book.description:
        lines += [book.description, ""]
    for ch in _collect_chapters(book):
        lines += [f"# {ch.title}", "", ch.body, ""]
    text = "\n".join(lines)
    return text, "text/plain"


def render_markdown(book: Book) -> tuple[str, str]:
    parts = [f"# {book.title}", ""]
    if book.description:
        parts += [book.description, ""]
    for ch in _collect_chapters(book):
        parts += [f"# {ch.title}", "", ch.body, ""]
    return "\n".join(parts), "text/markdown"


def render_html(book: Book, *, full_page: bool = True) -> tuple[str, str]:
    body_parts: list[str] = []
    body_parts.append(f"<h1>{html.escape(book.title)}</h1>")
    if book.description:
        body_parts.append(_md_to_html(book.description))
    for ch in _collect_chapters(book):
        body_parts.append(f"<h2>{html.escape(ch.title)}</h2>")
        body_parts.append(_md_to_html(ch.body))
    body = "\n".join(body_parts)
    if not full_page:
        return body, "text/html"
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(book.title)}</title>
<style>
  body {{ max-width: 40rem; margin: 2rem auto; padding: 0 1rem;
         font: 1.1rem/1.6 Georgia, serif; }}
  h1, h2 {{ line-height: 1.2; }}
  img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
{body}
</body>
</html>"""
    return page, "text/html"


def render_amazon(book: Book) -> tuple[str, str]:
    """KDP-friendly HTML (no external CSS/JS, embedded images, clean headings).

    This file can be imported into Kindle Create or uploaded to KDP directly.
    """
    html_body, _ = render_html(book, full_page=False)
    page = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
<meta charset="utf-8"/>
<title>{html.escape(book.title)}</title>
<style>
  body {{ font-family: Georgia, serif; line-height: 1.5; margin: 5%; }}
  h1 {{ page-break-before: always; text-align: center; }}
  h2 {{ text-align: left; }}
  img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
    return page, "application/xhtml+xml"


def render_epub(book: Book) -> bytes:
    """Build an EPUB3 file in memory using ebooklib."""
    from ebooklib import epub

    settings = {
        "title": book.title,
        "identifier": f"urn:uuid:{book.id}",
        "lang": "en",
    }
    e = epub.EpubBook()
    e.set_identifier(settings["identifier"])
    e.set_title(settings["title"])
    e.set_language(settings["lang"])
    if book.series_id:
        # attach author/series metadata when available
        pass

    # Cover / intro page
    intro = epub.EpubHtml(title="Title", file_name="title.xhtml", lang=settings["lang"])
    intro.content = f"<h1>{html.escape(book.title)}</h1>" + (
        f"<p>{html.escape(book.description)}</p>" if book.description else ""
    )
    e.add_item(intro)

    chapters: list[epub.EpubHtml] = []
    for i, ch in enumerate(_collect_chapters(book), start=1):
        doc = epub.EpubHtml(title=ch.title, file_name=f"chap_{i}.xhtml", lang=settings["lang"])
        doc.content = f"<h2>{html.escape(ch.title)}</h2>\n{_md_to_html(ch.body)}"
        chapters.append(doc)
        e.add_item(doc)

    e.toc = [intro] + chapters
    e.add_item(epub.EpubNcx())
    e.add_item(epub.EpubNav())
    e.spine = ["nav", intro] + chapters

    buf = io.BytesIO()
    epub.write_epub(buf, e, {})
    return buf.getvalue()


EXPORTERS = {
    "txt": render_txt,
    "md": render_markdown,
    "markdown": render_markdown,
    "html": render_html,
    "amazon": render_amazon,
    "epub": render_epub,
}


def export_book(book: Book, fmt: str):
    """Return ``(payload, content_type, filename)`` for the requested format.

    ``payload`` is ``str`` for text formats and ``bytes`` for EPUB.
    """
    fmt = fmt.lower()
    if fmt not in EXPORTERS:
        raise ValueError(f"Unsupported format: {fmt}")
    if fmt == "epub":
        payload = render_epub(book)
        return payload, "application/epub+zip", f"{book.title}.epub"
    payload, content_type = EXPORTERS[fmt](book)
    ext = {"txt": "txt", "md": "md", "markdown": "md", "html": "html", "amazon": "html"}[fmt]
    return payload, content_type, f"{book.title}.{ext}"
