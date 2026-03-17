#!/usr/bin/env python3
"""
analyze_gpi.py — Analysis of Tertiary Enrollment Gender Parity Index (GPI)
Source: World Bank Education Statistics (SE.ENR.TERT.FM.ZS)
"""

import csv
import statistics
import json
from collections import defaultdict

# ── Load data ────────────────────────────────────────────────────────────────

def load_data(path="data/gpi_tertiary_enrollment.csv"):
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            gpi_str = r["gpi"].strip()
            if gpi_str:
                r["gpi"] = float(gpi_str)
                r["pop_millions"] = float(r["pop_millions"])
                rows.append(r)
    return rows


# ── Summary statistics ───────────────────────────────────────────────────────

def summary_stats(data):
    gpis = [r["gpi"] for r in data]
    pops = [r["pop_millions"] for r in data]
    
    # Population-weighted mean
    pw_mean = sum(g * p for g, p in zip(gpis, pops)) / sum(pops)
    
    # Population-weighted median (interpolated)
    sorted_data = sorted(zip(gpis, pops), key=lambda x: x[0])
    cum_pop = 0
    half = sum(pops) / 2
    pw_median = None
    for gpi, pop in sorted_data:
        cum_pop += pop
        if cum_pop >= half:
            pw_median = gpi
            break

    n = len(gpis)
    above_parity = sum(1 for g in gpis if g > 1.0)
    below_parity = sum(1 for g in gpis if g < 1.0)
    at_parity = sum(1 for g in gpis if g == 1.0)
    
    stats = {
        "n": n,
        "mean": statistics.mean(gpis),
        "median": statistics.median(gpis),
        "stdev": statistics.stdev(gpis),
        "min": min(gpis),
        "max": max(gpis),
        "p10": sorted(gpis)[int(n * 0.10)],
        "p25": sorted(gpis)[int(n * 0.25)],
        "p75": sorted(gpis)[int(n * 0.75)],
        "p90": sorted(gpis)[int(n * 0.90)],
        "iqr": sorted(gpis)[int(n * 0.75)] - sorted(gpis)[int(n * 0.25)],
        "pop_weighted_mean": pw_mean,
        "pop_weighted_median": pw_median,
        "above_parity": above_parity,
        "below_parity": below_parity,
        "at_parity": at_parity,
        "pct_above": 100 * above_parity / n,
        "total_pop_millions": sum(pops),
        # Share of world population in female-majority-enrollment countries
        "pop_share_above": 100 * sum(p for g, p in zip(gpis, pops) if g > 1.0) / sum(pops),
    }
    return stats


# ── By region ────────────────────────────────────────────────────────────────

def by_group(data, key):
    groups = defaultdict(list)
    pops = defaultdict(list)
    for r in data:
        groups[r[key]].append(r["gpi"])
        pops[r[key]].append(r["pop_millions"])
    
    results = {}
    for grp in sorted(groups.keys()):
        g = groups[grp]
        p = pops[grp]
        pw = sum(gi * pi for gi, pi in zip(g, p)) / sum(p) if sum(p) > 0 else None
        results[grp] = {
            "n": len(g),
            "mean": statistics.mean(g),
            "median": statistics.median(g),
            "stdev": statistics.stdev(g) if len(g) > 1 else 0,
            "min": min(g),
            "max": max(g),
            "pop_weighted_mean": pw,
            "pct_above_parity": 100 * sum(1 for x in g if x > 1.0) / len(g),
        }
    return results


# ── Extremes ─────────────────────────────────────────────────────────────────

def extremes(data, n=10):
    sorted_asc = sorted(data, key=lambda r: r["gpi"])
    sorted_desc = sorted(data, key=lambda r: r["gpi"], reverse=True)
    bottom = [(r["economy"], r["gpi"], r["region"]) for r in sorted_asc[:n]]
    top = [(r["economy"], r["gpi"], r["region"]) for r in sorted_desc[:n]]
    return {"bottom_10": bottom, "top_10": top}


# ── Reversal index: female > male disparity ──────────────────────────────────

def reversal_analysis(data):
    """
    Characterize the 'reversal': where GPI > 1 by a wide margin,
    meaning women substantially outnumber men in tertiary enrollment.
    """
    above_120 = [r for r in data if r["gpi"] >= 1.20]
    above_140 = [r for r in data if r["gpi"] >= 1.40]
    above_160 = [r for r in data if r["gpi"] >= 1.60]
    
    total_pop = sum(r["pop_millions"] for r in data)
    
    return {
        "n_above_120": len(above_120),
        "pct_above_120": 100 * len(above_120) / len(data),
        "pop_above_120": sum(r["pop_millions"] for r in above_120),
        "pop_share_above_120": 100 * sum(r["pop_millions"] for r in above_120) / total_pop,
        "n_above_140": len(above_140),
        "n_above_160": len(above_160),
        "examples_above_160": [(r["economy"], r["gpi"]) for r in sorted(above_160, key=lambda x: -x["gpi"])],
    }


# ── Big-country decomposition ───────────────────────────────────────────────

