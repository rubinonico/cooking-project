#!/usr/bin/env python3
"""
shelf_stability.py — classify ingredients by room-temperature shelf stability.

Usage:
    python tools/shelf_stability.py --in data/seed_ingredients.txt \\
                                    --out data/shelf_stability.json

Reads a plain-text ingredient list (comments on # lines, one ingredient per line),
classifies each as shelf_stable | not_shelf_stable | method_dependent,
attaches a source for every row, and writes structured JSON.

Reusable — re-run over a different input for T1.3b by changing the --in path.
"""

import argparse
import json
import sys
from pathlib import Path

# ── Classification table ────────────────────────────────────────────────────
# Every row carries:
#   class   — shelf_stable | not_shelf_stable | method_dependent
#   source  — the authority for the row's classification
#   note    — brief explanation of what the class means for this ingredient
#
# Authorities used:
#   USDA-FK  = USDA FSIS FoodKeeper dataset
#   USDA-SS  = USDA FSIS "Shelf-Stable Food Safety" page
#   USDA-SSC = USDA FSIS Shelf-Stable Food storage chart (appended to SS page)
#   USDA-FQ  = USDA FSIS FAQ ("Does all cheese need to be refrigerated?")
#   CLEMSON  = Clemson Extension "Food Storage: Pantry" (HGIC 3521)
#   NDSU-EX  = NDSU Extension "Food Storage Guide" (FN579)
#   FDA-FC   = FDA Food Code 2022 (TCS / non-TCS classification)
#   CDR-WISC = Center for Dairy Research, Wisconsin (cheese safety/storage)
#   COMM     = Commercial food-safety guideline (named per entry)
#   NOT-EST  = Not established by standard food-safety authorities

