#!/usr/bin/env python3
"""Validate a Larder week JSON against data/week.schema.json and four constraints.

Exit codes:
  0 = all constraints pass (printed per-constraint)
  1 = one or more constraints fail (printed, named)
  2 = usage/parse/schema error

Usage: python tools/validate_week.py <week.json>
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None  # fall back to manual structural checks


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "week.schema.json"


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_schema(data: dict) -> list[str]:
    """Validate against the JSON Schema. Returns list of error messages (empty = pass)."""
    if not SCHEMA_PATH.exists():
        return [f"Schema file not found: {SCHEMA_PATH}"]

    schema = _load_json(SCHEMA_PATH)
    if jsonschema is None:
        # Standard-library-only structural check
        return _manual_structural_check(data, schema)

    try:
        jsonschema.validate(data, schema)
        return []
    except jsonschema.exceptions.ValidationError as e:
        return [e.message]


def _manual_structural_check(data: dict, schema: dict) -> list[str]:
    """Fallback structural validation when jsonschema is not installed."""
    errors = []

    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required top-level field: {field}")

    props = schema.get("properties", {})

    # Check grocery_haul items
    haul_schema = props.get("grocery_haul", {}).get("items", {})
    haul_required = haul_schema.get("required", [])
    haul_items = data.get("grocery_haul", [])
    for i, item in enumerate(haul_items):
        for field in haul_required:
            if field not in item:
                errors.append(f"grocery_haul[{i}] missing required field: {field}")

    # Check dishes items
    dishes_schema = props.get("dishes", {}).get("items", {})
    dishes_required = dishes_schema.get("required", [])
    dishes = data.get("dishes", [])
    for i, dish in enumerate(dishes):
        for field in dishes_required:
            if field not in dish:
                errors.append(f"dishes[{i}] missing required field: {field}")

    # Check overlap
    overlap_schema = props.get("overlap", {})
    overlap_required = overlap_schema.get("required", [])
    overlap = data.get("overlap", {})
    for field in overlap_required:
        if field not in overlap:
            errors.append(f"overlap missing required field: {field}")

    # Check prep_level
    prep_schema = props.get("prep_level", {})
    prep_required = prep_schema.get("required", [])
    prep = data.get("prep_level", {})
    for field in prep_required:
        if field not in prep:
            errors.append(f"prep_level missing required field: {field}")

    # additionalProperties check
    for key in data:
        if key not in props and schema.get("additionalProperties") is False:
            errors.append(f"Additional property not allowed: {key}")

    # Dishes minItems
    if not isinstance(dishes, list) or len(dishes) < 1:
        errors.append("dishes must be a non-empty array")

    return errors


def _check_c1(data: dict) -> list[str]:
    """C1: One grocery haul — every dish ingredient in haul; no special_order items."""
    failures: list[str] = []
    haul_items = {item["ingredient"]: item for item in data.get("grocery_haul", [])}

    # Collect all ingredients used across dishes
    dish_ingredients: set[str] = set()
    for i, dish in enumerate(data.get("dishes", [])):
        for ing in dish.get("ingredients", []):
            dish_ingredients.add(ing)

    # Check every dish ingredient appears in haul
    missing = dish_ingredients - set(haul_items.keys())
    if missing:
        failures.append(
            f"C1 FAIL: ingredients used in dishes but missing from grocery_haul: {sorted(missing)}"
        )

    # Check no special_order items in haul
    specials = [item["ingredient"] for item in haul_items.values() if item.get("special_order")]
    if specials:
        failures.append(
            f"C1 FAIL: grocery_haul contains special_order items: {sorted(specials)}"
        )

    return failures


def _check_c2(data: dict) -> list[str]:
    """C2: every dish has day-1 work — unless it declares itself a decompress meal.

    A DECOMPRESS dish (`day1_required: false`) does no day-1 work by design: prep <= 20 min, cook <= 30
    min, <= 12 ingredients, comfort-class name (`larder/decompress.py`). Skipping it must not become a
    loophole, so the week also has to contain at least ONE dish that does carry day-1 work — otherwise
    "five weeknight dinners" would quietly become "five quick dishes" and the method in the name would
    be gone.
    """
    failures: list[str] = []
    elements = 0
    for dish in data.get("dishes", []):
        if dish.get("day1_required", True) is False:
            if dish.get("day1_parts"):
                failures.append(
                    f"C2 FAIL: dish '{dish.get('dish_id', '?')}' is marked day1_required=false "
                    f"but carries day1_parts"
                )
            continue
        if not dish.get("day1_parts"):
            failures.append(
                f"C2 FAIL: dish '{dish.get('dish_id', '?')}' has empty or missing day1_parts"
            )
        else:
            elements += 1
    if not elements:
        failures.append("C2 FAIL: no dish in the week carries day-1 work — that is not this method")
    return failures


def _check_c3(data: dict) -> list[str]:
    """C3: Every dish has a non-empty serve_day_parts array."""
    failures: list[str] = []
    for dish in data.get("dishes", []):
        if not dish.get("serve_day_parts"):
            failures.append(
                f"C3 FAIL: dish '{dish.get('dish_id', '?')}' has empty or missing serve_day_parts"
            )
    return failures


def _check_c5(data: dict) -> list[str]:
    """C5: Cross-cuisine — week spans at least K distinct cuisines.

    K comes from the week file's 'min_cuisines' field (top level).
    If absent, defaults to 3. Prints the default when applied.
    """
    failures: list[str] = []

    min_cuisines = data.get("min_cuisines", None)
    if min_cuisines is None:
        min_cuisines = 3
        print(f"C5: min_cuisines not found — defaulted to {min_cuisines}")
    elif not isinstance(min_cuisines, int) or min_cuisines < 1:
        failures.append(
            f"C5 FAIL: min_cuisines must be a positive integer, got {min_cuisines!r}"
        )
        return failures

    cuisines: set[str] = set()
    for dish in data.get("dishes", []):
        c = dish.get("cuisine")
        if c:
            cuisines.add(c)

    distinct = len(cuisines)
    if distinct < min_cuisines:
        failures.append(
            f"C5 FAIL: week spans {distinct} distinct cuisine(s) "
            f"({sorted(cuisines)}), needs at least {min_cuisines}"
        )

    # Store for reporting
    if "_computed" not in data:
        data["_computed"] = {}
    data["_computed"]["distinct_cuisines"] = distinct
    data["_computed"]["min_cuisines"] = min_cuisines

    return failures


def _check_c4(data: dict) -> list[str]:
    """C4: Shared ingredient pool.

    Computes from dishes[]:
      - pool_size = total unique ingredients across dishes
      - shared_by_two_or_more = count of ingredients used by ≥2 dishes
      - overlap_ratio = shared / total
      - single_use_ingredients = ingredients used by exactly 1 dish

    (a) REPORTED: prints single-use count and list (never gates).
    (b) FAIL if file's declared overlap numbers disagree with recomputed.
    """
    failures: list[str] = []

    # Count usage per ingredient across dishes
    usage: dict[str, int] = {}
    for dish in data.get("dishes", []):
        for ing in dish.get("ingredients", []):
            usage[ing] = usage.get(ing, 0) + 1

    pool_size = len(usage)
    shared = sum(1 for c in usage.values() if c >= 2)
    single_use = sorted(ing for ing, c in usage.items() if c == 1)
    overlap_ratio = round(shared / pool_size, 4) if pool_size > 0 else 0.0

    file_overlap = data.get("overlap", {})

    # (a) Single-use ingredients — REPORTED, NOT GATED
    # C4a is infeasible at n=5 for any cuisine span (see T2.1c finding).
    # Store for reporting; never add to failures.
    data["_computed"] = {
        "pool_size": pool_size,
        "shared_by_two_or_more": shared,
        "overlap_ratio": overlap_ratio,
        "single_use_ingredients": single_use,
    }
    declared_pool = file_overlap.get("pool_size")
    declared_shared = file_overlap.get("shared_by_two_or_more")
    declared_ratio = file_overlap.get("overlap_ratio")
    declared_single = file_overlap.get("single_use_ingredients", None)

    mismatches: list[str] = []
    if declared_pool is not None and declared_pool != pool_size:
        mismatches.append(f"pool_size (declared={declared_pool}, computed={pool_size})")
    if declared_shared is not None and declared_shared != shared:
        mismatches.append(
            f"shared_by_two_or_more (declared={declared_shared}, computed={shared})"
        )
    # Allow tiny float tolerance for ratio
    if declared_ratio is not None and abs(declared_ratio - overlap_ratio) > 1e-6:
        mismatches.append(
            f"overlap_ratio (declared={declared_ratio}, computed={overlap_ratio})"
        )
    if declared_single is not None and sorted(declared_single) != single_use:
        mismatches.append(
            f"single_use_ingredients (declared={sorted(declared_single)}, computed={single_use})"
        )

    if mismatches:
        failures.append(
            f"C4b FAIL: declared overlap numbers disagree with recomputed: {'; '.join(mismatches)}"
        )

    return failures


def _compute_prep_tasks(data: dict) -> int:
    """Count total prep tasks across all dishes (day1_parts + serve_day_parts)."""
    total = 0
    for dish in data.get("dishes", []):
        total += len(dish.get("day1_parts", []))
        total += len(dish.get("serve_day_parts", []))
    return total


def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/validate_week.py <week.json>")
        sys.exit(2)

    week_path = Path(sys.argv[1])
    if not week_path.exists():
        print(f"Error: file not found — {week_path}")
        sys.exit(2)

    try:
        data = _load_json(week_path)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}")
        sys.exit(2)

    # --- Schema validation — non-negotiable, exit 2 on failure ---
    schema_errors = _validate_schema(data)
    if schema_errors:
        print("SCHEMA FAIL:")
        for err in schema_errors:
            print(f"  {err}")
        sys.exit(2)

    # --- Constraint checks ---
    all_failures: list[str] = []

    all_failures.extend(_check_c1(data))
    all_failures.extend(_check_c2(data))
    all_failures.extend(_check_c3(data))
    all_failures.extend(_check_c4(data))
    all_failures.extend(_check_c5(data))

    # --- Per-constraint verdicts ---
    # C4 is split: C4a (shared pool) is REPORTED only — measured infeasible at n=5 for every cuisine
    # span, so it cannot be a pass/fail gate; C4b (declared == recomputed) remains a hard gate.
    c_labels = ["C1", "C2", "C3", "C4b", "C5"]
    c_failures: dict[str, list[str]] = {}
    for f in all_failures:
        raw_prefix = f.split(" FAIL")[0]
        prefix = raw_prefix if raw_prefix in ("C4a", "C4b") else raw_prefix[:2]
        c_failures.setdefault(prefix, []).append(f)

    for label in c_labels:
        if label in c_failures:
            print(f"{label} FAIL")
        else:
            print(f"{label} PASS")

    # --- Reports (never gate) ---
    computed = data.get("_computed", {})
    pool_size = computed.get("pool_size", 0)
    shared = computed.get("shared_by_two_or_more", 0)
    ratio = computed.get("overlap_ratio", 0.0)

    print(f"\npool_size={pool_size}")
    print(f"overlap_ratio={ratio}")
    print(f"shared_by_two_or_more={shared}")

    # C4a report — never gates
    single_use = computed.get("single_use_ingredients", [])
    print(f"C4a REPORTED, NOT GATED: {len(single_use)} single-use ingredient(s) "
          f"(infeasible to reach 0 at n=5 for any cuisine span — see T2.1c)")
    print(f"single_use_count={len(single_use)}")
    if single_use:
        print(f"single_use_ingredients={single_use}")

    total_prep = _compute_prep_tasks(data)
    print(f"total_prep_tasks={total_prep}")

    prep = data.get("prep_level", {})
    band = prep.get("band", "null")
    band_note = prep.get(
        "band_note",
        "Barrie's band rubric is unpublished. Cannot assign a 1-15 score.",
    )
    print(f"prep_band={band}")
    print(f"prep_band_note={band_note}")

    if all_failures:
        print("\nFAILURES:")
        for f in all_failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\nALL CONSTRAINTS PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()