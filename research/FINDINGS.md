# FINDINGS.md — Evidence layer for week-001

**Deliverable:** `out/week-001.json` (passes `tools/validate_week.py` exit 0).
**This file is by-product only:** the numbers, falsification, and honest gaps. Every claim carries a source and confidence per PROJECT.md D5/D7.

---

## 1. Want A is FALSIFIED

Union of the five cuisines ÷ largest single cuisine = **124/48 = 2.583**.
- [src: data/compression.json without_biased_merges; independently re-aggregated from data/cuisines/*.yaml] (confidence: high) — verified against raw cuisine files; parent independently recomputed the same number.

Shelf-stable only: union 49 → **2.450**.
- [src: data/compression.json without_biased_merges; independently computed from cuisine files + shelf_stability.json] (confidence: high) — verified against source data; parent independently recomputed.

If method-dependent forms also count as stockable: **2.625**.
- [src: parent computation, stated in the brief for this ticket] (confidence: moderate) — parent-verified; not independently recomputable from files I hold.

Threshold ≤2.0. **All three readings exceed it.**

**86 of 124 parts (69%) serve exactly one cuisine.**
- [src: data/compression.json without_biased_merges; independently aggregated from cuisine yamls] (confidence: high) — I counted exclusive-to-one-cuisine ingredients from the five cuisine files and got exactly 86.

The user's Want A — *"a decomposition of most of the popular cuisines that can be shelf stable so individuals can just stock up on those and not hunt every blue moon for the niche ingredient or blend"* — **does not hold** at the observed compression ratios. A shared shelf-stable backbone across these five cuisines is not dense enough to justify a single stock-up.

---

## 2. Want B survives

C1 (one grocery haul): **PASS**. C2 (day-1-preppable part per dish): **PASS**. C3 (serving-day finish per dish): **PASS**. C4b (declared overlap == recomputed overlap): **PASS**. C5 (cross-cuisine, min 3): **PASS**.
- [src: `python tools/validate_week.py out/week-001.json` → exit 0; re-run just now] (confidence: high) — the validator printed all five PASS, and I observed it. The spec is self-validating: the procedure constraints are satisfied.

Barrie's procedure (one grocery haul, prep day 1, finish on serving day, overlapping ingredients) is automatable by M2 across 3 cuisines at ratio 0.7647. **The weekly generator is viable; the universal pantry is not.**

---

## 3. Cuisine-span trade-off (the K-sweep table)

Parent-verified and parent-corrected — the project's own selector could not produce K=5, but brute force could:

| K | Overlap ratio | Single-use ingredients | Cuisines in the week |
|---|---|---|---|
| 1 | 0.8182 | 2 | italian, italian-american |
| 2 | 0.8182 | 2 | — |
| 3 | **0.7647** | **4** | american, indian, italian-american |
| 4 | 0.5263 | 9 | — |
| 5 | 0.4762 | 11 | all five |

- [src: PLAN.md Result column T2.1c] (confidence: high for K=3; moderate for K=1/2/4/5) — K=3 verified against out/week-001.json (overlap_ratio=0.7647, single_use_count=4, cuisines=american/indian/italian-american). K=5 parent brute-forced all 190,080 one-dish-per-cuisine combinations; K=1/2/4 not independently re-run.

**The K=5 row came from the parent, by brute force over all 190,080 one-dish-per-cuisine combinations** — the project's own selector could not find a 5-cuisine week and wrongly reported K=5 as 'unreachable'. Any 5-dish week spanning 5 cuisines must be one-per-cuisine, so that search is exhaustive.
- [src: PLAN.md Result column T2.1c] (confidence: high) — parent documented the brute-force and its exhaustive justification.

**Shape of the finding as the finding:** overlap is cheap to give up from 1→3 cuisines (0.82→0.76) and expensive from 3→5 (0.76→0.48). The marginal cost of the 4th and 5th cuisines is more than double the marginal cost of the 1st through 3rd.

---

## 4. Constraint pass/fail

**C1** (one grocery haul): **PASS** — all 17 ingredients on one list; no special-order items.
- [src: out/week-001.json grocery_haul] (confidence: high)

**C2** (day-1-preppable part in every dish): **PASS** — all 5 selected dishes have non-empty `day1_parts`.
- [src: out/week-001.json dishes[].day1_parts; validator re-run] (confidence: high)

**C3** (serving-day finish in every dish): **PASS** — all 5 selected dishes have non-empty `serve_day_parts`.
- [src: out/week-001.json dishes[].serve_day_parts; validator re-run] (confidence: high)

**C4b** (declared overlap == recomputed overlap): **PASS** — validator confirmed.
- [src: validator output line "C4b PASS"] (confidence: high)

**C5** (cross-cuisine, min 3): **PASS** — week spans american, indian, italian-american (3 cuisines).
- [src: out/week-001.json dishes[].cuisine; validator output "C5 PASS"] (confidence: high)

**C4a** (zero single-use ingredients): **REPORTED, NOT GATED.** 4 single-use: cheddar, cumin, ricotta, yogurt. C4a is infeasible at n=5 for every cuisine span including a single cuisine. The spec was re-scoped mid-flight (PLAN.md §4): C4a reports the degree; the user judges it.
- [src: validator output "C4a REPORTED, NOT GATED: 4 single-use ingredient(s) (infeasible to reach 0 at n=5 for any cuisine span — see T2.1c)"] (confidence: high)

---

## 5. Three dishes fail C2

These made-to-order dishes have no Element — only mise en place. They are correctly excluded from the generated week (leaving 57 eligible dishes):

- **Spaghetti alla Carbonara** — the only day-1 work is grating pecorino, portioning eggs, dicing pancetta. Sauce forms in the pan in ~3 minutes. Listed as `unsplittable` with reason. [src: data/dishes.json, unsplittable[] entry italian-spaghetti-carbonara] (confidence: high) — the day1_parts the worker originally wrote are recorded in that entry's evidence field.
  - [src: data/dishes.json unsplittable[0]] (confidence: high)

- **Fettuccine Alfredo** — the only day-1 work is grating parmesan. Sauce is butter, cream and pasta water emulsified table-side. Listed as `unsplittable` with reason. [src: data/dishes.json, unsplittable[] entry italian-american-fettuccine-alfredo] (confidence: high) — the day1_parts the worker originally wrote are recorded in that entry's evidence field.
  - [src: data/dishes.json unsplittable[1]] (confidence: high)

- **Shrimp Scampi** — the only day-1 work is peeling shrimp, mincing garlic, chopping parsley. The dish is a 5-minute pan finish. Listed as `unsplittable` with reason. [src: data/dishes.json, unsplittable[] entry italian-american-shrimp-scampi] (confidence: high) — the day1_parts the worker originally wrote are recorded in that entry's evidence field.
  - [src: data/dishes.json unsplittable[2]] (confidence: high)

This is a limit of the Element/Full-Meal model — dishes that are inherently made-to-order. Not a defect in the work.

---

## 6. M2 (the engine) works — the parent's initial scepticism was refuted

Across 48 direction-checks: **10 above p90, 33 within range, 5 below p10**. The culture check discriminates, and cuisine-coherently — turmeric/coconut_milk/rice/tomato clear South_Asian; fish_sauce/soy_sauce fall *below p10* for Mediterranean.
- [src: PLAN.md Result column T2.3; parent independently re-ran every Epicure call] (confidence: high) — parent re-called Epicure independently and every `epicure_fit` number reproduced exactly. The 48 direction-checks are the parent's own measurement, not a subagent report's.

The parent's own initial suspicion — that p90 thresholds sit near zero and the check would be non-discriminating — was refuted by the measurement. **This refutation is attributed to the parent, not to the subagent that wrote T2.3-m2-pass.md.** The subagent under-claimed ("M2 adds little discrimination"); the parent's re-run showed it discriminates meaningfully and correctly.

**One caveat:** `Western_Atlantic` was asserted as the analogue for 'American cuisine' **without argument**. This is the one mapping of the three (Mediterranean→italian-american, South_Asian→indian, Western_Atlantic→american) that is not self-evident and that lets Mac and Cheese pass its cuisine-fit check. The brief said to use `null` rather than pick a nearest-sounding direction; it did not.
- [src: PLAN.md Result column T2.3; T2.3-m2-pass.md analogue-mapping notes] (confidence: high) — the mapping is documented but the rationale is absent.

---

## 7. Honest gaps

The following could NOT be verified, or are assumptions the user should check.

### Barrie's prep-level rubric is unpublished
The generated week correctly reports `prep_band: null` with the note "Barrie's band rubric is unpublished. Cannot assign a 1-15 score." The 1-15 band stays null until her paywalled rubric is available.
- [src: out/week-001.json prep_level] (confidence: high)

### Alias-map bias flatters Want A
The resolver's alias map collapses 4 pairs, two of which merge a shelf-stable form onto a fresh one (`tomato_sauce`→`tomato`, `garlic_powder`→`garlic`). This shrinks the shelf-stable union and therefore flatters the SS ratio. The unbiased SS ratio (2.450) is higher than the aliased one (2.286). The conservative headline uses the unbiased SS ratio.
- [src: data/compression.json delta; PLAN.md 'Known measurement bias' section] (confidence: high)

### Meta-cookbook 'Forty preparations' does not reconcile
The artifact's own "Forty preparations" claim does not reconcile with its structure (47 by enumeration). The user was asked and answered "I don't know yet." Still open.
- [src: PLAN.md Result column T0.1] (confidence: high)

### Nothing in this project has ever tasted a dish
The generated week passes every written constraint. It has not been cooked, tasted, or evaluated for palatability by a human. Stop condition §7.3 (PROJECT.md) — "A correct-but-unappetising week is a failure" — is untested.
- [src: PROJECT.md §7.3] (confidence: high)

### The M2 `Western_Atlantic` mapping is the weakest analogue
As noted in §6, the mapping of American cuisine to Epicure's Western_Atlantic direction is asserted without argument. If a different analogue were chosen, Mac and Cheese's `epicure_fit` could change. The file itself documents the mapping but provides no justification.
- [src: T2.3-m2-pass.md] (confidence: moderate) — the file documents the mapping but not the reasoning.

### The K=5 brute force result is undocumented in `out/`
The parent's 5-cuisine week (Texas Chili, Baingan Bharta, Parmigiana di Melanzane, Chicken Parmesan, Thai Fried Rice) was never written to a file in `out/`. It exists only as claims in PLAN.md.
- [src: only week-001.json exists in out/] (confidence: high)

### Single most important open question
**Would a real cook actually make this week?** Every numeric constraint is satisfied, but the week has never been evaluated for appetite, variety, or practical weeknight cookability. If the answer is 'no', the project has satisfied the wrong constraints.

---

*Generated 2026-10-25. Every claim carries [src: ...] and (confidence: high|moderate|low) per PROJECT.md D5/D7.*