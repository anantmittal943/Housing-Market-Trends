# -*- coding: utf-8 -*-
"""
generate_dataset.py
-------------------
Generates a synthetic King County-style housing dataset with 21,609 rows.
Run this script once to produce:   data/housing_data.csv

Usage:
    python generate_dataset.py

The CSV is then imported directly into Tableau Desktop / Tableau Public.
"""

import os
import random
import math
import csv
from datetime import date, timedelta

# ── Reproducible output ──────────────────────────────────────────────────────
random.seed(42)

# ── Constants ────────────────────────────────────────────────────────────────
NUM_ROWS      = 21_609
OUTPUT_DIR    = "data"
OUTPUT_FILE   = os.path.join(OUTPUT_DIR, "housing_data.csv")

# King County, WA approximate bounding box
LAT_MIN, LAT_MAX = 47.15, 47.78
LON_MIN, LON_MAX = -122.52, -121.31

ZIPCODES = [
    98001, 98002, 98003, 98004, 98005, 98006, 98007, 98008,
    98010, 98011, 98014, 98019, 98022, 98023, 98024, 98027,
    98028, 98029, 98030, 98031, 98032, 98033, 98034, 98038,
    98039, 98040, 98042, 98045, 98047, 98050, 98051, 98052,
    98053, 98055, 98056, 98057, 98058, 98059, 98065, 98068,
    98070, 98072, 98074, 98075, 98077, 98092, 98102, 98103,
    98105, 98106, 98107, 98108, 98109, 98112, 98115, 98116,
    98117, 98118, 98119, 98122, 98125, 98126, 98133, 98136,
    98144, 98146, 98148, 98155, 98166, 98168, 98177, 98178,
    98188, 98198, 98199,
]

SALE_START = date(2014, 5, 2)
SALE_END   = date(2015, 5, 27)

# ── Helper utilities ─────────────────────────────────────────────────────────

def rand_date(start: date, end: date) -> str:
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).strftime("%Y%m%dT000000")


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def normal(mu: float, sigma: float, lo: float = None, hi: float = None) -> float:
    """Box-Muller normal sample, optionally clamped."""
    while True:
        u1, u2 = random.random(), random.random()
        z = math.sqrt(-2 * math.log(u1 + 1e-12)) * math.cos(2 * math.pi * u2)
        v = mu + sigma * z
        if (lo is None or v >= lo) and (hi is None or v <= hi):
            return v


