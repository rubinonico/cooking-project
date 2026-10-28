"""Shared loader + normaliser for the What's Cooking (Yummly) corpus.

One implementation, imported by every tool that reads the corpus, so a fix to the
normaliser cannot drift between them.

Two rules encoded here, both learned the hard way:
  * Exact-match rules must precede pattern rules — `singular("cloves")` hit a generic
    `ves -> f` rule first and produced `garlic clof`, splitting garlic across two keys.
  * PRESERVATION words (dried/powdered/canned/...) are NOT stripped. The form is the
    answer to "can I stock this", so they are returned as tags beside the canonical name.
"""
from __future__ import annotations

import collections
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/external/whats-cooking-train.json"

PREP = (r"\b(large|small|medium|extra|fresh|chopped|minced|diced|sliced|grated|crushed|whole|finely|"
        r"thinly|roughly|halved|quartered|peeled|seeded|ground|boneless|skinless|to taste|plus|more|"
        r"about|into|cut|or|stick|head|clove|stalk|can|package|bunch)\b")

FORMS = ("dried", "powdered", "dehydrated", "canned", "frozen", "smoked", "cured", "pickled",
         "fermented", "bottled", "jarred", "toasted", "roasted", "condensed", "evaporated")

#: Forms that genuinely store on a shelf. `frozen` is excluded on purpose — it is a
#: preserved form but it is not shelf-stable, and conflating the two is the whole trap.
SHELF_STABLE_FORMS = ("dried", "powdered", "dehydrated", "canned", "smoked", "cured",
                      "pickled", "fermented", "bottled", "jarred", "condensed", "evaporated")

#: Corpus-internal name collisions. This corpus writes the same ingredient several ways
#: (`lemongrass` / `lemon grass`, `cilantro` / `cilantro sprig` / `cilantro stem`,
#: `chily` for chilli, `yoghurt` for yogurt, `garlic` / `garlic paste`, `salt` / `sea salt`).
#: Left unmerged, one ingredient is counted as two and the single-use metric inflates —
#: measured at 38 single-use items where the true figure was far lower.
#: Kept explicit rather than a suffix-stripping rule: stripping a trailing word is unsafe
#: (`bay leaf` -> `bay` destroys the ingredient; `coriander seed` vs `coriander` are genuinely
#: different purchases; `garlic powder` vs `garlic` is a FORM, which this project must preserve).
MERGE = {
    "garlic clove": "garlic", "black pepper": "pepper", "scallion": "green onion",
    "cilantro leaf": "cilantro", "lime juice": "lime", "lemon juice": "lemon",
    "tumeric": "turmeric", "cinnamon stick": "cinnamon", "dried oregano": "oregano",
    "dried thyme": "thyme", "dried parsley": "parsley", "flat leaf parsley": "parsley",
    "purple onion": "red onion", "bell pepper": "red bell pepper",
    # --- observed collisions in this corpus ---
    "lemon grass": "lemongrass", "sea salt": "salt", "kosher salt": "salt",
    "peppercorn": "pepper", "black peppercorn": "pepper", "white pepper": "pepper",
    "basmati rice": "rice", "jasmine rice": "rice", "white rice": "rice", "brown rice": "rice",
    "chicken breast": "chicken", "chicken thigh": "chicken", "chicken piece": "chicken",
    "yoghurt": "yogurt", "greek yogurt": "yogurt", "plain yogurt": "yogurt",
    "chily": "chili", "green chily": "green chili", "red chily": "red chili",
    "chili pepper": "chili", "chile": "chili", "chilli": "chili",
    "garlic paste": "garlic", "ginger paste": "ginger", "minced garlic": "garlic",
    "green cardamom": "cardamom", "black cardamom": "cardamom",
    "red chili powder": "chili powder", "coriander powder": "coriander",
    "unsweetened coconut milk": "coconut milk", "coconut milk powder": "coconut milk",
    "cilantro sprig": "cilantro", "cilantro stem": "cilantro", "mint leaf": "mint",
    "kaffir lime leaf": "kaffir lime", "lime wedge": "lime", "lemon wedge": "lemon",
    "mixed green": "mixed greens", "spring onion": "green onion",
    "capsicum": "red bell pepper", "aubergine": "eggplant", "courgette": "zucchini",
    "prawn": "shrimp", "prawns": "shrimp", "garbanzo bean": "chickpea",
    "chilly": "chili", "chillies": "chili",
    "green curry paste": "thai green curry paste", "red curry paste": "thai red curry paste",
    "green pea": "pea", "frozen pea": "pea", "sweet pea": "pea", "frozen peas": "pea",
    "parmigiano reggiano cheese": "parmesan", "parmigiano reggiano": "parmesan",
    "parmesan cheese": "parmesan", "pecorino romano cheese": "pecorino",
    "pecan half": "pecan", "pecan piece": "pecan",
    "plum tomato": "tomato", "grape tomato": "tomato", "cherry tomato": "tomato",
    "roma tomato": "tomato", "tomatoe": "tomato",
    "rock salt": "salt", "table salt": "salt", "iodized salt": "salt",
    "yellow onion": "onion", "spanish onion": "onion", "white onion": "onion",
    "brown onion": "onion", "sweet onion": "onion", "yellow onion": "onion",
    "light soy sauce": "soy sauce", "dark soy sauce": "soy sauce",
    "basil leaf": "basil", "oregano leaf": "oregano", "mint sprig": "mint",
    "pinenut": "pine nut", "pine nuts": "pine nut",
    "red chili pepper": "red chili", "green chili pepper": "green chili",
    "dark chicken stock": "chicken stock", "thai fish sauce": "fish sauce",
    "chicken bouillon": "chicken stock", "chicken bouillon cube": "chicken stock",
    "extra virgin olive oil": "virgin olive oil", "golden raisin": "raisin",
    "garlic clove": "garlic", "coconut extract": "coconut milk",
    "coarse salt": "salt", "coarse sea salt": "salt", "tomato puree": "tomato paste",
    "jalapeno pepper": "jalapeno", "chipotle pepper": "chipotle",
}

