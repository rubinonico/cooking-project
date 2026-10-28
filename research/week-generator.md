# The week generator — built and running

**Run it:**
```
python tools/plan_week.py --cuisines italian,indian,thai,southern_us \
    --dishes 5 --min-cuisines 3 --max-per-cuisine 2 --out out/week-002.json
```

**New files:** `tools/plan_week.py` (the generator), `larder/corpus.py` (shared loader + normaliser +
self-test), `out/week-002.json` (the week), `out/week-002.txt` (readable).
**Corpus:** 39,774 recipes / 20 cuisines — 662x the 60-dish pool the old selector used.

## The design decision that mattered: rarity-weighted objective

Maximising "ingredients shared by >=2 dinners" is free garbage — salt, onion, garlic and water are shared
by everything, so every week scores well and every week is the same. Ingredients are therefore weighted by
**IDF, log(N / dishes_containing_it)**: staples fall to ~0.1, specialties to ~7. **The score is the IDF mass
the week SHARES — what the one haul actually buys.** Sharing `fish sauce` counts; sharing `salt` does not.

## The cuisine-span trade-off, reproduced at a different scale

Measured with the new objective, new corpus, new metric — and it **agrees with the original finding**:

| cuisine span | overlap ratio | IDF mass shared | single-use |
|---|---|---|---|
| **K=2** | 0.5357 | 97.47 | 26 |
| **K=3** | 0.3934 | 72.93 | 37 |
| **K=4** | 0.2787 | 45.46 | 44 |

**Overlap roughly halves going from 2 to 4 cuisines and single-use rises 26 -> 44, monotonically.** This is
the fourth independent confirmation that the user's four cuisines are near-disjoint, and the first on real
recipes rather than a hand-tagged pool.

## What it does NOT do — reported, not invented

**The corpus is `{id, cuisine, ingredients[]}`. It has NO instructions, so the day-1 Element /
serving-day Full-Meal split CANNOT be derived.** Every dish reports
`"day1_element": "not established (corpus has no instructions)"`. This is the half of Barrie's method that
this corpus cannot supply, and it is printed on every run rather than faked. Closing it needs a corpus with
directions — RecipeNLG (2.23M recipes) is verified and named in `research/datasets-recon.md`.

## Five defects found by running it, all fixed

An earlier version shipped all five. Listed because each one produced a *believable* number:

1. **Dessert in the dinner list** — a cool-whip / instant-pudding / toffee-bit recipe. The corpus is
   user-submitted and mixes desserts, single-sauces and brand-name convenience items. Fixed with an explicit
   `NON_DINNER` marker filter, not by tuning the score.
2. **`hand` and `essence` in the shopping list** — parsing debris from the source. Fixed with a
   `NON_INGREDIENT` fence that drops and reports them.
3. **`couscou`** — the singulariser ate the `s` off `couscous` and split one ingredient into two. Fixed with
   a guard for words ending `us`/`is`/`ous`/`ss`.
4. **`lemongrass` vs `lemon grass`, `cilantro` vs `cilantro sprig`, `chily` vs `chili`** — three spellings of
   one ingredient each counted separately. **This inflated single-use from a true ~26 to 38.**
5. **`tomato pur e`** — accented characters split before punctuation stripping. Fixed by folding accents
   (NFKD) first.
6. **A gain function with no cost term** — it scored "IDF mass this dish would newly share" and ignored the
   ingredients the dish INTRODUCES, so a 40-ingredient recipe beat an 8-ingredient one and the week ended
   with **57 single-use items**. Fixed by scoring the resulting week, not the increment.

## The self-test — because the normaliser failed four separate times

`larder/corpus.py` now runs **22 known-good assertions on import**. A regression raises *before any number is
printed*. Cases pin both directions of the trap: `couscous`/`asparagus`/`hummus` must NOT be singularised;
`garlic powder` and `coriander seed` must NOT be merged away (the first is a FORM, the second is a different
purchase); `tomato purée` must fold to `tomato paste`.

**Name normalisation was the single largest source of wrong numbers in this entire project** — it appeared in
the alias map (T1.2a), in the union recomputation, in the Yummly merge, and four times here. Baking the test
into the module is the fix, because every one of those failures produced a plausible number rather than an error.

## Known limits, stated plainly

- **No quantities.** The corpus has ingredient *names* only, so the grocery list has no amounts. It says what
  to buy, not how much.
- **No step-1/step-2 split** (above).
- **Ingredient names are still noisy at the tail.** Merges are explicit for the ~90 collisions actually
  observed; a `price per item` or `curry sauce` may still surface as its own row. The `other` aisle bucket
  being large is the signal that the map needs extending.
- **`indian` is North-Indian-weighted** (coconut milk at only 7.2%) — a within-country regional fact this
  label cannot resolve.
