# Food.com corpus — the prep split, found

**Verified 2026-10-25.** `Karo8870/food.com-parsed-dataset` on HuggingFace —
`parsed_recipes.csv`, **652 MB, 490,457 recipes**. Loader: `larder/foodcom.py` (self-checking).

## Measured coverage — 490,457 recipes

| field | coverage |
|---|---|
| `preparation_time` + `cooking_time` | **490,457 / 490,457 — 100%** |
| prep > 0 | 477,454 (97.4%) |
| cook > 0 | 419,921 (85.6%) |
| cuisine-like tag | 50,751 (10.3%) |
| **distinct ingredients** | **328,255** |

## The split is REAL, and it is measured — not inferred

Barrie's day-1 prep / serving-day finish, read straight off real recipes as
`preparation_time >= 4 h AND cooking_time <= 45 min`:

> **4,743 recipes match the pattern exactly.**

| prep | cook | recipe | cuisine |
|---|---|---|---|
| 240m | 25m | **Biryani** | indian |
| 480m | 10m | **Chicken Fajitas** | mexican |
| 480m | 8m | Grilled Swordfish or Tuna Steaks | — |
| 1,440m | 20m | Carina's Tofu-Vegetable Kebabs | — |
| 1,440m | 30m | Pork Liver Pudding | — |

Distribution across the corpus: prep <30 m **80.9%** · 30-60 m **13.1%** · 1-4 h **4.3%** ·
**≥4 h 1.4% (6,781)**. Medians: prep 15 min, cook 30 min.

## What this closes that Yummly could not

1. **Quantities.** `ingredients` is structured — `{quantity, unit, name, description}`, e.g.
   `{"quantity": "4", "unit": "cups", "name": "blueberries"}`. A shopping list can now carry
   amounts. Yummly gave bare names, which is why the earlier list said *what* to buy, not how much.
2. **The day-1 / serving-day split** — the last piece of Barrie's method, previously
   `not established` on every dish.
3. **Scale and reach.** 328,255 distinct ingredients vs Yummly's 6,286 (**52x**), and cuisines
   Yummly does not carry at all: **african 4,343 · caribbean 2,718 · german 2,263 · creole 1,586**.

## ⚠️ What is WRONG with this mirror — do not paper over it

- **`steps` is polluted with image URLs, not instructions.** Sampled rows hold
  `https://img.sndimg.com/...` lists in the `steps` field. A coverage count reads "32% have steps" —
  those are largely image lists, so **true instruction coverage here is ~0**. Instructions therefore
  CANNOT be taken from this mirror, and the split is derived from the TIMES instead. That is arguably
  the better input anyway: times are quantitative and 100% covered, whereas instructions would need
  parsing. Per-step detail ("which steps belong to day 1") still needs RecipeNLG.
- **Only ~10% carry a cuisine tag**, so the cuisine axis is thinner than Yummly's clean 20-label
  field. Tags are kept for absolute volume (mexican 12,391 vs Yummly's 6,438).
- **Mirror license unstated.** Flag before any redistribution.

## Two broken datasets caught before they shipped

1. **`Vatazh0k/recipes_data_food.com` and `AkashPS11/recipes_data_food.com` are the same truncated
   file** — both exactly 34,074,734 bytes. 1,048,543 rows, of which only **1,228 are populated
   (0.1%)**; rows 1230 onward are empty. A first pass reported it as "1,048,543 recipes with
   instructions, quantities, prep/cook times, MIT-licensed" — all true of the *header*, false of the
   *file*. Caught by spot-checking row 1230. The most-downloaded mirror (421 downloads, 43 likes) is
   the broken one.
2. **`prep_min and cook_min` in my own loader** — a legitimate `0` (no prep needed) is falsy, so it
   read as missing and collapsed the coverage figure. Caught by the module's own self-check.

## Recipe1M+ — gated, and not needed

`pic2recipe.csail.mit.edu` (the link supplied) requires a **submission form, an emailed download
link, and a research-only license** — it cannot be fetched headlessly, and it is not a substitute for
what was already found. RecipeNLG remains the open route if per-step instruction detail is wanted:
2.23M recipes with directions, ~2.9 GiB, **but disk here is 17 GB free at 99% full**.