#: Tokens that are not ingredients at all — parsing debris from the source corpus. Dropped
#: explicitly and reported, rather than passed through as if they were purchasable items.
#: (`hand` and `essence` both appeared in a generated week's shopping list before this fence.)
NON_INGREDIENT = {"hand", "essence", "such", "as needed", "taste", "desired", "your choice"}


# ---------------------------------------------------------------------------------------------
# SELF-TEST — runs on import of the module, so a normaliser regression cannot reach a number.
# Written after THREE separate instances of this component silently splitting one ingredient
# into two (and so inflating single-use counts): `cloves`->`clof`, `couscous`->`couscou`, and
# `chily`/`chilly` surviving as distinct from `chili`.
# ---------------------------------------------------------------------------------------------
_KNOWN_GOOD = {
    "couscous": "couscous", "asparagus": "asparagus", "hummus": "hummus",     # must NOT be singularised
    "garlic cloves": "garlic", "cilantro sprig": "cilantro",
    "green chily": "green chili", "chilly": "chili", "lemon grass": "lemongrass",
    "unsweetened coconut milk": "coconut milk", "sea salt": "salt",
    "basmati rice": "rice", "chicken breast": "chicken", "yoghurt": "yogurt",
    "tomatoes": "tomato", "leaves": "leaf", "berries": "berry", "bay leaf": "bay leaf",
    "garlic powder": "garlic powder",                 # FORM must be preserved, not merged
    "coriander seed": "coriander seed",               # distinct purchase, not merged to coriander
    "dried oregano": "oregano",
    "tomato purée": "tomato paste",                   # accents must fold before punctuation strips
    "jalapeño": "jalapeno",
}


def self_test() -> None:
    bad = {raw: (canon(raw)[0], want) for raw, want in _KNOWN_GOOD.items() if canon(raw)[0] != want}
    if bad:
        raise AssertionError(f"normaliser self-test FAILED — {len(bad)} of {len(_KNOWN_GOOD)}: {bad}")



