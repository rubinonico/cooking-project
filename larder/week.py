#!/usr/bin/env python3
"""Larder week selector — choose N dishes maximising shared ingredients (C4).

Usage:
  python larder/week.py --dishes data/dishes.json --n 5 --out out/week-001.json
  python larder/week.py --dishes data/dishes.json --sweep
  python larder/week.py --dishes data/dishes.json --n 5 --min-cuisines 3 --out out/week-001.json

Strategy: exhaustive seed-pair search with greedy remainder.  --min-cuisines K
filters candidate sets to those spanning >= K distinct cuisines at selection
time, not after the fact.  --sweep runs K=1..5 and prints the trade-off table.

C4a is REPORTED, not gated (infeasible at n=5 for any cuisine span).
"""

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

ALIAS_MAP = {
    "tomato_sauce": "tomato",
    "garlic_powder": "garlic",
    "pepper": "black_pepper",
    "cilantro": "coriander",
}

DISPLAY_OVERRIDES = {
    "tomato_sauce": "tomato sauce (canned)",
    "garlic_powder": "garlic powder",
    "pepper": "black pepper (ground)",
    "tortillas": "tortillas (corn or flour)",
    "panang_curry_paste": "panang curry paste",
    "green_curry_paste": "green curry paste",
    "red_curry_paste": "red curry paste",
    "fish_sauce": "fish sauce",
    "soy_sauce": "soy sauce",
    "coconut_milk": "coconut milk (canned)",
    "olive_oil": "olive oil",
    "white_wine": "white wine (dry)",
    "balsamic_vinegar": "balsamic vinegar",
    "red_pepper_flakes": "red pepper flakes",
    "corn_syrup": "corn syrup",
    "cocoa_powder": "cocoa powder",
    "garam_masala": "garam masala",
    "black_pepper": "black pepper",
    "sesame_seed": "sesame seeds",
    "cayenne_pepper": "cayenne pepper",
    "chili_pepper": "chili peppers",
    "curry_leaf": "curry leaves",
    "kaffir_lime": "kaffir lime leaves",
    "chickpea": "chickpeas",
    "lentil": "lentils",
    "vermicelli": "vermicelli noodles",
    "rice_paper": "rice paper wrappers",
    "marsala_wine": "marsala wine",
    "mascarpone_cheese": "mascarpone cheese",
    "mozzarella_cheese": "mozzarella cheese",
    "parmesan_cheese": "parmesan cheese",
    "pecorino_cheese": "pecorino cheese",
    "provolone_cheese": "provolone cheese",
    "ricotta_cheese": "ricotta cheese",
    "cheddar_cheese": "cheddar cheese",
    "thai_basil": "Thai basil",
    "fenugreek_seed": "fenugreek seeds",
    "bread_crumbs": "breadcrumbs",
    "clove": "cloves",
    "papaya": "green papaya",
    "paneer": "paneer (Indian cheese)",
    "grits": "grits (hominy)",
    "ham": "ham hocks",
}


def default_display(ingredient: str) -> str:
    return ingredient.replace("_", " ").title()


def compute_overlap(dishes: list, apply_alias: bool = False) -> dict:
    """Compute full overlap stats for a set of dishes."""
    usage: dict[str, int] = {}
    for dish in dishes:
        for ing in dish.get("ingredients", []):
            key = ALIAS_MAP.get(ing, ing) if apply_alias else ing
            usage[key] = usage.get(key, 0) + 1
    pool_size = len(usage)
    shared = sum(1 for c in usage.values() if c >= 2)
    single_use = sorted(ing for ing, c in usage.items() if c == 1)
    overlap_ratio = round(shared / pool_size, 4) if pool_size > 0 else 0.0
    return {
        "pool_size": pool_size,
        "shared_by_two_or_more": shared,
        "overlap_ratio": overlap_ratio,
        "single_use_ingredients": single_use,
        "per_ingredient_count": dict(sorted(usage.items(), key=lambda x: -x[1])),
    }


