#!/usr/bin/env python
"""The Horizon-A receipt.  ⚠️ SUSPENDED 2026-10-25 — see PROJECT.md.

    python tools/verify_research.py research/LARDER-RESEARCH.md

**This checker enforces a rule that has since been corrected in place.**
It FAILS a document that contains a "recipe list" section (see FORBIDDEN below), because the generated
brief forbade one. `PROJECT.md §1` wants artifacts, not a report, and `.scratch/larder/DECISIONS.md` D8
is corrected: recipes are the deliverable, not a violation.

So: this script validates the *report shape* of a superseded plan. Keep it for the structural checks
(sections present, every claim tagged with a source and a confidence) — those are epistemic rules and
still stand. **Delete the FORBIDDEN block before this receipt is used for anything real.**

Exits 0 when the report passes every STRUCTURAL check; exits 1 naming the failing check.

Claim count is REPORTED, never gated. A numeric threshold invented before the first parse is a
hypothesis, and a hard count is either trivially met or unreachable. See DECISIONS.md D5.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "Q1 cuisine coverage": r"(?im)^#{2,4}.*(Q1|cuisine coverage)",
    "Q2 prep-day feasibility": r"(?im)^#{2,4}.*(Q2|prep[- ]day)",
    "Q3 pairing logic": r"(?im)^#{2,4}.*(Q3|pairing logic)",
    "Q4 prior art": r"(?im)^#{2,4}.*(Q4|prior art)",
    "Q5 counter-evidence": r"(?im)^#{2,4}.*(Q5|counter[- ]evidence)",
    "unverified claims": r"(?im)^#{2,4}.*unverified",
    "assumptions to check": r"(?im)^#{2,4}.*assumption",
    "single most important open question": r"(?im)^#{2,4}.*open question",
}

CLAIM_RE = re.compile(r"^\s*[-*]\s+\S")
SRC_RE = re.compile(r"\[src:\s*[^\]]+\]", re.I)
CONF_RE = re.compile(r"\(confidence:\s*(high|moderate|low)\s*\)", re.I)

FORBIDDEN = {
    "shopping list": r"(?im)^#{2,4}.*shopping list",
    "recipe list": r"(?im)^#{2,4}.*recipe list",
    "implementation plan": r"(?im)^#{2,4}.*implementation plan",
}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python tools/verify_research.py <report.md>")
        return 2

    path = Path(argv[1])
    if not path.is_file():
        print(f"FAIL  report not found: {path}")
        return 1

    text = path.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []
    notes: list[str] = []

    # --- structural: required sections present ---------------------------------
    for label, pattern in REQUIRED_SECTIONS.items():
        if not re.search(pattern, text):
            failures.append(f"missing section: {label}")

    # --- structural: forbidden pass-1 content (D8) -----------------------------
    for label, pattern in FORBIDDEN.items():
        if re.search(pattern, text):
            failures.append(f"forbidden in pass 1 (D8): a '{label}' section")

    # --- claims: every claim line tagged with source + confidence (D5) ---------
    claims = [ln for ln in text.splitlines() if CLAIM_RE.match(ln)]
    untagged = [ln for ln in claims if not (SRC_RE.search(ln) and CONF_RE.search(ln))]
    if untagged:
        failures.append(f"{len(untagged)} of {len(claims)} claim lines lack [src: ...] and/or (confidence: ...)")
        for ln in untagged[:5]:
            notes.append(f"    untagged: {ln.strip()[:110]}")

    # --- structural: the closing three sections are non-empty ------------------
    for label, pattern in (
        ("unverified claims", REQUIRED_SECTIONS["unverified claims"]),
        ("assumptions to check", REQUIRED_SECTIONS["assumptions to check"]),
        ("single most important open question", REQUIRED_SECTIONS["single most important open question"]),
    ):
        m = re.search(pattern, text)
        if not m:
            continue  # already failed above
        body = text[m.end():]
        nxt = re.search(r"(?im)^#{2,4} ", body)
        body = body[: nxt.start()] if nxt else body
        if len(body.strip()) < 40:
            failures.append(f"section is empty or near-empty: {label}")

    # --- report (never gate) ---------------------------------------------------
    tagged = len(claims) - len(untagged)
    n_high = len(re.findall(r"confidence:\s*high", text, re.I))
    n_mod = len(re.findall(r"confidence:\s*moderate", text, re.I))
    n_low = len(re.findall(r"confidence:\s*low", text, re.I))
    n_missing = sum(1 for f in failures if f.startswith("missing section"))
    print(f"report        : {path}")
    print(f"claim lines   : {len(claims)}")
    print(f"tagged        : {tagged}")
    print(f"untagged      : {len(untagged)}")
    print(f"high/med/low  : {n_high}/{n_mod}/{n_low}")
    print(f"sections ok   : {len(REQUIRED_SECTIONS) - n_missing}/{len(REQUIRED_SECTIONS)}")
    print()

    if notes:
        print("details:")
        for n in notes:
            print(n)
        print()

    if failures:
        print(f"FAIL  {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("PASS  all structural checks green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
