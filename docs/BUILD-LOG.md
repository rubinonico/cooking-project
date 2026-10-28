# Build log — five weeknight dinners, measured

*A publishable narrative of the build. Written to be read by someone who was not in the session. Every
number below is from a command in this repo; `docs/CHANGELOG.md` has the itemised version and
`docs/PUBLISHING.md` says what may leave the machine.*

---

## The claim being tested

Zoe Barrie ("Restaurant Dropout") runs a manual weekly method she calls **Ingredient Prep**: one grocery
haul, most of the work done on day one, each dinner finished on the night, several ingredients used more
than once, zero leftovers by Sunday. She does it by hand, every week.

The question this project asks: **can that method be computed instead of performed?** Not "can an LLM
write recipes" — can a system *prove*, per week, that five dinners share a small pantry, that each has a
day-1 phase and a serving-day phase, and that none of it requires a second trip to the shop?

That reframing matters, because the constraint is the product. Anyone can generate five recipes. The
non-obvious part is that five recipes **share a shopping list**.

## What "quantified" means here

Five named gates, checked by `tools/validate_week.py`, not by prose:

| gate | question |
|---|---|
| **C1** | does one haul cover every ingredient of every dish? |
| **C2** | does every dish have day-1 work (or declare itself a meal that needs none)? |
| **C3** | does every dish have a serving-day finish? |
| **C4** | is the overlap real — recomputed from the dishes, not asserted? |
| **C5** | does the week span the required number of cuisines? |

The generator emits a machine-readable *contract* shaped by a JSON schema. The validator recomputes the
overlap from the dish list and **fails if the declared numbers disagree with the recomputation**. That
single rule caught a real bug on day one of the wiring.

## The four things that went wrong, in order

**1. The passing test was a fixture.** The project's flagship artifact, `week-001.json`, passed the
validator — because it was written by hand. The generator's actual output failed on schema. The
difference between "the validator passes" and "the generator is validated" had never been measured. It
is now a test.

**2. The day-1 split did not exist.** Running the generator's real output through the gates gave
C1 PASS, **C2 FAIL, C3 FAIL**. Every dish carried the literal string `not established`. The corpus had no
instructions, and the earlier report had said so honestly — but "reported as not established" reads like
caution and functions like absence. Closing it required a different corpus (490,457 Food.com recipes with
structured quantities and populated prep/cook times) and one honest decision: **derive the split from
time, not from text, and say so in the artifact.**

**3. Free-text ingredient names wrecked the shopping list.** The first real week had 49 single-use
ingredients, several of them duplicates of things already on the list — because Food.com users write
`"kosher salt or 1 teaspoon table salt"`, `"vegetable oil to grill the chicken"`, `"boneless skinless
chicken breast halves"`. A normaliser now strips presentation noise while **keeping** distinctions that
change what you buy: `ground cumin` ≠ `cumin seed`, `white` ≠ `brown sugar`, `kosher` ≠ `table salt`.
Three of those protections exist because the older normaliser over-collapsed them, which would have
*flattered* the overlap metric — the exact direction a self-interested system errs.

**4. The objective bought five chickens.** Maximising shared pantry across five dinners converges on
chicken, because chicken is the cheapest route to a shared ingredient. Then it put a **Cranberry
Chutney** in the dinner list, later a **filipino pastry**, and — when a "decompress" slot was added — a
**Chili Powder Spice Mix**. Every one of those is the same class of failure: *the score was satisfied by
something no one would cook.* The fixes are structural (protein cap, dish-class filter, word-boundary
matching so `pancake` stops matching `cake`), not prompt tweaks.

## The scope decisions the owner made

- **Desserts and breakfasts are out**, unless it is *breakfast for dinner* (his carve-out, and it beats a
  `breakfast` tag in the classifier). Dropped at pool build: 2,403 desserts, 2,081 breakfast/brunch.
- **Staples are assumed, not deleted.** Salt, pepper, water, a cooking fat, flour, sugar move to an
  "assumed in your kitchen" block with a disclaimer — but stay in the contract's haul, so C1 keeps
  meaning what it means.
- **One dinner per week is a "decompress" meal** — his word: something quick and comforting after a rough
  day. Defined by the four things that decide whether a tired person cooks: prep ≤20 min, cook ≤30 min,
  ≤12 ingredients, a comfort-class dish, not diet-coded. "Comforting" is *not* measured and the module
  says so.

## Current state

- **Element pool: 429** dinners (prep ≥4 h, cook ≤45 m, 5–15 ingredients, ≥1 cuisine tag).
- **Decompress pool: 2,911** dinners.
- **A week:** 4 element + 1 decompress = 5 mains, one haul.
- **Latest week** (`out/week-fc-011.json`): Mexican hoagie · Priscilla's Chicken '65 · Thai BBQ Chicken ·
  Chili Chicken · Tacos Homemade (decompress) — **48 haul lines, 8 shared, overlap 0.1667, C1–C5 PASS**,
  full test suite green.

## What is deliberately not claimed

1. **Nothing has been cooked.** Five gates and a test suite say the plan is internally consistent. They
   say nothing about whether the food is good. The tasting gate has not run.
2. **The day-1 split is coarse.** One prep block, one serve block, both from times. "Step 3 is the
   marinade" would be invention; the corpus has no readable instructions.
3. **Overlap is not the product.** Adding the decompress slot cost overlap (0.2683 → 0.1667) because a
   week of four braises shares more than a week of three braises plus tacos. That is the trade, stated.
4. **Cuisine labels are missing where it hurts.** This corpus has no `italian`, `french`, `american` or
   `southern` tag at all — 15 of 53 tags are absent — even though it holds 4,945 short pasta-and-sauce
   dinners. The Italian and Southern weekly menus he actually wants are in the data, unlabelled.
5. **A withdrawn claim stays withdrawn in the record.** "Capping ingredients improves overlap" was wrong
   and is logged as wrong, with the numbers that refuted it.

## Why publish it at all

Because the interesting artifact is not the recipe generator. It is the **gate ladder and the defect
ledger**: eleven separate defects, each of which produced a plausible number, each caught by running the
thing rather than reading it. That is a reusable story about automated systems that grade their own
homework — and it is honest about the fact that the food remains untested.
