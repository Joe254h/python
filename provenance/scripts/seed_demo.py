#!/usr/bin/env python3
"""Create a demo account, some redemption codes, and a small corpus.

Run it against a throwaway database to get a dashboard with something on it:

    python scripts/seed_demo.py --db data/demo.db --corpus data/demo-corpus.db
    PROVENANCE_DB=data/demo.db PROVENANCE_CORPUS=data/demo-corpus.db \\
        python -m apps.api.main

The seeded documents are written for this purpose and are not anyone's work.
The point of the pair is to show the product doing its actual job: the second
document reuses two paragraphs of the first, so the report has real matches
with real spans -- produced by the real detector, not by MockDetector.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages"))

from apps.api import auth, credits  # noqa: E402
from apps.api.db import connect, transaction  # noqa: E402
from detector import Corpus, Pipeline, extract_text  # noqa: E402

ORIGINAL = """Academic integrity and the limits of automated detection

Academic integrity is the moral code of academia. It involves honesty in
research, teaching and learning, and it requires that scholars acknowledge the
contributions of others through accurate and complete citation of their work.

Institutions maintain policies that define academic misconduct. These policies
typically cover plagiarism, collusion between students, fabrication of research
data, and the purchase of written work from a third party contractor. Penalties
range from a formal warning through to expulsion from a programme of study.

Automated similarity detection changed enforcement in the 1990s by making
large-scale comparison practical. A similarity score is not by itself evidence
of misconduct: correctly quoted and cited material produces matches, and so do
standard method sections and common phrases in a technical field.

The purpose of these rules is not punishment but the preservation of public
trust in the qualifications that an institution awards to all of its graduates.
"""

REUSED = """Detection tooling in postgraduate assessment

Institutions maintain policies that define academic misconduct. These policies
typically cover plagiarism, collusion between students, fabrication of research
data, and the purchase of written work from a third party contractor. Penalties
range from a formal warning through to expulsion from a programme of study.

This paragraph is entirely original to the second document, and discusses the
seasonal migration of the intertropical convergence zone across the Sahel and
what that implies for the onset of the rainy season in a warming climate.

A similarity score is not by itself evidence of misconduct: correctly quoted
and cited material produces matches, and so do standard method sections and
common phrases in a technical field.
"""

UNRELATED = """Rainfall variability in the West African Sahel

The intertropical convergence zone migrates seasonally across West Africa, and
its position controls the onset of the rainy season across the Sahel. Coupled
models disagree about how anthropogenic forcing will shift that position over
the coming decades, which matters for agricultural planning in the region.

Observational records from ground stations remain sparse throughout the region,
which complicates any attempt to validate the reanalysis products that most
published studies depend upon for boundary conditions and for verification.
"""

CODES = [("PROV-DEMO-0001", 10), ("PROV-DEMO-0002", 25), ("PROV-DEMO-0003", 50)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(ROOT / "data" / "demo.db"))
    parser.add_argument("--corpus", default=str(ROOT / "data" / "demo-corpus.db"))
    parser.add_argument("--email", default="demo@provenance.local")
    parser.add_argument("--password", default="demo-password")
    args = parser.parse_args()

    conn = connect(args.db)
    corpus = Corpus(args.corpus)
    pipeline = Pipeline(corpus=corpus)

    try:
        user_id = auth.create_user(conn, args.email, args.password, "Demo user")
        credits.grant(conn, user_id, 25, "demo seed", f"seed:{user_id}")
        print(f"created  {args.email} / {args.password}")
    except auth.AuthError:
        user_id = auth.authenticate(conn, args.email, args.password)
        print(f"reusing  {args.email}")

    for code, amount in CODES:
        credits.create_code(conn, code, amount)
    print(f"codes    {', '.join(c for c, _ in CODES)}")

    docs = [
        ("seed-original", "integrity-review.txt", ORIGINAL),
        ("seed-unrelated", "sahel-rainfall.txt", UNRELATED),
        ("seed-reused", "detection-tooling.txt", REUSED),
    ]
    for doc_id, title, text in docs:
        doc = extract_text(text)
        report = pipeline.run(doc_id, doc, title=title)
        # Also record it as a submission, so the seeded dashboard opens showing
        # real completed work rather than an empty shell.
        with transaction(conn):
            conn.execute(
                "INSERT OR REPLACE INTO submission (submission_id, user_id, "
                "filename, size_bytes, stage, word_count, similarity, band, "
                "ai_probability, is_mock, report_json, text_cache, completed_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,0,?,?,datetime('now'))",
                (
                    doc_id, user_id, title, len(text), "complete",
                    report.word_count, report.similarity, report.band.value,
                    report.ai_probability, report.to_json(), doc.text,
                ),
            )
        credits.charge(conn, user_id, doc_id, reason="submission")
        print(
            f"  {title:<26} {report.similarity:6.1%}  {report.band.value:<6} "
            f"{len(report.matches)} match(es)"
        )

    print(f"\ncorpus   {corpus.size()} documents in {args.corpus}")
    print(f"database {args.db}")
    print(
        "\nStart the app against them:\n"
        f"  PROVENANCE_DB={args.db} PROVENANCE_CORPUS={args.corpus} "
        "python -m apps.api.main"
    )
    conn.close()
    corpus.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