def singular(w: str) -> str:
    if w in ("cloves", "clove"):            # exact match FIRST, before the pattern rules
        return "clove"
    if w.endswith("oes"):
        return w[:-2]                       # tomatoes -> tomato
    if w.endswith("ves"):
        return w[:-3] + "f"                 # leaves -> leaf
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    # Guard: these already look plural but are not — `couscous` -> `couscou` was a real
    # defect that split one ingredient into two and inflated the single-use count.
    if w.endswith(("us", "is", "ous", "ss")):
        return w
    if w.endswith("s") and len(w) > 3:
        return w[:-1]
    return w


def canon(raw: str) -> tuple[str, tuple[str, ...]]:
    """Return (canonical_name, attested_preservation_forms)."""
    t = raw.lower()
    t = unicodedata.normalize("NFKD", t)                      # purée -> puree, jalapeño -> jalapeno
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    forms = tuple(w for w in FORMS if re.search(rf"\b{w}\b", t))
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(PREP, " ", t)
    t = re.sub(r"\b\d+([./]\d+)?\b", " ", t)
    t = " ".join(singular(w) for w in t.split())
    t = re.sub(r"\s+", " ", t).strip()
    t = MERGE.get(t, t)
    if t in NON_INGREDIENT:
        return "", forms
    return t, forms


#: Coarse grocery-aisle buckets. Only for the shopping list's readability.
#: An unmapped item goes to `other` rather than being forced into a wrong aisle — and the
#: `other` bucket being large is a signal the map needs extending, not that the item is odd.
AISLE = {
    "produce": {"onion", "red onion", "garlic", "ginger", "carrot", "tomato", "potato", "lime", "lemon",
                "cilantro", "parsley", "green onion", "shallot", "cucumber", "red bell pepper",
                "green bell pepper", "yellow bell pepper", "mint", "dill", "basil", "thai basil",
                "beansprout", "lemongrass", "cayenne pepper", "chili", "green chili", "red chili",
                "jalapeno", "mushroom", "broccoli", "cabbage", "spinach", "celery", "eggplant",
                "zucchini", "corn", "peas", "green bean", "avocado", "kafir lime", "kaffir lime",
                "galangal", "black eyed pea", "chickpea", "mixed greens", "lettuce", "scallion",
                "sweet potato", "butternut squash", "kale", "cauliflower", "radish", "beet",
                "coconut", "curry leaf", "pea", "red potato", "snow pea", "leek", "fennel",
                "artichoke", "okra", "collard green", "mustard green", "turnip", "parsnip"},
    "spice": {"salt", "pepper", "cumin", "cumin seed", "coriander", "coriander seed", "turmeric",
              "cinnamon", "paprika", "cayenne pepper", "curry powder", "chili powder", "bay leaf",
              "oregano", "thyme", "saffron", "saffron thread", "nutmeg", "cardamom", "clove",
              "sesame seed", "mustard seed", "fennel seed", "allspice", "sumac", "garam masala",
              "biryani masala", "mace", "shahi jeera", "stone flower", "star anise", "ginger powder",
              "onion powder", "garlic powder", "vanilla extract", "five spice powder", "zaatar",
              "ras el hanout", "asafoetida", "fenugreek seed", "caraway seed", "celery seed",
              "dried oregano", "dried thyme", "dried parsley", "chili flake", "red pepper flake",
              "poppy seed", "dried rosemary", "amchur", "kasuri methi", "juniper berry"},
    "oil_fat": {"oil", "olive oil", "virgin olive oil", "sesame oil", "vegetable oil", "butter",
                "unsalted butter", "ghee", "margarine", "shortening", "lard", "coconut oil",
                "cooking spray", "vegetable oil cooking spray"},
    "sauce_condiment": {"soy sauce", "fish sauce", "oyster sauce", "rice vinegar", "vinegar",
                        "balsamic vinegar", "miso", "ketchup", "mayonnaise", "mustard", "hot sauce",
                        "worcestershire sauce", "tamarind", "curry paste", "thai green curry paste",
                        "thai red curry paste", "harissa", "gochujang", "liquid smoke", "honey",
                        "maple syrup", "molasses", "tomato paste", "tomato sauce", "salsa", "pesto",
                        "peanut butter", "tahini", "shrimp paste", "italian salad dressing",
                        "chicken broth", "vegetable broth", "beef broth", "stock", "coconut milk",
                        "coconut cream", "sriracha", "barbecue sauce", "chutney"},
    "grain_pasta": {"rice", "flour", "all purpose flour", "rice noodle", "noodle", "pasta", "spaghetti",
                    "bread", "breadcrumb", "tortilla", "couscous", "quinoa", "oat", "cornmeal",
                    "rice paper", "vermicelli noodle", "baking soda", "baking powder", "yeast",
                    "sugar", "brown sugar", "cornstarch", "semolina", "barley", "lentil",
                    "black bean", "kidney bean", "pinto bean"},
    "protein": {"chicken", "beef", "ground beef", "pork", "bacon", "sausage", "shrimp", "fish",
                "salmon", "tuna", "egg", "egg yolk", "tofu", "lamb", "turkey", "anchovy", "clam",
                "crab", "pancetta", "ham", "cod", "tilapia", "boiled egg", "prawn",
                "bone in chicken", "italian turkey sausage", "paneer", "duck breast", "chuck",
                "sausage link", "ground turkey", "ground pork", "beef steak"},
    "dairy": {"milk", "cream", "heavy cream", "sour cream", "yogurt", "cheese", "parmesan",
              "mozzarella", "feta cheese", "buttermilk", "cream cheese", "cheddar", "ricotta",
              "cottage cheese", "half and half", "whipped cream"},
}