CLASSIFICATION = {
    # ── spices / dried herbs / seasonings ──────────────────────────────
    "ALLSPICE": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: ground spices 2-3 yr pantry",
        "note": "Dried spice — shelf-stable in airtight container."
    },
    "CAYENNE": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: ground spices 2-3 yr pantry",
        "note": "Dried ground chile — shelf-stable."
    },
    "CINNAMON": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole spices 4-5 yr pantry",
        "note": "Dried bark — shelf-stable as sticks or ground."
    },
    "CUMIN": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole spices 4-5 yr pantry",
        "note": "Dried seeds — shelf-stable whole or ground."
    },
    "OREGANO": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: dried herbs 2-3 yr pantry",
        "note": "Dried herb — shelf-stable."
    },
    "PAPRIKA": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: ground spices 2-3 yr pantry",
        "note": "Dried ground spice — shelf-stable."
    },
    "PEPPER": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole spices 4-5 yr pantry",
        "note": "Dried peppercorns or ground — shelf-stable."
    },
    "SAFFRON": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: dried herbs 2-3 yr pantry",
        "note": "Dried stigma — shelf-stable."
    },
    "STAR ANISE": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole spices 4-5 yr pantry",
        "note": "Dried spice pod — shelf-stable."
    },
    "TARRAGON": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: dried herbs 2-3 yr pantry",
        "note": "Dried herb — shelf-stable."
    },
    "THYME": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: dried herbs 2-3 yr pantry",
        "note": "Dried herb — shelf-stable."
    },
    "CARDAMOM": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole spices 4-5 yr pantry",
        "note": "Dried pods/seeds — shelf-stable."
    },
    "CLOVES": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole spices 4-5 yr pantry",
        "note": "Dried flower buds — shelf-stable."
    },
    "CORIANDER": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole seeds 4-5 yr pantry",
        "note": "Dried seeds (cilantro seeds) — shelf-stable."
    },
    "FENUGREEK": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole seeds 4-5 yr pantry",
        "note": "Dried seeds — shelf-stable."
    },
    "TURMERIC": {
        "class": "method_dependent",
        "source": "USDA-FK (ground: 2-3 yr pantry); fresh rhizome: needs refrigeration per USDA FoodKeeper",
        "note": "Ground/dried = shelf-stable; fresh rhizome = not shelf-stable."
    },
    "GARAM MASALA": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: spice blends ~6 mo pantry",
        "note": "Dried spice blend — shelf-stable."
    },
    "MUSTARD SEEDS": {
        "class": "shelf_stable",
        "source": "USDA-FK; Clemson Extension: whole seeds 4-5 yr pantry",
        "note": "Dried seeds — shelf-stable."
    },

    # ── nuts / seeds / legumes ─────────────────────────────────────────
    "ALMONDS": {
        "class": "shelf_stable",
        "source": "CLEMSON: unshelled nuts 6-12 mo pantry",
        "note": "Dried nut — shelf-stable in cool pantry, longer if refrigerated."
    },
    "SESAME": {
        "class": "shelf_stable",
        "source": "CLEMSON: seeds in airtight container, months in pantry",
        "note": "Dried seeds — shelf-stable; sesame oil is also shelf-stable."
    },
    "CHICKPEAS": {
        "class": "method_dependent",
        "source": "USDA-SSC: low-acid canned goods 2-5 yr pantry; CLEMSON: dried legumes 1 yr pantry",
        "note": "Dried or canned = shelf-stable; cooked-fresh = not (needs refrigeration)."
    },
    "LENTILS": {
        "class": "method_dependent",
        "source": "USDA-SSC: low-acid canned goods 2-5 yr; CLEMSON: dried legumes 1 yr pantry",
        "note": "Dried = shelf-stable; canned = shelf-stable; cooked = not."
    },

    # ── grains / staples ────────────────────────────────────────────────
    "RICE": {
        "class": "shelf_stable",
        "source": "USDA-SSC: rice 2 yr pantry; CLEMSON: white rice 1 yr, brown 6 mo",
        "note": "Dried grain — shelf-stable."
    },
    "SEA SALT": {
        "class": "shelf_stable",
        "source": "CLEMSON: salt indefinitely shelf-stable",
        "note": "Mineral — indefinitely shelf-stable."
    },

    # ── oils / fats ─────────────────────────────────────────────────────
    "OLIVE OIL": {
        "class": "shelf_stable",
        "source": "CLEMSON: olive oil 6 mo pantry; USDA-FK: oils shelf-stable before opening",
        "note": "Bottled oil — shelf-stable in cool dark pantry."
    },
    "GHEE": {
        "class": "shelf_stable",
        "source": "USDA-FK: ghee 6-8 mo pantry; 1-2 yr refrigerated",
        "note": "Clarified butter — shelf-stable in airtight container. America's Test Kitchen confirms at least 3 mo at cool room temp."
    },
    "BUTTER": {
        "class": "not_shelf_stable",
        "source": "USDA-FK; USDA-FQ: butter 1-3 mo refrigerated; 1-2 d room temp only",
        "note": "Requires refrigeration — not shelf-stable."
    },

    # ── vinegars / fermented condiments ─────────────────────────────────
    "VINEGAR": {
        "class": "shelf_stable",
        "source": "CLEMSON: vinegar 30 mo pantry; USDA-SS: bottled condiments shelf-stable",
        "note": "Acetic acid preserves indefinitely — shelf-stable."
    },
    "SOY SAUCE": {
        "class": "shelf_stable",
        "source": "NDSU-EX: soy sauce unopened 3 yr pantry; USDA-FK: 1 yr after opening refrigerated",
        "note": "Fermented — shelf-stable unopened; can be kept at room temp after opening."
    },
    "FISH SAUCE": {
        "class": "shelf_stable",
        "source": "NDSU-EX: fermented condiments comparable to soy sauce; USDA pattern",
        "note": "Fermented — shelf-stable unopened at room temp."
    },
    "MISO": {
        "class": "method_dependent",
        "source": "USDA-FK: miso 1 yr refrigerated (no pantry time listed); COMM: some shelf-stable formulations exist",
        "note": "Traditional miso: refrigerate after opening. Some commercial pastes are shelf-stable (heat-treated). Check label."
    },
    "MUSTARD": {
        "class": "shelf_stable",
        "source": "USDA-FK: prepared mustard 1-2 yr unopened pantry; NDSU-EX: 1 yr opened refrigerated",
        "note": "Prepared condiment (yellow/Dijon) — shelf-stable unopened. Seed list has MUSTARD separate from MUSTARD SEEDS."
    },

    # ── alliums (store like shelf-stable root veg) ──────────────────────
    "GARLIC": {
        "class": "method_dependent",
        "source": "CLEMSON: whole bulbs 1-3 mo cool pantry; USDA FoodCode: peeled garlic in oil = TCS (needs refrigeration)",
        "note": "Fresh whole bulbs = shelf-stable (weeks-months in cool pantry). Peeled/minced in oil = not (botulism risk, must refrigerate)."
    },
    "ONION": {
        "class": "shelf_stable",
        "source": "CLEMSON: onions 1-3 mo at cool room temp (45-50°F), ~1 wk at standard room temp",
        "note": "Fresh whole onion keeps weeks in pantry — shelf-stable in culinary practice."
    },
    "SHALLOTS": {
        "class": "shelf_stable",
        "source": "CLEMSON: shallots similar storage to onions — weeks in cool pantry",
        "note": "Fresh whole shallots — weeks in cool pantry."
    },
    "SCALLIONS": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: scallions/green onions 1-2 d room temp, must refrigerate",
        "note": "Fresh green — needs refrigeration, not shelf-stable."
    },

    # ── vegetables ──────────────────────────────────────────────────────
    "MUSHROOMS": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh mushrooms 1 wk refrigerated; CLEMSON: dried mushrooms 1 yr pantry",
        "note": "Dried = shelf-stable; fresh = not."
    },
    "TOMATOES": {
        "class": "method_dependent",
        "source": "USDA-SSC: high-acid canned tomatoes 12-18 mo pantry; fresh tomatoes: room temp only until ripe, then refrigerate",
        "note": "Canned/processed = shelf-stable; fresh whole = perishable (days at room temp)."
    },
    "POTATOES": {
        "class": "method_dependent",
        "source": "CLEMSON: potatoes 1-3 mo at 45-50°F, ~1 wk at standard room temp (70°F)",
        "note": "Shelf-stable for weeks at cool pantry temp; shorter at standard room temp. Method-dependent on storage conditions."
    },

    # ── herbs (fresh vs dried) ─────────────────────────────────────────
    "BASIL": {
        "class": "method_dependent",
        "source": "USDA-FK; CLEMSON: dried herbs 2-3 yr pantry; fresh basil: refrigerate, days only",
        "note": "Dried = shelf-stable; fresh = not."
    },
    "CILANTRO": {
        "class": "method_dependent",
        "source": "USDA-FK; CLEMSON: dried seeds (coriander) shelf-stable; fresh leaves: refrigerate, days",
        "note": "Dried seeds (coriander) = shelf-stable; fresh leaves = not."
    },
    "PARSLEY": {
        "class": "method_dependent",
        "source": "USDA-FK; CLEMSON: dried herbs 2-3 yr pantry; fresh: refrigerate, 1-2 wk",
        "note": "Dried = shelf-stable; fresh = not."
    },
    "CURRY LEAVES": {
        "class": "method_dependent",
        "source": "COMM: dried curry leaves shelf-stable; fresh curry leaves: refrigerate, limited life",
        "note": "Dried = shelf-stable; fresh = not. No established USDA FoodKeeper entry for curry leaves."
    },
    "THAI BASIL": {
        "class": "method_dependent",
        "source": "COMM: dried form shelf-stable; fresh = perishable (same pattern as basil per USDA-FK)",
        "note": "Dried = shelf-stable; fresh = not."
    },

    # ── chiles ──────────────────────────────────────────────────────────
    "CHILE PEPPERS": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh chiles 1 wk refrigerated; dried = spice, shelf-stable per USDA-FK",
        "note": "Dried whole/ground = shelf-stable; fresh = not."
    },

    # ── fruit / citrus / aromatics ─────────────────────────────────────
    "COCONUT": {
        "class": "method_dependent",
        "source": "USDA-FK; CLEMSON: dried/desiccated coconut 6 mo pantry; fresh coconut: refrigerate after opening",
        "note": "Dried/desiccated = shelf-stable; fresh = not."
    },
    "COCONUT MILK": {
        "class": "method_dependent",
        "source": "USDA-SSC: canned goods shelf-stable; COMM: canned coconut milk months in pantry; fresh/carton = perishable",
        "note": "Canned = shelf-stable; fresh carton or opened = not."
    },
    "LEMON": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh lemons 1-2 wk room temp, longer refrigerated; bottled juice: USDA-SSC high-acid canned 12-18 mo",
        "note": "Fresh whole fruit = limited room-temp life (1-2 wk); bottled juice = shelf-stable."
    },
    "LIME": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh limes 1-2 wk room temp; bottled juice: USDA-SSC high-acid canned 12-18 mo",
        "note": "Fresh = limited room-temp life; bottled juice = shelf-stable."
    },
    "YUZU": {
        "class": "method_dependent",
        "source": "COMM: fresh yuzu fruit = refrigerate; bottled yuzu juice = shelf-stable (pattern per USDA high-acid canned juices)",
        "note": "Fresh = not; bottled juice = shelf-stable."
    },
    "LEMONGRASS": {
        "class": "method_dependent",
        "source": "COMM: dried lemongrass shelf-stable; fresh = refrigerate, 1-2 wk",
        "note": "Dried/powdered = shelf-stable; fresh stalk = not."
    },
    "GALANGAL": {
        "class": "method_dependent",
        "source": "COMM: dried galangal shelf-stable; fresh = refrigerate (follows ginger storage pattern per USDA-FK)",
        "note": "Dried/powdered = shelf-stable; fresh = not."
    },
    "KAFFIR LIME": {
        "class": "method_dependent",
        "source": "COMM: dried kaffir lime leaves shelf-stable; fresh leaves/fruit = refrigerate",
        "note": "Dried leaves = shelf-stable; fresh leaves/fruit = not."
    },
    "GINGER": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh ginger refrigerate; CLEMSON: ground ginger (spice) 2-3 yr pantry",
        "note": "Dried/ground = shelf-stable; fresh rhizome = not."
    },
    "HORSERADISH": {
        "class": "method_dependent",
        "source": "USDA-FK: prepared horseradish (jar) 12 mo unopened pantry, 3-4 mo refrigerated after opening; fresh root = refrigerate",
        "note": "Prepared (jarred) = shelf-stable unopened; fresh root = not."
    },
    "TAMARIND": {
        "class": "shelf_stable",
        "source": "COMM: tamarind paste/concentrate/block shelf-stable in cool pantry; USDA-FK pattern for preserved condiments",
        "note": "Paste/concentrate/block — shelf-stable."
    },

    # ── dairy / cheese ─────────────────────────────────────────────────
    "PARMESAN": {
        "class": "method_dependent",
        "source": "USDA-FQ: hard cheese (block Parmesan) does not require refrigeration for safety; FDA-FC + CDR-WISC: Parmesan is non-TCS when whole, below 86°F",
        "note": "Whole block/wedge = shelf-stable (non-TCS per FDA Food Code); grated/shredded = not (needs refrigeration)."
    },
    "YOGURT": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: yogurt 7-14 d refrigerated; room temp >2 h discard per FoodSafety.gov",
        "note": "Requires refrigeration — not shelf-stable."
    },
    "PANEER": {
        "class": "not_shelf_stable",
        "source": "COMM: fresh Indian cheese, high moisture — needs refrigeration, 3-5 d; follows cottage cheese pattern per USDA-FK",
        "note": "Fresh, high-moisture cheese — not shelf-stable."
    },
    "CREAM": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: cream 1 mo refrigerated; room temp >2 h discard per FoodSafety.gov",
        "note": "Requires refrigeration — not shelf-stable."
    },

    # ── pickled / brined ────────────────────────────────────────────────
    "CAPERS": {
        "class": "shelf_stable",
        "source": "USDA-FK; USDA-SSC: pickled/brined items shelf-stable; Clemson: pickles 12-18 mo pantry",
        "note": "Pickled/brined in vinegar or salt — shelf-stable."
    },
    "ANCHOVIES": {
        "class": "method_dependent",
        "source": "COMM: salt-cured anchovies in jars/tins 12-24 mo at cool room temp (aw <0.75 per FDA BAM); fresh anchovies = refrigerate, 1-2 d",
        "note": "Salt-cured/canned = shelf-stable; fresh = not."
    },

    # ── wine / alcohol ──────────────────────────────────────────────────
    "WHITE WINE": {
        "class": "shelf_stable",
        "source": "USDA-SS: bottled beverages shelf-stable; commercial wine is shelf-stable unopened",
        "note": "Bottled — shelf-stable (sealed, unopened)."
    },
    "RED WINE": {
        "class": "shelf_stable",
        "source": "USDA-SS: bottled beverages shelf-stable; commercial wine is shelf-stable unopened",
        "note": "Bottled — shelf-stable (sealed, unopened)."
    },

    # ── fresh vegetable / not shelf-stable in any common form ─────────
    "FENNEL": {
        "class": "method_dependent",
        "source": "USDA-FK: fennel bulb refrigerate; CLEMSON: fennel seeds (dried spice) shelf-stable",
        "note": "Fresh bulb = not; dried seeds = shelf-stable."
    },
    "HONEY": {
        "class": "shelf_stable",
        "source": "USDA-FK: honey 2 yr pantry (quality window); CLEMSON: indefinitely shelf-stable in sealed container",
        "note": "Indefinitely shelf-stable — low water activity prevents spoilage."
    },

    # ── NEW POOL ENTRIES (T1.3b) ──────────────────────────────────────────
    #
    # ── fresh produce / vegetables ───────────────────────────────────────
    "APPLES": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh apples 1-3 wk refrigerated; USDA-SSC: high-acid canned applesauce 12-18 mo pantry; CLEMSON: dried apples 3 mo pantry",
        "note": "Fresh = not shelf-stable (refrigerate). Canned/dried = shelf-stable."
    },
    "BROCCOLI": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh broccoli 3-5 d refrigerated; USDA-SSC: low-acid canned vegetables 2-5 yr pantry",
        "note": "Fresh = not; frozen/canned = shelf-stable."
    },
    "CARROTS": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh carrots 2 wk refrigerated; USDA-SSC: low-acid canned carrots 2-5 yr pantry",
        "note": "Fresh = not; canned = shelf-stable."
    },
    "CAULIFLOWER": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh cauliflower 1 wk refrigerated; USDA-SSC: low-acid canned 2-5 yr pantry",
        "note": "Fresh = not; canned = shelf-stable."
    },
    "CELERY": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: fresh celery 1 wk refrigerated; COMM: no common shelf-stable form for celery",
        "note": "Fresh celery requires refrigeration. Dehydrated celery exists but is not a standard form. Not shelf-stable in common use."
    },
    "COLLARD GREENS": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh collard greens 1-2 wk refrigerated; USDA-SSC: low-acid canned greens 2-5 yr pantry",
        "note": "Fresh = not; canned = shelf-stable."
    },
    "EGGPLANT": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh eggplant 3-5 d refrigerated; COMM: dried/roasted-in-oil shelf-stable forms exist; USDA-SSC: canned 2-5 yr",
        "note": "Fresh = not; canned/dried = shelf-stable."
    },
    "GREEN PAPAYA": {
        "class": "method_dependent",
        "source": "COMM: fresh green papaya = refrigerate (follows melon pattern per CLEMSON); dried/pickled = shelf-stable",
        "note": "Fresh = not shelf-stable; dried/pickled = shelf-stable."
    },
    "LETTUCE": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: fresh lettuce 1 wk refrigerated; USDA-FK: salad greens 1 wk refrigerated; no shelf-stable form",
        "note": "Fresh greens — requires refrigeration. Not shelf-stable."
    },
    "BEAN SPROUTS": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: fresh bean sprouts refrigerate 1-2 d; FDA Food Code: sprouts are TCS (Time/Temperature Control for Safety)",
        "note": "Fresh sprouts — requires refrigeration. High-moisture, perishable. Not shelf-stable."
    },
    "BELL PEPPERS": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh bell peppers 1 wk refrigerated; COMM: dried bell pepper flakes shelf-stable; USDA-SSC: canned 2-5 yr",
        "note": "Fresh = not; dried/canned = shelf-stable."
    },
    "SPINACH": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh spinach 1-2 wk refrigerated; USDA-SSC: low-acid canned spinach 2-5 yr pantry",
        "note": "Fresh = not shelf-stable; canned = shelf-stable."
    },

    # ── fresh herbs (method_dependent for dried) ────────────────────────
    "MINT": {
        "class": "method_dependent",
        "source": "USDA-FK; CLEMSON: dried herbs 2-3 yr pantry; fresh mint: refrigerate, days only",
        "note": "Dried = shelf-stable; fresh = not."
    },
    "ROSEMARY": {
        "class": "method_dependent",
        "source": "USDA-FK; CLEMSON: dried herbs 2-3 yr pantry; fresh rosemary: refrigerate, 1-2 wk",
        "note": "Dried = shelf-stable; fresh = not."
    },
    "SAGE": {
        "class": "method_dependent",
        "source": "USDA-FK; CLEMSON: dried herbs 2-3 yr pantry; fresh sage: refrigerate, 1-2 wk",
        "note": "Dried = shelf-stable; fresh = not."
    },

    # ── fresh meat / poultry / seafood ──────────────────────────────────
    "BEEF": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh beef 3-5 d refrigerated; USDA-SSC: low-acid canned beef 2-5 yr pantry",
        "note": "Fresh = not shelf-stable; canned = shelf-stable."
    },
    "CHICKEN": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh chicken 1-2 d refrigerated; USDA-SSC: low-acid canned chicken 2-5 yr pantry",
        "note": "Fresh = not shelf-stable; canned = shelf-stable."
    },
    "LAMB": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: fresh lamb roasts/chops 3-5 d refrigerated; CLEMSON: fresh lamb 3-5 d refrigerated",
        "note": "Fresh lamb — requires refrigeration. Not shelf-stable in common form."
    },
    "PORK": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh pork 3-5 d refrigerated; USDA-SSC: low-acid canned pork 2-5 yr pantry",
        "note": "Fresh = not; canned = shelf-stable."
    },
    "VEAL": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: fresh veal steaks/chops 3-5 d refrigerated (same pattern as beef per FoodKeeper)",
        "note": "Fresh veal — requires refrigeration. Not shelf-stable."
    },
    "GROUND BEEF": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: ground beef 1-2 d refrigerated; CLEMSON: ground meat 1-2 d refrigerated, 3-4 mo frozen",
        "note": "Fresh ground beef — requires refrigeration. Not shelf-stable."
    },
    "GROUND PORK": {
        "class": "not_shelf_stable",
        "source": "USDA-FK: ground meat 1-2 d refrigerated; follows ground beef pattern per USDA",
        "note": "Fresh ground pork — requires refrigeration. Not shelf-stable."
    },
    "SAUSAGE": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh sausage 1-2 d refrigerated; USDA-FK: dry-cured sausage/salami shelf-stable; USDA-SSC: canned 2-5 yr",
        "note": "Fresh/raw = not; dry-cured = shelf-stable; canned = shelf-stable."
    },
    "BACON": {
        "class": "method_dependent",
        "source": "USDA-FK: shelf-stable fully-cooked bacon until use-by date at room temp (below 85°F); raw bacon = refrigerated 1 wk per USDA-FSIS",
        "note": "Fully cooked/shelf-stable bacon = shelf-stable (vacuum sealed); raw = not."
    },
    "HAM HOCK": {
        "class": "method_dependent",
        "source": "USDA-FK: smoked/cured ham = shelf-stable canned 6-9 mo pantry; fresh ham = 3-5 d refrigerated",
        "note": "Smoked/cured = shelf-stable; fresh = not."
    },
    "PANCETTA": {
        "class": "method_dependent",
        "source": "COMM: cured pancetta (unsmoked Italian bacon) similar to bacon per USDA-FK pattern; cured meats shelf-stable unopened",
        "note": "Cured = shelf-stable (unopened); fresh = not."
    },
    "PROSCIUTTO": {
        "class": "method_dependent",
        "source": "USDA-FK: dry-cured prosciutto (Parma/Serrano type) 2-3 mo refrigerated after cut; USDA-FSIS: dry-cured ham is non-TCS at room temp when whole, aw <0.85",
        "note": "Whole dry-cured prosciutto = shelf-stable (low water activity); sliced = refrigerate. Fresh = not."
    },
    "SALAMI": {
        "class": "method_dependent",
        "source": "USDA-FK: dry-cured salami shelf-stable; USDA-FSIS: dry fermented sausages non-TCS when aw <0.85; fresh = refrigerate per FoodKeeper",
        "note": "Dry-cured = shelf-stable; fresh/soft = not."
    },

    # ── shellfish / seafood ────────────────────────────────────────────
    "CLAMS": {
        "class": "method_dependent",
        "source": "USDA-FK: live clams 5-10 d refrigerated; USDA-SSC: low-acid canned clams 2-5 yr pantry",
        "note": "Fresh = not; canned = shelf-stable."
    },
    "SHRIMP": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh shrimp 1-3 d refrigerated; USDA-SSC: low-acid canned shrimp 2-5 yr pantry; COMM: dried shrimp shelf-stable",
        "note": "Fresh/frozen = not; canned/dried = shelf-stable."
    },
    "TUNA": {
        "class": "method_dependent",
        "source": "USDA-FK: canned tuna 3-5 yr pantry; USDA-FK: fresh tuna 1-3 d refrigerated; USDA-SSC: low-acid canned fish 2-5 yr",
        "note": "Canned = shelf-stable; fresh = not."
    },

    # ── dairy ───────────────────────────────────────────────────────────
    "MILK": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: fresh milk 5-7 d refrigerated; USDA-FK: milk 1 wk refrigerated; UHT shelf-stable milk exists but is a distinct product",
        "note": "Fresh milk — requires refrigeration. UHT/aseptic milk is shelf-stable (different product). Not shelf-stable in standard form."
    },
    "BUTTERMILK": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: buttermilk 1-2 wk refrigerated; USDA-FK: buttermilk 7-14 d refrigerated",
        "note": "Requires refrigeration — not shelf-stable."
    },
    "CHEDDAR": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: hard natural cheese (cheddar) refrigerate 2-3 mo; USDA-FQ: cheddar requires refrigeration; FDA-FC: cheddar is TCS",
        "note": "Requires refrigeration — not shelf-stable (unlike Parmesan, cheddar moisture permits spoilage at room temp)."
    },
    "CHEESE": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: all cheese refrigerate between 35-40°F; USDA-FK: most cheese varieties require refrigeration",
        "note": "Generic cheese — requires refrigeration. Some hard cheeses (Parmesan) are exceptions. Not shelf-stable as a category."
    },
    "MASCARPONE": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: cream cheese pattern — refrigerate; USDA-FK: fresh soft cheese 5-7 d refrigerated",
        "note": "Fresh, high-moisture cheese — requires refrigeration. Not shelf-stable."
    },
    "MOZZARELLA": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: semi-soft cheese (mozzarella) refrigerate; USDA-FK: fresh mozzarella 5-7 d refrigerated",
        "note": "Fresh, high-moisture cheese — requires refrigeration. Not shelf-stable."
    },
    "PECORINO": {
        "class": "method_dependent",
        "source": "USDA-FQ: hard cheese (Romano/Pecorino) same pattern as Parmesan — non-TCS when whole below 86°F per FDA-FC; grated = refrigerate",
        "note": "Whole wheel/wedge = shelf-stable (non-TCS per FDA Food Code, same as Parmesan); grated = not."
    },
    "PROVOLONE": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: semi-soft cheese (provolone) refrigerate; USDA-FK: provolone 2-3 mo refrigerated; FDA-FC: semi-soft cheese is TCS",
        "note": "Semi-soft cheese — requires refrigeration. Not shelf-stable."
    },
    "RICOTTA": {
        "class": "not_shelf_stable",
        "source": "CLEMSON: fresh ricotta 5-7 d refrigerated; USDA-FK: fresh soft cheese 5-7 d refrigerated",
        "note": "Fresh cheese, high moisture — requires refrigeration. Not shelf-stable."
    },

    # ── grains / pasta / bread ──────────────────────────────────────────
    "PASTA": {
        "class": "shelf_stable",
        "source": "CLEMSON: dried pasta 1-2 yr pantry; USDA-FK: dried pasta shelf-stable",
        "note": "Dried pasta — shelf-stable in sealed container. Fresh pasta = not shelf-stable."
    },
    "BREAD": {
        "class": "shelf_stable",
        "source": "CLEMSON: bread 3-7 d at room temp; USDA-FK: bread 3-7 d pantry; refrigeration promotes staling",
        "note": "Fresh bread — shelf-stable for days at room temp. Stales faster in fridge."
    },
    "BREADCRUMBS": {
        "class": "shelf_stable",
        "source": "CLEMSON: bread crumbs 4 mo pantry; USDA-FK: dried bread products shelf-stable",
        "note": "Dried breadcrumbs — shelf-stable."
    },
    "BUN": {
        "class": "shelf_stable",
        "source": "CLEMSON: bread/rolls 3-7 d at room temp; follows bread storage pattern per USDA-FK",
        "note": "Baked bun — shelf-stable for days at room temp."
    },
    "BASMATI RICE": {
        "class": "shelf_stable",
        "source": "USDA-SSC: white rice 2 yr pantry; CLEMSON: white rice 1 yr pantry; basmati is a white rice variety",
        "note": "Dried grain — shelf-stable (same as white rice)."
    },
    "GRITS": {
        "class": "shelf_stable",
        "source": "CLEMSON: hominy grits 12 mo pantry; USDA-FK: dry cereal/grain products shelf-stable",
        "note": "Dried ground grain — shelf-stable."
    },
    "POLENTA": {
        "class": "method_dependent",
        "source": "CLEMSON: cornmeal 12 mo pantry (polenta = coarsely ground cornmeal); USDA-FK: refrigerate prepared polenta",
        "note": "Dry (uncooked) = shelf-stable; prepared/refrigerated tube = not."
    },
    "RICE NOODLES": {
        "class": "shelf_stable",
        "source": "CLEMSON: dried pasta/noodles 1-2 yr pantry; COMM: dried rice noodles shelf-stable same pattern as pasta",
        "note": "Dried rice noodles — shelf-stable."
    },
    "RICE PAPER": {
        "class": "shelf_stable",
        "source": "COMM: dried rice paper wrappers shelf-stable in sealed package; follows dried grain product pattern per CLEMSON",
        "note": "Dried rice paper — shelf-stable."
    },
    "VERMICELLI NOODLES": {
        "class": "shelf_stable",
        "source": "CLEMSON: dried pasta 1-2 yr pantry; vermicelli is a dried noodle/pasta form",
        "note": "Dried noodles — shelf-stable."
    },
    "TORTILLAS": {
        "class": "method_dependent",
        "source": "USDA-FK: corn tortillas 1-3 wk pantry; flour tortillas 1-2 wk pantry; USDA-FK: refrigerate after opening",
        "note": "Corn/flour tortillas = shelf-stable for weeks at room temp (lower moisture). Refrigerate after opening for extended life."
    },
    "LADYFINGERS": {
        "class": "shelf_stable",
        "source": "CLEMSON: baked cookies 4-6 mo pantry; COMM: ladyfingers (dry baked biscuit) follow cookie storage pattern",
        "note": "Dry baked biscuit — shelf-stable for weeks-months in sealed container."
    },

    # ── nuts / seeds ────────────────────────────────────────────────────
    "PEANUTS": {
        "class": "shelf_stable",
        "source": "CLEMSON: unshelled nuts 6-12 mo pantry; USDA-FK: peanuts shelf-stable in cool pantry",
        "note": "Dried nuts — shelf-stable in cool pantry. Shelled = shorter."
    },
    "PEAS": {
        "class": "method_dependent",
        "source": "CLEMSON: fresh peas 3-5 d refrigerated; CLEMSON: dried peas 1 yr pantry; USDA-SSC: low-acid canned peas 2-5 yr pantry",
        "note": "Fresh = not; dried/canned = shelf-stable."
    },
    "PECANS": {
        "class": "shelf_stable",
        "source": "CLEMSON: unshelled nuts 6-12 mo pantry; follows nut storage pattern",
        "note": "Dried nuts — shelf-stable in cool pantry."
    },
    "PINE NUTS": {
        "class": "shelf_stable",
        "source": "CLEMSON: unshelled nuts 6-12 mo pantry; follows nut storage pattern for shelf stability",
        "note": "Dried pine nuts — shelf-stable in cool pantry."
    },
    "PISTACHIOS": {
        "class": "shelf_stable",
        "source": "CLEMSON: unshelled nuts 6-12 mo pantry; follows nut storage pattern",
        "note": "Dried nuts — shelf-stable in cool, dry pantry."
    },

    # ── condiments / oils / vinegars ────────────────────────────────────
    "BALSAMIC VINEGAR": {
        "class": "shelf_stable",
        "source": "CLEMSON: vinegar 30 mo pantry; USDA-SS: bottled condiments shelf-stable",
        "note": "Acetic acid preserves — shelf-stable."
    },
    "KETCHUP": {
        "class": "shelf_stable",
        "source": "CLEMSON: catsup/ketchup 1 yr unopened pantry; USDA-FK: ketchup 1 yr unopened pantry",
        "note": "Bottled condiment — shelf-stable unopened; refrigerate after opening."
    },
    "OLIVES": {
        "class": "method_dependent",
        "source": "USDA-SSC: high-acid canned/brined olives 12-18 mo pantry; CLEMSON: pickled items shelf-stable; fresh olives = inedible without curing",
        "note": "Brined/canned = shelf-stable; fresh = not (requires curing)."
    },
    "PEPPERONCINI": {
        "class": "shelf_stable",
        "source": "USDA-SSC: pickled/brined vegetables shelf-stable; CLEMSON: pickles 12-18 mo pantry",
        "note": "Pickled in brine/vinegar — shelf-stable."
    },
    "RED PEPPER FLAKES": {
        "class": "shelf_stable",
        "source": "USDA-FK; CLEMSON: ground spices/dried herbs 2-3 yr pantry",
        "note": "Dried crushed chile — shelf-stable."
    },
    "GARLIC POWDER": {
        "class": "shelf_stable",
        "source": "USDA-FK; CLEMSON: ground spices 2-3 yr pantry",
        "note": "Dried ground garlic — shelf-stable."
    },

    # ── curry pastes ────────────────────────────────────────────────────
    "GREEN CURRY PASTE": {
        "class": "method_dependent",
        "source": "COMM: commercial jarred/canned curry paste shelf-stable unopened (follows canned condiment pattern per USDA-SSC); fresh/house-made = refrigerate",
        "note": "Jarred/canned (unopened) = shelf-stable; fresh/house-made = not."
    },
    "PANANG CURRY PASTE": {
        "class": "method_dependent",
        "source": "COMM: commercial jarred/canned curry paste shelf-stable unopened (same pattern as green curry paste per USDA-SSC)",
        "note": "Jarred/canned (unopened) = shelf-stable; fresh/house-made = not."
    },
    "RED CURRY PASTE": {
        "class": "method_dependent",
        "source": "COMM: commercial jarred/canned curry paste shelf-stable unopened (same pattern as green curry paste per USDA-SSC)",
        "note": "Jarred/canned (unopened) = shelf-stable; fresh/house-made = not."
    },

    # ── beans / legumes ─────────────────────────────────────────────────
    "BEANS": {
        "class": "method_dependent",
        "source": "CLEMSON: dried beans 1 yr pantry; USDA-SSC: low-acid canned beans 2-5 yr pantry; fresh beans = refrigerate per CLEMSON",
        "note": "Dried or canned = shelf-stable; fresh green beans = not."
    },

    # ── sweeteners / baking ─────────────────────────────────────────────
    "BROWN SUGAR": {
        "class": "shelf_stable",
        "source": "CLEMSON: brown sugar 18 mo pantry; CLEMSON: sugar indefinitely shelf-stable",
        "note": "Shelf-stable in airtight container (may harden but remains safe)."
    },
    "SUGAR": {
        "class": "shelf_stable",
        "source": "CLEMSON: granulated sugar indefinitely; brown/powdered 18 mo pantry",
        "note": "Indefinitely shelf-stable in airtight container."
    },
    "CORN SYRUP": {
        "class": "shelf_stable",
        "source": "CLEMSON: syrups 1 yr pantry; follows honey/syrup storage pattern per USDA-FK",
        "note": "Shelf-stable — high sugar content prevents spoilage."
    },
    "COCOA": {
        "class": "shelf_stable",
        "source": "CLEMSON: cocoa powder 18 mo pantry; CLEMSON: chocolate products 2 yr pantry",
        "note": "Dry cocoa powder — shelf-stable."
    },
    "COFFEE": {
        "class": "shelf_stable",
        "source": "CLEMSON: canned coffee 12 mo pantry; USDA-FK: coffee shelf-stable unopened",
        "note": "Dried coffee beans/ground — shelf-stable in sealed container."
    },
    "FLOUR": {
        "class": "shelf_stable",
        "source": "CLEMSON: white flour 10-15 mo pantry; CLEMSON: all-purpose flour 1 yr pantry at 70°F",
        "note": "White/all-purpose flour — shelf-stable in airtight container. Whole wheat = shorter (3 mo pantry)."
    },
    "VANILLA": {
        "class": "shelf_stable",
        "source": "CLEMSON: vanilla extract shelf-stable; USDA-SS: bottled extracts shelf-stable; high alcohol content",
        "note": "Vanilla extract — shelf-stable (alcohol preserves). Whole beans also shelf-stable."
    },

    # ── wines / alcohol (new) ───────────────────────────────────────────
    "MARSALA": {
        "class": "shelf_stable",
        "source": "USDA-SS: bottled beverages shelf-stable; fortified wine follows same wine storage pattern",
        "note": "Bottled fortified wine — shelf-stable (sealed, unopened)."
    },

    # ── tomato products ─────────────────────────────────────────────────
    "TOMATO SAUCE": {
        "class": "method_dependent",
        "source": "USDA-SSC: high-acid canned tomato products 12-18 mo pantry; fresh = refrigerate per USDA-FK",
        "note": "Canned/jarred = shelf-stable; opened = refrigerate; fresh = not."
    },

    # ── eggs ────────────────────────────────────────────────────────────
    "EGG": {
        "class": "method_dependent",
        "source": "USDA-FK: fresh eggs 3-5 wk refrigerated; CLEMSON: dried egg powder 12 mo pantry; USDA-FK: fresh eggs room temp >2 h discard",
        "note": "Fresh eggs = not shelf-stable (refrigerate). Dried/powdered eggs = shelf-stable."
    },
}


