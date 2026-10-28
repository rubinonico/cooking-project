#!/usr/bin/env python
"""Resolve ingredient names against Epicure MCP, normalise, apply alias map.

Usage:
    python tools/resolve_ingredients.py --in data/seed_ingredients.txt --out data/ingredients.json

Pipeline per ingredient:
    lowercase -> strip punctuation -> singularise each word -> snake_case -> alias map -> Epicure cultural_profile

Exit: writes ingredients.json + aliases.yaml, prints resolved/total, lists every unresolvable name.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import yaml

# ── Normalisation ──────────────────────────────────────────────────────────


def singularise(word: str) -> str:
    """Crude English singularisation.  Handles the seed list's plurals."""
    if len(word) <= 3:
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    # NOTE: "ves" → "f" (leaves→leaf) is deliberately omitted here.
    # The only seed ingredient needing it is "curry leaves" → "curry_leaf",
    # handled via explicit alias ("curry_leave" → "curry_leaf") below.
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("xes"):
        return word[:-2]
    if word.endswith("ches"):
        return word[:-2]
    if word.endswith("shes"):
        return word[:-2]
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def normalise(name: str) -> str:
    """Normalise an ingredient name: lowercase, strip punct, singularise, snake_case."""
    raw = name.strip().lower()
    # strip punctuation (keep spaces and internal hyphens for splitting)
    raw = re.sub(r"[^\w\s]", " ", raw)
    # collapse whitespace
    raw = re.sub(r"\s+", " ", raw).strip()
    # singularise each word
    words = [singularise(w) for w in raw.split()]
    # snake_case
    return "_".join(words)


# ── Epicure resolver ───────────────────────────────────────────────────────


def load_aliases(path: str | Path) -> dict[str, str]:
    """Load alias map from YAML.  Returns empty dict if file missing."""
    p = Path(path)
    if not p.exists():
        return {}
    with open(p) as f:
        data = yaml.safe_load(f)
    return data.get("aliases", {}) if isinstance(data, dict) else {}


def resolve_one(
    normalised: str,
    aliases: dict[str, str],
    epicure: "Epicure",
) -> dict:
    """Resolve a single normalised ingredient against Epicure.

    Returns:
        {
            "input_name": <original>,
            "canonical": <canonical name sent to Epicure>,
            "resolved": <name Epicure returned> or None,
            "cultural_profile": <dict from Epicure> or None,
            "error": str or None,
        }
    """
    canonical = aliases.get(normalised, normalised)
    result = {
        "canonical": canonical,
        "error": None,
    }
    try:
        profile = epicure.call("cultural_profile", ingredient=canonical)
    except Exception as exc:
        result["error"] = str(exc)
        return result

    # Epicure returns a plain-text error string for unresolvable ingredients
    if isinstance(profile, str):
        result["error"] = profile
        return result

    result["cultural_profile"] = profile
    return result


# ── Main ───────────────────────────────────────────────────────────────────


def build_aliases_yaml() -> dict:
    """The canonical alias map, seeded from probe measurements."""
    return {
        "aliases": {
            # Known from T2.2 probe — Epicure resolves these differently
            # than normalisation alone produces.
            "cilantro": "coriander",
            "sea_salt": "salt",
            "pepper": "black_pepper",
            "sesame": "sesame_seed",
            "cayenne": "cayenne_pepper",
            # Plural→singular (the common case, kept explicit per spec)
            "almonds": "almond",
            "tomatoes": "tomato",
            "shallots": "shallot",
            "scallions": "scallion",
            "mushrooms": "mushroom",
            "capers": "caper",
            "anchovies": "anchovy",
            # CORRECTION from T1.2a parent review — fenugreek_seed and parmesan_cheese
            # resolve on Epicure; these are ALIAS-MAP GAPS, not Epicure vocabulary gaps.
            "fenugreek": "fenugreek_seed",
            "parmesan": "parmesan_cheese",
            # Pool aliases discovered during T1.2b variant sweep
            "breadcrumb": "bread_crumbs",
            "cheddar": "cheddar_cheese",
            "cocoa": "cocoa_powder",
            "garlic_powder": "garlic",
            "green_papaya": "papaya",
            "grits": "grits",
            "grit": "grits",
            "ham_hock": "ham",
            "marsala": "marsala_wine",
            "mascarpone": "mascarpone_cheese",
            "mozzarella": "mozzarella_cheese",
            "pecorino": "pecorino_cheese",
            "provolone": "provolone_cheese",
            "ricotta": "ricotta_cheese",
            "tomato_sauce": "tomato",
            "vermicelli_noodles": "vermicelli",
            "vermicelli_noodle": "vermicelli",
            # Additional uncovered by probe
            "chickpeas": "chickpea",
            "lentils": "lentil",
            "cloves": "clove",
            "potatoes": "potato",
            "curry_leaves": "curry_leaf",
            "mustard_seeds": "mustard_seed",
            # Different Epicure vocabulary entirely
            "chile_pepper": "chili_pepper",
            "chile_peppers": "chili_pepper",
            "kaffir_lime": "kaffir_lime",
            "thai_basil": "thai_basil",
            # Singularisation edge cases
            "cloves": "clove",
            "curry_leave": "curry_leaf",
            # Snake_case compounds that Epicure resolves identically with spaces
            "fish_sauce": "fish_sauce",
            "coconut_milk": "coconut_milk",
            "olive_oil": "olive_oil",
            "soy_sauce": "soy_sauce",
            "star_anise": "star_anise",
            "garam_masala": "garam_masala",
            "white_wine": "white_wine",
            "red_wine": "red_wine",
        },
    }


