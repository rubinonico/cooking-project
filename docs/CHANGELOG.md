# CHANGELOG — TBA (the cooking project)

Dated, factual, per-change. Every number here was produced by a command in this repo; anything not
measured says **not established**. Companion docs: `docs/PIPELINE.md` (how to run), `docs/BUILD-LOG.md`
(the publishable narrative), `docs/PUBLISHING.md` (what may leave the machine).

> **Why this file exists:** the working repo's git history does not cover this project's changes (the
> tree is shared and its HEAD is another project). Until that is fixed, **this changelog is the record.**

---

## 2026-10-28 — v0.4 — five weeknight dinners, dinner-only, with a decompress slot

### Scope reframed (owner)
- **Product = five weeknight dinners.** Not "a week of food", not meal prep. Recorded as `PROJECT.md §0`.
- **Desserts and breakfasts excluded** unless the title says *breakfast for dinner*.

### Added
| file | what | self-check |
|---|---|---|
| `larder/mealclass.py` | dinner / breakfast / dessert classification from corpus **meal tags**, not titles | 15 assertions |
| `larder/decompress.py` | the quick-comfort slot: prep ≤20m, cook ≤30m, ≤12 ingredients, comfort-class name, not diet-coded | 11 assertions |
| `larder/pantry.py` | staple split — salt/pepper/water/fat/flour/sugar assumed on hand | 14 assertions |
| `larder/fcnames.py` | Food.com free-text name normaliser | 27 cases + 4 invariants |
| `larder/quantities.py` | unit-aware quantity aggregation | 11 assertions |
| `tools/build_fc_pool.py` | builds the ELEMENT and DECOMPRESS pools | — |
| `tools/plan_week_fc.py` | week generator + `--contract` validator input | — |
| `tests/test_pipeline.py` | end-to-end contract test (9 sections) | — |
| `docs/PIPELINE.md`, `docs/BUILD-LOG.md`, `docs/PUBLISHING.md`, `docs/NAME-AND-VIABILITY-2026-10-28.md` | runbook, narrative, publishing rules, name+viability memo | — |

### Changed
- `data/week.schema.json` — added `staple` (grocery item) and `day1_required` (dish).
- `tools/validate_week.py` — C2 skips dishes declaring `day1_required: false`; **fails the week if no
  dish carries day-1 work**.
- `tools/plan_week.py` — added `to_contract()` + `--contract` (it previously emitted output the validator
  could not read).
- Ingredient cap **25 → 15**.
- `--dishes` is now the TOTAL dinner count (default 5 = 4 element + 1 decompress).

### Pool numbers (all from `python tools/build_fc_pool.py`)
| stage | rows |
|---|---|
| corpus | 490,457 |
| survived the shape/title pre-filter (element times, or quick shape + comfort name) | 43,721 |
| **ELEMENT pool** | **429** |
| **DECOMPRESS pool** | **2,911** |
| dropped: dessert | 2,403 |
| dropped: breakfast/brunch | 2,081 |
| dropped: no cuisine tag | 31,738 |
| dropped: ingredient count | 3,252 |
| rejected on title alone (quick shape, not a comfort name — never parsed) | 226,098 |

### Current week (`out/week-fc-011.json`)
Mexican hoagie · Priscilla's Chicken '65 · Thai BBQ Chicken · Chili Chicken · **Tacos Homemade
(decompress)** — 5 mains, 48 haul lines, 8 shared by ≥2, overlap ratio **0.1667**, C1–C5 **PASS**.

---

## 2026-10-28 — v0.3 — the pipeline is wired end to end

### Added
- `tools/build_fc_pool.py` (614 day-1 recipes out of 490,457 at cap 25), `tools/plan_week_fc.py`,
  `larder/quantities.py`, `larder/fcnames.py`, `tests/test_pipeline.py`.

### Fixed — the two gaps open since 2026-10-25
1. **Quantities** — every haul line carries an amount (42 of 73 measured; rest honestly `as needed`).
2. **Day-1 / serving-day split** — non-empty on every dish, labelled `time-derived`. It comes from
   `preparation_time` / `cooking_time`; the mirror's `steps` column is image URLs, so **no instruction
   text is used and none is invented**.

