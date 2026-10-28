# PROJECT — TBA (the cooking project)

**Name:** TBA. **Refer to it as "the cooking project"** in all future sessions — "TBA" is a placeholder, not a search term.
**Folder stays `MISC/Larder/`** — renaming it breaks the Mandos index and hardcoded paths. Folder ≠ name; the name is TBA.
**Opened:** 2026-10-25 · **Authority:** this file. Everything in `.scratch/larder/` is subordinate to it.
**Rule:** §1 is the user's words, verbatim, immutable. Nobody but the user edits §1.

## §0 — THE FRAME (owner, 2026-10-28)

> *"let's omit desserts and breakfasts unless its a 'breakfast for dinner' and reframe this as 5 weeknight
> dinners, again like [Zoe] Barrie but Quantitative/Automated."*

**The product is FIVE WEEKNIGHT DINNERS.** Not "a week of food", not a meal-prep plan, not a recipe
generator. Scope is dinner:

- **Desserts out.** Removed at pool build by `larder/mealclass.py`, which reads the corpus's own
  `dessert` tag (**2,403 rows** dropped on the 2026-10-28 full run) rather than guessing from titles.
- **Breakfasts out** (**2,081 rows**) — **unless it is breakfast for dinner**, which is a real dinner and is
  an explicit override: `"breakfast for dinner"`, `brinner`, or `dinner` in the title beats a
  `breakfast` tag.
- **Five mains, one haul, one prep day.** The Barrie method, quantified: the overlap objective, the
  day-1/serve-day split, and the C1–C5 gate ladder are the "Quantitative/Automated" half.

**Why the tag matters more than the title:** eggs are in carbonara, frittata and bibimbap, so
ingredient-level breakfast detection would delete dinners. Class comes from meal tags; titles only
decide when no meal tag exists.

### §0.1 — The decompress slot (owner, 2026-10-28)

> *"Maybe make them a 'decompress' meal — something quick and comforting after a rough day at work?"*

One of the five is a **decompress dinner**: `prep <= 20 min`, `cook <= 30 min`, `<= 12 ingredients`,
comfort-class dish, not diet-coded (`larder/decompress.py`). **No day-1 work at all** — it is the
"Full-Meal only" shape Barrie's own system has. `--dishes` stays the total, so the default week is
**4 element + 1 decompress = 5**. Comfort is a labelled proxy, not a measurement.

### §0.2 — Documentation for publication (owner, 2026-10-28)

> *"We should also be documenting the changes to this build/project for publishing purposes."*

| doc | purpose |
|---|---|
| `docs/CHANGELOG.md` | **the record.** Dated per-change entries, the 11-item defect ledger, and the claims that were withdrawn — the working repo's git history does not cover this project, so this file is the history. |
| `docs/BUILD-LOG.md` | the publishable narrative: what was measured, what broke, what stays unclaimed. |
| `docs/PUBLISHING.md` | what may leave the machine — licence reality for three unlicensed corpora, the copyrighted cookbook, attribution requirements, claim register, pre-publish checklist. |
| `docs/PIPELINE.md` | runbook: four commands, what each stage may claim. |

**Rule that follows from it:** every change to the pipeline or the gates gets a dated `CHANGELOG.md` entry
in the same session it lands, including a defect if one was found. A withdrawn claim stays in the file,
marked withdrawn, with the numbers that refuted it.

---

## §1 — The want, as a result

> 2 things that can be utilized from the same souce. A decomposition of most of the popular cuisines
> that can be shelf stable so individuals can just stock up on those and not "hunt" every blue moon for
> the niche ingredient or "blend". The more ambitious "project" is an app/program that generates weekly
> meals that have overlapping ingredients and where most of the meals can be prepped on day 1 and then
> finished on the serving day.

— Nico, 2026-10-25, verbatim. Untidied. **Two wants** (§1.2). **Do not edit this block.**

## §1.1 — The words he reached for

Pointers, **not the spec**. Promoting one to the spec is the failure this file exists to prevent.