def aisle_for(ingredient: str) -> str:
    for name, members in AISLE.items():
        if ingredient in members:
            return name
    return "other"


class Corpus:
    """The 39,774-recipe, 20-cuisine What's Cooking corpus, normalised."""

    def __init__(self, path: Path | None = None):
        self.records = json.loads((path or CORPUS).read_text(encoding="utf-8"))
        self.cuisine_size = collections.Counter(r["cuisine"] for r in self.records)
        self.n = len(self.records)
        self.dishes: list[dict] = []
        self.forms: dict[str, set[str]] = collections.defaultdict(set)
        self.dish_tot: collections.Counter = collections.Counter()
        for rec in self.records:
            ings, seen = [], set()
            for raw in rec["ingredients"]:
                c, f = canon(raw)
                if not c or len(c) < 3 or c in seen:
                    continue
                seen.add(c)
                ings.append(c)
                self.dish_tot[c] += 1
                if f:
                    self.forms[c].add(f[0])
            if ings:
                self.dishes.append({"id": rec["id"], "cuisine": rec["cuisine"],
                                    "ingredients": ings, "iset": frozenset(ings)})
        # ingredient -> indices of dishes containing it: makes the search tractable,
        # without it every candidate step is a scan of 39,774 dishes
        self.by_ingredient: dict[str, list[int]] = collections.defaultdict(list)
        for idx, d in enumerate(self.dishes):
            for i in d["ingredients"]:
                self.by_ingredient[i].append(idx)

    def ubiquity(self, ingredient: str) -> float:
        return self.dish_tot[ingredient] / self.n


#: Markers of dessert / convenience-product recipes. The corpus is user-submitted Yummly data and
#: contains desserts, single-sauce recipes and brand-name convenience items, so "is this a dinner"
#: must be filtered explicitly: an early run put a cool-whip / instant-pudding recipe into the
#: dinner list and a 40-ingredient fusion recipe alongside it.
NON_DINNER = {"cool whip", "whipped topping", "instant pudding", "vanilla instant pudding",
              "english toffee bit", "toffee bit", "frosting", "icing", "cake mix", "brownie mix",
              "jello", "marshmallow", "graham cracker", "food coloring", "cream of tartar",
              "cake", "cookie", "pie crust", "chocolate chip", "sprinkle", "candy",
              "caramel ice cream topping", "ice cream", "sherbet", "whipped cream"}


def is_plausible_dinner(ingredients: list[str], max_markers: int = 1) -> bool:
    """True when the dish is not a dessert or a convenience-product assembly."""
    return sum(1 for i in ingredients if i in NON_DINNER) <= max_markers


#: Run the normaliser self-test at import: a regression here silently inflates every
#: single-use count downstream, so it must fail before a number is ever printed.
self_test()
