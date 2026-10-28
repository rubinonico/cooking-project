"""Food.com corpus (490,457 recipes) — quantities, prep/cook times, tags.

    python -m larder.foodcom            # self-check + coverage report

Source: `Karo8870/food.com-parsed-dataset` on HuggingFace (parsed_recipes.csv, 652 MB,
490,457 rows). Derived from Food.com / GeniusKitchen. License on the mirror: unstated —
flag before redistribution.

WHY THIS CORPUS
---------------
It closes the two gaps the What's Cooking / Yummly corpus could not:
  * `ingredients` is STRUCTURED — {quantity, unit, name, description} — so a shopping list
    can carry amounts. Yummly had bare names.
  * `preparation_time` and `cooking_time` are **100% populated**, which is Barrie's
    day-1 / serving-day split as measured data rather than an inference.

WHAT IS WRONG WITH IT — reported, not hidden
--------------------------------------------
  * **`steps` is polluted with image URLs, not instructions.** Sampled rows show the field
    holding `https://img.sndimg.com/...` lists. So instructions CANNOT be taken from this
    mirror, and the day-1 split must come from the TIMES. An earlier coverage count read
    "32% have steps" — those 32% are largely image lists, so the true instruction coverage
    here is ~0.
  * Only ~10% of rows carry a cuisine-like tag, so the cuisine axis is thinner than Yummly's
    clean 20-label field. Tags are kept for volume (12,391 Mexican vs Yummly's 6,438).
  * `servings` is 65% populated.
"""
from __future__ import annotations

import ast
import collections
import csv
import json
import statistics
from pathlib import Path

from larder.corpus import canon

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data/external/foodcom_recipes.csv"
csv.field_size_limit(10 ** 9)

#: Minutes. Barrie's split read off real recipes: a long prep with a short cook IS
#: "do the work on day 1, finish on serving day".
DAY1_PREP_MIN = 240      # >= 4 h of preparation
SERVING_COOK_MAX = 45    # finishable in a normal evening

CUISINE_TAGS = ("italian", "indian", "thai", "mexican", "chinese", "french", "japanese", "greek",
                "korean", "vietnamese", "moroccan", "spanish", "british", "irish", "russian",
                "brazilian", "jamaican", "filipino", "cajun", "creole", "american", "southern",
                "german", "caribbean", "african", "mediterranean", "turkish", "lebanese",
                "portuguese", "polish", "hungarian", "swedish", "norwegian", "danish", "dutch",
                "austrian", "swiss", "israeli", "egyptian", "ethiopian", "peruvian", "cuban",
                "argentinian", "colombian", "chilean", "indonesian", "malaysian", "pakistani",
                "bangladeshi", "sri lankan", "nepali", "burmese", "taiwanese")


def _parse_ingredients(raw: str) -> list[dict]:
    """The column is a Python-repr list of dicts, not JSON — hence ast, not json."""
    try:
        v = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    out = []
    for d in v if isinstance(v, list) else []:
        if isinstance(d, dict) and d.get("name"):
            out.append({"quantity": d.get("quantity"), "unit": d.get("unit"),
                        "name": d["name"], "description": d.get("description")})
    return out