`decomposition` · `shelf stable` · `stock up` · `hunt` · `blue moon` · `niche ingredient` · `blend` ·
`app/program` · `generates weekly meals` · `overlapping ingredients` · `prepped on day 1` ·
`finished on the serving day` · `more ambitious` · `2 things` · `same source`

**And one named practitioner, from him:** *"the one grocery haul/meal prep idea (and most of this is just
quantifying it) is based off the food influencer **Zoe Barrie**."* This is the most valuable sentence in
the brief — it converts the whole thing from an invention into a **quantification of an existing method**.
Resolved in §3.

**The target, restated by him 2026-10-25:** *"I'm basically trying to **clone Barrie's idea and then
automate it**."* Straightforward and worth taking at face value. Consequence: **A is not a parallel
want — it is the sub-problem that makes B generate without hunting.** Logged in the goal-change log; §1
itself is untouched.

**And two candidate mechanisms, offered by him the same day:**

> *"a random number rolled and then each step follows a tree path"* — **M1, tree walk**
> *"or discretize each ingredient and vectorize/embed them based on which culture they partake in"* —
> **M2, embeddings by culture**

Recorded in §4.5. These are **techniques, not requirements** — he supplied them, so they are logged rather
than adopted, and they do not enter §1.

## §1.2 — The two wants, marked separately

| | Want | His own framing |
|---|---|---|
| **A** | A **decomposition of popular cuisines into shelf-stable components**, so a person stocks up once and never hunts a niche ingredient or a blend again | stated as a fact of what exists at the end |
| **B** | A **program that generates weekly meals with overlapping ingredients**, most prepped on day 1 and finished on the serving day | *"the more ambitious project"* |

**They are not the same project.**

- **A's hard part is reuse.** A cuisine must become a finite parts list where each part is shelf-stable
  *and* used by many dishes. Otherwise "stock up once" is really "buy 60 things once". Taxonomy problem.
- **B's hard part is scheduling.** Maximise shared ingredients across a week, and split every dish across
  a day-1 phase and a serving-day phase. Constraint problem.

**B depends on A** — you cannot generate a week before you know the parts. He said "more ambitious" for B
himself, which is the same ordering.

**A is the part that does not exist yet** — see §3. That is the finding of this document.

## §1.3 — Where the meta-cookbook sits: UNRESOLVED

Asked directly, 2026-10-25. His answer: **"I don't know yet."**

Recorded as open. Two candidate readings, both **mine and unendorsed**: (1) a hand-built example of Want A
for one cuisine — French decomposed into shelf-stable trunks and finish-on-the-day branches; (2) a
separate hobby artifact that merely shares the word "cookbook". **Not a finding. Do not resolve it for him.**

## §1.4 — The pointer, resolved: Zoe Barrie / "Restaurant Dropout"

Fetched from primary sources, 2026-10-25 (her own Substack **`restaurantdropout.substack.com`**, its
About and FAQ pages, and a podcast interview on The Dinner Plan). This is **new information**, not a
restatement of anything he said — he supplied the name, the resolution is this project's.

**She already runs Want B by hand, weekly, as a human.** Verbatim from her own pages:

| Her words | What it is |
|---|---|
| *"**Ingredient Prep**"* — *"ingredient prep > meal prep"* | Her method, and its name. Explicitly **not** batch cooking: *"you won't be eating the same dinner five days in a row"* |
| *"**one grocery haul** will result in **5 different dishes** for the week"* | Want B, stated exactly |
| *"**Several ingredients get used more than once**"* | **The overlap objective**, stated exactly |
| **"Element"** recipes vs **"Full-Meal"** recipes | Prepped ahead for Prep Day **vs** cooked as you go. This is his day-1 / serving-day split, already named |
| **"Essentials"** — *"ingredients you likely already have on hand"* | Her always-stocked shelf-stable base |
| **"Time Savers"** | Ingredients you buy already prepped |
| *"I aim to have **zero leftover ingredients** by the end of the week"* | Her stated objective — zero waste |
| **Prep level score**: Minimal ≤6 → 1.5-2 h; Average 7-9 → 2-3.5 h; Substantial 10-15 → 3.5 h+ | **She already has a numeric prep-load scorecard.** Do not invent one (§5) |
| Serves 2; *"built for flexibility rather than batch cooking"* | Her scale |
| *"by weeks 6-8, you'll know exactly how much you need"* | The system **converges** with repetition |

