#!/usr/bin/env python3
"""
01_fetch_data.py — Download tertiary enrollment GPI from the World Bank API.

Usage:
    python scripts/01_fetch_data.py

Output:
    data/gpi_tertiary_enrollment_raw.csv
    data/gpi_tertiary_enrollment.csv  (cleaned, with region/income/pop metadata)

Notes:
    The World Bank API (v2) is free and requires no authentication.
    Indicator: SE.ENR.TERT.FM.ZS (School enrollment, tertiary, gender parity index)
    We pull the most recent non-null observation per country.

    Region, income group, and population metadata come from the API's country
    endpoint. Population is approximate and taken from the most recent year
    available (usually 2023).

    If the API is down or rate-limited, the repo ships a snapshot in
    data/gpi_tertiary_enrollment.csv so the analysis is always reproducible.
"""

import csv
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError

API_BASE = "https://api.worldbank.org/v2"
INDICATOR = "SE.ENR.TERT.FM.ZS"
POP_INDICATOR = "SP.POP.TOTL"


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


def fetch_countries():
    """Fetch country metadata (region, income group)."""
    url = f"{API_BASE}/country?format=json&per_page=500"
    result = api_get(url)
    countries = {}
    for c in result[1]:
        countries[c["id"]] = {
            "name": c["name"],
            "region": c["region"]["value"],
            "income_group": c["incomeLevel"]["value"],
            "iso3": c["id"],
        }
    return countries


def main():
    print("Fetching GPI data from World Bank API...")
    try:
        gpi_data = fetch_indicator(INDICATOR)
    except (URLError, Exception) as e:
        print(f"Error fetching GPI data: {e}")
        print("Use the shipped data/gpi_tertiary_enrollment.csv instead.")
        sys.exit(1)

    print(f"  Got {len(gpi_data)} records")

    print("Fetching population data...")
    pop_data = fetch_indicator(POP_INDICATOR)
    pop_map = {}
    for r in pop_data:
        if r["value"] is not None:
            iso3 = r.get("countryiso3code") or r["country"]["id"]
            pop_map[iso3] = r["value"] / 1e6

    print("Fetching country metadata...")
    countries = fetch_countries()

    # Write raw
    with open("data/gpi_tertiary_enrollment_raw.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iso3", "country", "year", "gpi"])
        for r in sorted(gpi_data, key=lambda x: x.get("countryiso3code") or x["country"]["id"]):
            iso3 = r.get("countryiso3code") or r["country"]["id"]
            w.writerow([
                iso3,
                r["country"]["value"],
                r["date"],
                r["value"] if r["value"] is not None else "",
            ])
    print(f"  Wrote data/gpi_tertiary_enrollment_raw.csv")

    # Write cleaned
    rows = []
    for r in gpi_data:
        iso3 = r.get("countryiso3code") or r["country"]["id"]
        meta = countries.get(iso3, {})
        region = meta.get("region", "")
        if region in ("", "Aggregates"):
            continue
        rows.append({
            "economy": r["country"]["value"],
            "year": r["date"],
            "iso3": iso3,
            "gpi": r["value"] if r["value"] is not None else "",
            "region": region,
            "income_group": meta.get("income_group", ""),
            "pop_millions": f'{pop_map.get(iso3, ""):.2f}' if iso3 in pop_map else "",
        })

    rows.sort(key=lambda x: x["economy"])

    with open("data/gpi_tertiary_enrollment.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "economy", "year", "iso3", "gpi", "region", "income_group", "pop_millions"
        ])
        w.writeheader()
        w.writerows(rows)

    n_with_gpi = sum(1 for r in rows if r["gpi"] != "")
    print(f"  Wrote data/gpi_tertiary_enrollment.csv ({len(rows)} countries, {n_with_gpi} with GPI)")
    print("Done.")


if __name__ == "__main__":
    main()