def read_ingredient_list(path: str | Path) -> list[str]:
    """Read ingredient names from a text file (skip comments and blanks)."""
    names: list[str] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            names.append(line)
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve ingredients against Epicure MCP")
    parser.add_argument("--in", dest="in_path", required=True, help="Input ingredient list (text)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    # ── Load input and alias map ───────────────────────────────────────────
    ingredients = read_ingredient_list(args.in_path)
    aliases_data = build_aliases_yaml()
    aliases = aliases_data["aliases"]

    out_dir = Path(args.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write aliases.yaml first (it is a deliverable)
    aliases_path = out_dir / "aliases.yaml"
    with open(aliases_path, "w") as f:
        yaml.dump(aliases_data, f, default_flow_style=False, sort_keys=False)

    # ── Connect to Epicure ────────────────────────────────────────────────
    sys.stderr.write(f"Connecting to Epicure MCP...\n")
    # Add project root to sys.path so tools.epicure resolves from anywhere
    _project_root = Path(__file__).resolve().parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from tools.epicure import Epicure  # noqa: E402
    epicure = Epicure()
    sys.stderr.write(f"Connected. Session: {epicure.sid}\n")

    # ── Resolve each ingredient ────────────────────────────────────────────
    resolved_ok: list[dict] = []
    unresolved: list[dict] = []

    for i, raw_name in enumerate(ingredients):
        normalised = normalise(raw_name)
        out = resolve_one(normalised, aliases, epicure)

        entry = {
            "raw": raw_name,
            "normalised": normalised,
            "canonical": out["canonical"],
            "cultural_profile": out.get("cultural_profile"),
            "error": out.get("error"),
        }

        if out["error"] is None:
            resolved_ok.append(entry)
        else:
            unresolved.append(entry)

        # Rate-limit: server allows ~60 req/min → 1 req/s comfortably
        if i < len(ingredients) - 1:
            time.sleep(1.0)

    # ── Build output ───────────────────────────────────────────────────────
    output = {
        "meta": {
            "total": len(ingredients),
            "resolved": len(resolved_ok),
            "unresolved": len(unresolved),
            "resolution_rate": f"{len(resolved_ok)}/{len(ingredients)}",
            "epicure_vocabulary_gap": [
                {
                    "raw": e["raw"],
                    "normalised": e["normalised"],
                    "canonical": e["canonical"],
                    "error_precis": e["error"][:120] if e["error"] else None,
                }
                for e in unresolved
            ],
        },
        "aliases": aliases,
        "ingredients": resolved_ok + unresolved,
    }

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── Print report ───────────────────────────────────────────────────────
    print(f"\nResolution: {len(resolved_ok)}/{len(ingredients)}")
    if unresolved:
        print(f"\nUnresolved ({len(unresolved)}):  (Epicure vocabulary limits, not bad ingredients)")
        for e in unresolved:
            print(f"  {e['raw']!r}  → canonical={e['canonical']!r}  :: {e['error'][:100]}")
    else:
        print("All ingredients resolved.")

    sys.stderr.write(f"\nWrote: {args.out}\n")
    sys.stderr.write(f"Wrote: {aliases_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())