def parse_ingredients(path: Path) -> list[str]:
    """Read ingredient list, one per line, skipping comments and blanks."""
    ingredients = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            ingredients.append(stripped)
    return ingredients


# ── Alias map: pool snake_case → canonical key ──────────────────────────
ALIAS_MAP = {
    "BLACK PEPPER": "PEPPER",
    "BLACK_PEPPER": "PEPPER",
    "SEA SALT": "SEA SALT",  # identity
    "SALT": "SEA SALT",
    "COCONUT MILK": "COCONUT MILK",
        "COCONUT_MILK": "COCONUT MILK",
        "GARAM MASALA": "GARAM MASALA",
        "GARAM_MASALA": "GARAM MASALA",
        "THAI BASIL": "THAI BASIL",
        "THAI_BASIL": "THAI BASIL",
        "WHITE WINE": "WHITE WINE",
        "WHITE_WINE": "WHITE WINE",
        "OLIVE OIL": "OLIVE OIL",
        "OLIVE_OIL": "OLIVE OIL",
        "SOY SAUCE": "SOY SAUCE",
        "SOY_SAUCE": "SOY SAUCE",
        "FISH SAUCE": "FISH SAUCE",
        "FISH_SAUCE": "FISH SAUCE",
        "CHILE PEPPERS": "CHILE PEPPERS",
        "CHILE_PEPPERS": "CHILE PEPPERS",
    "LEMONGRASS": "LEMONGRASS",
    "GALANGAL": "GALANGAL",
    "EGGS": "EGG",
}


