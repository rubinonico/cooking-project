# Publishing rules — what may leave this machine

Written 2026-10-28, before anything is published. Three of the four source corpora here have **no stated
licence**, and one of them is a copyrighted book. The rules below are constraints, not preferences.

---

## 1. Verdict table

| asset | may publish? | why |
|---|---|---|
| **Your own code** (`larder/*`, `tools/*`, `tests/*`) | ✅ yes — after a licence decision | written here |
| **Aggregate statistics** (pool counts, overlap ratios, gate results) | ✅ yes | facts about a process, no rows reproduced |
| **This changelog, build log, pipeline doc** | ✅ yes — after path scrubbing | your writing |
| **Food.com recipe rows** (`data/external/foodcom_recipes.csv`) | ❌ no | mirror `Karo8870/food.com-parsed-dataset` states **no licence**; derived from Food.com/GeniusKitchen content |
| **Yummly / What's Cooking rows** (`whats-cooking-train.json`) | ❌ no | dataset states **no licence** |
| **Flavor Bible text + its parser output** | ❌ no | copyrighted book; locked as local, personal use only (decision D9, 2026-10-25) |
| **Zoe Barrie's menus / Recipe Vault** | ❌ no | behind her paid subscription |
| **Her method, vocabulary and stated objectives** | ✅ yes, **with attribution** | publicly described by her; the project quantifies it, does not reproduce it |
| **`data/external/fc_pool.json`, `out/week-*.json`** | ⚠️ no as-is | they contain recipe names, ingredient lists and quantities copied from the corpus. Publish a *schema example* with invented rows instead. |
| **Screenshots / terminal output** | ✅ after scrubbing | remove `C:\Users\rubin\...`, machine names, any vault path |

## 2. Attribution requirement

Every publication must say, in the body and not in a footnote:

1. The method — one haul, day-1 prep, serving-day finish, shared ingredients — is **Zoe Barrie's**
   ("Restaurant Dropout", *Ingredient Prep*). This project **quantifies and automates her procedure**; it
   does not invent it and does not reproduce her paid material.
2. The stockable-form and trunk→branch taxonomy are the **owner's** design, documented in his
   meta-cookbook.
3. `epicure-mcp` (KAIKAKU.AI, MIT) supplied the cross-check cuisine axis used in the earlier research.

## 3. Claim register — publish the sentence, not a bigger one

| number | may be published as | may **NOT** be published as |
|---|---|---|
| C1–C5 PASS on a week | "the generated week satisfies five stated structural constraints" | "the meal plan works" |
| overlap ratio 0.1667 | "16.7% of the week's ingredients are used by more than one dinner" | "efficient shopping" |
| 429 element / 2,911 decompress pools | "the pools contain N dinners meeting stated filters" | "N recipes tested" |
| 48 haul lines | "the current week lists 48 purchases" | "a normal grocery run" |
| prep/cook times | "day-1 and serving-day phases **derived from preparation and cooking times**" | "verified instructions" |
| **nothing cooked** | must be stated wherever results are shown | — |

**Hard rule:** any publication that shows gate results must also state that *no dish has been cooked and
tasted.* A green gate table without that sentence overstates the artifact.

## 4. Pre-publish checklist

1. No absolute paths (`C:\Users\…`), no machine names, no vault names.
2. No row-level recipe data. Invented examples only, clearly marked as invented.
3. No Flavor Bible text, no parse output, no paywalled Barrie material.
4. Attribution block present (§2).
5. The "nothing has been cooked" sentence present wherever gates appear.
6. Licence chosen for the code (recommendation: MIT) and stated in the repo root.
7. Withdrawn claims stay withdrawn — if the build log is quoted, the `withdrawn claims` section goes with it.

## 5. Open decisions (owner)

1. **Code licence** — recommend MIT; nothing in the code depends on the unlicensed corpora, but the
   *data loaders* point at files that must not ship.
2. **Format** — the build log is written to be readable as a standalone post; it can also serve as a
   repo README section or a portfolio artifact.
3. **Data-free reproduction** — if this is ever published with runnable code, it needs a synthetic
   5-dinner sample so a reader can run the gates without any corpus.