def weighted_choice(choices, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for c, w in zip(choices, weights):
        cumulative += w
        if r <= cumulative:
            return c
    return choices[-1]


# ── Price model ──────────────────────────────────────────────────────────────

def compute_price(sqft_living, bedrooms, bathrooms, floors, waterfront,
                  view, condition, grade, yr_built, yr_renovated,
                  sqft_basement, lat) -> int:
    """
    Deterministic price model with random noise.
    Mimics real housing price drivers:
      - Size (sqft_living) is the strongest predictor
      - Grade and location (lat) add premium/discount
      - Waterfront is a large multiplier
      - Renovation reduces age penalty
    """
    base = sqft_living * 150.0

    # Grade premium  (1-13 scale, avg ~7)
    grade_mult = 0.5 + (grade / 7.0) * 1.1
    base *= grade_mult

    # Condition (1-5)
    base *= (0.85 + condition * 0.04)

    # View (0-4)
    base *= (1 + view * 0.08)

    # Waterfront
    if waterfront:
        base *= 1.65

    # Age penalty
    current_year = 2015
    effective_age = current_year - (yr_renovated if yr_renovated > 0 else yr_built)
    effective_age = max(0, effective_age)
    base *= max(0.6, 1 - effective_age * 0.003)

    # Latitude premium (closer to Seattle core ~ lat 47.6)
    lat_delta = abs(lat - 47.62)
    base *= max(0.75, 1 - lat_delta * 0.8)

    # Basement adds value
    base += sqft_basement * 55

    # Bedrooms / bathrooms minor effect
    base += bedrooms * 3_000
    base += bathrooms * 8_000

    # Random noise ±18 %
    noise = random.gauss(1.0, 0.18)
    price = int(base * noise)

    # Clamp to realistic range
    return clamp(price, 75_000, 5_500_000)


# ── Main generation ───────────────────────────────────────────────────────────

def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fieldnames = [
        "id", "date", "price",
        "bedrooms", "bathrooms", "sqft_living", "sqft_lot",
        "floors", "waterfront", "view", "condition", "grade",
        "sqft_above", "sqft_basement",
        "yr_built", "yr_renovated",
        "zipcode", "lat", "long",
        "sqft_living15", "sqft_lot15",
        # Derived / extra columns (31 total features)
        "house_age", "years_since_renovation", "renovated",
        "price_per_sqft", "total_rooms", "basement_flag",
        "bed_bath_ratio", "grade_category", "condition_label",
        "size_category",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        used_ids = set()

        for i in range(NUM_ROWS):
            # ── Unique ID ──────────────────────────────────────────────────
            while True:
                house_id = random.randint(1_000_000, 9_999_999_999)
                if house_id not in used_ids:
                    used_ids.add(house_id)
                    break

            # ── Location ───────────────────────────────────────────────────
            lat  = round(random.uniform(LAT_MIN, LAT_MAX), 6)
            lon  = round(random.uniform(LON_MIN, LON_MAX), 6)
            zipcode = random.choice(ZIPCODES)

            # ── Construction ───────────────────────────────────────────────
            yr_built = random.randint(1900, 2014)
            renovated_flag = 1 if (random.random() < 0.05 and yr_built <= 2009) else 0
            yr_renovated = random.randint(yr_built + 5, 2014) if renovated_flag else 0

            # ── Physical features ──────────────────────────────────────────
            bedrooms  = weighted_choice([1, 2, 3, 4, 5, 6, 7, 8, 9],
                                        [2, 12, 32, 28, 14, 7, 3, 1, 1])
            bathrooms = round(weighted_choice(
                [1.0, 1.5, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5, 4.0, 4.5, 5.0],
                [8,   10,  22,  10,   18,  8,    10,  7,   4,   2,   1]), 2)
            floors    = weighted_choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
                                        [44,  8,   34,  4,   8,   2])

            sqft_living  = int(normal(2080, 920, lo=370, hi=13_540))
            sqft_lot     = int(normal(15_100, 41_420, lo=520, hi=1_651_359))
            sqft_above   = int(sqft_living * random.uniform(0.55, 1.0))
            sqft_basement = sqft_living - sqft_above

            sqft_living15 = int(sqft_living * random.uniform(0.75, 1.30))
            sqft_lot15    = int(sqft_lot    * random.uniform(0.80, 1.25))

            # ── Quality / condition ────────────────────────────────────────
            grade     = weighted_choice(range(1, 14),
                                        [0.1, 0.2, 0.6, 1.5, 3, 8, 20, 28, 22, 11, 4, 1, 0.5])
            condition = weighted_choice([1, 2, 3, 4, 5],
                                        [1, 2, 57, 26, 14])
            waterfront = 1 if random.random() < 0.007 else 0
            view       = weighted_choice([0, 1, 2, 3, 4], [90, 3, 4, 2, 1])

            # ── Price ──────────────────────────────────────────────────────
            price = compute_price(sqft_living, bedrooms, bathrooms, floors,
                                  waterfront, view, condition, grade,
                                  yr_built, yr_renovated, sqft_basement, lat)

            # ── Derived columns ────────────────────────────────────────────
            house_age = 2015 - yr_built
            years_since_reno = (2015 - yr_renovated) if yr_renovated > 0 else house_age
            price_per_sqft   = round(price / sqft_living, 2)
            total_rooms      = bedrooms + int(bathrooms)
            bed_bath_ratio   = round(bedrooms / bathrooms, 2) if bathrooms > 0 else 0

            if grade <= 4:
                grade_cat = "Low"
            elif grade <= 7:
                grade_cat = "Average"
            elif grade <= 10:
                grade_cat = "Good"
            else:
                grade_cat = "Luxury"

            cond_labels = {1: "Poor", 2: "Fair", 3: "Average", 4: "Good", 5: "Excellent"}
            cond_label = cond_labels[condition]

            if sqft_living < 1000:
                size_cat = "Small"
            elif sqft_living < 2000:
                size_cat = "Medium"
            elif sqft_living < 4000:
                size_cat = "Large"
            else:
                size_cat = "Very Large"

            writer.writerow({
                "id":                  house_id,
                "date":                rand_date(SALE_START, SALE_END),
                "price":               price,
                "bedrooms":            bedrooms,
                "bathrooms":           bathrooms,
                "sqft_living":         sqft_living,
                "sqft_lot":            sqft_lot,
                "floors":              floors,
                "waterfront":          waterfront,
                "view":                view,
                "condition":           condition,
                "grade":               grade,
                "sqft_above":          sqft_above,
                "sqft_basement":       sqft_basement,
                "yr_built":            yr_built,
                "yr_renovated":        yr_renovated,
                "zipcode":             zipcode,
                "lat":                 lat,
                "long":                lon,
                "sqft_living15":       sqft_living15,
                "sqft_lot15":          sqft_lot15,
                "house_age":           house_age,
                "years_since_renovation": years_since_reno,
                "renovated":           renovated_flag,
                "price_per_sqft":      price_per_sqft,
                "total_rooms":         total_rooms,
                "basement_flag":       1 if sqft_basement > 0 else 0,
                "bed_bath_ratio":      bed_bath_ratio,
                "grade_category":      grade_cat,
                "condition_label":     cond_label,
                "size_category":       size_cat,
            })

            if (i + 1) % 2000 == 0:
                print(f"  Generated {i + 1:,} / {NUM_ROWS:,} rows …")

    print(f"\nDataset saved to: {OUTPUT_FILE}")
    print(f"Total rows: {NUM_ROWS:,}  |  Columns: {len(fieldnames)}")


if __name__ == "__main__":
    generate()
