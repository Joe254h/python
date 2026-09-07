"""File in, canonical text out, with offsets that survive the whole pipeline.

Every highlight in every report is a character range into the string this
module returns, so the contract here is stricter than "get the words out":

  * The returned text is the *only* coordinate system. Nothing downstream ever
    re-reads the file.
  * Normalisation happens before offsets are handed out, never after. Changing
    the string later would silently move every match.
  * Page boundaries are recorded rather than inferred, so a report can say
    which page a passage came from.

Plain text and DOCX are handled with the standard library alone -- a .docx is
a zip of XML, which `zipfile` and `xml.etree` read without help. PDF needs a
real parser; PyMuPDF or pypdf is used when installed and a clear error is
raised when not, because a silently empty extraction would look like a clean
document rather than a broken one.
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .types import Document, PageBreak

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

#: Characters that carry no meaning for similarity but wreck exact matching.
_SMART = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "−": "-",
    " ": " ", " ": " ", " ": " ", "​": "",
    "﻿": "", "…": "...",
}

SUPPORTED = (".txt", ".md", ".markdown", ".docx", ".pdf")


class ExtractionError(RuntimeError):
    """Raised when a file cannot be read into text we would be willing to score."""


def normalise(raw: str) -> str:
    """Canonicalise text *before* any offset is derived from it.

    NFKC folds compatibility forms so that ligatures and full-width characters
    compare equal to their plain equivalents. Smart punctuation is flattened
    because a quotation copied through two word processors should still match
    its source. Runs of whitespace collapse to a single space, but newlines
    survive -- paragraph structure is what the AI detector scores over.
    """
    text = unicodedata.normalize("NFKC", raw)
    for bad, good in _SMART.items():
        text = text.replace(bad, good)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def _extract_txt(path: Path) -> tuple[str, list[PageBreak]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return raw, [PageBreak(page=1, offset=0)]


def _extract_docx(path: Path) -> tuple[str, list[PageBreak]]:
    """Read paragraph text straight out of word/document.xml.

    We join <w:t> runs inside each <w:p> with no separator (Word splits a
    single word across runs whenever formatting changes mid-word, so inserting
    anything here would corrupt the text) and separate paragraphs with a
    newline. Explicit page breaks are recorded; Word does not store the
    positions of *automatic* page breaks at all, so a docx without manual
    breaks reports as one page rather than guessing.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ExtractionError(f"{path.name} is not a readable .docx file") from exc

    root = ET.fromstring(xml)
    parts: list[str] = []
    breaks = [PageBreak(page=1, offset=0)]
    page = 1
    cursor = 0

    for para in root.iter(f"{WORD_NS}p"):
        runs: list[str] = []
        for node in para.iter():
            tag = node.tag
            if tag == f"{WORD_NS}t":
                runs.append(node.text or "")
            elif tag == f"{WORD_NS}tab":
                runs.append(" ")
            elif tag == f"{WORD_NS}br" and node.get(f"{WORD_NS}type") == "page":
                page += 1
                breaks.append(PageBreak(page=page, offset=cursor + len("".join(runs))))
        line = "".join(runs)
        parts.append(line)
        cursor += len(line) + 1

    if not any(p.strip() for p in parts):
        raise ExtractionError(f"{path.name} contained no extractable text")
    return "\n".join(parts), breaks


def _extract_pdf(path: Path) -> tuple[str, list[PageBreak]]:
    """PyMuPDF if present, pypdf as fallback. No silent empty result."""
    pages: list[str] = []
    try:
        import fitz  # PyMuPDF

        with fitz.open(path) as doc:
            pages = [p.get_text("text") for p in doc]
    except ImportError:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ExtractionError(
                "PDF extraction needs PyMuPDF or pypdf. Install one of them: "
                "pip install pymupdf"
            ) from exc
        reader = PdfReader(str(path))
        pages = [(p.extract_text() or "") for p in reader.pages]

    if not any(p.strip() for p in pages):
        raise ExtractionError(
            f"{path.name} yielded no text. It is probably a scan; OCR is not "
            "wired up yet, so this document cannot be scored."
        )

    text_parts: list[str] = []
    breaks: list[PageBreak] = []
    cursor = 0
    for i, page_text in enumerate(pages, start=1):
        breaks.append(PageBreak(page=i, offset=cursor))
        text_parts.append(page_text)
        cursor += len(page_text) + 1
    return "\n".join(text_parts), breaks


def _rescale_breaks(
    raw: str, clean: str, breaks: list[PageBreak]
) -> list[PageBreak]:
    """Move page offsets from raw coordinates into normalised coordinates.

    Normalisation only ever removes or shortens whitespace, so the ratio of
    non-space characters before a point is preserved. We count non-space
    characters up to each raw offset, then walk the clean string until the same
    count is reached. Exact, and cheap enough at page granularity.
    """
    if not breaks:
        return [PageBreak(page=1, offset=0)]

    targets = sorted(breaks, key=lambda b: b.offset)
    dense_at: list[int] = []
    dense = 0
    idx = 0
    for i, ch in enumerate(raw):
        while idx < len(targets) and targets[idx].offset == i:
            dense_at.append(dense)
            idx += 1
        if not ch.isspace():
            dense += 1
    while idx < len(targets):
        dense_at.append(dense)
        idx += 1

    out: list[PageBreak] = []
    want = 0
    dense = 0
    for i, ch in enumerate(clean):
        while want < len(dense_at) and dense_at[want] <= dense:
            out.append(PageBreak(page=targets[want].page, offset=i))
            want += 1
        if not ch.isspace():
            dense += 1
    while want < len(dense_at):
        out.append(PageBreak(page=targets[want].page, offset=len(clean)))
        want += 1
    return out


def extract(path: str | Path) -> Document:
    """Read a file into a `Document` with normalised text and page offsets."""
    path = Path(path)
    if not path.exists():
        raise ExtractionError(f"no such file: {path}")

    suffix = path.suffix.lower()
    if suffix in (".txt", ".md", ".markdown"):
        raw, breaks = _extract_txt(path)
    elif suffix == ".docx":
        raw, breaks = _extract_docx(path)
    elif suffix == ".pdf":
        raw, breaks = _extract_pdf(path)
    else:
        raise ExtractionError(
            f"unsupported file type '{suffix}'. Supported: {', '.join(SUPPORTED)}"
        )

    clean = normalise(raw)
    if not clean.strip():
        raise ExtractionError(f"{path.name} contained no extractable text")

    return Document(
        text=clean,
        page_breaks=_rescale_breaks(raw, clean, breaks),
        meta={
            "filename": path.name,
            "suffix": suffix,
            "bytes": path.stat().st_size,
            "pages": len(breaks),
        },
    )


def extract_text(raw: str, filename: str = "inline.txt") -> Document:
    """Same contract as `extract`, for text already in memory."""
    clean = normalise(raw)
    if not clean.strip():
        raise ExtractionError("no extractable text")
    return Document(
        text=clean,
        page_breaks=[PageBreak(page=1, offset=0)],
        meta={"filename": filename, "suffix": ".txt", "bytes": len(raw), "pages": 1},
    )
