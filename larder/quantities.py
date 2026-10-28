"""Unit-aware ingredient quantity aggregation for the shopping list.

    python -m larder.quantities     # self-test

The shopping list must say WHAT TO BUY, not just what to look for. Food.com ingredient rows are
`{quantity, unit, name, description}`, so 5 dinners routinely call for "2 tablespoons" of the same
spice three times — 6 tbsp is a real answer and 3 separate lines is not.

Rules, all of them chosen to avoid inventing numbers:

1. **Never convert across families.** Volume (tsp/tbsp/cup/ml/l) and weight (oz/lb/g/kg) stay
   separate; a recipe that says "1 cup cilantro" and another that says "50 g cilantro" produces
   two lines, not one fabricated total.
2. **Counts stay counts.** "3 cloves garlic" + "1 head garlic" is two lines. A clove has no
   established weight here, so no arithmetic is done on it.
3. **Unmeasured is a real answer.** Missing or non-numeric quantity ("to taste", None) is tracked
   as `unmeasured: true` and displayed as "as needed" only when NOTHING else was measured.
4. **Display prefers the largest readable unit** — 16 tbsp becomes "1 cup", 60 ml becomes "4 tbsp".

This module self-tests on import (`_self_check`), matching `larder/corpus.py` and `larder/foodcom.py`:
a wrong arithmetic step here silently corrupts every shopping list, and a corrupt total is worse
than no total.
"""
from __future__ import annotations

import collections

# ---------------------------------------------------------------- units ----

ML_PER = {"tsp": 4.92892, "tbsp": 14.7868, "fl oz": 29.5735, "cup": 236.588,
          "pint": 473.176, "quart": 946.353, "gallon": 3785.41, "ml": 1.0, "l": 1000.0}
G_PER = {"oz": 28.3495, "lb": 453.592, "g": 1.0, "kg": 1000.0}

UNIT_ALIASES = {
    "teaspoon": "tsp", "teaspoons": "tsp", "t": "tsp", "tsp.": "tsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbs": "tbsp", "tbsp.": "tbsp", "tbl": "tbsp",
    "cup": "cup", "cups": "cup", "c": "cup",
    "ounce": "oz", "ounces": "oz", "oz.": "oz",
    "pound": "lb", "pounds": "lb", "lbs": "lb", "lb.": "lb",
    "gram": "g", "grams": "g", "gr": "g",
    "kilogram": "kg", "kilograms": "kg",
    "milliliter": "ml", "milliliters": "ml", "millilitre": "ml", "cc": "ml",
    "liter": "l", "liters": "l", "litre": "l",
    "fluid ounce": "fl oz", "fluid ounces": "fl oz", "floz": "fl oz",
    "pint": "pint", "pints": "pint", "quart": "quart", "quarts": "quart",
    "gallon": "gallon", "gallons": "gallon",
    "clove": "clove", "cloves": "clove", "slice": "slice", "slices": "slice",
    "can": "can", "cans": "can", "package": "package", "packages": "package",
    "pkg": "package", "bunch": "bunch", "bunches": "bunch", "head": "head", "heads": "head",
    "stalk": "stalk", "stalks": "stalk", "sprig": "sprig", "sprigs": "sprig",
    "piece": "piece", "pieces": "piece", "pinch": "pinch", "dash": "dash",
    "stick": "stick", "sticks": "stick", "bag": "bag", "bottle": "bottle",
    "jar": "jar", "box": "box", "envelope": "envelope", "sheet": "sheet",
    "": "", None: "",
}


def norm_unit(u) -> str | None:
    """Canonical unit token, '' for unitless counts, None for an unusable unit."""
    if u is None:
        return None
    s = str(u).strip().lower().rstrip(".")
    if s in UNIT_ALIASES:
        return UNIT_ALIASES[s]
    return UNIT_ALIASES.get(s + ".", s)


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 0.02:
        return str(int(round(x)))
    return f"{x:.1f}".rstrip("0").rstrip(".")


# ------------------------------------------------------------ aggregation ----


