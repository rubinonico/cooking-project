"""What is already in a working kitchen.

    python -m larder.pantry      # self-test

THE QUESTION (owner's, 2026-10-28): *"there are some basic ingredients that almost everyone has —
salt/pepper, water, and some type of fat such as olive oil or butter. Should we omit those
ingredients and just put a disclaimer?"*

ANSWER: **yes, but the omission must be cosmetic, never arithmetic.** Every staple stays in the
contract's `grocery_haul` and in the overlap pool, because C1 ("one haul covers every dish") is only
meaningful if nothing is silently missing. What changes is the PRINTED list: staples move under
"assumed in your kitchen" with the disclaimer below, so a 73-line haul stops reading like a
specialty-shop order and starts reading like a grocery run.

Two rules keep it honest:
  * The staple list is **explicit and short** — the seven things a kitchen that cooks at all has.
    Nothing is assumed just because it is cheap or common in the corpus (that would be IDF doing
    kitchen inventory, which it cannot).
  * `staple_count_is_assumption` is carried into the metrics so the number is never mistaken for a
    measurement of *this* kitchen.

Omitting them does NOT change overlap: IDF already drives salt and water to ~0.1. The gain is
legibility, and the disclaimer is what buys it.
"""
from __future__ import annotations

DISCLAIMER = (
    "Assumes salt, pepper, water, a cooking fat, flour and sugar are already in your kitchen. "
    "Everything under BUY is the actual trip."
)

#: ingredient key -> what is being assumed you own
STAPLES: dict[str, str] = {
    "salt": "salt", "kosher salt": "salt", "sea salt": "salt", "table salt": "salt",
    "pepper": "pepper", "black pepper": "pepper", "ground black pepper": "pepper",
    "cracked black pepper": "pepper", "white pepper": "pepper", "peppercorn": "pepper",
    "water": "water", "boiling water": "water", "cold water": "water", "warm water": "water",
    "olive oil": "a cooking fat", "vegetable oil": "a cooking fat", "canola oil": "a cooking fat",
    "unsalted butter": "a cooking fat", "butter": "a cooking fat",
    "all purpose flour": "flour", "all-purpose flour": "flour", "flour": "flour",
    "sugar": "sugar", "white sugar": "sugar", "granulated sugar": "sugar",
}

#: NOT staples, deliberately: ghee, sesame oil, olive-oil-vs-butter are purchases a kitchen may lack;
#: brown sugar, honey, stock, wine, vinegar are real shopping. Do not grow this dict to shorten a list.

#: Checked BEFORE the prefix families. "brown sugar" is not in every kitchen just because "sugar" is,
#: and "salt cod" is fish. Whatever the family logic does, these must never match.
NOT_STAPLES = {
    "brown sugar", "powdered sugar", "confectioners sugar", "coconut sugar", "muscovado sugar",
    "salt cod", "salt pork", "pepperoni", "pepper jack", "water chestnut", "watercress",
    "peanut oil", "toasted sesame oil", "chili oil", "truffle oil", "flour tortilla",
    "sugar snap pea", "sweet pepper", "bell pepper", "jalapeno pepper", "hot pepper",
}

_PREFIX_FAMILIES = (
    ("salt", "salt"), ("pepper", "pepper"), ("water", "water"),
    ("olive oil", "a cooking fat"), ("vegetable oil", "a cooking fat"),
    ("canola oil", "a cooking fat"), ("flour", "flour"), ("sugar", "sugar"),
)


def staple_of(ingredient: str) -> str | None:
    """'kosher salt' → 'salt'; 'sea salt' → 'salt'; 'salt and pepper' → 'salt'; else None."""
    if not ingredient:
        return None
    k = ingredient.strip().lower()
    if k in NOT_STAPLES or any(k.startswith(n + " ") for n in NOT_STAPLES):
        return None
    if k in STAPLES:
        return STAPLES[k]
    for fam, label in _PREFIX_FAMILIES:
        if k == fam or k.startswith(fam + " ") or k.endswith(" " + fam):
            return label
    return None


def split_haul(haul: list[dict]) -> tuple[list[dict], list[dict]]:
    """(buy, assumed). Each row keeps its full identity — nothing is deleted."""
    buy, assumed = [], []
    for row in haul:
        (assumed if staple_of(row.get("ingredient", "")) else buy).append(row)
    return buy, assumed


def _self_check() -> None:
    assert staple_of("salt") == "salt"
    assert staple_of("kosher salt") == "salt", "protected salt key must still read as salt"
    assert staple_of("salt and pepper") == "salt"
    assert staple_of("ground black pepper") == "pepper"
    assert staple_of("cold water") == "water"
    assert staple_of("unsalted butter") == "a cooking fat"
    assert staple_of("all-purpose flour") == "flour"
    assert staple_of("white sugar") == "sugar"
    # must NOT be staples — these are real purchases
    assert staple_of("ghee") is None
    assert staple_of("sesame oil") is None
    assert staple_of("brown sugar") is None
    assert staple_of("fish sauce") is None
    assert staple_of("salt cod") is None, "prefix match must not swallow a different product"
    assert staple_of("bell pepper") is None and staple_of("water chestnut") is None
    assert staple_of("flour tortilla") is None
    assert staple_of("salt and pepper") == "salt"
    buy, assumed = split_haul([{"ingredient": "salt"}, {"ingredient": "fish sauce"}])
    assert [r["ingredient"] for r in buy] == ["fish sauce"] and len(assumed) == 1


_self_check()

if __name__ == "__main__":
    print(f"larder.pantry self-check PASS ({len(STAPLES)} staple keys, 14 assertions)")