def big_country_table(data, threshold=50):
    """Countries with pop > threshold (millions)."""
    big = [r for r in data if r["pop_millions"] >= threshold]
    big.sort(key=lambda r: -r["pop_millions"])
    return [(r["economy"], r["pop_millions"], r["gpi"], r["region"]) for r in big]


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    data = load_data()
    
    print("=" * 72)
    print("TERTIARY ENROLLMENT GPI — CROSS-COUNTRY ANALYSIS")
    print("Source: World Bank (SE.ENR.TERT.FM.ZS), most recent year available")
    print("=" * 72)
    
    # 1. Summary
    s = summary_stats(data)
    print(f"\n{'─' * 40}")
    print("OVERALL SUMMARY")
    print(f"{'─' * 40}")
    print(f"  N countries:             {s['n']}")
    print(f"  Unweighted mean:         {s['mean']:.3f}")
    print(f"  Median:                  {s['median']:.3f}")
    print(f"  Std dev:                 {s['stdev']:.3f}")
    print(f"  IQR:                     [{s['p25']:.3f}, {s['p75']:.3f}] (width {s['iqr']:.3f})")
    print(f"  Range:                   [{s['min']:.3f}, {s['max']:.3f}]")
    print(f"  10th / 90th percentile:  [{s['p10']:.3f}, {s['p90']:.3f}]")
    print(f"  Pop-weighted mean:       {s['pop_weighted_mean']:.3f}")
    print(f"  Pop-weighted median:     {s['pop_weighted_median']:.3f}")
    print(f"  Above parity (GPI > 1):  {s['above_parity']}/{s['n']} ({s['pct_above']:.1f}%)")
    print(f"  Pop share above parity:  {s['pop_share_above']:.1f}%")
    print(f"  Total pop covered:       {s['total_pop_millions']:.0f}M")
    
    # 2. By region
    print(f"\n{'─' * 40}")
    print("BY WORLD BANK REGION")
    print(f"{'─' * 40}")
    regions = by_group(data, "region")
    print(f"  {'Region':<35} {'N':>3} {'Mean':>6} {'Med':>6} {'PW Mean':>8} {'%>1':>6}")
    for rgn, v in sorted(regions.items(), key=lambda x: x[1]["pop_weighted_mean"]):
        print(f"  {rgn:<35} {v['n']:>3} {v['mean']:>6.3f} {v['median']:>6.3f} {v['pop_weighted_mean']:>8.3f} {v['pct_above_parity']:>5.1f}%")
    
    # 3. By income group
    print(f"\n{'─' * 40}")
    print("BY INCOME GROUP")
    print(f"{'─' * 40}")
    income = by_group(data, "income_group")
    for grp, v in sorted(income.items(), key=lambda x: x[1]["pop_weighted_mean"]):
        print(f"  {grp:<25} N={v['n']:>3}  mean={v['mean']:.3f}  pw_mean={v['pop_weighted_mean']:.3f}  %>1={v['pct_above_parity']:.1f}%")
    
    # 4. Extremes
    print(f"\n{'─' * 40}")
    print("BOTTOM 10 (male-dominated)")
    print(f"{'─' * 40}")
    ext = extremes(data)
    for name, gpi, rgn in ext["bottom_10"]:
        print(f"  {name:<35} {gpi:.3f}  ({rgn})")
    
    print(f"\n{'─' * 40}")
    print("TOP 10 (female-dominated)")
    print(f"{'─' * 40}")
    for name, gpi, rgn in ext["top_10"]:
        print(f"  {name:<35} {gpi:.3f}  ({rgn})")
    
    # 5. Reversal analysis
    print(f"\n{'─' * 40}")
    print("REVERSAL ANALYSIS (GPI substantially > 1)")
    print(f"{'─' * 40}")
    rev = reversal_analysis(data)
    print(f"  GPI >= 1.20:  {rev['n_above_120']} countries ({rev['pct_above_120']:.1f}%), pop share = {rev['pop_share_above_120']:.1f}%")
    print(f"  GPI >= 1.40:  {rev['n_above_140']} countries")
    print(f"  GPI >= 1.60:  {rev['n_above_160']} countries")
    if rev["examples_above_160"]:
        for name, gpi in rev["examples_above_160"]:
            print(f"    {name}: {gpi:.3f}")
    
    # 6. Big countries
    print(f"\n{'─' * 40}")
    print("BIG COUNTRIES (pop >= 50M)")
    print(f"{'─' * 40}")
    print(f"  {'Country':<25} {'Pop(M)':>7} {'GPI':>6} {'Region'}")
    for name, pop, gpi, rgn in big_country_table(data):
        direction = "F>M" if gpi > 1 else "M>F"
        print(f"  {name:<25} {pop:>7.0f} {gpi:>6.3f} [{direction}]  {rgn}")
    
    # 7. Export JSON for visualization
    viz_data = []
    for r in data:
        viz_data.append({
            "economy": r["economy"],
            "iso3": r["iso3"],
            "gpi": r["gpi"],
            "pop": r["pop_millions"],
            "region": r["region"],
            "income": r["income_group"],
        })
    with open("data/gpi_viz_data.json", "w") as f:
        json.dump(viz_data, f, indent=2)
    print(f"\n[Exported data/gpi_viz_data.json for visualization]")


if __name__ == "__main__":
    main()
