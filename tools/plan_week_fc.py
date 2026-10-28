"""plan_week_fc.py — FIVE WEEKNIGHT DINNERS from the Food.com corpus: quantities + the day-1 split.

Scope is dinner. Desserts and breakfasts are removed at pool build by `larder/mealclass.py`, which
reads the mirror's own `dessert` / `breakfast` / `brunch` tags rather than guessing from titles, and
honours one carve-out: "breakfast for dinner" stays.

    python tools/plan_week_fc.py --cuisines indian,mexican,chinese,thai --dishes 5 --min-cuisines 3 \
        --out out/week-fc-001.json --contract

WHAT THIS ADDS OVER tools/plan_week.py
--------------------------------------
`plan_week.py` reads the Yummly corpus (`{cuisine, ingredients[]}`) and cannot answer two things:
no quantities, and no day-1 / serving-day split. This tool reads `data/external/fc_pool.json`
(`tools/build_fc_pool.py`), which is the Food.com mirror filtered to **prep >= 4 h AND cook <= 45 m**
— Barrie's exact pattern — and adds:

  * `grocery_haul[].quantity` — real aggregated amounts (`larder/quantities.py`)
  * `day1_parts` / `serve_day_parts` — **derived from TIMES, not from instructions**

THE HONESTY LINE, stated once and repeated in the output
-------------------------------------------------------
The mirror's `steps` column is image URLs, so there is no instruction text in this corpus. The
split therefore says "this dish has a 4 h prep and a 25 m cook", which is a measured fact, and
NOT "step 3 is the marinade", which would be invented. Every action string says which it is.
`servings` is carried through per dish; the week-level `serves` is an explicit --serves assumption.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from larder.corpus import aisle_for, is_plausible_dinner  # noqa: E402
from larder.fcnames import clean as fc_clean, norm as fc_norm  # noqa: E402
from larder.pantry import DISCLAIMER as STAPLE_DISCLAIMER, staple_of  # noqa: E402
from larder.quantities import aggregate  # noqa: E402

AISLE_ORDER = ["produce", "protein", "dairy", "grain_pasta", "oil_fat", "spice", "sauce_condiment", "other"]

#: Protein families. The objective alone is happy with five chicken dinners — chicken is the cheapest
#: way to share IDF mass, and the first normalised run returned exactly that (5/5 chicken). A cook
#: will not eat five chickens. This is a diversity constraint for the same reason `max_sim` exists.
PROTEINS = ("chicken", "beef", "pork", "shrimp", "fish", "lamb", "turkey", "tofu", "salmon",
            "tuna", "bacon", "sausage", "egg", "chickpea", "lentil", "bean", "paneer")


#: Dish-name words that mean "this is a component, not a dinner". `is_plausible_dinner` reads
#: INGREDIENTS and cannot see that a "Cranberry Chutney" is a condiment — the first run put one in
#: the week. Checked against the recipe NAME, which is where the dish class is actually stated.
NOT_A_DINNER_TITLE = (
    "chutney", "jam", "jelly", "marmalade", "preserve", "pickle", "relish", "dip", "dressing",
    "smoothie", "cocktail", "punch", "juice", "cake", "cookie", "brownie", "pie", "tart",
    "pudding", "ice cream", "fudge", "candy", "brittle", "granola", "muffin", "loaf", "bread",
    "sauce", "gravy", "condiment", "seasoning", "marinade", "syrup", "buttercream", "frosting",
    "pastry", "croissant", "danish", "donut", "doughnut", "cupcake", "scone", "biscotti",
    # 2026-10-28: the decompress pick returned "Chili Powder Spice Mix" — comfort word "chili" matched
    # a spice blend. A component is not a dinner no matter how comforting its name sounds.
    "spice mix", "spice blend", "seasoning blend", "dry rub", "chili powder mix", "soup mix",
)


def is_dinner_name(name: str) -> bool:
    n = (name or "").lower()
    return not any(w in n for w in NOT_A_DINNER_TITLE)


def proteins_of(iset) -> set[str]:
    return {p for p in PROTEINS for ing in iset if ing == p or ing.startswith(p + " ")}
POOL_PATH = ROOT / "data/external/fc_pool.json"
SPLIT_BASIS = ("TIMES ONLY — the Food.com mirror's `steps` are image URLs, so no instruction text "
               "exists in this corpus and none is invented")


def fmt_minutes(m: float) -> str:
    if m < 60:
        return f"{int(round(m))} min"
    h = m / 60
    return f"{h:.1f}".rstrip("0").rstrip(".") + " h"


def load_pool() -> dict:
    if not POOL_PATH.exists():
        raise SystemExit(f"missing {POOL_PATH} — run: python tools/build_fc_pool.py")
    return json.loads(POOL_PATH.read_text(encoding="utf-8"))


class FcCorpus:
    """Adapter so a pool recipe answers the fields the selector needs.

    Two pools live in one file: `pool` (ELEMENT dishes, real day-1 work) and `quick_pool` (DECOMPRESS
    meals, no day-1 work). `kind` is carried on every dish so the renderer never has to guess which
    one it is holding.
    """

    def __init__(self, doc: dict):
        self.meta = doc["meta"]
        self.dishes: list[dict] = []
        records = [(r, "element") for r in doc["pool"]] + [(r, "quick") for r in doc.get("quick_pool") or []]
        for i, (r, kind) in enumerate(records):
            ings = r["ingredients"]
            items_by_ing: dict[str, list[dict]] = collections.defaultdict(list)
            display: dict[str, str] = {}
            for it in r["items"]:
                c = fc_norm(it.get("name") or "")
                if not c:
                    continue
                items_by_ing[c].append(it)
                display.setdefault(c, fc_clean(it.get("name") or "") or c)
            # Ingredients are re-derived from the structured items, NOT taken from the stored list:
            # the stored list was frozen at pool-build time with an older normaliser, and mixing the
            # two put "tablespoon soy sauce" next to "soy sauce" on one shopping list (found by C1
            # failing on week-fc-009). One normaliser, applied at read time.
            ings = sorted(items_by_ing) or ings
            self.dishes.append({
                "id": i,
                "kind": kind,
                "name": r["name"],
                "cuisines": r["cuisines"],
                "cuisine": r["cuisines"][0],          # primary, first tag in canonical order
                "ingredients": ings,
                "iset": frozenset(ings),
                "items": r["items"],
                "items_by_ing": dict(items_by_ing),
                "display": display,
                "prep_min": r["prep_min"],
                "cook_min": r["cook_min"],
                "servings": r["servings"],
            })
        self.n = len(self.dishes)
        self.dish_tot = collections.Counter()
        for d in self.dishes:
            for ing in d["ingredients"]:
                self.dish_tot[ing] += 1

    def idf(self, ing: str) -> float:
        return math.log(self.n / max(1, self.dish_tot[ing]))


def select(c: FcCorpus, pool: list[int], n: int, min_cuisines: int, max_sim: float,
           restarts: int, seed: int, max_per_cuisine: int, max_per_protein: int = 2) -> dict:
    """Random-restart greedy on IDF mass of SHARED ingredients, with diversity constraints.

    Same reason as plan_week.py: maximising shared mass alone picks five near-identical dishes,
    and maximising raw shared count picks five bland ones. `max_sim` (Jaccard) and
    `max_per_cuisine` are what keep the optimum edible-shaped.
    """
    W = {ing: c.idf(ing) for ing in c.dish_tot}
    by_cuisine: dict[str, list[int]] = collections.defaultdict(list)
    for i in pool:
        for cu in c.dishes[i]["cuisines"]:
            by_cuisine[cu].append(i)
    cuisines = sorted(cu for cu in by_cuisine if by_cuisine[cu] and any(
        c.dishes[i]["kind"] == "element" for i in by_cuisine[cu]))
    if len(cuisines) < min_cuisines:
        raise SystemExit(f"only {len(cuisines)} cuisines in pool {cuisines}; need {min_cuisines}")

    best = None
    rng = random.Random(seed)
    for _ in range(restarts):
        chosen: list[int] = []
        counts: collections.Counter = collections.Counter()
        per_cuis: collections.Counter = collections.Counter()
        per_prot: collections.Counter = collections.Counter()

        def ok(i: int) -> bool:
            if i in chosen or per_cuis[c.dishes[i]["cuisine"]] >= max_per_cuisine:
                return False
            prots = proteins_of(c.dishes[i]["iset"])
            if max_per_protein and prots and any(per_prot[p] >= max_per_protein for p in prots):
                return False
            for j in chosen:
                a, b = c.dishes[i]["iset"], c.dishes[j]["iset"]
                if len(a & b) / max(1, len(a | b)) > max_sim:
                    return False
            return True

        # seed one dish per cuisine so the span constraint is structural
        order = cuisines[:]
        rng.shuffle(order)
        for cu in order:
            if len(chosen) >= n or sum(1 for x in chosen if cu in c.dishes[x]["cuisines"]) > 0:
                continue
            cands = [i for i in by_cuisine[cu] if ok(i) and c.dishes[i]["kind"] == "element"]
            if cands:
                pick = max(cands, key=lambda i: sum(W[t] for t in c.dishes[i]["ingredients"]
                                                  if counts[t] >= 1))
                chosen.append(pick)
                counts.update(c.dishes[pick]["ingredients"])
                per_cuis[c.dishes[pick]["cuisine"]] += 1
                for p in proteins_of(c.dishes[pick]["iset"]):
                    per_prot[p] += 1
        while len(chosen) < n:
            bestc, bestg = None, None
            for i in pool:
                if not ok(i) or c.dishes[i]["kind"] != "element":
                    continue
                trial = collections.Counter(counts)
                trial.update(c.dishes[i]["ingredients"])
                shared = sum(W[t] for t, k in trial.items() if k >= 2)
                single = sum(1 for k in trial.values() if k == 1)
                g = (shared, -single)
                if bestg is None or g > bestg:
                    bestc, bestg = i, g
            if bestc is None:
                break
            chosen.append(bestc)
            counts.update(c.dishes[bestc]["ingredients"])
            per_cuis[c.dishes[bestc]["cuisine"]] += 1
            for p in proteins_of(c.dishes[bestc]["iset"]):
                per_prot[p] += 1
        if len(chosen) < n:
            continue
        counts = collections.Counter()
        for i in chosen:
            counts.update(c.dishes[i]["ingredients"])
        shared = {t for t, k in counts.items() if k >= 2}
        span = sorted({cu for i in chosen for cu in c.dishes[i]["cuisines"]})
        score = (sum(W[t] for t in shared), len(span), -len(counts) + len(shared))
        if best is None or score > best[0]:
            best = (score, {"chosen": chosen, "counts": counts, "shared": shared,
                            "single": sorted(t for t, k in counts.items() if k == 1),
                            "cuisines": span,
                            "weighted": sum(W[t] for t in shared),
                            "max_pair_sim": round(max((len(c.dishes[a]["iset"] & c.dishes[b]["iset"]) /
                                                       max(1, len(c.dishes[a]["iset"] | c.dishes[b]["iset"]))
                                                       for a in chosen for b in chosen if a < b), default=0.0), 3)})
    if best is None:
        raise SystemExit("no week satisfied the constraints — relax --max-similarity or --max-per-cuisine")
    return best[1]


def pick_decompress(c: FcCorpus, res: dict, n: int, max_sim: float) -> list[int]:
    """Choose decompress meals that ADD the least shopping.

    Barrie's overlap objective applies here too: a quick dish that brings five new ingredients costs the
    same trip as an element dish does. Ties break toward fewer ingredients, then shorter cook time —
    the whole point is the night you cannot be bothered.
    """
    W = {ing: c.idf(ing) for ing in c.dish_tot}
    have = set(res["counts"])
    chosen: list[int] = []
    for _ in range(max(0, n)):
        best, best_key = None, None
        for i, d in enumerate(c.dishes):
            if d["kind"] != "quick" or i in chosen:
                continue
            if not is_dinner_name(d["name"]):      # a spice mix is not a decompress dinner
                continue
            if any(len(d["iset"] & c.dishes[j]["iset"]) / max(1, len(d["iset"] | c.dishes[j]["iset"])) > max_sim
                   for j in list(res["chosen"]) + chosen):
                continue
            new_ings = d["iset"] - have
            key = (-sum(W.get(t, 0.0) for t in new_ings), len(d["ingredients"]), d["cook_min"])
            if best_key is None or key < best_key:
                best, best_key = i, key
        if best is None:
            break
        chosen.append(best)
        have |= c.dishes[best]["iset"]
    return chosen


def render(c: FcCorpus, res: dict, args) -> dict:
    chosen = list(res["chosen"]) + list(res.get("decompress") or [])
    dishes = [c.dishes[i] for i in chosen]
    # Recompute over the FINAL dish list. `res["counts"]` only covers element dishes, so using it
    # here made the contract's declared overlap disagree with the validator's recomputation
    # (C4b FAIL on week-fc-009) and left decompress ingredients off the haul (C1 FAIL).
    counts: collections.Counter = collections.Counter()
    for d in dishes:
        counts.update(d["ingredients"])
    shared = sorted(t for t, k in counts.items() if k >= 2)
    single = sorted(t for t, k in counts.items() if k == 1)
    res = {**res, "counts": counts, "shared": shared, "single": single}
    haul: list[dict] = []
    for ing in sorted(res["counts"]):
        items = [it for d in dishes for it in d["items_by_ing"].get(ing, [])]
        agg = aggregate(items)
        # display = the canonical key: already singular and noise-free ("onions"/"tomatoes"/"basil
        # leaves" all normalise down). Showing the raw cook-typed phrase put plural duplicates on the
        # list next to their singular twin.
        disp = ing
        assumed = staple_of(ing)
        haul.append({"ingredient": ing, "display": disp, "quantity": agg["display"],
                     "shelf_stable": None, "special_order": False,
                     "staple": bool(assumed), "assumed_on_hand": assumed,
                     "aisle": aisle_for(ing),
                     "used_by_dishes": sum(1 for d in dishes if ing in d["iset"]),
                     "quantities_as_written": agg["exact"],
                     "quantity_unmeasured": agg["unmeasured"],
                     "quantity_mixed_families": agg["mixed_families"]})
    by_aisle: dict[str, list[str]] = collections.defaultdict(list)
    for row in haul:
        if row["staple"]:
            continue                       # printed separately; still IN the haul for C1
        by_aisle[row["aisle"]].append(f"{row['display']} — {row['quantity']}")
    return {
        "source": POOL_PATH.name + " (Food.com mirror filtered to prep>=4h, cook<=45m)",
        "split_basis": SPLIT_BASIS,
        "params": vars(args),
        "cuisine_span": res["cuisines"],
        "dishes": [{
            "dish_id": f"{d['cuisines'][0]}#{d['id']}",
            "name": d["name"],
            "cuisines": d["cuisines"],
            "cuisine": d["cuisines"][0],
            "servings": d["servings"],
            "prep_min": d["prep_min"], "cook_min": d["cook_min"],
            "ingredients": d["ingredients"],
            "kind": d["kind"],
            "decompress": d["kind"] == "quick",
            "day1_required": d["kind"] != "quick",
            # A decompress meal has NO day-1 work by design. Empty is the honest value; writing a
            # fake prep block here would be the exact failure this project keeps catching.
            "day1_parts": [{"part": "whole-dish prep block",
                            "action": (f"{fmt_minutes(d['prep_min'])} of preparation before serving day "
                                       f"(time-derived from preparation_time, NOT from instructions)"),
                            "holds_days": None}] if d["kind"] != "quick" else [],
            "serve_day_parts": [{
                "part": "the whole dinner" if d["kind"] == "quick" else "final cook",
                "action": ((f"{fmt_minutes(d['prep_min'])} prep + {fmt_minutes(d['cook_min'])} cook, "
                            f"start to table on the night — no day-1 work (time-derived, NOT from instructions)")
                           if d["kind"] == "quick" else
                           (f"{fmt_minutes(d['cook_min'])} of cooking on the serving day "
                            f"(time-derived from cooking_time, NOT from instructions)")),
            }],
        } for d in dishes],
        "pantry_shared": shared,
        "single_use": res["single"],
        "grocery_list": {a: by_aisle[a] for a in AISLE_ORDER if by_aisle.get(a)},
        "grocery_haul": haul,
        "metrics": {
            "dishes": len(dishes),
            "ingredients_total": len(res["counts"]),
            "shared_by_2plus": len(shared),
            "single_use_count": len(res["single"]),
            "overlap_ratio": round(len(shared) / max(1, len(res["counts"])), 4),
            "idf_mass_shared": round(res["weighted"], 2),
            "cuisine_span": len(res["cuisines"]),
            "decompress": sum(1 for d in dishes if d["kind"] == "quick"),
            "elements": sum(1 for d in dishes if d["kind"] != "quick"),
            "max_pairwise_similarity": res["max_pair_sim"],
            "buy_lines": sum(1 for r in haul if not r["staple"]),
            "staples_assumed": sum(1 for r in haul if r["staple"]),
            "quantities_measured": sum(1 for r in haul if not r["quantity_unmeasured"]),
            "quantities_asis_only": sum(1 for r in haul if r["quantity"] == "as needed"),
        },
    }


def to_contract(plan: dict, week_id: str, serves: int) -> dict:
    return {
        "week_id": week_id,
        "serves": serves,
        "meals_per_week": plan["metrics"]["dishes"],
        "notes": (f"FIVE WEEKNIGHT DINNERS — generated by tools/plan_week_fc.py from {plan['source']}. "
                  f"Desserts and breakfasts excluded at pool build (larder/mealclass.py) unless the title "
                  f"says breakfast for dinner. "
                  f"Assumes on hand: {STAPLE_DISCLAIMER} "
                  f"Split basis: {SPLIT_BASIS}. serves={serves} is an ASSUMPTION — per-dish `servings` "
                  f"are in the plan file and are null where the corpus has none."),
        "grocery_haul": [{"ingredient": r["ingredient"], "display": r["display"],
                          "quantity": r["quantity"], "shelf_stable": None, "special_order": False,
                          "staple": r["staple"]}
                         for r in plan["grocery_haul"]],
        "dishes": [{"dish_id": d["dish_id"], "name": d["name"], "cuisine": d["cuisine"],
                    "ingredients": d["ingredients"], "day1_required": d["day1_required"],
                    "day1_parts": d["day1_parts"], "serve_day_parts": d["serve_day_parts"],
                    "source_entry": f"food.com mirror — {plan['source']}"} for d in plan["dishes"]],
        "overlap": {"pool_size": plan["metrics"]["ingredients_total"],
                    "shared_by_two_or_more": plan["metrics"]["shared_by_2plus"],
                    "overlap_ratio": plan["metrics"]["overlap_ratio"],
                    "single_use_ingredients": plan["single_use"]},
        "prep_level": {"total_prep_tasks": sum(len(d["day1_parts"]) + len(d["serve_day_parts"])
                                               for d in plan["dishes"]),
                       "band": None,
                       "band_note": ("One prep block + one serve block per dish, both TIME-DERIVED. "
                                     "Barrie's 1-15 rubric is unpublished, so band stays null.")},
        "min_cuisines": int(plan["params"].get("min_cuisines", 3)),
    }


def print_plan(plan: dict) -> None:
    m = plan["metrics"]
    print("=" * 78)
    print(f"FIVE WEEKNIGHT DINNERS — {m['dishes']} mains · {m['cuisine_span']} cuisines · ONE HAUL")
    print("=" * 78)
    for d in plan["dishes"]:
        tag = "  ← DECOMPRESS" if d.get("decompress") else ""
        print(f"\n  [{d['cuisine']}] {d['name'][:52]}{tag}")
        print(f"    prep {fmt_minutes(d['prep_min']):>6}  →  serve-day cook {fmt_minutes(d['cook_min']):>6}"
              f"   serves {d['servings'] or 'not stated'}"
              + ("   (start to table tonight, no day-1 work)" if d.get("decompress") else ""))
    print("\n" + "-" * 78)
    print(f"ONE HAUL — {m['buy_lines']} to buy (+{m['staples_assumed']} assumed in your kitchen), "
          f"{m['shared_by_2plus']} used by 2+ dinners")
    print("-" * 78)
    for a, rows in plan["grocery_list"].items():
        print(f"  {a}")
        for r in rows:
            print(f"      {r}")
    assumed = [r for r in plan["grocery_haul"] if r["staple"]]
    if assumed:
        print("  ASSUMED IN YOUR KITCHEN — do not buy")
        print("      " + ", ".join(r["display"] for r in assumed))
        print(f"      {STAPLE_DISCLAIMER}")
    flagged = [r for r in plan["grocery_haul"] if r["quantity_mixed_families"]]
    print(f"\n  quantities measured: {m['quantities_measured']}/{len(plan['grocery_haul'])}"
          f" · 'as needed' only: {m['quantities_asis_only']}"
          f" · volume+weight split across lines: {len(flagged)}")
    print(f"  single-use: {m['single_use_count']} · overlap {m['overlap_ratio']:.4f} · "
          f"IDF mass {m['idf_mass_shared']} · max pair sim {m['max_pairwise_similarity']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Plan a week with quantities and a day-1/serve-day split.")
    ap.add_argument("--cuisines", default="indian,mexican,chinese,thai")
    ap.add_argument("--dishes", type=int, default=5,
                    help="TOTAL dinners in the week, decompress included")
    ap.add_argument("--min-cuisines", type=int, default=3)
    ap.add_argument("--max-similarity", type=float, default=0.45)
    ap.add_argument("--max-per-cuisine", type=int, default=2)
    ap.add_argument("--decompress", type=int, default=1,
                    help="how many quick comfort dinners to include (no day-1 work; default 1)")
    ap.add_argument("--max-per-protein", type=int, default=2,
                    help="cap dinners sharing a protein family — the objective alone buys five chickens")
    ap.add_argument("--restarts", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--serves", type=int, default=4, help="ASSUMPTION carried into the contract file")
    ap.add_argument("--out", default="out/week-fc-001.json")
    ap.add_argument("--contract", action="store_true", help="also write <out>.contract.json for the validator")
    args = ap.parse_args()

    c = FcCorpus(load_pool())
    want = {s.strip() for s in args.cuisines.split(",") if s.strip()}
    known = {cu for d in c.dishes for cu in d["cuisines"]}
    unknown = want - known
    if unknown:
        raise SystemExit(f"cuisine(s) not in the day-1 pool: {sorted(unknown)}\navailable: {sorted(known)}")
    pool = [d["id"] for d in c.dishes
            if want & set(d["cuisines"]) and is_plausible_dinner(d["ingredients"])
            and is_dinner_name(d["name"])]
    rejected_by_name = sum(1 for d in c.dishes if want & set(d["cuisines"]) and not is_dinner_name(d["name"]))
    print(f"name filter rejected {rejected_by_name} component/dessert recipes (chutney, sauce, cake…)")
    print(f"pool: {c.n} day-1 recipes · {len(pool)} in {{{', '.join(sorted(want))}}} after dinner filter")

    # --dishes is the TOTAL number of dinners in the week; the decompress slot is one of them.
    n_elements = max(1, args.dishes - max(0, args.decompress))
    res = select(c, pool, n_elements, args.min_cuisines, args.max_similarity,
                 args.restarts, args.seed, args.max_per_cuisine, args.max_per_protein)
    if args.decompress:
        res = dict(res)
        res["decompress"] = pick_decompress(c, res, args.decompress, args.max_similarity)
        if not res["decompress"]:
            print("  !! no decompress dish satisfied the constraints — running without one")
    plan = render(c, res, args)
    print_plan(plan)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    print(f"\nwrote {out}")
    if args.contract:
        cpath = out.with_suffix(".contract.json")
        cpath.write_text(json.dumps(to_contract(plan, out.stem, args.serves), indent=1), encoding="utf-8")
        print(f"wrote {cpath}  →  python tools/validate_week.py {cpath}")


if __name__ == "__main__":
    main()