**What she does not have, and it is exactly Want A:** she rotates **dishes** within roughly one pantry
(American / Italian-leaning). She does **not** decompose multiple cuisines into shelf-stable parts. There
is one "Essentials" list, not a per-cuisine decomposition. *"Aim for zero leftover ingredients"* is a
per-week goal for one menu, not a stock-the-pantry-once goal across cuisines.

**So the split is:** B is a **quantification/automation of her manual weekly process**. A is **genuinely
new work** — and A is what makes "stock up once and never hunt" true rather than "subscribe and shop
weekly", which is what she sells.

**Access note:** her menus, prep lists and Recipe Vault sit behind a **paid Substack subscription**. The
About/FAQ pages are public and carry the method and its vocabulary. Anything deeper needs either the
subscription or her published free posts — **not assumed available.**

### §1 AMENDMENT — 2026-10-25 01:41 (user's words, verbatim)

Want A is **DROPPED** as stated. The user said:

> "drop want A, if anything I was more or less looking for what niche ingredients can I have stocked either
> shelf stable or not that serves as the base of a few culinary cultures for instance coconut milk is rather
> expensive but can be shelf stable if powderized and serves as the key ingredient for a lot of south asian
> dishes."

**Re-read as A′ — and it is a different question, not a smaller A:**

A asked *"how big is the union of five cuisines"* — a COMPRESSION question. A′ asks *"which few niche items
are load-bearing across several cultures, and can they sit on a shelf"* — a LEVERAGE question.

They are not the same metric, and **the falsification of A does not falsify A′.** A was falsified because the
union is 2.583x the largest cuisine. A′ never depended on the union being small: **a dozen jars can be
load-bearing across many cuisines while the full union stays huge.** The 2.583 number is evidence against A
and is irrelevant to A′.

**A′ definition, from the user's own words:**
  1. **niche** — you would have to make a special trip for it (not a supermarket staple; his example is
     coconut milk, which he calls "rather expensive")
  2. **load-bearing across a few culinary cultures** — serves as "the key ingredient" for more than one
  3. **stockable** — shelf-stable, OR reducible to a shelf-stable FORM ("can be shelf stable if powderized")

**His example is a FORM transformation, not an ingredient substitution** — powderized coconut milk. This is
the same axis the alias map collapsed (`tomato_sauce`→`tomato`, `garlic_powder`→`garlic`) and that collapse
was recorded as a BIAS for A. For A′ the form IS the answer, so that collapse must be UNDONE here.

## §2 — The question this phase answers

**v3, 2026-10-25 — derived from his four answers, not from any document.** Supersedes v1 (rejected) and
v2 (superseded). *Correct me if v3 mis-states you.*

> **Can M2 (culture-embedded ingredients) generate a week that satisfies all four of Barrie's procedure
> constraints at once — a single grocery haul, every dish carrying a day-1-preppable part, every dish
> finishing on the serving day, and an ingredient pool shared across the week's dishes — with zero
> special purchases?**

**The target is her procedure, not her output.** His words: *"copy her style procedure (one grocery haul,
prep on day 1, finish on serving day utilizing overlapping ingredients)."* This is the re-statement that
matters most, because of what it removes:

> **Ground truth is no longer needed.** Cloning her *output* would have required her paywalled weeks as a
> reference corpus. Cloning her *procedure* does not — **the procedure is the spec**, and a generated week
> either satisfies all four constraints or it does not. **The spec is self-validating.** The
> "ground-truth blocker" logged earlier the same day is **withdrawn**; see the correction in the log.

**Why four constraints and not one.** Each is independently falsifiable, and they are what make the output
*her* system rather than a recipe list:

