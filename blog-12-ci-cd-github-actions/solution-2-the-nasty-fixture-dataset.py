# Blog 12 — CI/CD for Data Pipelines with GitHub Actions
# Exercise 2: The nasty fixture dataset
# Requires: Everything here runs locally — a repo directory, `ruff`/`pytest`, and YAML files. No workspace needed.

import random

random.seed(42)

def make_fixture(n=200):
    rows = []
    regions = ["north", "south", "east", "west"]
    for i in range(n):
        r = random.random()
        rows.append({
            "order_id": f"O{i:04d}",
            # order_ref exists but is NOT the dedupe key (the trap for exercise 3's bug)
            "order_ref": f"REF-{i:04d}" if r > 0.02 else f"REF-{random.randint(0, n):04d}",
            "total": None if r < 0.05 else (-round(random.uniform(1, 100), 2) if r < 0.08
                                           else round(random.uniform(5, 500), 2)),
            "region": random.choice(regions),
            "day": f"day-{random.randint(1, 7):02d}",
            "updated_at": i,  # arrival order; late events handled below
        })
    # duplicates: same order_id, newer updated_at (late-arriving correction wins)
    for i in [3, 40, 150]:
        dup = dict(rows[i])
        dup["total"] = round((dup["total"] or 50) + 10, 2)
        dup["updated_at"] = n + i
        rows.append(dup)
    # one late event with an OLDER timestamp arriving last (sequencing matters)
    late = dict(rows[10])
    late["total"] = 999.99
    late["updated_at"] = 5
    rows.append(late)
    return rows
# --- next cell ---

def clean_orders(rows):
    """Dedupe by order_id (latest updated_at wins); quarantine null/negative totals."""
    latest = {}
    for r in rows:
        oid = r["order_id"]
        if oid not in latest or r["updated_at"] > latest[oid]["updated_at"]:
            latest[oid] = r
    cleaned, quarantined = [], []
    for r in latest.values():
        if r["total"] is None or r["total"] < 0:
            quarantined.append(r)
        else:
            cleaned.append(r)
    return cleaned, quarantined

def gold_daily_revenue(cleaned):
    """Exactly one row per (day, region)."""
    agg = {}
    for r in cleaned:
        key = (r["day"], r["region"])
        agg[key] = agg.get(key, 0) + r["total"]
    return [{"day": d, "region": g, "revenue": round(v, 2)} for (d, g), v in sorted(agg.items())]
# --- next cell ---

from src.transforms import clean_orders, gold_daily_revenue
from tests.fixtures import make_fixture

def test_dedupe_keeps_latest():
    cleaned, _ = clean_orders(make_fixture())
    ids = [r["order_id"] for r in cleaned]
    assert len(ids) == len(set(ids)), "duplicate order_ids survived"

def test_no_rows_lost_in_dedupe():
    cleaned, quarantined = clean_orders(make_fixture())
    # 200 distinct order_ids in the fixture; dedupe must not collapse distinct orders
    assert len(cleaned) + len(quarantined) == 200, "dedupe dropped distinct orders (wrong key?)"

def test_quarantine_counts():
    cleaned, quarantined = clean_orders(make_fixture())
    # seed 42 plants ~5% nulls and ~3% negatives of 200 rows
    assert len(quarantined) > 0, "expected quarantined rows, found none"
    assert all(r["total"] is None or r["total"] < 0 for r in quarantined)
    assert all(r["total"] is not None and r["total"] >= 0 for r in cleaned)

def test_late_event_does_not_win():
    cleaned, _ = clean_orders(make_fixture())
    row = next(r for r in cleaned if r["order_id"] == "O0010")
    assert row["total"] != 999.99, "late event with older timestamp overwrote newer data"

def test_gold_one_row_per_day_per_region():
    cleaned, _ = clean_orders(make_fixture())
    gold = gold_daily_revenue(cleaned)
    keys = [(g["day"], g["region"]) for g in gold]
    assert len(keys) == len(set(keys)), "gold has duplicate (day, region) rows"
# --- next cell ---

oid = r["order_ref"]  # BUG: wrong key
