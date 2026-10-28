# hermes-context — TBA (the cooking project)

**Name:** TBA — call it **"the cooking project"** in conversation. The folder keeps its old name; folder ≠ name.
**Domain:** MISC · **Root:** `C:\Users\rubin\projects\MISC\Larder\`
**Vault note:** `MISC/Larder.md`

## What this is

An ingredient-first cooking system: one stocked fridge/freezer/pantry/spice inventory that yields
improvised dishes across many cuisines, plus a generative cookbook that reads the inventory and emits
recipes. The reference framework is *The Flavor Bible* (Page & Dornenburg, 2008) for pairings.

The **differentiator** is coverage: not a meal-prep plan for one cuisine, but a measured minimum base
set that serves the largest number of cuisine families — with the failing cuisines named.

## Where to start a session

1. `.scratch/larder/DECISIONS.md` — the contract. Read first, always.
2. `.scratch/larder/DESTINATION.md` — what "done" is, both horizons, and the receipts.
3. `.scratch/larder/FIELD.md` — locations and vocabulary. **Do not re-scan.**
4. `.scratch/larder/PLAN.md` — the status line only, then your claimed ticket.

## Structure

```
Larder/
├── .scratch/larder/       the three artifacts + the plan. Session protocol lives here.
├── sources/               flavor-bible.md (full text), 00-brief.md (the want)
├── tools/verify_research.py   the pass-1 receipt
├── research/              pass-1 outputs (Q1-Q6)
└── data/                  cuisines.yaml, flavor_bible_entries.json, coverage.json
```

## Gotchas

- **The meta-cookbook is a FROZEN artifact.** `sources/meta-cookbook.md` — 74,804 bytes, 1,385 lines,
  `sha256 c510cf2b…d6352`. **Never edit it in place**, or the hash stops proving inputs are unmodified.
  Census and tree list: `sources/meta-cookbook-INDEX.md`. **Its structure is his design — test it, never
  re-present it as a finding** (D14). Its closing "Forty preparations" line does **not** reconcile with
  its own structure (47 by count) — see D16, and ask him, don't guess.
  Original: <https://claude.ai/share/a937fc28-c12b-4bef-bdaa-9ed128fe0eba> (share page hides files).
- **The Flavor Bible's `## ` headers merge entries.** `## **ALMOND OIL (See Oil, Almond) ALMONDS**` is
  one cross-reference plus one entry. Splitting on `## ` gives 835 phantom entries. Split on the
  BOLD-CAPS name inside the header, and resolve `(See X)` to pointers. See D4.
- **Hindsight memory (`127.0.0.1:8888`) was down during the kickoff scan.** If `hindsight_recall` fails,
  it is the server, not the query.
- **`hermes mcp add` is interactive** and hangs on a `Y/n` auth prompt. Epicure needs no auth, so it was
  registered through `hermes_cli.mcp_config._save_mcp_server` with the Hermes venv interpreter instead.
- **`/tmp` does not resolve for native Windows python.** Pass project-relative paths to scripts.
- **Do not commit the Flavor Bible or any full extraction of it.** D9.

## Related

- Skill: `youtube-full` (TranscriptAPI) — the acquisition path for the meta-cookbook transcript corpus.
  `TRANSCRIPT_API_KEY` is unset.
- Vault: `MISC/MISC Hub.md` — the index this project is linked from.
- Mandos: `unified_search.py --lib projects` covers this folder.