| # | Constraint | Fails when |
|---|---|---|
| 1 | **One grocery haul** | the week needs a second trip, or a special-order item |
| 2 | **Day-1-preppable part in every dish** | a dish is start-to-finish on its serving day |
| 3 | **Serving-day finish in every dish** | a dish can only be fully cooked in advance |
| 4 | **Shared ingredient pool** | five dishes use five disjoint ingredient sets |

Constraints 2 and 3 are her **Element / Full-Meal** split. Constraint 4 is her *"several ingredients get
used more than once"*. Constraint 1 is *"one grocery haul"*. **Her vocabulary is the spec's vocabulary —
that is what "copy her procedure" means, and it is why §3 was worth filling before §2.**

**The engine is M2** — his choice. See §4.5.

**What "at once, five cuisines" still buys** (his earlier correction, carried forward — it was right):
one cuisine tells you nothing about whether the *method* generalises, and the want is about most popular
cuisines. So the generator runs across Italian, Italian-American, American, Thai and Indian together, and
the same run yields the number that decides Want A:

> **Parts in the union of the five cuisines ÷ parts needed for the largest single cuisine.**

≈1 → a shared shelf-stable backbone exists and "stock up once" is real. ≈5 → ~200 items, nobody stocks
that, and **Want A is a fiction**. **One cuisine cannot produce this number. Five can.**

## §3 — The field's vocabulary

**Filled 2026-10-25, from primary sources** (§1.4). Each term is hers and each is cited above.

`Ingredient Prep` · `Element recipe` / `Full-Meal recipe` · `Essentials` · `Time Savers` ·
`one grocery haul` · `prep day` · `Mise en Place` (her section name for the prep list) ·
`Time to Shop` (her section name for the grocery list) · `Recipe Vault` · `prep level score` ·
`zero leftover ingredients` · `essential ingredients`

**Note the vocabulary gap A sits in.** Her lexicon has no word for *"a cuisine decomposed into parts"* —
only *"Essentials"*, one flat list. **The field has no term for Want A because the field has not done
Want A.** If a later session invents a term, mark it as invented, not borrowed.

**Earlier seeds — MINE, unverified, kept only for search recall:** `batch cooking` ·
`component cooking` · `par-cooking` · `meal kits` · `pantry taxonomy` · `cook-once-eat-twice` ·
`prep-ahead / finish-to-order`. Each must be checked against a real source before use. Note her explicit
rejection: *"this isn't traditional meal prep"* — so `meal prep` is the field's **anti-term**.

## §4 — The variables he controls, costed

Swept **in cost order, free first**. Free variables dominate and are conventionally swept last, because
plans get organised around techniques and techniques are never free.

| Variable | Cost | Value |
|---|---|---|
| **Cuisines in the set** | free | **FILLED: Italian, Italian-American, American, Thai, Indian** |
| Number of cuisines | free | 5, and he wants them **together** (§2) |
| Meals per week | free | Not stated. Her system: 5. Reuse 5 unless he says otherwise |
| Day-1 (prep-day) time budget | free | Not stated. **Her published bands give the units**: ≤6 → 1.5-2 h, 7-9 → 2-3.5 h, 10-15 → 3.5 h+ |
| Serving-day time budget | free | Not stated. Her whole pitch is "minutes" |
| Number of people | free | Not stated. Hers is 2 |
| Fridge / freezer capacity | cheap, fixed | Constrains how many parts can be held — and may be the real limit on A's union size |
| Willingness to buy one appliance | expensive | Sweep last |

**Numbers missing on purpose.** Filling them would be writing his spec for him. The cuisines were the
highest-leverage free variable and he supplied them.

## §4.5 — Candidate mechanisms (his hypotheses, not yet tested)

Offered 2026-10-25. Logged as **techniques**, deliberately kept out of §1. A mechanism is evaluated
against §5's proxies; it never defines the goal.

| | His words | What it is | Guarantees | Does NOT guarantee |
|---|---|---|---|---|
| **M1** | *"a random number rolled and then each step follows a tree path"* | stochastic traversal of a work-tree — roll, then walk a branch | **structure** (every output is a legal dish) | **edibility** — needs a filter, or most rolls produce bad food |
| **M2** | *"discretize each ingredient and vectorize/embed them based on which culture they partake in"* | per-ingredient embedding, disambiguated by culture | **affinity** (plausible combinations) | **shopping-list overlap** — affinity is not co-occurrence in a fixed week |

