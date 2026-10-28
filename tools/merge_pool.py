#!/usr/bin/env python
"""Merge pool-resolved data into ingredients.json, preserving seed entries with source field.

Handles the T1.2a correction: fenugreek and parmesan were ALIAS-MAP GAPS, not
Epicure gaps. This script replaces their old seed entries with correct data.

Usage:
    python tools/merge_pool.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

SEED_PATH = PROJECT / "data" / "ingredients.json"
POOL_PATH = PROJECT / "data" / "_tmp_pool_resolved.json"
OUT_PATH = PROJECT / "data" / "ingredients.json"
ALIASES_YAML = PROJECT / "data" / "aliases.yaml"


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ── Known alias-map gaps that the old seed file has as "unresolved" ──
# These were reported as Epicure gaps but the server HAS them under a variant.
# The pool run resolves them correctly.
CORRECTED_NORMS: dict[str, str] = {
    "fenugreek": "fenugreek_seed",   # not in pool; re-resolved via terminal
    "parmesan": "parmesan_cheese",   # in pool; pool data replaces seed
}


def main() -> int:
    seed_data = load_json(SEED_PATH)
    pool_data = load_json(POOL_PATH)

    # ── Build seed entries with source="seed" ────────────────────────────
    old_seed_ingredients: list[dict] = seed_data.get("ingredients", [])
    seed_by_norm: dict[str, dict] = {}
    for entry in old_seed_ingredients:
        entry["source"] = "seed"
        seed_by_norm[entry["normalised"]] = entry

    # ── Build pool lookup ────────────────────────────────────────────────
    pool_ingredients: list[dict] = pool_data.get("ingredients", [])
    pool_by_norm: dict[str, dict] = {}
    for entry in pool_ingredients:
        pool_by_norm[entry["normalised"]] = entry

    # ── Apply correction: replace fenugreek and parmesan in seed ─────────
    for norm, canonical in CORRECTED_NORMS.items():
        old_entry = seed_by_norm.get(norm)
        pool_entry = pool_by_norm.get(norm)

        if pool_entry:
            # Pool has it resolved — use it (preserving seed raw name)
            replacement = dict(pool_entry)
            replacement["raw"] = old_entry["raw"]
            replacement["source"] = "seed"
            seed_by_norm[norm] = replacement
            print(f"CORRECTED: {norm} (seed entry replaced with pool-resolved data) → {canonical}")
        elif old_entry and old_entry.get("error"):
            # Not in pool but needs fixing (fenugreek)
            # Import the re-resolved data we confirmed
            old_entry["canonical"] = canonical
            old_entry["error"] = None
            old_entry["cultural_profile"] = {
                "resolved": canonical,
                "cuisines": {
                    "South_Asian": {"score": 0.3737, "range": {"p10": -0.0808, "p90": 0.071}},
                    "Southeast_Asian": {"score": 0.0507, "range": {"p10": -0.1625, "p90": 0.193}},
                    "Latin_American": {"score": 0.0364, "range": {"p10": -0.1672, "p90": 0.1281}},
                    "Eastern_European": {"score": 0.0221, "range": {"p10": -0.1466, "p90": 0.1034}},
                    "Mediterranean": {"score": 0.0084, "range": {"p10": -0.2323, "p90": 0.206}},
                    "Western_Atlantic": {"score": -0.0381, "range": {"p10": -0.2304, "p90": 0.183}},
                    "Japanese": {"score": -0.0803, "range": {"p10": -0.1359, "p90": 0.1896}},
                    "East_Asian": {"score": -0.1035, "range": {"p10": -0.1649, "p90": 0.3039}},
                },
                "note": "Cosine similarity to each cuisine direction. Use p10/p90 to judge whether a score is typical or extreme.",
            }
            seed_by_norm[norm] = old_entry
            print(f"CORRECTED: {norm} (seed entry data patched) → {canonical}")
        else:
            print(f"  SKIP {norm}: no fix needed")

    # ── Combine: seed entries first, then NEW pool entries ───────────────
    pool_new_entries: list[dict] = []
    pool_norms_seen: set[str] = set()

    for entry in pool_ingredients:
        norm = entry["normalised"]
        if norm in pool_norms_seen:
            continue
        pool_norms_seen.add(norm)

        if norm in seed_by_norm:
            # Already in seed — skip unless seed entry is unresolved
            # (handled above by CORRECTED_NORMS)
            if norm in CORRECTED_NORMS:
                continue  # already replaced
            print(f"  SKIP (already seed): {norm}")
            continue

        entry["source"] = "pool"
        pool_new_entries.append(entry)

    # Seed entries first, maintaining original order
    combined = list(old_seed_ingredients)  # these have source="seed" already set
    # But we need to update in case replacements changed
    combined = [seed_by_norm[e["normalised"]] for e in old_seed_ingredients]
    combined += pool_new_entries

    # ── Separate alias-map gaps from Epicure vocabulary gaps ─────────────
    unresolved_combined = [e for e in combined if e.get("error")]
    alias_map_gaps: list[dict] = []
    epicure_gaps: list[dict] = []

    for entry in unresolved_combined:
        if entry["normalised"] in CORRECTED_NORMS:
            alias_map_gaps.append(entry)
        else:
            epicure_gaps.append(entry)

    resolved_count = sum(1 for e in combined if not e.get("error"))
    unresolved_count = sum(1 for e in combined if e.get("error"))

    # ── Combine aliases: seed aliases (from old file) + pool aliases ────
    # Pool run may have added entries. Use pool's alias set since it's the
    # superset (the resolver's build_aliases_yaml is now our canonical source).
    merged_aliases = pool_data.get("aliases", seed_data.get("aliases", {}))

    output = {
        "meta": {
            "total": len(combined),
            "resolved": resolved_count,
            "unresolved": unresolved_count,
            "resolution_rate": f"{resolved_count}/{len(combined)}",
            "seed_count": len(old_seed_ingredients),
            "pool_new_count": len(pool_new_entries),
            "alias_map_gaps": [
                {
                    "raw": e["raw"],
                    "normalised": e["normalised"],
                    "canonical": e["canonical"],
                    "error_precis": (e["error"] or "")[:120],
                }
                for e in alias_map_gaps
            ],
            "epicure_vocabulary_gaps": [
                {
                    "raw": e["raw"],
                    "normalised": e["normalised"],
                    "canonical": e["canonical"],
                    "error_precis": (e["error"] or "")[:120],
                }
                for e in epicure_gaps
            ],
        },
        "aliases": merged_aliases,
        "ingredients": combined,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── Print report ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"T1.2b MERGE COMPLETE")
    print(f"{'='*60}")
    print(f"Seed entries preserved:  {len(old_seed_ingredients)}")
    print(f"Pool entries added:      {len(pool_new_entries)}")
    print(f"Total entries:           {len(combined)}")
    print(f"Resolved:                {resolved_count}")
    print(f"Unresolved:              {unresolved_count}")
    print(f"  Alias-map gaps:        {len(alias_map_gaps)}")
    print(f"  Epicure gaps:          {len(epicure_gaps)}")
    print(f"  → Genuine Epicure gaps: {[e['normalised'] for e in epicure_gaps]}")
    print(f"Corrected entries:       {list(CORRECTED_NORMS.keys())}")
    print(f"Wrote: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())