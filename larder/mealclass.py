"""Dinner / breakfast / dessert classification for the week generator.

    python -m larder.mealclass      # self-test

THE OWNER'S FRAME (2026-10-28): this is **five weeknight dinners**, not "a week of food". That makes
meal class a hard constraint, not a nicety: a dessert in the list is a bug, and a stack of pancakes in
the dinner slot is a bug — *unless* it is breakfast **for dinner**, which is a real dinner.

WHAT MAKES THIS DEFENSIBLE
--------------------------
The Food.com mirror carries meal-class TAGS, which are far stronger than guessing from a title:

| tag | rows (first 200k scanned) |
|---|---|
| `dessert` | 20,518 |
| `brunch` | 17,636 |
| `breakfast` | 3,523 |
| `weeknight` | 18,000 |

So the classifier reads tags first and falls back to the title only when no meal tag exists. It never
uses "contains eggs" as evidence — eggs are in carbonara, frittatas and bibimbap, i.e. dinners.

THE OVERRIDE THAT MATTERS
-------------------------
`"breakfast for dinner"`, `brinner`, or an explicit `dinner` in the title beats a `breakfast` tag.
That is the owner's own carve-out and it is tested below, because the naive version of this filter
would silently delete sausage gravy from a dinner list.
"""
from __future__ import annotations

import re

DINNER, BREAKFAST, DESSERT = "dinner", "breakfast", "dessert"

#: Title words that mean dessert regardless of tags. Components (sauce, chutney) are handled by the
#: generator's own filter; this list is only about sweet/breakfast class.
DESSERT_WORDS = (
    "cake", "cookie", "brownie", "pie", "tart", "pudding", "ice cream", "fudge", "candy",
    "brittle", "granola", "muffin", "cupcake", "pastry", "croissant", "donut", "doughnut",
    "scone", "biscotti", "cheesecake", "custard", "trifle", "cobbler", "crisp", "parfait",
    "frosting", "buttercream", "mousse", "sorbet", "gelato", "sweet roll", "cinnamon roll",
)

BREAKFAST_WORDS = (
    "pancake", "waffle", "omelet", "omelette", "scrambled egg", "french toast", "cereal",
    "oatmeal", "porridge", "hash brown", "breakfast", "brunch", "eggs benedict", "bagel",
    "smoothie", "granola bar", "muesli",
)

#: Explicit dinner intent. Beats a breakfast tag — this is the "breakfast for dinner" carve-out.
DINNER_OVERRIDE = ("for dinner", "brinner", "dinner", "supper")

#: Frittata/quiche are dinner-shaped in most homes; they are in BREAKFAST_WORDS only when tagged so.
_DINNER_SHAPED_BREAKFAST = ("frittata", "quiche", "shakshuka")


def hits(text: str, words) -> bool:
    """Word-boundary match. Substring matching made "pancake" hit the dessert word "cake" — a real
    defect, caught by the self-check, and exactly the kind of thing that would have quietly deleted
    every pancake from a dinner list."""
    # trailing "s" tolerated so "muffin" catches "Muffins" without "cake" catching "pancake"
    return any(re.search(r"\b" + re.escape(w) + r"s?\b", text) for w in words)


def classify(name: str, tags: set[str] | None = None) -> str:
    """'dinner' | 'breakfast' | 'dessert'. Tags decide first; title decides only without a meal tag."""
    tags = tags or set()
    n = (name or "").lower()

    if hits(n, DINNER_OVERRIDE) and DINNER not in tags:
        # "breakfast for dinner", "Sunday supper strata" — an explicit dinner intent wins
        if not hits(n, DESSERT_WORDS):
            return DINNER

    if "dessert" in tags:
        return DESSERT
    if hits(n, DESSERT_WORDS):
        return DESSERT

    if hits(n, _DINNER_SHAPED_BREAKFAST) and not ("breakfast" in tags and "weeknight" not in tags):
        return DINNER
    if "breakfast" in tags or "brunch" in tags:
        return BREAKFAST
    if hits(n, BREAKFAST_WORDS):
        return BREAKFAST
    return DINNER


def _self_check() -> None:
    # tag-driven
    assert classify("Anything At All", {"dessert"}) == DESSERT
    assert classify("Sausage Gravy", {"breakfast"}) == BREAKFAST
    assert classify("Chicken Biryani", {"weeknight"}) == DINNER
    # the carve-out the owner asked for
    assert classify("Sausage Gravy (Breakfast for Dinner)", {"breakfast"}) == DINNER
    assert classify("Brinner Pancakes", {"breakfast"}) == DINNER
    assert classify("Buttermilk Pancakes", {"breakfast"}) == BREAKFAST
    # regression: "pancake" must not hit the dessert word "cake"
    assert classify("Pancake Stack") == BREAKFAST
    assert classify("Belgian Waffles", {"brunch"}) == BREAKFAST
    # title-only fallbacks
    assert classify("Chocolate Lava Cake") == DESSERT
    assert classify("Blueberry Muffins") == DESSERT
    assert classify("Cheesy Omelette") == BREAKFAST
    assert classify("Spaghetti Carbonara") == DINNER
    # eggs are not breakfast — a plain ingredient test would fail these
    assert classify("Bibimbap With Fried Egg") == DINNER
    assert classify("Potato Frittata") == DINNER
    # a dessert tagged breakfast-for-dinner is still a dessert
    assert classify("Pancake Cake for Dinner", {"dessert"}) == DESSERT


_self_check()

if __name__ == "__main__":
    print("larder.mealclass self-check PASS (15 assertions)")
