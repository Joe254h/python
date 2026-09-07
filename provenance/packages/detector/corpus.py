"""The corpus the retrieval engine searches against.

Phase 2 of the plan searches one corpus only: documents previously submitted to
this deployment. That is a deliberate starting point rather than a limitation to
apologise for. It needs no external API quota, no crawl and no licence
negotiation, and it catches the case that actually happens in a cohort -- two
students handing in the same work. Turnitin's real advantage over an independent
tool is a student-paper repository, and this is the one part of it anybody can
build.

Winnowed fingerprints and the document signature are persisted alongside the
text, so the inverted index rebuilds at startup without re-tokenising every
document. The index itself stays in memory; at the scale where that stops
working, `FingerprintIndex`'s two dictionaries move to Redis and nothing else
changes.

Internal matches are anonymised at this boundary rather than in the UI. A
similarity report needs to say "this matches another submission in this
institution" and must not say whose -- the person reading a report is usually
not entitled to another student's identity, and the pipeline should make
leaking it awkward rather than trusting a template to remember.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .fingerprint import (
    Fingerprint,
    FingerprintIndex,
    Signature,
    align,
    minhash,
    winnow,
)
from .segment import SHINGLE_SIZE, mark_exclusions, shingles
from .types import Document, Match, Source, Span

SCHEMA = """
CREATE TABLE IF NOT EXISTS corpus_document (
    doc_id       TEXT PRIMARY KEY,
    origin       TEXT NOT NULL,
    title        TEXT NOT NULL,
    url          TEXT,
    anonymised   INTEGER NOT NULL DEFAULT 0,
    text         TEXT NOT NULL,
    signature    TEXT NOT NULL,
    fingerprints TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_corpus_origin ON corpus_document(origin);
"""


class Corpus:
    """SQLite-backed document store with an in-memory fingerprint index."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self.index = FingerprintIndex()
        self.signatures: dict[str, Signature] = {}
        self._load_index()

    def close(self) -> None:
        self.conn.close()

    # ---------------------------------------------------------------- loading

    def _load_index(self) -> None:
        for row in self.conn.execute(
            "SELECT doc_id, origin, title, url, anonymised, signature, fingerprints "
            "FROM corpus_document"
        ):
            fps = [
                Fingerprint(hash=h, span=Span(s, e))
                for h, s, e in json.loads(row["fingerprints"])
            ]
            self.index.add(row["doc_id"], fps, _source(row))
            self.signatures[row["doc_id"]] = Signature(
                values=tuple(json.loads(row["signature"]))
            )

    # ------------------------------------------------------------------ write

    def fingerprint(self, doc: Document) -> tuple[list[Fingerprint], Signature]:
        """Winnowed fingerprints plus a document-level signature."""
        mark_exclusions(doc)
        grams = shingles(doc.text, SHINGLE_SIZE, exclude=doc.excluded)
        return winnow(grams), minhash(grams)

    def add(
        self,
        doc_id: str,
        doc: Document,
        title: str,
        origin: str = "internal",
        url: str | None = None,
        anonymised: bool | None = None,
        fingerprints: list[Fingerprint] | None = None,
        signature: Signature | None = None,
    ) -> None:
        """Put a document in the searchable corpus.

        Fingerprints may be passed in when the caller has already computed them
        -- the pipeline always has, and recomputing would double the cost of
        every submission.
        """
        if anonymised is None:
            anonymised = origin == "internal"
        if fingerprints is None or signature is None:
            fingerprints, signature = self.fingerprint(doc)

        self.conn.execute(
            "INSERT OR REPLACE INTO corpus_document "
            "(doc_id, origin, title, url, anonymised, text, signature, fingerprints) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                doc_id,
                origin,
                title,
                url,
                int(anonymised),
                doc.text,
                json.dumps(list(signature.values)),
                json.dumps([[f.hash, f.span.start, f.span.end] for f in fingerprints]),
            ),
        )
        self.conn.commit()
        self.index.add(
            doc_id,
            fingerprints,
            Source(
                source_id=doc_id,
                title=title,
                origin=origin,
                url=url,
                anonymised=anonymised,
            ),
        )
        self.signatures[doc_id] = signature

    # ------------------------------------------------------------------- read

    def text_of(self, doc_id: str) -> str:
        row = self.conn.execute(
            "SELECT text FROM corpus_document WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        return row["text"] if row else ""

    def size(self) -> int:
        return len(self.index)

    def search(
        self,
        doc: Document,
        fingerprints: list[Fingerprint],
        signature: Signature | None = None,
        exclude_id: str | None = None,
        max_sources: int = 25,
    ) -> list[Match]:
        """Find and align every match for a fingerprinted document."""
        hits = self.index.query(fingerprints, exclude=exclude_id)

        # Most shared fingerprints first: the sources a reader most needs to
        # see are the ones a truncated report must not drop.
        ranked = sorted(hits.items(), key=lambda kv: -len(kv[1]))[:max_sources]

        matches: list[Match] = []
        for doc_id, pairs in ranked:
            doc_sim = 0.0
            if signature is not None and doc_id in self.signatures:
                doc_sim = signature.jaccard(self.signatures[doc_id])
            matches.extend(
                align(
                    pairs=pairs,
                    source=self.index.sources[doc_id],
                    text=doc.text,
                    source_text=self.text_of(doc_id),
                    doc_similarity=doc_sim,
                )
            )
        return sorted(matches, key=lambda m: (m.span.start, -m.score))


def _source(row: sqlite3.Row) -> Source:
    return Source(
        source_id=row["doc_id"],
        title=row["title"],
        origin=row["origin"],
        url=row["url"],
        anonymised=bool(row["anonymised"]),
    )
