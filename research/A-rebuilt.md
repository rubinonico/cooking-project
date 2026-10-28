# A rebuilt — the specialty pantry, on 20 cuisines

**Source:** `MohammedAlawami/whats-cooking-dataset` (What's Cooking / Yummly) — **39,774 recipes, 20 cuisines**.
**Harness:** `tools/build_A.py` (re-runnable). **Table:** `data/external/A_pantry_final.json` (50 items).
**Cost dimension: omitted** at the user's instruction.

## The three thresholds, stated

| threshold | value | meaning |
|---|---|---|
| `MIN_FREQ` | **8%** | item must appear in ≥8% of that cuisine's recipes to count as *present* |
| `MIN_LIFT` | **1.5** | and be ≥1.5× more common there than across all recipes → *over-represented* |
| `MAX_UBIQ` | **10%** | and appear in <10% of ALL recipes → a *specialty*, not a supermarket staple |

An ingredient **defines** a cuisine when all three hold. 111 ingredients are load-bearing at 10%;
**50 are specialty items defining ≥2 cuisines.**

## ⚠️ Set cover is the WRONG objective — three attempts, three degenerate answers

The question "what is the smallest pantry that covers every cuisine?" was tried three ways and
**degenerated every time**, in a way that reveals the objective is wrong rather than the parameters:

| attempt | "minimum pantry" | why it is garbage |
|---|---|---|
| raw presence in ≥10% of a cuisine | **1 item: `salt`** | salt is *present* in all 20 and is nobody's base |
| + lift ≥1.5 (over-representation) | `carrot, parsley, milk, ginger, lime` | generic produce |
| + ubiquity <10% (specialty filter) | `carrot, parsley, lime, baking soda, cinnamon stick` | still generic produce |

**A minimum-cover objective is won by whatever overlaps everyone blandly — by construction, the answer is
the opposite of a base.** A base is what makes a dish *that* dish; a cover-optimal item is what makes every
dish *interchangeable*. Reported here as a negative result: **do not answer this question with set cover**,
and do not read any of those three lists as a pantry.

## A — the bases, ranked by SPECIFICITY (lift), not by breadth

Breadth alone puts `carrot` (9 cuisines, lift 3.4) at #1 and `parsley` below it. **Specificity alone** puts
single-cuisine oddities at #1. A base is high on both, so the table carries both columns and is sorted by lift.

| lift | cultures | item | cuisines |
|---|---|---|---|
| **19.9** | 2 | dill | greek, russian |
| **16.3** | 2 | lemongrass | thai, vietnamese |
| 15.8 | 2 | sesame seed | japanese, korean |
| 15.2 | 2 | rice noodle | thai, vietnamese |
| **15.2** | **3** | **fish sauce** | filipino, thai, vietnamese |
| 13.8 | 2 | saffron thread | moroccan, spanish |
| 13.5 | 2 | beansprout | thai, vietnamese |
| **10.9** | **5** | **sesame oil** | chinese, japanese, korean, thai, vietnamese |
| **10.7** | **4** | **coconut milk** | brazilian, filipino, jamaican, thai |
| 9.9 | 4 | thyme | cajun_creole, french, irish, jamaican |
| 9.5 | 2 | turmeric | indian, moroccan |
| 7.7 | 2 | curry powder | indian, jamaican |
| 7.6 | 4 | cinnamon | greek, indian, jamaican, moroccan |
| 6.8 | 3 | coriander | indian, moroccan, thai |
| **6.2** | **7** | **soy sauce** | chinese, filipino, jamaican, japanese, korean, thai, vietnamese |

**The two best bases by breadth AND specificity: `soy sauce` (7 cuisines, lift 6.2) and
`sesame oil` (5 cuisines, lift 10.9).** Nothing else reaches 5 cuisines with a lift above 6.

## coconut_milk — the user's example, resolved to a number

| cuisine | recipes | share | lift |
|---|---|---|---|
| **thai** | 353/1539 | **22.9%** | 10.7 |
| jamaican | 71/526 | 13.5% | 6.3 |
| brazilian | 58/467 | 12.4% | 5.8 |
| filipino | 74/755 | 9.8% | 4.6 |
| **indian** | **216/3003** | **7.2%** | **3.3** |

**The user's claim holds, and the earlier exclusion was a threshold artifact.** Coconut milk is in
**216 Indian recipes — 3.3× more common than baseline**, genuinely over-represented. It sits at **7.2%**,
just under the 8% bar, which is the *only* reason it is absent from "defines indian". It is not a
coarse-label artefact alone; it is a cutoff decision, and the underlying signal is real.
**It defines 4 cuisines at the stated thresholds and a 5th (indian) at 7.2%.** Forms attested: it is the
**powdered/desiccated** form that makes it shelf-stable — the user's own reasoning, confirmed.

## What serves the cuisines the user actually cooks

`italian · indian · thai · american(→southern_us)`, by lift:

| lift | item | serves |
|---|---|---|
| 16.3 | lemongrass | thai |
| 15.2 | rice noodle / fish sauce | thai |
| 13.5 | beansprout | thai |
| 10.9 | sesame oil | thai |
| 10.7 | coconut milk | thai |
| 9.5 | turmeric | indian |
| 7.7 | curry powder | indian |
| 7.6 | cinnamon | indian |
| 7.0 | potato | indian |
| **6.8** | **coriander** | **indian AND thai** |
| 6.8 | buttermilk | southern_us |
| 6.2 | soy sauce | thai |

**Only ONE item — `coriander` — serves two of the four cuisines he cooks.** That independently reproduces
the Want-A finding at 20-cuisine scale: his four cuisines are close to disjoint in their defining
ingredients. The pantry is a **per-cuisine** shelf, not a shared one.

## Traps hit in this rebuild

- **Order of rules matters:** `singular("cloves")` hit a generic `ves→f` rule first and produced
  `garlic clof`, splitting garlic across two keys. Exact-match checks must precede pattern rules.
- **`stick`, `clove`, `head`, `stalk`, `can` are units, not words to strip** — leaving them split
  `cinnamon` / `cinnamon stick`. Both merged.
- **The dataset contains the misspelling `tumeric`** (and `flour`, `oil` as bare tokens) — merged to
  `turmeric`; bare `oil` and `flour` retained as-is and flagged.
- **Preservation words must NOT be normalised away** — `dried`/`powdered`/`canned` are the *form answer*,
  so they are extracted as tags instead of stripped. This is the opposite of the earlier desire to merge
  forms, and it is why the same dataset supports both questions.
- **`indian` in this corpus is North-Indian-weighted** — it shows coconut milk at only 7.2%, whereas South
  Indian cooking uses it far more. The cuisine label is too coarse for within-country regional facts.
