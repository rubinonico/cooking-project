# AGENTS.md — the cooking project (Larder)

**Read `PROJECT.md` before anything else.** §1 is the owner's words, verbatim and immutable. `docs/PUBLISHING.md`
is a hard constraint set, not a style guide. This file is orientation only.

## What this is

A generator for a **five-dinner week from one grocery haul**: one prep day, five serving days, and an overlap
objective over a real recipe corpus. Method is Zoe Barrie's "Ingredient Prep", quantified. Five structural
gates: C1 one haul · C2 day-1 Element · C3 serving-day finish · C4 overlap · C5 cuisine span.

## Structure

| Path | What it is |
|---|---|
| `PROJECT.md` | **The authority.** §1 immutable; §2–§7 rules, scope, decisions |
| `docs/PIPELINE.md` | The runbook: `build_fc_pool.py` → `plan_week_fc.py --contract` → `validate_week.py` → `tests/test_pipeline.py` |
| `docs/PUBLISHING.md` | **Read before publishing anything.** Verdict table per asset, attribution rules, claim register |
| `larder/` | Library: corpus, foodcom loader, week model, quantities, pantry, decompression, meal classification |
| `tools/` | Runners and builders. `validate_week.py` is the gate implementation |
| `tests/` | Pipeline and validator tests |
| `research/` | Research notes, including the Epicure probe |
| `data/`, `sources/`, `out/` | **Never published.** Excluded by `.gitignore` |

## Rules for an agent working here

1. **Gates before prose.** A week is either C1–C5 PASS or it is not. Never describe a plan as working.
2. **"Nothing has been cooked" follows every gate table**, in the repo and in any post. Removing that
   sentence converts a structural claim into a false one.
3. **Do not add corpus rows to the repo.** Invented example rows only, marked as invented.
4. **Withdrawn claims stay withdrawn.** If the build log is quoted, its `withdrawn claims` section goes with it.
5. The tasting test is the next real gate — it is not a code task, and no amount of refactoring substitutes.

## State

Pipeline wired end to end. Current week: 5 mains, 5 cuisines, ~41 haul lines, C1–C5 PASS. Nothing cooked.
