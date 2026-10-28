"""Ingredient-name normalisation for the Food.com mirror.

    python -m larder.fcnames      # self-test

WHY THIS EXISTS
---------------
Food.com ingredient names are free text written by home cooks: *"kosher salt or 1 teaspoon table
salt"*, *"vegetable oil to grill the chicken"*, *"boneless skinless chicken breast halves"*,
*"grated peeled gingerroot"*. `larder.corpus.canon` was written for Yummly's tidy single-word
names and leaves all of that intact, so the same purchase appears as 3-4 distinct "ingredients".
Measured on the first real week (out/week-fc-001): **49 single-use ingredients, several of them
duplicates of things already in the haul.** Name normalisation is the largest single source of
wrong numbers in this project (4 prior failures), so every rule below is a test.

WHAT IS DELIBERATELY NOT STRIPPED
---------------------------------
`ground` vs whole seed, `dried` vs fresh, `baby` vs mature, `white` vs `brown` sugar: those are
genuinely different purchases. Stripping them would make the haul look tighter and the list wrong.
Affixes are removed only where the shelf product is identical.
"""
from __future__ import annotations

import re

from larder.corpus import canon

#: Preparation / appearance adjectives that do NOT change what you buy.
STRIP_LEADING = (
    "sliced", "torn", "shredded", "grated", "peeled", "chopped", "diced", "minced", "crushed",
    "packed", "toasted", "boneless", "skinless", "halved", "trimmed", "cleaned", "divided",
    "room temperature", "cold", "large", "small", "medium", "thinly sliced", "finely chopped",
    "roughly chopped", "cooked", "uncooked", "frozen", "thawed",
    "fine", "coarse",          # "fine sea salt" is still sea salt
    "melted", "softened", "sifted", "hard boiled", "hard-boiled", "room-temperature",
)

#: Trailing cut/shape words. A "half" and a whole breast are the same purchase.
STRIP_TRAILING = ("halves", "half", "pieces", "cubes", "chunks", "wedges", "slices")

#: Same shelf product, different wording. Only entries observed in the real pool.
ALIASES = {
    "dark soy sauce": "soy sauce",
    "low sodium soy sauce": "soy sauce",
    "low-sodium soy sauce": "soy sauce",
    "light soy sauce": "soy sauce",
    "dark sesame oil": "sesame oil",
    "toasted sesame oil": "sesame oil",
    "rice wine vinegar": "rice vinegar",
    "unseasoned rice vinegar": "rice vinegar",
    "gingerroot": "ginger",
    "ginger root": "ginger",
    "chicken breast half": "chicken breast",
    "chicken breasts": "chicken breast",
    "scallion": "green onion",
    "scallions": "green onion",
    "cilantro leaves": "cilantro",
    "lime zest": "lime",
    "lemon zest": "lemon",
    "reduced sodium soy sauce": "soy sauce",
    "fresh gingerroot": "ginger",
    "fresh ginger root": "ginger",
    "natural yoghurt": "yogurt",
    "plain yoghurt": "yogurt",
    "whole milk yoghurt": "yogurt",
    "greek yoghurt": "greek yogurt",
}

#: `larder.corpus.canon` was tuned on Yummly's tidy names and over-collapses some purchases:
#: it maps "ground cumin" → "cumin" (same key as the whole seed), "chicken breast" → "chicken"
#: (same key as a whole bird), "kosher salt" → "salt". For a SHOPPING LIST those merges are wrong:
#: they make the haul look tighter than it is, which is a believable wrong number. Keys here
#: bypass canon.
PROTECTED = {
    "chicken breast", "chicken thigh", "chicken wing", "chicken leg",
    "ground cumin", "ground coriander", "ground ginger", "ground turmeric",
    "kosher salt", "sea salt", "table salt",
}

_PAREN = re.compile(r"\([^)]*\)")
#: Food.com's `name` field sometimes carries the amount: "1/2 cup ground cumin". Strip it, but only
#: when a real unit follows, so a name that legitimately starts with a number survives.
_LEADING_QTY = re.compile(
    r"^[\d\s/.,\u00bc\u00bd\u00be-]+\s*"
    r"(?:cups?|c\.|tbsp|tbs|tablespoons?|tsp|teaspoons?|oz|ounces?|lb|lbs|pounds?|"
    r"g|grams?|kg|ml|liters?|litres?|cloves?|cans?|packages?|pkgs?|pinch(?:es)?|dash(?:es)?|"
    r"slices?|pieces?|bunch(?:es)?|heads?|stalks?|sprigs?)\b\.?\s*",
    re.IGNORECASE)
#: Food.com splits quantity/unit into their own columns, but some rows leave the unit inside the NAME:
#: "g dried funghi porcini", "tablespoon soy sauce", "stalk bok choy", "ml vegetable broth". Strip a
#: leading bare unit when a word follows it.
_LEADING_BARE_UNIT = re.compile(
    r"^(?:g|gr|kg|ml|l|oz|lb|lbs|cups?|tbsp|tbs|tablespoons?|tsp|teaspoons?|"
    r"cloves?|cans?|stalks?|sprigs?|bunch(?:es)?|heads?|slices?|pieces?|packages?|pkgs?|pinch(?:es)?|"
    r"dash(?:es)?|jars?|bottles?)\b\.?\s+",
    re.IGNORECASE)
#: "thumb sized piece ginger"
_SIZE_DESCRIPTOR = re.compile(r"^(?:thumb[- ]sized )?(?:piece|knob|chunk)(?: of)?\s+")

