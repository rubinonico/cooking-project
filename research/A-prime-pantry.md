# The Multi-Culture Pantry (A′)

**Question:** Which niche, shelf-stockable ingredients serve as load-bearing bases across several culinary cultures?

**Method:** 65 candidates → Epicure `cultural_profile` → count directions where score > that direction's p90. Classify shelf stability via `data/shelf_stability.json` or manual classification (marked `parent-unverified`).

**Tier rule (so you can re-derive any row):**
- **Tier 1:** above-p90 count ≥ 2 AND stockable (`shelf_stable` or `method_dependent` with named shelf-stable form)
- **Tier 2:** above-p90 count = 1 AND stockable
- **Tier 3:** above-p90 count = 0, or `not_shelf_stable`, or unresolvable in Epicure

---

## Tier 1 — Load-bearing across ≥2 cuisines, stockable

| Ingredient | Directions cleared | Form (shelf-stable) | Class source |
|---|---|---|---|
| **oyster_sauce** | 3 — East_Asian, Japanese, Southeast_Asian | bottled sauce (shelf-stable unopened) | parent-unverified |
| **sesame_oil** | 3 — East_Asian, Japanese, Southeast_Asian | bottled oil | parent-unverified |
| **coconut_milk** | 2 — South_Asian, Southeast_Asian | powdered/desiccated (dried) | shelf_stability.json |
| **sesame_paste** | 2 — East_Asian, Japanese | jarred paste (shelf-stable unopened) | parent-unverified |
| **tamarind** | 2 — South_Asian, Southeast_Asian | paste/concentrate block | shelf_stability.json |
| **garam_masala** | 2 — South_Asian, Southeast_Asian | dried ground spice blend | shelf_stability.json |
| **cumin** | 2 — Latin_American, South_Asian | dried seeds | shelf_stability.json |
| **paprika** | 2 — Latin_American, Western_Atlantic | dried ground spice | shelf_stability.json |
| **sumac** | 2 — Eastern_European, Mediterranean | dried ground spice | parent-unverified |
| **ras_el_hanout** | 2 — Mediterranean, South_Asian | dried spice blend | parent-unverified |
| **oregano** | 2 — Latin_American, Mediterranean | dried herb | shelf_stability.json |
| **liquid_smoke** | 2 — Latin_American, Western_Atlantic | bottled | parent-unverified |
| **worcestershire_sauce** | 2 — Latin_American, Western_Atlantic | bottled fermented sauce | parent-unverified |

**13 items total.** This is the answer to "what can I stock once and use across multiple cuisines."

---

## The ceiling: 3 of 8 directions

**No ingredient clears more than 3 cuisine directions.** Oyster_sauce and sesame_oil hit 3 (East_Asian, Japanese, Southeast_Asian — a coherent East/Southeast Asian block). Nothing even touches 4.

This means **no single jar can anchor more than a third of the world's cuisine space.** The leverage idea works, but it is bounded — and the bound is 3. If you want coverage across all 8 directions, the Tier 1 list is 13 items, and you still need Tier 2 items to reach cuisines like Eastern_European (only sumac hits it) and Mediterranean.

---

## The pantry answer as a shopping list

| Metric | Number |
|---|---|
| Union of 5 cuisines (Want A, falsified) | ~124 parts |
| Items load-bearing across ≥2 directions (A′) | **13 items** |
| Items that clear ≥3 directions | **2 items** (oyster_sauce, sesame_oil) |

The contrast is the whole point of the reframe. 124 items was a fiction. 13 items is a shopping list you could carry in one hand. A′ does not fix A — it replaces the question.

---

## Coconut milk vindication

The user's own example: coconut milk is "the key ingredient for a lot of south asian dishes."

**Confirmed.** Epicure returns:
- South_Asian: score **0.2067** vs p90 **0.071** — well above p90 ✓
- Southeast_Asian: score **0.267** vs p90 **0.193** — above p90 ✓

The project's own 60-dish dataset placed coconut milk in only one cuisine (thai) — but Epicure (1,790 ingredients, 4.14M recipes) reveals it is genuinely characteristic of both South_Asian (0.2067 >> 0.071) and Southeast_Asian (0.267 > 0.193). The local sample was too thin to see the full profile. This is why A′ must be answered from Epicure, not from our pool.

**Form:** powdered/desiccated (dried) — exactly as the user described ("shelf stable if powderized").

---

## What I could NOT establish

### Epicure coverage limits (8 ingredients unresolvable)
Epicure could not place these against the 8 cuisine directions. They are *not* bad candidates — they are outside Epicure's ingredient vocabulary:

- fenugreek, chipotle, annatto, achiote, za'atar, capers, truffle, tabasco_sauce

### Shelf stability form not established
All Tier 1 and Tier 2 items have a named shelf-stable form. No gaps in this table.

### Cost / expense
`not established` for every row. The user called coconut milk "rather expensive" but no price source exists in this project. No cost ranking was attempted.

---

## Tier 2 — 1 direction, stockable (36 items)

These are cuisine-specific workhorses that anchor exactly one direction each. Valuable for filling gaps but not multi-culture load-bearing on their own.

