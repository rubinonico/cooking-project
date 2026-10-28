"""plan_week.py — a week of dinners: N dishes, ONE shared haul, from 39,774 recipes.

    python tools/plan_week.py --cuisines italian,indian,thai,southern_us --out out/week-002.json

WHY THE OBJECTIVE IS RARITY-WEIGHTED
------------------------------------
Maximising "number of ingredients shared by >=2 dishes" degenerates: salt, onion, garlic and
water are shared by everything, so every week scores well and every week is the same. Sharing
`salt` is worth nothing to a cook; sharing `fish sauce` is worth a trip.

So ingredients are weighted by IDF, log(N / dishes_containing_it). Staples fall to ~0.1 and
specialties to ~7. The score is the IDF mass of ingredients the week SHARES — i.e. what the one
haul actually buys you.

WHAT THIS DOES NOT DO
---------------------
The corpus is `{id, cuisine, ingredients[]}` — it has NO instructions, so the day-1
Element / serving-day Full-Meal split CANNOT be derived from it. That half of Barrie's method is
reported as `not established` per dish rather than invented. Closing it needs a corpus with
directions (RecipeNLG, 2.23M recipes) — see `research/datasets-recon.md`.

Constraints are REPORTED, never gated (the C4a lesson): the run always prints the overlap ratio,
the single-use list, the cuisine span and the weighted score, and you judge them.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from larder.corpus import Corpus, aisle_for, is_plausible_dinner  # noqa: E402

AISLE_ORDER = ["produce", "protein", "dairy", "grain_pasta", "oil_fat", "spice", "sauce_condiment", "other"]


def idf(corpus: Corpus, ing: str) -> float:
    return math.log(corpus.n / max(1, corpus.dish_tot[ing]))


def select(corpus: Corpus, pool: list[int], n: int, min_cuisines: int,
           max_sim: float, restarts: int, seed: int, max_per_cuisine: int = 2) -> dict:
    """Random-restart greedy. Seed one dish per cuisine so the span constraint is structural,
    then add the dish that converts the most currently-single-use IDF mass into shared.

    `max_per_cuisine` and `max_sim` exist because the objective ALONE degenerates: maximising
    shared IDF mass is best served by picking near-identical dishes, and the first run returned
    three near-identical biryanis out of five dinners. The diversity constraint is what stops
    the optimum being useless — the same failure mode as a selector maximising raw shared count
    returning five dishes from one family."""
    rng = random.Random(seed)
    by_cuisine: dict[str, list[int]] = {}
    for i in pool:
        by_cuisine.setdefault(corpus.dishes[i]["cuisine"], []).append(i)
    cuisines = sorted(by_cuisine)
    if len(cuisines) < min_cuisines:
        raise SystemExit(f"pool has {len(cuisines)} cuisines, need {min_cuisines}")

    W = {i: idf(corpus, i) for i in corpus.dish_tot}
    best = None
    for _ in range(restarts):
        chosen = []
        for c in rng.sample(cuisines, min_cuisines):            # one seed per required cuisine
            chosen.append(rng.choice(by_cuisine[c]))
        counts: dict[str, int] = collections.Counter()
        for i in chosen:
            counts.update(corpus.dishes[i]["ingredients"])

        while len(chosen) < n:
            cand_idx = set()
            # only dishes that share at least one currently-single-use ingredient can gain
            for ing, c in counts.items():
                if c == 1:
                    cand_idx.update(corpus.by_ingredient[ing])
            cand_idx -= set(chosen)
            if not cand_idx:
                break
            cand = rng.sample(sorted(cand_idx), min(600, len(cand_idx)))
            per_c: dict[str, int] = collections.Counter(corpus.dishes[k]["cuisine"] for k in chosen)
            best_c, best_score = None, None
            for j in cand:
                dj = corpus.dishes[j]
                if per_c[dj["cuisine"]] >= max_per_cuisine:      # diversity: cap per cuisine
                    continue
                if max((len(dj["iset"] & corpus.dishes[k]["iset"]) /
                        max(1, len(dj["iset"] | corpus.dishes[k]["iset"])) for k in chosen),
                       default=0) > max_sim:
                    continue
                # Score the RESULT, not the incremental gain. An earlier version scored
                # "IDF mass of currently-single-use ingredients this dish would share", which
                # has no term for the ingredients the dish INTRODUCES — so a 40-ingredient
                # recipe that shared 5 rare items beat an 8-ingredient one, and the week ended
                # with 57 single-use items. Score the resulting week instead.
                trial = counts + collections.Counter(dj["ingredients"])
                w = sum(W[ing] for ing, cnt in trial.items() if cnt >= 2)
                single = sum(1 for cnt in trial.values() if cnt == 1)
                score = (w, -single)
                if best_score is None or score > best_score:
                    best_c, best_score = j, score
            if best_c is None:
                break
            chosen.append(best_c)
            counts.update(corpus.dishes[best_c]["ingredients"])

        if len(chosen) < n:
            continue
        counts = collections.Counter()
        for i in chosen:
            counts.update(corpus.dishes[i]["ingredients"])
        shared = {i for i, c in counts.items() if c >= 2}
        weighted = sum(W[i] for i in shared)
        cuis = {corpus.dishes[i]["cuisine"] for i in chosen}
        # ties broken toward MORE cuisines (diversity) before anything else
        score = (weighted, len(cuis), -len(counts) + len(shared))
        if best is None or score > best[0]:
            best = (score, {"chosen": chosen, "counts": counts, "shared": shared,
                            "single": sorted(i for i, c in counts.items() if c == 1),
                            "cuisines": sorted(cuis), "weighted": weighted,
                            "max_pair_sim": round(max((len(corpus.dishes[a]["iset"] & corpus.dishes[b]["iset"]) /
                                                       max(1, len(corpus.dishes[a]["iset"] | corpus.dishes[b]["iset"]))
                                                       for a in chosen for b in chosen if a < b), default=0.0), 3)})
    return best[1]


def render(corpus: Corpus, res: dict, args) -> dict:
    dishes = [corpus.dishes[i] for i in res["chosen"]]
    plan = {
        "source": "whats-cooking-train.json (What's Cooking / Yummly, 39,774 recipes, 20 cuisines)",
        "generated_with": "tools/plan_week.py",
        "objective": "maximise IDF mass of ingredients shared by >=2 dishes",
        "params": vars(args),
        "cuisine_span": res["cuisines"],
        "dishes": [{"name": f"{d['cuisine']}#{d['id']}", "cuisine": d["cuisine"],
                    "ingredients": sorted(d["ingredients"]),
                    "day1_element": "not established (corpus has no instructions)",
                    "serving_day": "not established (corpus has no instructions)"} for d in dishes],
        "pantry_shared": sorted(res["shared"]),
        "single_use": res["single"],
        "metrics": {
            "dishes": len(dishes),
            "ingredients_total": len(res["counts"]),
            "shared_by_2plus": len(res["shared"]),
            "single_use_count": len(res["single"]),
            "overlap_ratio": round(len(res["shared"]) / max(1, len(res["counts"])), 4),
            "idf_mass_shared": round(res["weighted"], 2),
            "cuisine_span": len(res["cuisines"]),
            "max_pairwise_similarity": res.get("max_pair_sim"),
        },
        "grocery_list": {},
    }
    by_aisle: dict[str, list[str]] = {}
    for ing in sorted(res["counts"]):
        by_aisle.setdefault(aisle_for(ing), []).append(ing)
    for a in AISLE_ORDER:
        if by_aisle.get(a):
            plan["grocery_list"][a] = by_aisle[a]
    return plan


NOT_ESTABLISHED = "not established (corpus has no instructions)"


def to_contract(plan: dict, week_id: str, serves: int) -> dict:
    """Project generator output onto data/week.schema.json so tools/validate_week.py can run on REAL output.

    Written 2026-10-28. Before this, validate_week.py only ever saw out/week-001.json — a hand-authored
    fixture — so "week-001 passes" was never evidence about the generator. Empty day1_parts/serve_day_parts
    are deliberate: the schema permits empty arrays and the validator's C2/C3 gates then FAIL loudly, which
    is the true state. Nothing here is invented to make a gate go green.
    """
    m = plan["metrics"]
    return {
        "week_id": week_id,
        "serves": serves,
        "meals_per_week": m["dishes"],
        "notes": (f"generated by tools/plan_week.py from {plan['source']}; "
                  f"serves={serves} is an ASSUMPTION (the corpus carries no serving counts)"),
        "grocery_haul": [{"ingredient": ing, "display": ing, "quantity": None,
                          "shelf_stable": None, "special_order": False}
                         for ing in sorted(plan["pantry_shared"]) + list(plan["single_use"])],
        "dishes": [{"dish_id": d["name"],
                    "name": d["name"],
                    "cuisine": d["cuisine"],
                    "ingredients": d["ingredients"],
                    "day1_parts": [],
                    "serve_day_parts": [],
                    "source_entry": NOT_ESTABLISHED} for d in plan["dishes"]],
        "overlap": {"pool_size": m["ingredients_total"],
                    "shared_by_two_or_more": m["shared_by_2plus"],
                    "overlap_ratio": m["overlap_ratio"],
                    "single_use_ingredients": plan["single_use"]},
        "prep_level": {"total_prep_tasks": 0, "band": None,
                       "band_note": ("UNESTABLISHED: corpus has no instructions, so there are no prep tasks "
                                     "to count and Barrie's 1-15 rubric is unpublished")},
        "min_cuisines": int(plan["params"].get("min_cuisines", 3)),
    }


def print_plan(plan: dict) -> None:
    m = plan["metrics"]
    print("=" * 74)
    print(f"THE WEEK — {m['dishes']} dinners · {m['cuisine_span']} cuisines · ONE HAUL")
    print("=" * 74)
    for d in plan["dishes"]:
        print(f"\n  [{d['cuisine']}]  ({len(d['ingredients'])} ingredients)")
        print(f"    {', '.join(d['ingredients'])}")
    print("\n" + "-" * 74)
    print(f"SHARED PANTRY — {m['shared_by_2plus']} items used by 2+ dinners (this is the haul)")
    print("-" * 74)
    for a in AISLE_ORDER:
        if plan["grocery_list"].get(a):
            print(f"  {a:16} {', '.join(plan['grocery_list'][a])}")
    print(f"\n  SINGLE-USE — {m['single_use_count']} items bought for one dinner only:")
    print(f"    {', '.join(plan['single_use']) if plan['single_use'] else 'none'}")
    print("\n" + "-" * 74)
    print("REPORTED, NOT GATED — you judge these")
    print("-" * 74)
    print(f"  overlap ratio        {m['overlap_ratio']:.4f}   (shared / all ingredients)")
    print(f"  IDF mass shared      {m['idf_mass_shared']}   (rarity-weighted — the objective)")
    print(f"  single-use count     {m['single_use_count']}")
    print(f"  cuisine span         {m['cuisine_span']}")
    print(f"  max pair similarity  {m['max_pairwise_similarity']}   (no two dinners overlap more than this)")
    print("\n  day-1 Element / serving-day split: NOT ESTABLISHED — the corpus carries no")
    print("  instructions. Reported rather than invented. Needs a corpus with directions.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Plan a week from the 39,774-recipe corpus.")
    ap.add_argument("--cuisines", default="italian,indian,thai,southern_us")
    ap.add_argument("--dishes", type=int, default=5)
    ap.add_argument("--min-cuisines", type=int, default=3)
    ap.add_argument("--max-similarity", type=float, default=0.45,
                    help="reject a pair of dinners overlapping more than this (Jaccard)")
    ap.add_argument("--max-per-cuisine", type=int, default=2,
                    help="diversity cap: at most this many dinners from one cuisine")
    ap.add_argument("--min-ingredients", type=int, default=5)
    ap.add_argument("--max-ingredients", type=int, default=25,
                    help="exclude very long recipes; a 40-ingredient dish adds mostly single-use items")
    ap.add_argument("--restarts", type=int, default=400)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="out/week-002.json")
    ap.add_argument("--contract", action="store_true",
                    help="also write <out>.contract.json shaped for data/week.schema.json (validator input)")
    ap.add_argument("--serves", type=int, default=4,
                    help="ASSUMPTION carried into the contract file; the corpus has no serving counts")
    args = ap.parse_args()

    c = Corpus()
    want = {s.strip() for s in args.cuisines.split(",") if s.strip()}
    unknown = want - set(c.cuisine_size)
    if unknown:
        raise SystemExit(f"unknown cuisine(s): {sorted(unknown)}\nknown: {sorted(c.cuisine_size)}")
    pool = [i for i, d in enumerate(c.dishes)
            if d["cuisine"] in want
            and args.min_ingredients <= len(d["ingredients"]) <= args.max_ingredients
            and is_plausible_dinner(d["ingredients"])]
    print(f"corpus: {c.n} recipes / {len(c.cuisine_size)} cuisines")
    print(f"pool:   {len(pool)} dishes in {{{', '.join(sorted(want))}}} — "
          f"{args.min_ingredients}-{args.max_ingredients} ingredients, desserts/convenience excluded")

    res = select(c, pool, args.dishes, args.min_cuisines, args.max_similarity,
                 args.restarts, args.seed, args.max_per_cuisine)
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