def _normalise(name: str) -> str:
    """Normalise pool name → canonical CLASSIFICATION key."""
    raw = name.strip().upper()
    # Try direct match first
    if raw in CLASSIFICATION:
        return raw
    # Try alias map
    if raw in ALIAS_MAP:
        return ALIAS_MAP[raw]
    # Replace underscores with spaces and try again
    spaced = raw.replace("_", " ")
    if spaced in CLASSIFICATION:
        return spaced
    if spaced in ALIAS_MAP:
        return ALIAS_MAP[spaced]
    return raw  # will hit fallback


def classify_ingredient(name: str) -> dict:
    """Return classification dict for a single ingredient name.

    Falls back to 'not established' if unmatched.
    """
    canonical = _normalise(name)
    if canonical in CLASSIFICATION:
        entry = CLASSIFICATION[canonical]
        return {
            "ingredient": name,
            "class": entry["class"],
            "source": entry["source"],
            "note": entry["note"],
        }
    # Not found — this would only happen for ingredients not in the seed list
    # (T1.3b may add more)
    return {
        "ingredient": name,
        "class": "not_established",
        "source": "not_established",
        "note": f"No classification established for '{name}' by standard food-safety authorities.",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Classify ingredients by shelf stability."
    )
    parser.add_argument(
        "--in", dest="input_path", required=True,
        help="Path to ingredient list (one per line, # comments skip)."
    )
    parser.add_argument(
        "--out", dest="output_path", required=True,
        help="Path to write JSON output."
    )
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    ingredients = parse_ingredients(input_path)
    results = []
    counts = {"shelf_stable": 0, "not_shelf_stable": 0, "method_dependent": 0, "not_established": 0}

    for name in ingredients:
        result = classify_ingredient(name)
        results.append(result)
        counts[result["class"]] += 1

    # Build output
    output = {
        "meta": {
            "tool": "tools/shelf_stability.py",
            "input": str(input_path),
            "ingredient_count": len(ingredients),
            "counts": counts,
        },
        "results": results,
    }

    # Write JSON
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── stdout summary ──────────────────────────────────────────────────
    print(f"Ingredients classified: {len(ingredients)}")
    print(f"  shelf_stable:      {counts['shelf_stable']}")
    print(f"  not_shelf_stable:  {counts['not_shelf_stable']}")
    print(f"  method_dependent:  {counts['method_dependent']}")
    print(f"  not_established:   {counts['not_established']}")
    print()

    md_list = [r["ingredient"] for r in results if r["class"] == "method_dependent"]
    print(f"Method-dependent ingredients ({len(md_list)}):")
    for name in sorted(md_list):
        # Print with the note
        r = classify_ingredient(name)
        print(f"  {name} — {r['note']}")

    print(f"\nWritten to: {output_path.resolve()}")


if __name__ == "__main__":
    main()