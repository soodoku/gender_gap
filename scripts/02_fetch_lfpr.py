#!/usr/bin/env python3
"""
02_fetch_lfpr.py — Update female LFPR data from the World Bank API.

Usage:
    python scripts/02_fetch_lfpr.py

Output:
    Updates data/gpi_vs_lfpr.csv with fresh female_lfpr values

Notes:
    Indicator: SL.TLF.CACT.FE.ZS (Labor force participation rate, female, % of female population ages 15+)
    Fetches the most recent non-null observation per country.
    Preserves existing GPI, region, pop_millions, and highlight columns.
"""

import csv
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError

API_BASE = "https://api.worldbank.org/v2"
LFPR_INDICATOR = "SL.TLF.CACT.FE.ZS"
INPUT_FILE = "data/gpi_vs_lfpr.csv"


def api_get(url):
    """Fetch JSON from the World Bank API."""
    req = Request(url, headers={"User-Agent": "gpi-analysis/1.0"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_indicator(indicator, per_page=500):
    """Fetch all country-level data for an indicator, most recent value."""
    url = (
        f"{API_BASE}/country/all/indicator/{indicator}"
        f"?format=json&per_page={per_page}&mrnev=1"
    )
    pages = []
    page = 1
    while True:
        paged_url = f"{url}&page={page}"
        result = api_get(paged_url)
        meta, data = result[0], result[1]
        if data:
            pages.extend(data)
        if page >= meta.get("pages", 1):
            break
        page += 1
    return pages


def main():
    print("Reading existing gpi_vs_lfpr.csv...")
    fieldnames = ["iso3", "economy", "gpi", "female_lfpr", "region", "pop_millions", "highlight"]
    with open(INPUT_FILE, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  Found {len(rows)} countries")

    print("Fetching female LFPR data from World Bank API...")
    try:
        lfpr_data = fetch_indicator(LFPR_INDICATOR)
    except (URLError, Exception) as e:
        print(f"Error fetching LFPR data: {e}")
        sys.exit(1)

    lfpr_map = {}
    for r in lfpr_data:
        iso3 = r.get("countryiso3code") or r["country"]["id"]
        if r["value"] is not None:
            lfpr_map[iso3] = round(r["value"])

    print(f"  Got LFPR for {len(lfpr_map)} countries")

    updated = 0
    missing = []
    for row in rows:
        iso3 = row["iso3"]
        if iso3 in lfpr_map:
            row["female_lfpr"] = lfpr_map[iso3]
            updated += 1
        else:
            missing.append(iso3)

    if missing:
        print(f"  Warning: No LFPR data for {len(missing)} countries: {', '.join(missing)}")

    with open(INPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Updated {updated} LFPR values in {INPUT_FILE}")
    print("Done.")


if __name__ == "__main__":
    main()