def _num(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def prep_split(prep_min: float | None, cook_min: float | None) -> str:
    """Barrie's split, derived from the times. `unknown` is a real answer."""
    if prep_min is None or cook_min is None:
        return "unknown"
    if prep_min >= DAY1_PREP_MIN and cook_min <= SERVING_COOK_MAX:
        return "day1_prep_serving_finish"      # the pattern the whole project is cloning
    if prep_min >= DAY1_PREP_MIN:
        return "day1_prep_long_cook"
    if prep_min >= 60:
        return "partial_day1"
    return "same_day"


class FoodCom:
    def __init__(self, path: Path | None = None, limit: int | None = None):
        self.recipes: list[dict] = []
        self.by_ingredient: dict[str, list[int]] = collections.defaultdict(list)
        self.ingredient_count: collections.Counter = collections.Counter()
        self.cuisine_count: collections.Counter = collections.Counter()
        with open(path or CSV_PATH, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                ings = _parse_ingredients(row.get("ingredients") or "")
                if not ings:
                    continue
                names = sorted({canon(i["name"])[0] for i in ings if canon(i["name"])[0]})
                if not names:
                    continue
                tags = [t.strip().lower() for t in ast.literal_eval(row["tags"])] if \
                    (row.get("tags") or "").startswith("[") else []
                cuis = sorted({c for c in CUISINE_TAGS if c in tags})
                pm, cm = _num(row.get("preparation_time")), _num(row.get("cooking_time"))
                self.recipes.append({
                    "name": row.get("name", "").strip(),
                    "cuisines": cuis,
                    "tags": tags,
                    "ingredients": names,
                    "iset": frozenset(names),
                    "items": ings,                       # keeps quantity/unit/description
                    "prep_min": pm, "cook_min": cm,
                    "servings": _num(row.get("servings")),
                    "split": prep_split(pm, cm),
                })
                for n in names:
                    self.ingredient_count[n] += 1
                for c in cuis:
                    self.cuisine_count[c] += 1
                if limit and len(self.recipes) >= limit:
                    break
        for idx, r in enumerate(self.recipes):
            for n in r["ingredients"]:
                self.by_ingredient[n].append(idx)

    def __len__(self):
        return len(self.recipes)

    def coverage(self) -> dict:
        n = len(self.recipes) or 1
        both = [r for r in self.recipes if r["prep_min"] is not None and r["cook_min"] is not None]
        # NOTE: `r["prep_min"] and r["cook_min"]` was WRONG here — a legitimate 0 (no prep
        # needed) is falsy, so it read as missing and collapsed the coverage figure.
        prep_pos = [r["prep_min"] for r in self.recipes if (r["prep_min"] or 0) > 0]
        cook_pos = [r["cook_min"] for r in self.recipes if (r["cook_min"] or 0) > 0]
        return {
            "recipes": len(self.recipes),
            "with_cuisine_tag": sum(1 for r in self.recipes if r["cuisines"]),
            "prep_and_cook_not_null": len(both),
            "prep_positive": len(prep_pos),
            "cook_positive": len(cook_pos),
            "split_day1_prep_serving_finish": sum(1 for r in self.recipes
                                                  if r["split"] == "day1_prep_serving_finish"),
            "prep_median_min": statistics.median(prep_pos or [0]),
            "cook_median_min": statistics.median(cook_pos or [0]),
            "distinct_ingredients": len(self.ingredient_count),
        }


def _self_check() -> None:
    fc = FoodCom(limit=4000)
    c = fc.coverage()
    assert c["recipes"] == 4000, c
    assert c["prep_and_cook_not_null"] > 3000, f"prep/cook null coverage collapsed: {c}"
    assert c["prep_positive"] > 500, f"almost no positive prep times: {c}"
    # the split must be reachable at all, or the whole premise is untested
    assert any(r["split"] == "day1_prep_serving_finish" for r in fc.recipes), \
        "no recipe classified as day1_prep_serving_finish in the first 4000"
    print(f"foodcom self-check PASS — {c}")


if __name__ == "__main__":
    _self_check()
    fc = FoodCom()
    print(json.dumps(fc.coverage(), indent=1))
    print("\ntop cuisine tags:", fc.cuisine_count.most_common(12))
    ex = [r for r in fc.recipes if r["split"] == "day1_prep_serving_finish"][:8]
    print("\nday-1-prep / serving-day-finish examples:")
    for r in ex:
        print(f"  prep {r['prep_min']:>7.0f}m cook {r['cook_min']:>5.0f}m  {r['name'][:44]:46} "
              f"{'/'.join(r['cuisines']) or '-'}")
