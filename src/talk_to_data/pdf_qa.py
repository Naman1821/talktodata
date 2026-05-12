"""
Deterministic Q&A on extracted PDF text: matching lines only, no external model.
"""

from __future__ import annotations

import re

NOT_PRESENT = "Not present."


def answer_from_pdf_text(question: str, pdf_text: str) -> str:
    """Return lines from the PDF text that match the question tokens; else NOT_PRESENT."""
    text = (pdf_text or "").strip()
    if not text or text == "(No extractable text from PDF.)":
        return NOT_PRESENT
    q = question.strip()
    if not q:
        return NOT_PRESENT

    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return NOT_PRESENT

    ql = q.lower()
    direct = [ln for ln in lines if ql in ln.lower()]
    if direct:
        return "\n".join(direct[:80])

    tokens = [t for t in re.findall(r"[a-z0-9]+", ql) if len(t) > 2]
    if not tokens:
        return NOT_PRESENT

    scored: list[tuple[int, str]] = []
    for ln in lines:
        lnl = ln.lower()
        score = sum(1 for t in tokens if t in lnl)
        if score:
            scored.append((score, ln))
    if not scored:
        return NOT_PRESENT
    scored.sort(key=lambda x: (-x[0], x[1]))
    return "\n".join(ln for _, ln in scored[:80])