**M2 is Epicure.** That is very likely why he attached `KAIKAKU-AI/epicure-mcp` to the original brief:
its `cultural_profile` returns a per-cuisine position *with that cuisine's own p10/p90* — "vectorize by
culture" with the normalisation already solved. Probed and proven reachable (§3 / `research/T2.2-epicure-probe.md`):
13 tools, 39/40 Flavor Bible names resolve, `pairing_score` agrees with the book's tiering 6/6.

**M1 is his own meta-cookbook generalised.** He built a trunk→branch work-tree by hand for French sauces;
a random walk over that structure is the automated version of the thing he already made. **His idea, not
this project's.**

> ### ✅ ENGINE CHOSEN, 2026-10-25: **M2** — embed ingredients by culture (Epicure)
>
> His choice, with his reason in the options offered: **proven reachable, no authoring per cuisine.**
> M1 would need a hand-built work-tree *per cuisine* — five trees before the first generated week. M2
> needs none, and its normalisation is already solved (`cultural_profile` returns a per-cuisine p10/p90).
>
> **M1 is not killed, it is deferred** — and it keeps one advantage M2 lacks: a tree guarantees every
> output is a *legal* dish. If M2's generations need a legality filter, M1's structure is the obvious
> source of one. **Revisit at n≥1 generated week, not before.**

**My read — labelled as inference, not fact:** neither mechanism alone produces the thing Barrie's system
actually *is*. Her week is not a tree and not a vector space; it is a **set-cover constraint on top of
either**: N dishes must share a small ingredient pool, *and* each dish must split into an Element
(prep-ahead) phase and a Full-Meal (serve-day) phase. A random walk guarantees legality, embeddings
guarantee plausibility, and **neither guarantees that five dishes share eight ingredients.** Any generator
needs the overlap constraint enforced separately, whatever engine drives it. **§2 now states this as four
explicit constraints rather than a hope.**

## §5 — The proxy and its number

**Every row cites the §1 want it stands for. A proxy that cannot cite one is a goal change to log, not a
refinement.**

| §1 want | Proxy | Status |
|---|---|---|
| **A** | **Union of parts across the 5 cuisines ÷ parts for the largest single cuisine** | proposed — the compression ratio (§2). **The headline number of this phase** |
| A | Parts that serve ≥2 dishes (reuse count) | proposed |
| A | Special purchases per week — target **0** | proposed; this is the want in his own words ("not hunt") |
| **B** | **Prep level score, her 10-15 scale** | **adopted from the field, not invented.** She already scores it; inventing a second scale would make the two incomparable |
| B | Share of each week's meals finishable on the serving day ("Element" vs "Full-Meal" split) | proposed; her own two recipe types are the measurement unit |
| B | Overlapping-ingredient ratio across the week | proposed |
| — | ~~Minimum ingredient set covering the most cuisines~~ | **REJECTED.** Coverage maximisation is a different goal. It carried the only number in the generated brief, so it became the scoreboard. The want never entered the chain |
| — | ~~"Prove it for one cuisine"~~ | **REJECTED by the user.** Measures nothing about generalisation, and generalisation is the want |

## §6 — Anti-goals

Checked against **§1**, not against any label or brief. An inherited anti-goal is a scope error.

1. **Not a research report.** *(Corrects D8 in `.scratch/larder/DECISIONS.md`.)*
2. **Not a clone of Restaurant Dropout.** She sells a **human, weekly, paid** service. The want is the
   *quantified, generated* version. Reproducing her newsletter is failure, not success.
3. **Not a subscription, and not a paywalled menu service.**
4. **Not a cookbook** — unless the meta-cookbook resolves into Want A, which is open (§1.3).
5. **Not a nutrition, health, or medical optimiser.** He never mentioned health; the brief never did either.
6. **Not a grocery-delivery, shopping, or cost-minimisation service.** The pain is **hunting**, not price.
7. **Not traditional meal prep / batch cooking.** The field's own anti-term. Eating the same dinner five
   days running is explicitly not the goal.