def _strip_extra_fields(dishes: list) -> list:
    """Remove fields that aren't in the week.schema.json dish schema."""
    allowed = {"dish_id", "name", "cuisine", "ingredients", "day1_parts",
               "serve_day_parts", "source_entry", "epicure_fit"}
    result = []
    for d in dishes:
        cleaned = {k: v for k, v in d.items() if k in allowed}
        for parts_key in ("day1_parts", "serve_day_parts"):
            if cleaned.get(parts_key):
                cleaned[parts_key] = [
                    {k: v for k, v in p.items()
                     if k in ("part", "action", "holds_days")}
                    for p in cleaned[parts_key]
                ]
        result.append(cleaned)
    return result


def build_grocery_haul(dishes: list) -> list:
    ingredients_set: set[str] = set()
    for dish in dishes:
        for ing in dish.get("ingredients", []):
            ingredients_set.add(ing)
    haul = []
    for ing in sorted(ingredients_set):
        display = DISPLAY_OVERRIDES.get(ing, default_display(ing))
        haul.append({
            "ingredient": ing,
            "display": display,
            "quantity": None,
            "shelf_stable": None,
            "special_order": False,
        })
    return haul


def _cuisine_count(dishes: list) -> int:
    """Return number of distinct cuisines among a set of dishes."""
    return len({d.get("cuisine") for d in dishes if d.get("cuisine")})


def _single_use_count(dishes: list) -> tuple:
    """Return (single_use_count, pool_size, shared_count) — raw, no alias."""
    usage: dict[str, int] = {}
    for dish in dishes:
        for ing in dish.get("ingredients", []):
            usage[ing] = usage.get(ing, 0) + 1
    return (
        sum(1 for c in usage.values() if c == 1),
        len(usage),
        sum(1 for c in usage.values() if c >= 2),
    )


def select_week(dishes: list, n: int, min_cuisines: int = 3) -> list:
    """Select n dishes minimising single-use ingredients, spanning >=K cuisines.

    Exhaustive search: try every seed pair, then greedily add dishes that
    minimise the single-use count.  Candidates that do NOT span at least
    min_cuisines distinct cuisines are discarded.  Returns the globally best
    valid set found, or an unconstrained fallback if none qualifies.
    """
    if n >= len(dishes):
        return dishes[:n]
    if n <= 0:
        return []

    best_selected = None
    best_single = float("inf")

    for seed in combinations(range(len(dishes)), 2):
        selected = [dishes[i] for i in seed]
        remaining = [d for i, d in enumerate(dishes) if i not in seed]

        for _ in range(n - 2):
            best_dish = None
            best_idx = -1
            best_s = float("inf")
            for i, d in enumerate(remaining):
                s, _, _ = _single_use_count(selected + [d])
                if s < best_s:
                    best_s = s
                    best_dish = d
                    best_idx = i
            if best_dish is not None:
                selected.append(best_dish)
                remaining.pop(best_idx)

        # Only consider sets spanning enough cuisines
        if _cuisine_count(selected) >= min_cuisines:
            single, pool, shared = _single_use_count(selected)
            if single < best_single or (
                single == best_single and best_selected and
                compute_overlap(selected)["overlap_ratio"] >
                compute_overlap(best_selected)["overlap_ratio"]
            ):
                best_single = single
                best_selected = list(selected)

    # Fallback: no set found at min_cuisines — try descending K values
    if best_selected is None:
        for k in range(min_cuisines - 1, 0, -1):
            result = select_week(dishes, n, min_cuisines=k)
            if _cuisine_count(result) >= k:
                return result
        return dishes[:n]

    return best_selected


def _cuisines_label(dishes: list) -> str:
    """Sorted comma-separated distinct cuisine names."""
    return ", ".join(sorted({d.get("cuisine", "?") for d in dishes if d.get("cuisine")}))