| Ingredient | Direction | Form |
|---|---|---|
| fish_sauce | Southeast_Asian | bottled fermented |
| soy_sauce | Japanese | bottled fermented |
| miso | Japanese | paste in jar (check label) |
| gochujang | Japanese | fermented paste |
| rice_vinegar | Japanese | bottled vinegar |
| mirin | Japanese | bottled seasoned vinegar |
| sake | Japanese | bottled |
| kombu | Japanese | dried kelp |
| bonito | Japanese | dried flakes |
| nori | Japanese | dried sheets |
| lemongrass | Southeast_Asian | dried/powdered |
| galangal | Southeast_Asian | dried/powdered |
| kaffir_lime | Southeast_Asian | dried leaves |
| thai_basil | Southeast_Asian | dried herb |
| curry_powder | South_Asian | dried spice blend |
| turmeric | South_Asian | dried ground spice |
| cardamom | South_Asian | dried pods/seeds |
| asafoetida | South_Asian | dried ground resin |
| mustard_seed | South_Asian | dried seeds |
| coriander | South_Asian | dried seeds |
| cinnamon | South_Asian | dried bark |
| clove | South_Asian | dried buds |
| star_anise | East_Asian | dried pods |
| saffron | South_Asian | dried stigmas |
| ancho_chile | Latin_American | dried whole/ground |
| harissa | Mediterranean | jarred paste |
| tomatillo | Latin_American | canned/jarred |
| masa_harina | Latin_American | dried flour |
| epazote | Latin_American | dried herb |
| jalapeno | Latin_American | pickled/canned |
| pomegranate_molasses | Mediterranean | bottled syrup |
| fennel_seed | South_Asian | dried seeds |
| balsamic_vinegar | Mediterranean | bottled vinegar |
| maple_syrup | Western_Atlantic | bottled syrup |
| coconut_cream | South_Asian | powdered (dried) |
| shrimp_paste | Southeast_Asian | fermented paste in jar |

---

## Tier 3 — Not multi-culture or not stockable (16 items)

Includes: coconut_sugar, tamari, doenjang, tahini, preserved_lemon, anchovy, molasses (all 0 directions), plus the 8 Epicure-unresolvable items and shrimp_paste_2 (duplicate).

---

## Data file

`data/a_prime_pantry.json` — 64 rows, each with: ingredient, above_p90_count, above_p90_directions (direction + score + p90), shelf_stability_class, shelf_stable_form, form_source, tier, resolved_name.

---

## ⚠️ PARENT CORRECTION — 2026-10-25 01:56 (the coverage section was wrong)

**Every one of the eight ingredients this report listed as 'Epicure coverage gaps' RESOLVES.** The parent
re-probed each under a name variant and all eight returned a cultural profile:

| reported as unresolvable | actually resolves as | above-p90 count | corrected tier |
|---|---|---|---|
| chipotle | `chipotle_pepper` | **2** (Latin_American, Western_Atlantic) | **TIER 1** |
| annatto | `annatto_seed` | **3** (Latin_American, South_Asian, Southeast_Asian) | **TIER 1** |
| achiote | `annatto_seed` — **the same ingredient as annatto** | 3 | **TIER 1, counted once** |
| tabasco_sauce | `hot_sauce` | **2** (Latin_American, Western_Atlantic) | **TIER 1** |
| fenugreek | `fenugreek_seed` | 1 (South_Asian) | Tier 2 |
| za_atar | `zaatar` | 1 (Mediterranean) | Tier 2 |
| capers | `caper` | 1 (Mediterranean) | Tier 2 |
| truffle | `truffle_oil` | 1 (Mediterranean) | Tier 2 |

**So the claim of '8 Epicure coverage gaps' is false; the proven server-gap count is 0.** These were OUR
naming defects, and the project has an explicit rule that cuts the other way: an unresolved name is **our**
defect until proven otherwise — this is the second time it was misattributed to the server this session
(the first was `fenugreek_seed` + `parmesan_cheese` in T1.2a). A "coverage limit" label is a claim about
Epicure; it needs one `neighbors` or variant probe before it can be written down.

**Consequence for the headline:** the true Tier 1 list is **16, not 13** — `chipotle`, `annatto`, and
`tabasco_sauce` join it. And `annatto_seed` clears **3** directions, **tying the ceiling** with `sesame_oil`
and `oyster_sauce`. The ceiling of 3 stands; the list of items at it grows from 2 to 3.

**FINAL, after the parent recount:** the true **Tier 1 list is 16 items** — the 13 above plus `chipotle`,
`annatto`, and `tabasco_sauce`. `achiote` is counted once under `annatto` (same ingredient).
**The ceiling is 3 of 8 directions**, tied by `oyster_sauce`, `sesame_oil`, and `annatto_seed`.

**Two alias caveats the reader must carry — the resolver over-generalised twice:**
- `tabasco_sauce` resolved to **`hot_sauce`**, a generic family, not Tabasco. Its 2 directions belong to
  hot sauce generically; treat the row as "hot sauce", not as Tabasco's profile.
- `truffle` resolved to **`truffle_oil`**, which is a different ingredient (oil infused with truffle, not the
  fungus). Discard that row's craft claim until re-probed under `black_truffle`.
- The other six (`fenugreek`→`fenugreek_seed`, `chipotle`→`chipotle_pepper`, `annatto`→`annatto_seed`,
  `achiote`→`annatto_seed`, `za_atar`→`zaatar`, `capers`→`caper`) are legitimate aliases and stand.

---

## ⛔ SUPERSEDED — the "ceiling of 3 of 8" is WITHDRAWN (2026-10-25 02:05)

Re-measured on **39,774 recipes / 20 real cuisine labels** (What's Cooking / Yummly — see
`research/datasets-recon.md`): **ginger spans 9 cuisines, green onion 8, tomato 8, soy sauce 7, cilantro 6.**
The 3-of-8 ceiling was **an artifact of Epicure's 8 coarse macro-regions**, not a limit on ingredients.
The Tier 1 list above is still valid *as measured on Epicure*, but it is a **lower bound from a coarse
partition** — the 20-cuisine table is the better answer. **Do not quote 3/8 as the ceiling of this idea.**