8. **Not a restaurant-technique showcase.** Shelf-stability and weeknight time budgets are the point.

## §7 — What would make him stop

1. **A's union blows up.** If the parts across five cuisines share little, so stocking them means 150-200
   items, then "stock up once" is a fiction and Want A is dead. **This is the most likely stop** and §2
   is designed to hit it early.
2. If a cuisine **cannot** be decomposed without per-dish fresh purchases.
3. If the generated week **reads as food he would not eat.** A correct-but-unappetising week is a failure.
4. If it needs an appliance or a pantry expansion he would not actually buy.

---

## Goal-change log

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | §1 written from the user's own words. **Everything written earlier the same day was built on a different goal** — the "Five research questions" in `sources/00-brief.md`, a document he did not write | He asked to step back and separate his want from the generated prompt |
| 2026-10-25 | **D8 corrected in place.** "No recipe list / shopping list / implementation plan" was inherited from the *research-report* framing. §1 wants artifacts | An anti-goal inherited from a pointer is a scope error |
| 2026-10-25 | Wants **A** and **B** separated; B depends on A | His words contain two wants; the earlier documents merged them into one "Larder" |
| 2026-10-25 | The brief's Q1 rejected as a proxy | Coverage maximisation ≠ decomposition for reuse. It had the only number, so it became the scoreboard |
| 2026-10-25 | **§2 v1 rejected by the user.** "Prove it for one cuisine" → **"several cuisines at once — one proves nothing about the method"** | His correction produced the actual headline metric: the compression ratio across cuisines. **§2 v2 adopted** |
| 2026-10-25 | **§3 went from empty to filled** — the field's vocabulary is Zoe Barrie's, from primary sources | He named the practitioner; the pointer resolved. Her terms replace my invented seeds |
| 2026-10-25 | **§5 adopted her prep-level score (10-15) instead of inventing a scale** | Inventing a second scale would make the two systems incomparable |
| 2026-10-25 | **§1.4 added.** Finding: **B is a quantification of an existing manual method; A is new work.** She rotates dishes in one pantry, she does not decompose cuisines | Resolved from her own published pages. Labelled new information, not a restatement |
| 2026-10-25 | **He restated the target: "clone Barrie's idea and then automate it."** Recorded. **§1 unchanged.** Consequence logged: A is the sub-problem that makes B generate without hunting, not a parallel want | His words, same day. This narrows §1.2's ordering without editing §1 |
| 2026-10-25 | **§4.5 added — M1 (tree walk) and M2 (embeddings by culture), both his.** Recorded as techniques, kept out of §1 | He offered mechanisms. Mechanisms are evaluated against proxies; they never define the goal |
| 2026-10-25 | **M2 identified as Epicure** — the likely reason the repo was attached to the original brief | His pointer + my probe. Both existed; the connection is new |
| 2026-10-25 | ~~Ground truth identified as a hard gate: cloning Barrie requires her actual weeks, and her menus are paywalled.~~ **WITHDRAWN the same session.** | **He answered: *"copy her style procedure (one grocery haul, prep on day 1, finish on serving day utilizing overlapping ingredients)."*** Cloning her **procedure** needs no reference corpus — the procedure **is** the spec, and a generated week either satisfies the four constraints or it does not. **The spec is self-validating.** This row is struck rather than deleted, so the reasoning is not re-derived later |
| 2026-10-25 | **Engine chosen: M2** (embed by culture / Epicure) | His pick. M1 needs a hand-built tree per cuisine; M2 needs none and is already proven reachable |
| 2026-10-25 | **§2 v3 written** — four explicit constraints (one haul · day-1 part · serving-day finish · shared pool), replacing the v2 "shared backbone" proxy as the primary question | Derived from his four answers. Constraints are independently falsifiable; the overlap metric survives as the Want-A number |
| — | *(§1 has not moved. It is still his original sentence, unedited.)* | |
