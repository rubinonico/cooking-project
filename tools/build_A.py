"""A rebuild: the specialty pantry, measured on 39,774 recipes across 20 cuisines.

Input : data/external/whats-cooking-train.json  (What's Cooking / Yummly, 20 cuisines)
Output: data/external/A_pantry_final.json, data/external/A_matrix.json

Two axes are reported together because either alone misleads:
  n_cuisines  = how many cuisines the item is over-represented in  (breadth)
  lift        = how over-represented it is in its peak cuisine    (specificity)
Ranking by breadth alone puts carrot/parsley/milk on top; ranking by specificiy alone
puts single-cuisine oddities on top. A "base" is high on both.
"""
import json, re, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # tools/ -> Larder/
RECS = json.loads((ROOT / "data/external/whats-cooking-train.json").read_text(encoding="utf-8"))

# --- normalisation ------------------------------------------------------------------------
# Size/prep words are stripped; PRESERVATION words are KEPT (the form is the answer, not noise).
PREP = (r"\b(large|small|medium|extra|fresh|chopped|minced|diced|sliced|grated|crushed|whole|finely|"
        r"thinly|roughly|halved|quartered|peeled|seeded|ground|boneless|skinless|to taste|plus|more|"
        r"about|into|cut|or|stick|head|clove|stalk|can)\b")
FORMS = ["dried", "powdered", "dehydrated", "canned", "frozen", "smoked", "cured", "pickled",
         "fermented", "bottled", "jarred", "toasted", "roasted", "condensed", "evaporated"]


def singular(w):
    if w in ("cloves", "clove"):
        return "clove"
    if w.endswith("oes"):
        return w[:-2]                      # tomatoes -> tomato
    if w.endswith("ves"):
        return w[:-3] + "f"                # leaves -> leaf
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


MERGE = {
    "garlic clove": "garlic", "black pepper": "pepper", "scallion": "green onion",
    "cilantro leaf": "cilantro", "lime juice": "lime", "lemon juice": "lemon",
    "tumeric": "turmeric", "cinnamon stick": "cinnamon", "dried oregano": "oregano",
    "dried thyme": "thyme", "dried parsley": "parsley", "flat leaf parsley": "parsley",
    "purple onion": "red onion", "bell pepper": "red bell pepper",
}


def canon(raw):
    t = raw.lower()
    forms = tuple(w for w in FORMS if re.search(rf"\b{w}\b", t))
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(PREP, " ", t)
    t = re.sub(r"\b\d+([./]\d+)?\b", " ", t)
    t = " ".join(singular(w) for w in t.split())
    t = re.sub(r"\s+", " ", t).strip()
    return MERGE.get(t, t), forms


tot = collections.Counter(r["cuisine"] for r in RECS)
N = len(RECS)
cuisines = sorted(tot)

ing_cui = collections.defaultdict(collections.Counter)
ing_tot = collections.Counter()
ing_forms = collections.defaultdict(set)
for r in RECS:
    seen = set()
    for raw in r["ingredients"]:
        c, f = canon(raw)
        if not c or len(c) < 3:
            continue
        if f:
            ing_forms[c].add(f[0])
        if c in seen:
            continue
        seen.add(c)
        ing_cui[c][r["cuisine"]] += 1
        ing_tot[c] += 1

# --- thresholds (all three reported, none buried) ------------------------------------------
MIN_FREQ = 0.08    # must be in >=8% of that cuisine's recipes to count as present
MIN_LIFT = 1.5     # and >=1.5x more common there than across all recipes -> over-represented
MAX_UBIQ = 0.10    # and in <10% of ALL recipes -> a specialty, not a supermarket staple

rows = []
for i, cc in ing_cui.items():
    ub = ing_tot[i] / N
    if ub >= MAX_UBIQ:
        continue
    d = {c for c, n in cc.items() if n / tot[c] >= MIN_FREQ and (n / tot[c]) / ub >= MIN_LIFT}
    if len(d) >= 2:
        rows.append({
            "ingredient": i,
            "n_cuisines": len(d),
            "cuisines": sorted(d),
            "ubiquity": round(ub, 4),
            "lift": round(max((cc[c] / tot[c]) / ub for c in d), 2),
            "forms": sorted(ing_forms.get(i, [])),
        })
rows.sort(key=lambda r: (-r["lift"], -r["n_cuisines"]))

out = {
    "source": "MohammedAlawami/whats-cooking-dataset train.json (What's Cooking / Yummly)",
    "recipes": N, "cuisines": cuisines, "cuisine_sizes": dict(tot),
    "thresholds": {"MIN_FREQ": MIN_FREQ, "MIN_LIFT": MIN_LIFT, "MAX_UBIQ": MAX_UBIQ},
    "items": rows,
}
(ROOT / "data/external/A_pantry_final.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"saved {len(rows)} items -> data/external/A_pantry_final.json")

HIS = {"italian", "indian", "thai", "southern_us"}
print(f"\n=== A BASES by SPECIFICITY (lift), multi-culture specialty items ===")
for r in rows[:20]:
    print(f"  lift {r['lift']:>5.1f}  {r['n_cuisines']:>2} cultures  {r['ingredient']:20} "
          f"{', '.join(r['cuisines'])[:50]}")
print(f"\n=== by BREADTH the top is generic produce, which is why lift ranks instead ===")
for r in sorted(rows, key=lambda r: -r["n_cuisines"])[:5]:
    print(f"  {r['n_cuisines']} cultures, lift {r['lift']:>4.1f}  {r['ingredient']}")
print(f"\n=== YOUR CUISINES (italian/indian/thai/southern_us), by lift ===")
for r in [x for x in rows if set(x["cuisines"]) & HIS][:16]:
    ov = sorted(set(r["cuisines"]) & HIS)
    print(f"  lift {r['lift']:>5.1f}  {r['ingredient']:20} yours={','.join(ov):16} "
          f"all={', '.join(r['cuisines'])[:38]}")
print("\n=== coconut_milk per-cuisine (the user's example) ===")
cc = ing_cui["coconut milk"]
base = sum(cc.values()) / N
for c, n in sorted(cc.items(), key=lambda kv: -kv[1] / tot[kv[0]])[:8]:
    print(f"   {c:14} {n:>4}/{tot[c]:<5} = {n/tot[c]:>6.1%}  lift {(n/tot[c])/base:>5.1f}")
print(f"   indian: {cc.get('indian',0)}/{tot['indian']} = {cc.get('indian',0)/tot['indian']:.1%}")
