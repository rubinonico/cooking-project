# Larder — Names & Ship Viability
*2026-10-28. Sources labelled: **[check]** = live App Store/web search this session; **[project]** = from `MISC/Larder.md`; **[inference]** = my read, not measured.*

## 0. Why the name must change

`Larder` is occupied by at least four live meal-planning apps **[check]**:
- Larder: Meal Planner (`apps.apple.com/.../id6762561852`, also on Google Play)
- Larder: Family Meal Planner (`id6792101537`)
- larderapp.co

Every generic pantry word in the category is also taken: **Mise, Prep Day, Haul, Basket, Pan-try/Plantry** all return live apps in one search **[check]**. So a category-generic name cannot ship. The name has to be distinctive.

## 1. Naming rules used

Cut: `<x>ify`, "Chef", "Kitchen", "Pantry", "Plate", "Fork/Spoon/Whisk", "Eats", "Bite", misspelled words with dropped vowels, and anything with "AI" in it.

## 2. Shortlist — ranked

| # | Name | Why it works | Collision |
|---|---|---|---|
| **1** | **Trunk** | His own word from the meta-cookbook (trunk → branch). Names the mechanism: one base that branches into dishes. One syllable, no cringe, means storage. | Clean in food space **[check]** |
| **2** | **Repertoire** | The cook's native word for "five dishes I can actually make." Exact for a rotating weekly set. Old-money tone. | Only a dev portfolio page **[check]** |
| **3** | **Overlap** | States the actual differentiator — the rarity-weighted shared-ingredient constraint. No metaphor, no slop. | No app found **[check]** |
| 4 | **Commissary** | Chef-native: the shared kitchen that provisions many stations. | Taken by DeCA/military **[check]** — usable only if that reads as unrelated |
| 5 | **Fold** | Short cooking verb, "fold into the week." | Taken — family planner `foldapp.co` **[check]** |

**Killed:** Larder (4 apps), Mise, Prep Day, Haul, Basket, One Cart, Day One, Cellar, Stockpile, Mother, Mirepoix (unspellable), Backbone (aggressive, corporate).

**Recommendation: Trunk.** Provenance is his, it is the only candidate that names a mechanism instead of a mood, and the namespace is empty.

## 3. Ship viability — the honest verdict

**Verdict: not shippable as a paid product today. Shippable as a personal tool now, and the paid question is decidable in one weekend for ~$60.** **[inference, grounded in the two facts below]**

### What actually exists
- Week generator over 39,774 recipes / 20 cuisines, rarity-weighted (IDF) overlap objective, single grocery haul, reproducible K-sweep **[project]**
- `out/week-001.json` passes its own validator exit 0 **[project]**
- Food.com loader: 490,457 recipes, real quantities, 100% prep/cook times, **4,743 recipes match Barrie's 4h-prep / ≤45m-cook split exactly** — but not yet wired in, and `steps` in that mirror are image URLs, so per-step day-1 detail is ~0 coverage **[project]**
- No UI. No tasting. Ever. **[project]**

### The three things that would kill it

1. **Category is commoditized, and the one incumbent already proves the demand is for a person, not a program.** Barrie sells this exact method as a paid Substack; a dozen apps sell meal plans **[check]**. Whatever ships has to beat *her judgment*, not just "an app."
2. **The generator is weakest exactly where his cuisines are.** Overlap halves from K=2 to K=4 (0.536 → 0.279), single-use ingredients rise 26 → 44 **[project]**. The core promise — one haul, five dishes, zero leftover hunting — degrades on the four cuisines he actually cooks. A user would feel this in week one.
3. **Nothing has ever been tasted.** A meal-plan generator that has never produced a cooked meal is a hypothesis with a validator, not a product. This is the cheapest gate and it has not run.

### What is genuinely defensible
The overlap constraint is real and apparently unclaimed: competitors generate *plans*, few optimize *shared-ingredient coverage on a real corpus* with a prep/serve split **[check + inference]**. That is a feature, not a moat — a competitor with an LLM copies it in a week. Durability would have to come from the corpus quality (quantities + prep split) and from taste-tested output, neither of which exists yet.

## 4. The cheapest decisive test — one weekend, ~$60, ~4h

**Tasting gate:** pick the best generated week, buy it, cook two dishes (one Element, one Full-Meal finish), eat, and score: (a) did day-1 prep actually make serving-day fast, (b) would this repeat next week, (c) how much of the haul went unused.

**Baseline it must beat:** a naive random 5-recipe week from the same corpus — same shopping trip, no overlap objective. If the generated week does not visibly beat that on leftover waste and repeat-desire, the product is a validator with a grocery list and should be stopped at personal-tool scope.

## 5. Provenance
- His: the two wants, the retarget to Barrie's procedure, the trunk→branch model, the coconut-milk powder instinct.
- Mine: the name shortlist and collision checks, the three kill risks, the weekend gate design.
- Unverified: any claim about willingness to pay, market size, or that no competitor does overlap optimization. No pricing has been established anywhere in this project.
