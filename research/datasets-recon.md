# Dataset reconnaissance — verified 2026-10-25

Every row below was **fetched, not read about**. Licenses and sizes are from the live GitHub API.

## Verdict table

| dataset | license | what it actually is | fixes which A' gap | verdict |
|---|---|---|---|---|
| **What's Cooking (Yummly)** `MohammedAlawami/whats-cooking-dataset` | ⚠️ **none stated** | `train.json` 12.4 MB + `test.json` 2.8 MB — **39,774 recipes, 20 cuisines**, `{id, cuisine, ingredients[]}` | **cuisine coverage AND sample size** | ✅ **USE — by far the biggest win** |
| **FlavorGraph** `lamypark/FlavorGraph` | Apache-2.0 | `nodes_191120.csv` — **8,298 nodes = 6,653 ingredients + 1,645 flavour compounds**, each tagged `is_hub` (416 ingredient hubs); `edges_191120.csv` 5.2 MB pair graph | ingredient vocabulary + pairing graph + a **hub** centrality signal | ✅ USE for pairing/vocab |
| **FoodOn ontology** `FoodOntology/foodon` | CC-BY-4.0 | `foodon-base.owl` 32 MB, `foodon-full.owl` 40 MB — farm-to-fork ontology incl. **processing/form classes** | the **stockable-FORM gap** (raw → dried/powdered/canned) | ⚠️ candidate — heavy, needs OWL work |
| **GroceryDB** `Barabasi-Lab/GroceryDB` | MIT | 50,468 **branded grocery products** across 53 categories, with price + package weight | cost | ❌ **DOES NOT FIT — see below** |
| open-prices `openfoodfacts/open-prices` | AGPL-3.0 | a **service**, not a data dump (API + crowdsourced) | cost | ❌ not a dataset you download |
| RecipeNLG `Glorf/recipenlg` | ⚠️ on HF, not the repo | 2.23 M recipes, NER'd ingredients, **no cuisine labels** | scale only | ❌ no cuisine axis |

## The cost gap is NOT closed

GroceryDB is a **branded-consumer-product** database, not an ingredient price list. Matching the A′ items
against it produces false positives that survive every filter tried:

- `coconut milk` → *"Silk Unsweetened **Almond Coconut Milk** Blend"* — a beverage, not the cooking ingredient
- `miso` → *"Mini Babybel Light Semisoft Cheeses"*
- `garam masala` → *"Chutney Classical Vegetable Chutney"*
- `paprika` → *"Tyson Smoked Paprika Pork Back Ribs"* · `turmeric` → *"Turmeric Chicken Toddler Purees"*

Package sizes also vary by 10x, so `price/100g` medians are contaminated. **Cost therefore stays
`not established`** — a wrong price is worse than no price, and shipping one would launder it into a
pantry-buying decision. Closing it needs either hand-curated SKUs or a purpose-built price source.

## The correction the 20-cuisine rerun forced

**The Epicure "ceiling of 3 of 8 directions" was an artifact of Epicure's 8 coarse macro-regions, not a
fact about ingredients.** Re-measured on 39,774 recipes with 20 real cuisine labels (ingredient present in
≥10% of a cuisine's recipes):

| ingredient | cuisines spanned | which |
|---|---|---|
| **ginger** | **9** | chinese, filipino, indian, jamaican, japanese, korean, moroccan, thai, vietnamese |
| green onion | 8 | cajun_creole, chinese, jamaican, japanese, korean, mexican, thai, vietnamese |
| tomato | 8 | brazilian, cajun_creole, greek, indian, italian, mexican, moroccan, spanish |
| **soy sauce** | **7** | chinese, filipino, jamaican, japanese, korean, thai, vietnamese |
| cilantro | 6 | brazilian, indian, mexican, moroccan, thai, vietnamese |
| lime juice | 5 | brazilian, jamaican, mexican, thai, vietnamese |
| parsley | 5 | cajun_creole, greek, italian, moroccan, spanish |
| sesame oil | 4 | chinese, japanese, korean, vietnamese |
| fish sauce · coconut milk · cumin | 3 each | — |

**Only 3 of 115 qualifying ingredients are global staples** (onion, salt, water). **42 are niche and span
≥2 cuisines.** So multi-culture bases DO exist and are strong — the earlier "nothing is a base for more
than a third of the cuisine space" conclusion is **withdrawn**.

**A nuance on the coconut-milk claim, not a refutation:** in Yummly, coconut milk clears 10% in
**brazilian, jamaican, thai** — *not* indian. That is a **sampling artefact of the `indian` bucket being
North-Indian-dominated**; coconut milk is a South Indian / coastal staple. The user's statement ("key
ingredient for a lot of south asian dishes") is right; the cuisine label is too coarse to show it. This is
the same failure mode as the 8-direction ceiling — **a coarse partition hiding a real relationship.**

## Method notes / traps hit

- **Ingredient-name variants split counts.** `garlic` vs `garlic cloves`, `eggs` vs `large eggs`,
  `pepper` vs `ground black pepper` each scored separately, understating every span. Fixed by canonicalising
  **size and prep words only** — **preservation words (`dried`, `powdered`, `canned`, `smoked`) are KEPT**,
  because the form is the answer for A′, not noise. Report both merged and unmerged.
- **Threshold sensitivity is reported, not buried:** T=5% → 235 ingredients qualify; 10% → 115; 20% → 50.
  Every headline above is *ingredient present in ≥10% of that cuisine's recipes*.
- Yummly `train.json` carries **no license** — flag before any redistribution.

## Files
- `data/external/whats-cooking-train.json` (12.4 MB, 39,774 recipes, 20 cuisines)
- `data/external/ingredient_cuisine_matrix.json`, `data/external/cuisine_span_20.json`
- `data/external/fg_nodes.csv` (8,298 FlavorGraph nodes)
- `data/external/grocerydb_foods.csv` (50,468 products — retained for reference, **not** usable as prices)
