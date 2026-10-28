# TBA — the cooking project

**Five weeknight dinners, one grocery haul, one prep day.** Zoe Barrie's "Ingredient Prep" method —
quantified and automated: an overlap objective over a real recipe corpus, a day-1 / serving-day split,
and a five-gate validator (C1 one haul · C2 day-1 Element · C3 serving-day finish · C4 overlap ·
C5 cuisine span).

Call it **"the cooking project"**. The name is TBA; the folder keeps `MISC/Larder/`.

**Scope (2026-10-28):** dinner only. Desserts and breakfasts are excluded unless it is *breakfast for
dinner*. See `PROJECT.md §0`.

**Status:** 🟢 Active — pipeline wired end to end. `docs/PIPELINE.md` is the runbook:
`build_fc_pool.py` → `plan_week_fc.py --contract` → `validate_week.py` → `tests/test_pipeline.py`.
Current week: 5 mains, 5 cuisines, 41 haul lines (37 buy + 4 assumed), C1–C5 PASS. **Nothing has been
cooked yet** — the tasting gate is the next real test, not a code task.

> **⚠️ 2026-10-25 correction, kept for the record.** Earlier README text and the `.scratch` artifacts
> were written against a research brief the user did not author. `PROJECT.md §1` is the authority and
> its words are immutable.

## Files

| Path | What it is |
|---|---|
| **`PROJECT.md`** | **THE AUTHORITY.** §1 (his words, verbatim, immutable) through §7 |
| `.scratch/larder/DESTINATION.md` | ⚠️ suspended — written against the wrong goal |
| `.scratch/larder/FIELD.md` | Where things are, the field's vocabulary, scan budget. Still valid |
| `.scratch/larder/DECISIONS.md` | ⚠️ subordinate; **D8 corrected in place**; re-read §1 before applying |
| `.scratch/larder/PLAN.md` | ⚠️ suspended — 10 tickets serving a report |
| `sources/flavor-bible.md` | The Flavor Bible, full text (local, personal use — see D9) |
| `sources/meta-cookbook.md` | His work-tree cookbook, **frozen** (sha256 `c510cf2b…d6352`) |
| `sources/meta-cookbook-INDEX.md` | Census: 7 trees · 31 branches · 4 fish techniques |
| `tools/verify_research.py` | ⚠️ enforces a corrected rule — delete its FORBIDDEN block before reuse |
| `tools/epicure.py` | Epicure MCP client, works today |
| `research/T2.2-epicure-probe.md` | The Epicure probe: 39/40 vocabulary overlap, calibrated pairing scores |

## Pass 1 delivers

`research/LARDER-RESEARCH.md` — coverage of the minimum base set (Q1), prep-day holding windows grounded
in FDA/USDA (Q2), whether Flavor-Bible pairings become rule templates (Q3), prior art (Q4), and
counter-evidence given equal weight (Q5).

**Not in pass 1:** no recipe list, no shopping list, no implementation plan. Those are pass 2, and they
cannot be specified honestly until Q3 is answered.

## Epicure MCP

`https://epicure-mcp.kaikaku.ai/mcp` — public, anonymous, read-only, MIT. 13 deterministic tools over
1,790 ingredient embeddings learned from a 4.14M-recipe corpus. Wired into Hermes as MCP server
`epicure` (verified, 13 tools); the tools load from the next session onward.

Used as an **independent cross-check on pairing claims**, never as authority, and **never** cited for
food safety. See D1.

---

## Attribution

- The **method** — one grocery haul, a day-1 prep pass, serving-day finishing, ingredients shared across
  the week — is **Zoe Barrie's** ("Restaurant Dropout", *Ingredient Prep*). This project quantifies and
  automates her procedure. It does not invent it and does not reproduce her paid material.
- The **stockable-form and trunk→branch taxonomy** are the author's own design, documented in a private
  working cookbook that is not part of this repository.
- `epicure-mcp` (KAIKAKU.AI, MIT) supplied the cross-check cuisine axis used in the earlier research.

## What these numbers do and do not mean

| Published as | NOT published as |
|---|---|
| "the generated week satisfies five stated structural constraints" | "the meal plan works" |
| "16.7% of the week's ingredients are used by more than one dinner" | "efficient shopping" |
| "the pools contain N dinners meeting stated filters" | "N recipes tested" |
| "day-1 and serving-day phases derived from preparation and cooking times" | "verified instructions" |

**Nothing here has been cooked or tasted.** A passing gate table describes structural constraints on a
generated plan. It is not evidence that the food is good. That test has not been run.

## What is not in this repository

`data/`, `sources/` and `out/` are excluded. Three of the four source corpora carry no stated licence and
one is a copyrighted book; `docs/PUBLISHING.md` is the rule set that decided this, written before anything
was published. The code runs against local corpora that a reader would have to supply independently.

## Licence

MIT — see `LICENSE`. The licence covers the code and the documentation here, not any corpus.