### Discovered (before any of it shipped)
- **`out/week-001.json` passing the validator was not evidence about the generator.** It is a
  hand-authored fixture; real generator output failed on schema (`week_id` missing). Fixed with
  `to_contract()`.
- **C2/C3 measured on real output for the first time** (`out/week-003.contract.json`): C1 PASS,
  **C2 FAIL**, **C3 FAIL**, C4b PASS, C5 PASS. The day-1 split was literally absent.

---

## 2026-10-28 — v0.2 — name and viability

- `Larder` is unshippable: four live meal-planning apps use it (App Store `id6762561852`,
  `id6792101537`, Google Play `app.meal.planne`, `larderapp.co`). `Mise`, `Prep Day`, `Haul`, `Basket`
  are also taken. Project renamed **TBA**, referred to as **"the cooking project"**; folder keeps
  `MISC/Larder/` because renaming breaks the Mandos index.
- **Viability verdict:** not a paid product yet. Category commoditised; the incumbent (Zoe Barrie) sells
  the same method as a paid Substack, so demand is for a person, not a program; the overlap constraint is
  unclaimed but copyable in a week; **nothing has been cooked.**

---

## 2026-10-25 — v0.1 — research verdicts

- **Want A falsified** (union of 5 cuisines ÷ largest = **124/48 = 2.583**, threshold ≤2.0; 86 of 124
  parts serve exactly one cuisine).
- **A′ answered** — 16 stackable, multi-culture items (parent-verified; the child reported 13).
- **Want B build** — week generator over Yummly 39,774 recipes, `out/week-001.json` fixture passes.
- **Cuisine-span trade-off, reproduced four times** — overlap halves as cuisines go 2 → 4.

---

## Defect ledger (every one of these produced a believable wrong number)

| # | defect | how it surfaced | fix |
|---|---|---|---|
| 1 | hand-authored fixture passed the validator | re-ran the generator | `to_contract()` |
| 2 | `day1_parts` = `"not established"` on every dish | contract run | Food.com corpus + time-derived split |
| 3 | free-text names counted 1 purchase as 4 (`"kosher salt or 1 teaspoon table salt"`) | 49 single-use items | `larder/fcnames.py` |
| 4 | objective bought **five chicken dinners** | reading the week | `--max-per-protein 2` |
| 5 | a **Cranberry Chutney** entered the dinner list | reading the week | `is_dinner_name()` |
| 6 | a **pastry** entered the dinner list | reading the week | name filter extension |
| 7 | `pancake` matched the dessert word `cake` | mealclass self-check | word-boundary + plural match |
| 8 | **spice mix** selected as the decompress dinner | reading the week | component filter |
| 9 | `fcnames.norm()` kept a duplicate pipeline and **overwrote its own result** | unit-prefixed names survived a fix | one pipeline, one place |
| 10 | declared overlap ≠ recomputed (C4b FAIL); decompress ingredients off the haul (C1 FAIL) | validator | recompute over final dish list |
| 11 | `salt cod` matched `salt`; `brown sugar` matched `sugar` | pantry self-check | negative list before family match |

## Withdrawn claims (kept so they are not re-derived)

- **"Capping ingredients improves overlap."** Withdrawn 2026-10-28. Cap 25 → 15 gave 73 → 41 haul lines
  but overlap 0.2877 → 0.2683; the comparison was also contaminated by a pastry filter landing in
  between. All four seeds converge on the same week.
- **"Italian/Southern dishes rarely carry a 4 h prep."** Wrong and withdrawn. This Food.com mirror
  carries **no `italian`, `french`, `american` or `southern` tag at all** (15 of 53 tags absent). The
  dishes are present and unlabelled: pasta+sauce signature 6,113 rows (4,945 ≤60 m), "ragu" 3,088,
  "lasagna" 2,576, "carbonara" 316, "gnocchi" 367, "biscuits and gravy" 25.
