"""Build the day-1/serving-day pool from the Food.com mirror.

    python tools/build_fc_pool.py            # writes data/external/fc_pool.json

Why a separate pool file: the 652 MB CSV takes ~2 min to stream, and the useful slice is
`prep >= 240 min AND cook <= 45 min` — Barrie's exact pattern. That slice is small, so it is
materialised once with the structured `{quantity, unit, name, description}` ingredient rows kept.

Honesty rules baked in:
  * `steps` in this mirror are image URLs, so NO instruction text is carried. The split is
    derived from times and labelled as such.
  * A recipe whose `servings` is missing keeps `servings: null` — never assumed.
"""
from __future__ import annotations

import ast
import collections
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from larder.fcnames import norm as fc_norm   # noqa: E402  (Food.com free-text names)
from larder.mealclass import classify as meal_class, DINNER, DESSERT, BREAKFAST  # noqa: E402
from larder.decompress import (  # noqa: E402
    COOK_MAX_MIN, INGREDIENT_MAX, PREP_MAX_MIN, comfort_name_ok, is_decompress,
)
from larder.foodcom import CSV_PATH, CUISINE_TAGS, DAY1_PREP_MIN, SERVING_COOK_MAX, _num, _parse_ingredients  # noqa: E402

OUT = ROOT / "data/external/fc_pool.json"
MIN_INGREDIENTS = 5
#: 25 → 15 on 2026-10-28: a 73-line haul for five dinners is a specialty shop, not a grocery run. The
#: long tail was 20-25-ingredient recipes whose spice lists dwarf the shared pantry.
MAX_INGREDIENTS = 15
#: a decompress dish is small by definition; larder/decompress.py caps it at 12
QUICK_MIN_INGREDIENTS = 3

#: cuisine label -> the single canonical name used by the selector
CUSINE_PRIMARY_ORDER = list(CUISINE_TAGS)


def _tags(raw: str) -> list[str]:
    if not (raw or "").startswith("["):
        return []
    try:
        return [t.strip().lower() for t in ast.literal_eval(raw) if isinstance(t, str)]
    except (ValueError, SyntaxError):
        return []


def main() -> None:  # noqa: C901
    rows_total = rows_time_ok = 0
    drop_no_ing = drop_len = drop_no_cuisine = drop_dessert = drop_breakfast = drop_time = 0
    quick_name_rejected = 0
    pool: list[dict] = []
    quick: list[dict] = []
    quick_rejected: list[str] = []
    cuisines: collections.Counter = collections.Counter()

    with open(CSV_PATH, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            rows_total += 1
            name = (row.get("name") or "").strip()
            pm, cm = _num(row.get("preparation_time")), _num(row.get("cooking_time"))
            if pm is None or cm is None:
                drop_time += 1
                continue
            # TWO SHAPES. Element = real day-1 work (>= 4 h prep, short cook). Quick = the
            # "decompress" slot: no day-1 work at all, on the table inside half an hour.
            is_element = pm >= DAY1_PREP_MIN and cm <= SERVING_COOK_MAX
            is_quick_shape = pm <= PREP_MAX_MIN and cm <= COOK_MAX_MIN
            if not (is_element or is_quick_shape):
                drop_time += 1
                continue
            # Cheap title pre-check before the expensive ingredient parse: prep<=20/cook<=30 matches
            # ~150k rows, and only comfort-class names can become a decompress dish.
            if not is_element and not comfort_name_ok(name)[0]:
                quick_name_rejected += 1
                continue
            rows_time_ok += 1
            ings = _parse_ingredients(row.get("ingredients") or "")
            if not ings:
                drop_no_ing += 1
                continue
            names = sorted({fc_norm(i["name"]) for i in ings if fc_norm(i["name"])})
            if not (MIN_INGREDIENTS <= len(names) <= MAX_INGREDIENTS):
                # an element dish outside 5-15 ingredients is dropped; a quick dish may be smaller
                if not (is_quick_shape and QUICK_MIN_INGREDIENTS <= len(names) <= MAX_INGREDIENTS):
                    drop_len += 1
                    continue
            tags = _tags(row.get("tags") or "")
            # FIVE WEEKNIGHT DINNERS, not "a week of food" (owner's frame, 2026-10-28): desserts and
            # breakfasts are out unless the title explicitly says it is dinner. Tag-driven, not a guess.
            klass = meal_class(name, set(tags))
            if klass != DINNER:
                if klass == DESSERT:
                    drop_dessert += 1
                else:
                    drop_breakfast += 1
                continue
            cuis = [c for c in CUISINE_TAGS if c in tags]
            if not cuis:
                drop_no_cuisine += 1
                continue
            for c in cuis:
                cuisines[c] += 1
            entry = {
                "name": (row.get("name") or "").strip(),
                "cuisines": cuis,
                "ingredients": names,
                "items": ings,
                "prep_min": pm,
                "cook_min": cm,
                "servings": _num(row.get("servings")),
            }
            if is_element and MIN_INGREDIENTS <= len(names) <= MAX_INGREDIENTS:
                pool.append(entry)
                for c in cuis:
                    cuisines[c] += 1
                continue

            if not is_quick_shape:
                drop_len += 1
                continue
            q_ok, q_reason = is_decompress(entry["name"], pm, cm, len(names))
            if q_ok:
                quick.append(entry)
            elif len(quick_rejected) < 60:
                quick_rejected.append(f"{entry['name'][:44]} — {q_reason}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"meta": {
        "source": "data/external/foodcom_recipes.csv (Food.com mirror, 490,457 rows)",
        "filter": f"prep >= {DAY1_PREP_MIN} min AND cook <= {SERVING_COOK_MAX} min, "
                  f"{MIN_INGREDIENTS}-{MAX_INGREDIENTS} ingredients, >=1 cuisine tag",
        "rows_total": rows_total, "rows_time_ok": rows_time_ok, "rows_kept": len(pool),
        "elements": len(pool), "quick": len(quick),
        "quick_rejected_examples": quick_rejected,
        "dropped": {"no_ingredients": drop_no_ing, "ingredient_count": drop_len,
                    "no_cuisine_tag": drop_no_cuisine,
                    "dessert": drop_dessert, "breakfast": drop_breakfast,
                    "quick_not_comfort_name": quick_name_rejected},
        "meal_class": "dinner only — desserts and breakfasts excluded unless the title says breakfast for dinner",
        "split_basis": "TIMES ONLY — the mirror's `steps` are image URLs, so no instruction "
                       "text exists and none is invented",
    }, "cuisine_counts": dict(cuisines.most_common()), "pool": pool,
        "quick_pool": quick}, indent=1), encoding="utf-8")

    print(json.dumps({
        "rows_total": rows_total, "rows_with_day1_times": rows_time_ok,
        "element_pool": len(pool), "quick_pool": len(quick),
        "dropped": {"no_ingredients": drop_no_ing, "ingredient_count": drop_len,
                    "no_cuisine_tag": drop_no_cuisine,
                    "dessert": drop_dessert, "breakfast": drop_breakfast,
                    "quick_not_comfort_name": quick_name_rejected},
        "top_cuisines": cuisines.most_common(15), "wrote": str(OUT),
    }, indent=1))


if __name__ == "__main__":
    main()