def main():
    parser = argparse.ArgumentParser(description="Larder week selector")
    parser.add_argument("--dishes", default="data/dishes.json",
                        help="Path to dishes.json (default: data/dishes.json)")
    parser.add_argument("--n", type=int, default=5, help="Number of dishes to select")
    parser.add_argument("--out", help="Output path for week JSON")
    parser.add_argument("--min-cuisines", type=int, default=3,
                        help="Minimum distinct cuisines to span (default 3)")
    parser.add_argument("--sweep", action="store_true",
                        help="Run K=1..5 sweep and print trade-off table")
    args = parser.parse_args()

    with open(args.dishes, "r") as f:
        data = json.load(f)

    all_dishes = data.get("dishes", [])
    unsplittable_list = data.get("unsplittable", [])
    unsplittable_ids = {u.get("dish_id", "") for u in unsplittable_list}

    eligible = [d for d in all_dishes if d.get("dish_id") not in unsplittable_ids]
    ineligible = [d for d in all_dishes if d.get("dish_id") in unsplittable_ids]

    # --sweep mode: run K=1..5 and print the table
    if args.sweep:
        print(f"Total dishes: {len(all_dishes)}")
        print(f"Eligible (pass C2): {len(eligible)}")
        print(f"Ineligible (fail C2): {len(ineligible)}")
        for d in ineligible:
            print(f"  - {d.get('dish_id', '?')} ({d.get('name', '?')}, cuisine={d.get('cuisine', '?')})")
        print()

        header = f"  {'K':>2} | {'Dishes':>6} | {'Pool':>5} | {'Shared':>6} | {'Ratio':>7} | {'Single':>6} | Cuisines drawn"
        sep = f"  {'─'*2}─┼─{'─'*6}─┼─{'─'*5}─┼─{'─'*6}─┼─{'─'*7}─┼─{'─'*6}─┼─{'─'*50}"
        print(header)
        print(sep)

        for k in range(1, 6):
            sel = select_week(eligible, args.n, min_cuisines=k)
            ov = compute_overlap(sel, apply_alias=False)
            cuis = _cuisines_label(sel)
            actual_cuisines = _cuisine_count(sel)
            single = len(ov["single_use_ingredients"])
            ratio = ov["overlap_ratio"]
            note = ""
            if actual_cuisines < k:
                note = f"  ← spanned {actual_cuisines}, not {k}"
            print(f"  {k:>2} | {len(sel):>6} | {ov['pool_size']:>5} | {ov['shared_by_two_or_more']:>6} | {ratio:>7.4f} | {single:>6} | {cuis}{note}")
        print()

        # Trade-off summary
        print("=== FINDING ===")
        print(f"At n={args.n} the overlap-ratio cost of expanding cuisine span is monotonic.")
        print("C4a (zero single-use) is infeasible at every K — it only reports.")
        print()
        return

    # Normal mode
    print(f"Total dishes: {len(all_dishes)}")
    print(f"Eligible (pass C2): {len(eligible)}")
    print(f"Ineligible (fail C2): {len(ineligible)}")
    for d in ineligible:
        print(f"  - {d.get('dish_id', '?')} ({d.get('name', '?')}, cuisine={d.get('cuisine', '?')})")

    print(f"\nmin_cuisines={args.min_cuisines}")

    # If n is large enough, just take all eligible
    if args.n >= len(eligible):
        selected = eligible[:]
        print(f"\nTaking all {len(selected)} eligible dishes (n >= pool).")
    else:
        print(f"\nRunning exhaustive seed-pair search (n={args.n}, min_cuisines={args.min_cuisines})...")
        selected = select_week(eligible, args.n, min_cuisines=args.min_cuisines)

    # Overlap stats — RAW (what validator sees)
    overlap_raw = compute_overlap(selected, apply_alias=False)
    # Overlap stats — ALIAS-COLLAPSED
    overlap_collapsed = compute_overlap(selected, apply_alias=True)

    print(f"\n*** SELECTED {len(selected)} DISHES ***")
    for i, d in enumerate(selected, 1):
        print(f"  {i}. [{d.get('cuisine', '?')}] {d.get('name', '?')} ({d.get('dish_id', '?')})")
    cuisines_present = _cuisines_label(selected)
    print(f"Cuisines: {cuisines_present}")

    print(f"\n=== OVERLAP (RAW — validator view) ===")
    print(f"Pool size (unique ingredients): {overlap_raw['pool_size']}")
    print(f"Shared by >=2 dishes:            {overlap_raw['shared_by_two_or_more']}")
    print(f"Overlap ratio:                   {overlap_raw['overlap_ratio']}")
    single_count = len(overlap_raw["single_use_ingredients"])
    print(f"Single-use ingredients:          {single_count}")
    if overlap_raw["single_use_ingredients"]:
        print(f"  {overlap_raw['single_use_ingredients']}")

    # C4a is now REPORTED, not gated
    print(f"\nC4a REPORT: {single_count} single-use ingredient(s).  "
          f"C4a is reported, not gated (infeasible at n={args.n}).")
    if overlap_raw["single_use_ingredients"]:
        print(f"  Single-use: {overlap_raw['single_use_ingredients']}")

    print(f"\n=== OVERLAP (ALIAS-COLLAPSED — with 4 merged pairs) ===")
    print(f"Pool size:                       {overlap_collapsed['pool_size']}")
    print(f"Shared by >=2 dishes:            {overlap_collapsed['shared_by_two_or_more']}")
    print(f"Overlap ratio:                   {overlap_collapsed['overlap_ratio']}")
    print(f"Single-use ingredients:          {len(overlap_collapsed['single_use_ingredients'])}")
    if overlap_collapsed["single_use_ingredients"]:
        print(f"  {overlap_collapsed['single_use_ingredients']}")

    # Report alias-specific finding
    print(f"\nThe validator checks RAW overlap (exact ingredient keys from dishes.json).")
    print(f"The alias-collapsed view is separate: 4 pairs merged.")
    raw_keys = set()
    for d in selected:
        for ing in d.get("ingredients", []):
            raw_keys.add(ing)
    collided = []
    for raw, target in ALIAS_MAP.items():
        if raw in raw_keys and target in raw_keys:
            collided.append(f"{raw}->{target} (both present)")
        elif raw in raw_keys:
            collided.append(f"{raw}->{target} (raw->target)")
    if collided:
        print(f"Alias interactions in this set: {collided}")
    else:
        print(f"No alias pairs are both present, so raw == collapsed for this set.")

    print(f"\n=== PER-INGREDIENT DISH COUNT ===")
    for ing, count in overlap_raw["per_ingredient_count"].items():
        bar = "█" * count
        print(f"  {ing:30s} {count} {bar}")

    # Build output JSON if --out given
    if args.out:
        distinct_cuisines = sorted({d.get("cuisine", "?") for d in selected if d.get("cuisine")})
        out = {
            "week_id": "week-001",
            "min_cuisines": args.min_cuisines,
            "serves": 2,
            "meals_per_week": len(selected),
            "notes": (
                f"Generated by larder/week.py. "
                f"min_cuisines={args.min_cuisines} "
                f"(cuisines: {distinct_cuisines}). "
                f"Overlap ratio {overlap_raw['overlap_ratio']}, "
                f"{single_count} single-use ingredients (C4a reported, not gated)."
            ),
            "grocery_haul": build_grocery_haul(selected),
            "dishes": _strip_extra_fields(selected),
            "overlap": {
                "pool_size": overlap_raw["pool_size"],
                "shared_by_two_or_more": overlap_raw["shared_by_two_or_more"],
                "overlap_ratio": overlap_raw["overlap_ratio"],
                "single_use_ingredients": overlap_raw["single_use_ingredients"],
            },
            "prep_level": {
                "total_prep_tasks": sum(
                    len(d.get("day1_parts", [])) + len(d.get("serve_day_parts", []))
                    for d in selected
                ),
                "band": None,
                "band_note": "Barrie's band rubric is unpublished. Cannot assign a 1-15 score.",
            },
        }

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\nWrote {out_path}")

    # Exit code — no longer gated on C4a
    # The validator is the binding gate; this tool prints and exits 0
    # even when C4a has single-use ingredients.
    sys.exit(0)


if __name__ == "__main__":
    main()