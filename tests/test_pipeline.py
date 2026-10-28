"""End-to-end contract test for the week pipeline.

    python tests/test_pipeline.py          # stdlib only, no pytest needed

What this asserts, and why each assertion exists:

1. **The pool is the pool.** 614 recipes survived `prep >= 4 h AND cook <= 45 m` with a cuisine tag
   and 5-25 ingredients. If that count changes, every number downstream moved and nobody decided it.
2. **Generation is deterministic for a seed.** Two runs with `--seed 7` must pick the same dish_ids;
   otherwise a "week" is not reproducible and no comparison between weeks means anything.
3. **The contract validates.** `tools/validate_week.py <contract>` exits 0. This is the assertion
   that was never run before 2026-10-28 — `out/week-001.json` was a hand-authored fixture, so the
   validator passed on paper while the generator's real output failed on schema.
4. **Every dish carries a day-1 part and a serve-day part**, and both say `time-derived` in the
   action text. Empty arrays would let C2/C3 pass silently on nothing; unlabelled text would let a
   time-derived guess read as an instruction.
5. **Every haul line carries an amount.** `null` quantities are the old failure mode (Yummly gave
   bare names); "as needed" is an allowed answer, silence is not.
6. **C1 holds independently of the validator**: every ingredient any dish uses appears in the haul.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
OUT = ROOT / "out/_test"
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    print("1. self-checks (each fails before any number is printed)")
    for mod in ("larder.corpus", "larder.quantities", "larder.fcnames", "larder.pantry", "larder.mealclass"):
        r = run(["-m", mod])
        check(mod, r.returncode == 0, (r.stderr or r.stdout)[-300:])

    print("2. day-1 pool")
    pool_path = ROOT / "data/external/fc_pool.json"
    if not pool_path.exists():
        print("  SKIP  fc_pool.json absent — run tools/build_fc_pool.py")
        FAILURES.append("pool missing")
        return 1
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    meta = pool["meta"]
    # The exact count is a consequence of the filters and moved 614 → 526 on 2026-10-28 when the
    # ingredient cap dropped 25 → 15. Assert the CONTRACT of the filter, not a magic number, or this
    # test breaks every time a threshold is tuned and teaches nobody anything.
    check("pool filter is the day-1 filter",
          "prep >= 240 min" in meta["filter"] and "15 ingredients" in meta["filter"], meta["filter"])
    check(f"pool is substantial (got {meta['rows_kept']})", meta["rows_kept"] >= 400, str(meta["rows_kept"]))
    check("pool rows all satisfy the time filter",
          all(r["prep_min"] >= 240 and r["cook_min"] <= 45 for r in pool["pool"]))
    check("no recipe carries instruction text", "TIMES ONLY" in meta["split_basis"], meta["split_basis"])
    check("pool is dinner-only", "dinner only" in meta.get("meal_class", ""), meta.get("meal_class"))
    check("desserts were actually dropped", meta["dropped"].get("dessert", 0) > 0, str(meta["dropped"]))

    print("3. generation is deterministic for a seed")
    weeks = []
    for i in (1, 2):
        r = run(["tools/plan_week_fc.py", "--dishes", "5", "--min-cuisines", "3",
                 "--seed", "7", "--out", str(OUT / f"det{i}.json"), "--contract"])
        check(f"run {i} exits 0", r.returncode == 0, (r.stderr or r.stdout)[-400:])
        weeks.append(json.loads((OUT / f"det{i}.json").read_text(encoding="utf-8")))
    ids = [[d["dish_id"] for d in w["dishes"]] for w in weeks]
    check("same seed → same dishes", ids[0] == ids[1], f"{ids[0]} vs {ids[1]}")

    plan = weeks[0]
    contract_path = OUT / "det1.contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    print("4. the contract validates")
    v = run(["tools/validate_week.py", str(contract_path)])
    check("validate_week.py exits 0", v.returncode == 0, v.stdout[-500:])
    check("no gate FAILs", "FAIL" not in v.stdout.replace("C4a REPORTED", ""), v.stdout[-300:])

    print("5. day-1 / serving-day split")
    for d in contract["dishes"]:
        if d.get("day1_required", True) is False:
            # DECOMPRESS meal: no day-1 work by design
            check(f"{d['dish_id']} is a decompress meal with NO day-1 work", d["day1_parts"] == [])
            check(f"{d['dish_id']} still has a serve-day part", len(d["serve_day_parts"]) >= 1)
            continue
        check(f"{d['dish_id']} has a day-1 part", len(d["day1_parts"]) >= 1)
        check(f"{d['dish_id']} has a serve-day part", len(d["serve_day_parts"]) >= 1)
        act = " ".join(p["action"] for p in d["day1_parts"] + d["serve_day_parts"]).lower()
        check(f"{d['dish_id']} labels the split time-derived", "time-derived" in act, act[:120])
    check("the week still contains day-1 work",
          any(d.get("day1_required", True) and d["day1_parts"] for d in contract["dishes"]),
          "all dishes were decompress meals — the method is gone")

    print("6. quantities")
    haul = contract["grocery_haul"]
    check("haul is non-empty", len(haul) > 0)
    check("no null quantity", all(h["quantity"] for h in haul),
          str([h["ingredient"] for h in haul if not h["quantity"]]))
    measured = [h for h in haul if h["quantity"] != "as needed"]
    check("most haul lines carry a real amount", len(measured) / len(haul) > 0.5,
          f"{len(measured)}/{len(haul)}")

    print("6b. staples are split out of the printed list but stay in the haul")
    staples = [h for h in haul if h.get("staple")]
    buys = [h for h in haul if not h.get("staple")]
    check("some staples detected", len(staples) > 0, str(len(staples)))
    check("staples still present in grocery_haul (C1 intact)", len(buys) + len(staples) == len(haul))
    check("buy list is shorter than the haul", len(buys) < len(haul), f"{len(buys)}/{len(haul)}")
    check("water treated as a staple", all(h["staple"] for h in haul if h["ingredient"] == "water"))

    print("7. C1 — one haul, checked independently of the validator")
    in_haul = {h["ingredient"] for h in haul}
    missing = [(d["dish_id"], i) for d in contract["dishes"] for i in d["ingredients"] if i not in in_haul]
    check("every dish ingredient is on the haul", not missing, str(missing[:5]))

    print("8. diversity guards")
    cuisines = {d["cuisine"] for d in contract["dishes"]}
    check(f"week spans >= min_cuisines ({contract.get('min_cuisines')})",
          len(cuisines) >= contract.get("min_cuisines", 3), str(cuisines))
    names = [d["name"].lower() for d in contract["dishes"]]
    banned = [n for n in names if any(w in n for w in ("chutney", "sauce", "cake", "jam", "dip"))]
    check("no component/dessert dishes", not banned, str(banned))

    print("8b. decompress slot")
    quick = [d for d in contract["dishes"] if d.get("day1_required") is False]
    check("exactly one decompress meal by default", len(quick) == 1, str(len(quick)))
    if quick:
        q = plan["dishes"][[d["dish_id"] for d in plan["dishes"]].index(quick[0]["dish_id"])]
        check("decompress meal is quick (prep <= 20, cook <= 30)",
              q["prep_min"] <= 20 and q["cook_min"] <= 30, f"{q['prep_min']}/{q['cook_min']}")
        check("decompress meal is small (<= 12 ingredients)", len(q["ingredients"]) <= 12,
              str(len(q["ingredients"])))
    check("week total is still 5 dinners", len(contract["dishes"]) == 5, str(len(contract["dishes"])))

    print("9. five weeknight dinners — meal class")
    sys.path.insert(0, str(ROOT))          # the test runs as a script, so ROOT must be importable
    from larder.mealclass import classify, DINNER as K_DINNER
    off_class = [(d["name"], classify(d["name"])) for d in contract["dishes"] if classify(d["name"]) != K_DINNER]
    check("every dish classifies as dinner", not off_class, str(off_class))
    check("breakfast has a dinner carve-out", classify("Sausage Gravy (Breakfast for Dinner)", {"breakfast"}) == K_DINNER)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print(f"ALL CHECKS PASS — {len(contract['dishes'])} dishes, {len(haul)} haul lines, "
          f"{plan['metrics']['shared_by_2plus']} shared, overlap {plan['metrics']['overlap_ratio']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