def aggregate(items: list[dict]) -> dict:
    """`items` = [{'quantity', 'unit', 'name', 'description'}] for ONE canonical ingredient.

    Returns {'display': str, 'exact': [str], 'measured': bool, 'unmeasured': bool,
             'mixed_families': bool, 'lines': n}
    """
    vol_ml = 0.0
    wt_g = 0.0
    counts: collections.Counter = collections.Counter()     # canonical count unit -> qty
    exact: list[str] = []
    unmeasured = 0
    for it in items:
        q = it.get("quantity")
        u = norm_unit(it.get("unit"))
        try:
            q = float(q)
        except (TypeError, ValueError):
            q = None
        if q is None or q <= 0:
            unmeasured += 1
            continue
        if u in ML_PER:
            vol_ml += q * ML_PER[u]
            exact.append(f"{_fmt(q)} {u}")
        elif u in G_PER:
            wt_g += q * G_PER[u]
            exact.append(f"{_fmt(q)} {u}")
        elif u:
            counts[u] += q
            exact.append(f"{_fmt(q)} {u}")
        else:
            counts[""] += q
            exact.append(_fmt(q))

    parts: list[str] = []
    if vol_ml > 0:
        parts.append(_vol_display(vol_ml))
    if wt_g > 0:
        parts.append(_wt_display(wt_g))
    for u, q in sorted(counts.items()):
        parts.append(f"{_fmt(q)} {u}".strip())

    measured = bool(parts)
    if not measured:
        display = "as needed"
    else:
        display = " + ".join(parts)
        if unmeasured:
            display += " (+ as needed)"

    return {
        "display": display,
        "exact": exact,
        "measured": measured,
        "unmeasured": unmeasured > 0,
        "mixed_families": (vol_ml > 0 and wt_g > 0),
        "lines": len(items),
    }


def _vol_display(ml: float) -> str:
    if ml >= ML_PER["cup"] * 0.9:
        return f"{_fmt(ml / ML_PER['cup'])} cup" + ("" if abs(ml / ML_PER["cup"] - 1) < 0.05 else "s")
    if ml >= ML_PER["tbsp"] * 0.9:
        return f"{_fmt(ml / ML_PER['tbsp'])} tbsp"
    return f"{_fmt(ml / ML_PER['tsp'])} tsp"


def _wt_display(g: float) -> str:
    if g >= 453.592 * 0.9:
        lb = g / 453.592
        return f"{_fmt(lb)} lb"
    if g >= 1000:
        return f"{_fmt(g / 1000)} kg"
    return f"{_fmt(g)} g"


def grocery_quantities(dishes: list[dict]) -> dict[str, dict]:
    """Aggregate every dish's structured items. `dishes` = [{'items': [...]}]"""
    by_name: dict[str, list[dict]] = collections.defaultdict(list)
    for d in dishes:
        for it in d.get("items") or []:
            name = it.get("name")
            if not name:
                continue
            by_name[name.strip().lower()].append(it)
    return {n: aggregate(v) for n, v in by_name.items()}


# -------------------------------------------------------------- self-test ----


def _self_check() -> None:
    # unit normalisation
    assert norm_unit("Tablespoons") == "tbsp"
    assert norm_unit("tbsp.") == "tbsp"
    assert norm_unit("lbs") == "lb"
    assert norm_unit(None) is None
    # volume merges within family: 3 tbsp + 1 tbsp = 4 tbsp
    a = aggregate([{"quantity": 3, "unit": "tablespoon", "name": "x"},
                   {"quantity": 1, "unit": "tbsp", "name": "x"}])
    assert a["display"].startswith("4 tbsp"), a
    # 16 tbsp = 1 cup
    a = aggregate([{"quantity": 16, "unit": "tbsp", "name": "x"}])
    assert a["display"].startswith("1 cup"), a
    # volume vs weight never merge — two lines, flagged
    a = aggregate([{"quantity": 1, "unit": "cup", "name": "x"},
                   {"quantity": 50, "unit": "g", "name": "x"}])
    assert a["mixed_families"] is True and "+" in a["display"], a
    # counts stay counts
    a = aggregate([{"quantity": 3, "unit": "clove", "name": "garlic"},
                   {"quantity": 1, "unit": "head", "name": "garlic"}])
    assert "3 clove" in a["display"] and "1 head" in a["display"], a
    # unmeasured tracked, never silently dropped
    a = aggregate([{"quantity": None, "unit": None, "name": "salt"}])
    assert a["display"] == "as needed" and a["unmeasured"] is True, a
    # a legit 0 quantity is unmeasured, not a zero total
    a = aggregate([{"quantity": 0, "unit": "cup", "name": "x"}])
    assert a["measured"] is False, a
    # '+' in the source quantity string is not a number
    a = aggregate([{"quantity": "+", "unit": None, "name": "x"}])
    assert a["display"] == "as needed", a
    # weight display: 2 lb stays lb
    a = aggregate([{"quantity": 2, "unit": "pound", "name": "x"}])
    assert a["display"].startswith("2 lb"), a
    # grocery_quantities groups by lowercased name
    g = grocery_quantities([{"items": [{"quantity": 2, "unit": "tbsp", "name": "Cumin"}]},
                            {"items": [{"quantity": 1, "unit": "tbsp", "name": "cumin"}]}])
    assert list(g) == ["cumin"] and g["cumin"]["display"].startswith("3 tbsp"), g


_self_check()

if __name__ == "__main__":
    print("larder.quantities self-check PASS (11 assertions)")
