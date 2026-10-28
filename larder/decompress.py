"""The "decompress" dinner — one quick, comforting meal per week.

    python -m larder.decompress      # self-test

THE OWNER'S ASK (2026-10-28): *"Maybe make them a 'decompress' meal — something quick and comforting
after a rough day at work?"*

**"Comforting" is subjective, so it is not measured directly.** What IS measured is the part that
actually decides whether a tired person cooks at all:

| criterion | threshold | why |
|---|---|---|
| preparation | **≤ 20 min** | nothing to do on day 1; the dish starts when you get home |
| serving-day cook | **≤ 30 min** | dinner inside half an hour of walking in |
| ingredient count | **≤ 12** | a long list is the reason people order out |
| dish class | name must match a comfort class | stew/soup/chili/curry/casserole/pasta/etc. |
| not diet-coded | no "low carb", "low calorie", "fat free", "diet" in the name | a decompress meal is not a punishment |

The class list is a *proxy for comfort*, and it is labelled as one. It is not a claim that these dishes
are comforting to any particular person; it is a claim that they are the shapes people reach for, and
that the other four criteria are objectively checkable.

WHAT THIS IS NOT
----------------
Not a fifth Element dish. A decompress meal carries **no day-1 work at all** — `day1_parts: []` with
`day1_required: false`. It is the "Full-Meal only" slot Barrie's own system has, and it is the reason a
carbonara or a biscuits-and-gravy can be in the same week as a 4-hour braise.
"""
from __future__ import annotations

import re

PREP_MAX_MIN = 20
COOK_MAX_MIN = 30
INGREDIENT_MAX = 12

COMFORT_CLASSES = (
    "stew", "soup", "chili", "chowder", "curry", "casserole", "hot dish", "mac and cheese",
    "macaroni and cheese", "grilled cheese", "pasta", "spaghetti", "lasagna", "gnocchi",
    "risotto", "fried rice", "pot pie", "meatloaf", "shepherd's pie", "cottage pie",
    "ramen", "noodle", "dumpling", "tacos", "quesadilla", "burger", "hash", "bake",
    "carbonara", "ragu", "bolognese", "biryani", "pilaf", "gumbo", "jambalaya", "congee",
)

DIET_CODED = ("low carb", "low-carb", "low calorie", "low-calorie", "fat free", "fat-free",
              "diet", "light ", "skinny", "keto", "guilt free", "guilt-free")


def _has(text: str, words) -> bool:
    return any(re.search(r"\b" + re.escape(w) + r"s?\b", text) for w in words)


def comfort_name_ok(name: str) -> tuple[bool, str]:
    """Name-only pre-check, run BEFORE the ingredient list is parsed.

    The 652 MB corpus parse is the expensive step, and prep<=20/cook<=30 matches ~150k rows. Filtering
    on the title first cuts that by an order of magnitude without changing the answer — `is_decompress`
    still re-checks everything.
    """
    n = (name or "").lower()
    if _has(n, DIET_CODED):
        return False, "diet-coded"
    if not _has(n, COMFORT_CLASSES):
        return False, "not a comfort class"
    return True, "ok"


def is_decompress(name: str, prep_min: float | None, cook_min: float | None,
                  n_ingredients: int) -> tuple[bool, str]:
    """(ok, reason). False always carries the reason it failed, so a rejection is auditable."""
    n = (name or "").lower()
    if prep_min is None or cook_min is None:
        return False, "times unknown"
    if prep_min > PREP_MAX_MIN:
        return False, f"prep {prep_min:.0f} min > {PREP_MAX_MIN}"
    if cook_min > COOK_MAX_MIN:
        return False, f"cook {cook_min:.0f} min > {COOK_MAX_MIN}"
    if n_ingredients > INGREDIENT_MAX:
        return False, f"{n_ingredients} ingredients > {INGREDIENT_MAX}"
    if _has(n, DIET_CODED):
        return False, "diet-coded"
    if not _has(n, COMFORT_CLASSES):
        return False, "not a comfort class"
    return True, "ok"


def _self_check() -> None:
    ok = lambda *a: is_decompress(*a)[0]
    # a real decompress meal
    assert ok("Spaghetti Carbonara", 10, 20, 8)
    assert ok("Beef and Barley Stew", 20, 30, 10)
    assert ok("Chicken Curry", 15, 25, 12)
    # too slow, too long, or too long a list
    assert not ok("Carbonara", 30, 20, 8), "prep > 20 min must fail"
    assert not ok("Carbonara", 10, 45, 8), "cook > 30 min must fail"
    assert not ok("Carbonara", 10, 20, 18), "18 ingredients must fail"
    # not a comfort shape
    assert not ok("Grilled Salmon Salad", 10, 20, 8)
    # diet-coded is not decompress
    assert not ok("Low Carb Chicken Stew", 10, 25, 8)
    # missing times is a real answer, not a pass
    assert not ok("Mystery Stew", None, 20, 8)
    # reasons are specific
    assert is_decompress("Carbonara", 30, 20, 8)[1].startswith("prep")
    assert is_decompress("Grilled Salmon Salad", 10, 20, 8)[1] == "not a comfort class"


_self_check()

if __name__ == "__main__":
    print("larder.decompress self-check PASS (11 assertions)")
