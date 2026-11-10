"""Turn uploaded files into editor HTML. Supports .txt, .md and .docx."""
import html
import io
import re

import markdown
from docx import Document as DocxFile

SUPPORTED = {".txt", ".md", ".docx"}


def _txt(raw: bytes) -> str:
    text = raw.decode("utf-8-sig")
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "".join(f"<p>{html.escape(p.strip()).replace(chr(10), '<br>')}</p>" for p in paras)


def _docx(raw: bytes) -> str:
    out, open_list = [], None

    def close():
        nonlocal open_list
        if open_list:
            out.append(f"</{open_list}>")
            open_list = None

    for p in DocxFile(io.BytesIO(raw)).paragraphs:
        text = html.escape(p.text.strip())
        if not text:
            continue
        style = (p.style.name if p.style is not None else "").lower()
        kind = "ol" if "number" in style else "ul" if "list" in style else None
        if kind:
            if open_list != kind:
                close()
                out.append(f"<{kind}>")
                open_list = kind
            out.append(f"<li>{text}</li>")
            continue
        close()
        if style == "title" or style == "heading 1":
            out.append(f"<h1>{text}</h1>")
        elif style.startswith("heading"):
            out.append(f"<h2>{text}</h2>")
        else:
            out.append(f"<p>{text}</p>")
    close()
    return "".join(out)


def to_html(ext: str, raw: bytes) -> str:
    if ext == ".txt":
        return _txt(raw)
    if ext == ".md":
        return markdown.markdown(raw.decode("utf-8-sig"))
    if ext == ".docx":
        return _docx(raw)
    raise ValueError("unsupported type")