#: "X or 2 tablespoons Y" — the cook buys X; the alternative is a substitution, not an ingredient.
_OR = re.compile(r"\s+or\s+.*$")
#: "vegetable oil to grill the chicken" — the purpose clause is not part of the product.
_PURPOSE = re.compile(r"\s+to\s+(?:grill|serve|fry|decorate|garnish|coat|brush|drizzle|grease)\b.*$")
#: ", divided" / ", plus more for serving"
_COMMA_TAIL = re.compile(r",.*$")


def clean(raw: str) -> str:
    """Free-text Food.com ingredient name → a human-readable, noise-free phrase (no canonicalising)."""
    if not raw:
        return ""
    s = str(raw).strip().lower()
    s = _LEADING_QTY.sub("", s)          # "1/2 cup ground cumin" → "ground cumin"
    s = _LEADING_BARE_UNIT.sub("", s)    # "tablespoon soy sauce" → "soy sauce"
    s = _SIZE_DESCRIPTOR.sub("", s)      # "thumb sized piece ginger" → "ginger"
    s = _PAREN.sub(" ", s)
    s = _OR.sub("", s)
    s = _PURPOSE.sub("", s)
    s = _COMMA_TAIL.sub("", s)
    s = re.sub(r"\s+", " ", s).strip(" -,")
    words = s.split()
    changed = True
    while changed and words:
        changed = False
        joined = " ".join(words)
        for a in STRIP_LEADING:
            if joined.startswith(a + " "):
                words = words[len(a.split()):]
                changed = True
                break
    while words and words[-1] in STRIP_TRAILING:
        words.pop()
    s = " ".join(words)
    return ALIASES.get(s, s)


def norm(raw: str) -> str:
    """Free-text Food.com ingredient name → the canonical purchase key."""
    if not raw:
        return ""
    # NOTE 2026-10-28: this function used to carry a duplicate copy of the cleaning pipeline above
    # and then overwrite its own result with `s = clean(raw)`. Every regex in the copy was dead code —
    # which is why unit-prefixed names ("tablespoon soy sauce") survived a "fix" that added them. One
    # pipeline, one place.
    s = clean(raw)
    if not s:
        return ""
    if s in PROTECTED:
        return s
    return canon(s)[0] or s


def _self_check() -> None:
    # every string below was observed in out/week-fc-001.json — no invented cases
    cases = {
        "kosher salt or 1 teaspoon table salt": "kosher salt",   # protected: not table salt
        "vegetable oil or 2 tablespoons olive oil": "vegetable oil",
        "vegetable oil to grill the chicken": "vegetable oil",
        "sliced tomatoes or grape tomatoes": "tomato",
        "torn lettuce": "lettuce",
        "grated peeled gingerroot": "ginger",
        "boneless skinless chicken breast halves": "chicken breast",
        "shredded carrot": "carrot",
        "butter (cold and cut into small pats)": "butter",
        "dark soy sauce": "soy sauce",
        "low sodium soy sauce": "soy sauce",
        "dark sesame oil": "sesame oil",
        "rice wine vinegar": "rice vinegar",
        "packed brown sugar": "brown sugar",
        "toasted sesame seeds": "sesame seed",
        "white wine vinegar or 2 teaspoons unseasoned rice vinegar": "white wine vinegar",
        # must NOT collapse — different purchases
        "ground cumin": "ground cumin",
        "dried basil": "dried basil",
        "baby spinach": "baby spinach",
        "white sugar": "white sugar",
        "1/2 cup ground cumin": "ground cumin",
        "2 tablespoons olive oil": "olive oil",
        "1 pound skirt steak": "skirt steak",
        "fresh gingerroot": "ginger",
        "natural yoghurt": "yogurt",
        "fine sea salt": "sea salt",
        "reduced sodium soy sauce": "soy sauce",

    }
    bad = {k: (norm(k), want) for k, want in cases.items() if norm(k) != want}
    assert not bad, f"fcnames self-check FAILED: {bad}"
    assert norm("") == ""
    # brown vs white sugar must stay distinct
    assert norm("brown sugar") != norm("white sugar")
    # ground vs whole cumin must stay distinct
    assert norm("ground cumin") != norm("cumin seed")


_self_check.cases = {
    "kosher salt or 1 teaspoon table salt": "kosher salt",
    "vegetable oil or 2 tablespoons olive oil": "vegetable oil",
    "vegetable oil to grill the chicken": "vegetable oil",
    "sliced tomatoes or grape tomatoes": "tomato",
    "torn lettuce": "lettuce",
    "grated peeled gingerroot": "ginger",
    "boneless skinless chicken breast halves": "chicken breast",
    "shredded carrot": "carrot",
    "butter (cold and cut into small pats)": "butter",
    "dark soy sauce": "soy sauce",
    "low sodium soy sauce": "soy sauce",
    "dark sesame oil": "sesame oil",
    "rice wine vinegar": "rice vinegar",
    "packed brown sugar": "brown sugar",
    "toasted sesame seeds": "sesame seed",
    "white wine vinegar or 2 teaspoons unseasoned rice vinegar": "white wine vinegar",
    "ground cumin": "ground cumin",
    "dried basil": "dried basil",
    "baby spinach": "baby spinach",
    "white sugar": "white sugar",
    "1/2 cup ground cumin": "ground cumin",
    "2 tablespoons olive oil": "olive oil",
    "1 pound skirt steak": "skirt steak",
    "fresh gingerroot": "ginger",
    "natural yoghurt": "yogurt",
    "fine sea salt": "sea salt",
    "reduced sodium soy sauce": "soy sauce",
}

_self_check()

if __name__ == "__main__":
    print(f"larder.fcnames self-check PASS ({len(_self_check.cases)} cases + 4 invariants)")
