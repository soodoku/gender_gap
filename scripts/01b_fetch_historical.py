#!/usr/bin/env python3
"""
01b_fetch_historical.py — Download full annual time series of tertiary enrollment GPI.

Usage:
    python scripts/01b_fetch_historical.py

Output:
    data/gpi_historical.csv — Annual GPI values for all countries (1970-present)

The World Bank API has ~168 countries with 10+ annual observations.
This script fetches the complete time series (not just most recent value).
"""

import csv
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError

API_BASE = "https://api.worldbank.org/v2"
INDICATOR = "SE.ENR.TERT.FM.ZS"


def api_get(url):
    """Fetch JSON from the World Bank API."""
    req = Request(url, headers={"User-Agent": "gpi-analysis/1.0"})
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_all_indicator_data(indicator, per_page=1000):
    """Fetch all country-level data for an indicator (all years, all countries)."""
    url = f"{API_BASE}/country/all/indicator/{indicator}?format=json&per_page={per_page}"
    pages = []
    page = 1
    while True:
        paged_url = f"{url}&page={page}"
        print(f"  Fetching page {page}...")
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
    print("Fetching full GPI time series from World Bank API...")
    try:
        all_data = fetch_all_indicator_data(INDICATOR)
    except (URLError, Exception) as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    print(f"  Got {len(all_data)} records total")

    print("Fetching country metadata...")
    countries = fetch_countries()

    country_series = {}
    for r in all_data:
        if r["value"] is None:
            continue
        iso3 = r.get("countryiso3code") or r["country"]["id"]
        meta = countries.get(iso3, {})
        region = meta.get("region", "")
        if region in ("", "Aggregates"):
            continue
        year = int(r["date"])
        gpi = r["value"]

        if iso3 not in country_series:
            country_series[iso3] = {
                "iso3": iso3,
                "economy": r["country"]["value"],
                "region": region,
                "data": {},
            }
        country_series[iso3]["data"][year] = gpi

    rows = []
    for iso3, info in country_series.items():
        data = info["data"]
        years = sorted(data.keys())
        if len(years) < 2:
            continue
        rows.append({
            "iso3": iso3,
            "economy": info["economy"],
            "region": info["region"],
            "year": years[-1],
            "gpi": data[years[-1]],
            "first_year": years[0],
            "n_obs": len(years),
            "data": data,
        })

    rows.sort(key=lambda x: x["economy"])

    with open("data/gpi_historical.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iso3", "economy", "region", "year", "gpi"])
        for row in rows:
            for year in sorted(row["data"].keys()):
                w.writerow([
                    row["iso3"],
                    row["economy"],
                    row["region"],
                    year,
                    f"{row['data'][year]:.4f}",
                ])

    n_countries = len(rows)
    total_obs = sum(r["n_obs"] for r in rows)
    n_10plus = sum(1 for r in rows if r["n_obs"] >= 10)
    n_1990 = sum(1 for r in rows if r["first_year"] <= 1990)

    print(f"\nWrote data/gpi_historical.csv")
    print(f"  Countries: {n_countries}")
    print(f"  Total observations: {total_obs}")
    print(f"  Countries with 10+ years: {n_10plus}")
    print(f"  Countries with data from 1990 or earlier: {n_1990}")
    print("Done.")


if __name__ == "__main__":
    main()
