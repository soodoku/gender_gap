#!/usr/bin/env python3
"""
make_figures.py — Generate publication-quality figures for the blog post.
Outputs PNGs suitable for Ghost upload.
"""

import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from collections import defaultdict
from statsmodels.nonparametric.smoothers_lowess import lowess

# ── Style ────────────────────────────────────────────────────────────────────

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#333333',
    'text.color': '#333333',
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'grid.color': '#cccccc',
    'grid.alpha': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.3,
})

FEMALE = '#e8735a'
MALE = '#4a90d9'
PARITY = '#555555'
GOLD = '#b8860b'
BG = 'white'
MENA = '#2a8a6a'

REGION_COLORS = {
    'Sub-Saharan Africa': '#4a90d9',
    'Sub-Saharan Africa ': '#4a90d9',
    'South Asia': '#9b59b6',
    'Middle East & North Africa': '#2a8a6a',
    'Middle East, North Africa, Afghanistan & Pakistan': '#2a8a6a',
    'East Asia & Pacific': '#d68910',
    'Europe & Central Asia': '#e8735a',
    'Latin America & Caribbean': '#e74c3c',
    'Latin America & Caribbean ': '#e74c3c',
    'North America': '#333333',
}

# ── Load data ────────────────────────────────────────────────────────────────

def load_current():
    rows = []
    with open('data/gpi_tertiary_enrollment.csv', 'r') as f:
        for r in csv.DictReader(f):
            if r['gpi'].strip():
                r['gpi'] = float(r['gpi'])
                r['pop'] = float(r['pop_millions'])
                rows.append(r)
    return rows

def load_historical():
    """Load historical GPI data in long format (iso3, economy, region, year, gpi)."""
    country_data = {}
    with open('data/gpi_historical.csv', 'r') as f:
        for r in csv.DictReader(f):
            iso3 = r['iso3']
            if iso3 not in country_data:
                country_data[iso3] = {
                    'iso3': iso3,
                    'economy': r['economy'],
                    'region': r['region'],
                    'ts': {},
                }
            year = int(r['year'])
            gpi = float(r['gpi'])
            country_data[iso3]['ts'][year] = gpi
    rows = []
    for iso3, info in country_data.items():
        ts = info['ts']
        if len(ts) < 2:
            continue
        years = sorted(ts.keys())
        rows.append({
            'iso3': iso3,
            'economy': info['economy'],
            'region': info['region'],
            'ts': ts,
            'latest': ts[years[-1]],
            'latest_year': years[-1],
        })
    return rows

def load_lfpr():
    rows = []
    with open('data/gpi_vs_lfpr.csv', 'r') as f:
        for r in csv.DictReader(f):
            r['gpi'] = float(r['gpi'])
            r['female_lfpr'] = float(r['female_lfpr'])
            r['pop_millions'] = float(r['pop_millions'])
            r['highlight'] = r.get('highlight', '').strip() == 'yes'
            rows.append(r)
    return rows

data = load_current()
data.sort(key=lambda r: r['gpi'])
hist = load_historical()
lfpr_data = load_lfpr()

# ── Figure 1: Distribution strip + histogram ─────────────────────────────────

fig, (ax_hist, ax_strip) = plt.subplots(
    2, 1, figsize=(10, 5), height_ratios=[3, 1],
    gridspec_kw={'hspace': 0.05}
)

gpis = [r['gpi'] for r in data]
bins = np.round(np.arange(0.3, 1.95, 0.05), 2)
colors_hist = [FEMALE if b >= 1.0 else MALE for b in bins[:-1]]
n, _, patches = ax_hist.hist(gpis, bins=bins, edgecolor='white', linewidth=0.5)
for patch, c in zip(patches, colors_hist):
    patch.set_facecolor(c); patch.set_alpha(0.8)

ax_hist.axvline(1.0, color=PARITY, linewidth=1.5, linestyle='--', alpha=0.7)
ax_hist.axvline(np.median(gpis), color=GOLD, linewidth=1.5, linestyle='-', alpha=0.9)
ax_hist.annotate('Parity', xy=(1.0, ax_hist.get_ylim()[1]*0.92), fontsize=9, color=PARITY, ha='right', xytext=(-8,0), textcoords='offset points')
ax_hist.annotate(f'Median = {np.median(gpis):.1f}', xy=(np.median(gpis), ax_hist.get_ylim()[1]*0.92), fontsize=9, color=GOLD, ha='left', xytext=(8,0), textcoords='offset points')
ax_hist.set_ylabel('Number of countries'); ax_hist.set_xlim(0.3, 1.9)
ax_hist.set_xticks([]); ax_hist.spines['bottom'].set_visible(False)
ax_hist.set_title('Distribution of Tertiary Enrollment GPI across 203 Countries', pad=12)

maxpop = max(d['pop'] for d in data)
for r in data:
    size = max(8, min(120, 8 + np.sqrt(r['pop']/maxpop)*120))
    color = FEMALE if r['gpi'] >= 1.0 else MALE
    ax_strip.scatter(r['gpi'], 0.5+np.random.uniform(-0.35,0.35), s=size, c=color, alpha=0.6, edgecolors='none', zorder=3)

ax_strip.axvline(1.0, color=PARITY, linewidth=1.5, linestyle='--', alpha=0.7)
ax_strip.set_xlim(0.3, 1.9); ax_strip.set_ylim(0, 1); ax_strip.set_yticks([])
ax_strip.set_xlabel('Gender Parity Index (GPI)')

labels = {'AFG': ('Afghanistan','right',-6,12), 'USA': ('US','left',6,-10), 'IND': ('India','left',6,10),
          'CHN': ('China','left',6,-12), 'JPN': ('Japan','right',-6,-10), 'BRA': ('Brazil','left',6,8),
          'GMB': ('Gambia','right',-6,10), 'BGD': ('Bangladesh','right',-6,-10),
          'KOR': ('S. Korea','right',-6,8), 'QAT': ('Qatar','left',6,10)}
for r in data:
    if r['iso3'] in labels:
        name, ha, dx, dy = labels[r['iso3']]
        ax_strip.annotate(name, xy=(r['gpi'], 0.5), fontsize=7, color='#333333', ha=ha, va='center',
                          xytext=(dx, dy), textcoords='offset points',
                          arrowprops=dict(arrowstyle='-', color='#999999', lw=0.5))

fig.savefig('figs/fig1_distribution.png', facecolor=BG); plt.close()

# ── Figure 2: Region horizontal bars ─────────────────────────────────────────

all_regions = sorted(set(r['region'].strip() for r in data))
region_stats = {}
for rgn in all_regions:
    rd = [r for r in data if r['region'].strip() == rgn]
    if rd:
        pop = sum(r['pop'] for r in rd)
        pw = sum(r['gpi']*r['pop'] for r in rd) / pop if pop > 0 else 0
        region_stats[rgn] = pw
regions_order = sorted(region_stats.keys(), key=lambda x: region_stats[x])

fig, ax = plt.subplots(figsize=(10, 4))
y_pos = np.arange(len(regions_order))
vals = [region_stats[r] for r in regions_order]
colors = [FEMALE if v >= 1.0 else MALE for v in vals]
ax.barh(y_pos, vals, height=0.6, color=colors, alpha=0.8, edgecolor='none')
ax.axvline(1.0, color=PARITY, linewidth=1.5, linestyle='--', alpha=0.6, zorder=0)
ax.set_yticks(y_pos); ax.set_yticklabels(regions_order, fontsize=10)
ax.set_xlabel('Population-weighted mean GPI'); ax.set_xlim(0, 1.45); ax.invert_yaxis()
for i, v in enumerate(vals):
    ax.text(v+0.015, i, f'{v:.1f}', va='center', fontsize=10, fontweight='bold', color=colors[i])
ax.annotate('Parity', xy=(1.0, -0.6), fontsize=8, color=PARITY, ha='center')
ax.set_title('Population-Weighted Mean GPI by World Bank Region', pad=12)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.savefig('figs/fig2_regions.png', facecolor=BG); plt.close()

# ── Figure 3: Income group gradient ──────────────────────────────────────────

income_keys = ['Low income', 'Lower middle income', 'Upper middle income', 'High income']
income_labels = ['Low income', 'Lower middle\nincome', 'Upper middle\nincome', 'High income']
fig, ax = plt.subplots(figsize=(8, 4.5))
income_pw, income_n, income_pct = [], [], []
for ik in income_keys:
    rd = [r for r in data if r['income_group'] == ik]
    pop = sum(r['pop'] for r in rd)
    pw = sum(r['gpi']*r['pop'] for r in rd)/pop
    income_pw.append(pw); income_n.append(len(rd))
    income_pct.append(sum(1 for r in rd if r['gpi']>1.0)/len(rd)*100)

x_pos = np.arange(len(income_labels))
colors = [MALE if v < 1.0 else FEMALE for v in income_pw]
ax.bar(x_pos, income_pw, width=0.55, color=colors, alpha=0.8, edgecolor='none')
ax.axhline(1.0, color=PARITY, linewidth=1.5, linestyle='--', alpha=0.6, zorder=0)
for i, (v, n, pct) in enumerate(zip(income_pw, income_n, income_pct)):
    ax.text(i, v+0.025, f'{v:.1f}', ha='center', fontsize=12, fontweight='bold', color=colors[i])
    ax.text(i, 0.05, f'n={n}\n{pct:.0f}% > 1', ha='center', fontsize=8, color='#555555')
ax.set_xticks(x_pos); ax.set_xticklabels(income_labels, fontsize=10)
ax.set_ylabel('Population-weighted mean GPI'); ax.set_ylim(0, 1.35)
ax.set_title('The Income Gradient in Tertiary Gender Parity', pad=12)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.savefig('figs/fig3_income.png', facecolor=BG); plt.close()

# ── Figure 4: Big countries dot plot ──────────────────────────────────────────

big = [r for r in data if r['pop'] >= 50]
big.sort(key=lambda r: r['gpi'])
fig, ax = plt.subplots(figsize=(10, 7))
y_pos = np.arange(len(big))
for i, r in enumerate(big):
    color = FEMALE if r['gpi'] >= 1.0 else MALE
    size = 40 + (r['pop']/max(d['pop'] for d in big))*200
    ax.scatter(r['gpi'], i, s=size, c=color, alpha=0.8, edgecolors='white', linewidths=0.3, zorder=3)
ax.axvline(1.0, color=PARITY, linewidth=1.5, linestyle='--', alpha=0.6, zorder=0)
names = []
for r in big:
    name = r['economy'][:18] + '…' if len(r['economy']) > 20 else r['economy']
    names.append(f"{name} ({r['pop']:.0f}M)")
ax.set_yticks(y_pos); ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel('Gender Parity Index (GPI)'); ax.set_xlim(0.45, 1.5)
ax.set_title('GPI for Countries with Population > 50M', pad=12)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
for i, r in enumerate(big):
    color = FEMALE if r['gpi'] >= 1.0 else MALE
    ax.text(r['gpi']+0.02, i, f'{r["gpi"]:.1f}', va='center', fontsize=8, color=color, fontweight='bold')
fig.savefig('figs/fig4_big_countries.png', facecolor=BG); plt.close()


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5: Historical GPI trajectories — spaghetti + share above parity
# ══════════════════════════════════════════════════════════════════════════════

fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(10, 8.5), height_ratios=[3, 2],
                                      gridspec_kw={'hspace': 0.30})

# --- Top panel: country spaghetti lines ---
highlight_countries = {
    'USA': {'color': '#333333', 'lw': 2.0, 'label': 'United States'},
    'IND': {'color': '#7b3294', 'lw': 2.0, 'label': 'India'},
    'SAU': {'color': '#2a8a6a', 'lw': 2.0, 'label': 'Saudi Arabia'},
    'TUN': {'color': '#1e8449', 'lw': 1.5, 'label': 'Tunisia'},
    'JPN': {'color': '#d68910', 'lw': 2.0, 'label': 'Japan'},
    'KOR': {'color': '#ca6f1e', 'lw': 1.5, 'label': 'South Korea'},
    'CHN': {'color': '#c0392b', 'lw': 2.0, 'label': 'China'},
    'BRA': {'color': '#d35400', 'lw': 1.5, 'label': 'Brazil'},
    'QAT': {'color': '#148f77', 'lw': 1.5, 'label': 'Qatar'},
    'TUR': {'color': '#b7950b', 'lw': 1.5, 'label': 'Türkiye'},
    'BGD': {'color': '#2874a6', 'lw': 1.5, 'label': 'Bangladesh'},
}

# Only plot countries with 10+ observations for cleaner spaghetti
hist_with_data = [c for c in hist if len(c['ts']) >= 10]

# Draw background countries faintly
for c in hist_with_data:
    if c['iso3'] not in highlight_countries:
        ts = c['ts']
        yrs = sorted(ts.keys())
        vals = [ts[y] for y in yrs]
        ax_top.plot(yrs, vals, color='#cccccc', alpha=0.4, lw=0.5, zorder=1)

# Fit and draw LOWESS trend across all countries
all_points = []
for c in hist_with_data:
    for year, gpi in c['ts'].items():
        all_points.append((year, gpi))
all_points.sort()
years = np.array([p[0] for p in all_points])
gpis = np.array([p[1] for p in all_points])
smoothed = lowess(gpis, years, frac=0.2, return_sorted=True)
ax_top.plot(smoothed[:, 0], smoothed[:, 1], color='#1a1a1a', lw=3,
            alpha=0.8, zorder=4, label='LOWESS trend')

# Draw highlighted countries
for c in hist:
    if c['iso3'] in highlight_countries:
        ts = c['ts']
        yrs = sorted(ts.keys())
        vals = [ts[y] for y in yrs]
        style = highlight_countries[c['iso3']]
        ax_top.plot(yrs, vals, color=style['color'], lw=style['lw'], alpha=0.9, zorder=5)
        ax_top.annotate(style['label'], xy=(yrs[-1], vals[-1]),
                        fontsize=8, color=style['color'], fontweight='bold',
                        xytext=(6, 0), textcoords='offset points', va='center', zorder=6)

ax_top.axhline(1.0, color=PARITY, linewidth=1.5, linestyle='--', alpha=0.5, zorder=2)
ax_top.annotate('Parity', xy=(1972, 1.02), fontsize=9, color=PARITY)
ax_top.set_xlim(1970, 2030)
ax_top.set_ylim(0, 2.1)
ax_top.set_ylabel('Gender Parity Index')
ax_top.set_title('The Long March Past Parity: Tertiary Enrollment GPI, 1970–2024', pad=12)
ax_top.spines['top'].set_visible(False)
ax_top.spines['right'].set_visible(False)

# --- Bottom panel: share of countries with GPI > 1 over time ---
# Use consistent denominator: countries with data in ALL snapshot years
snapshot_years = [1990, 1995, 2000, 2005, 2010, 2015, 2020]

def get_gpi_for_year(c, target_year, window=2):
    """Get GPI for a year, allowing small window for missing exact years."""
    ts = c['ts']
    if target_year in ts:
        return ts[target_year]
    for delta in range(1, window + 1):
        if target_year + delta in ts:
            return ts[target_year + delta]
        if target_year - delta in ts:
            return ts[target_year - delta]
    return None

consistent_countries = []
for c in hist:
    vals = [get_gpi_for_year(c, y) for y in snapshot_years]
    if all(v is not None for v in vals):
        consistent_countries.append(c)

n_consistent = len(consistent_countries)
pct_above = []
n_above_list = []

for y in snapshot_years:
    above = sum(1 for c in consistent_countries if (get_gpi_for_year(c, y) or 0) > 1.0)
    n_above_list.append(above)
    pct_above.append(100 * above / n_consistent)

snapshot_years_display = snapshot_years

ax_bot.bar(snapshot_years_display, pct_above, width=4, color=FEMALE, alpha=0.8, edgecolor='none')
ax_bot.axhline(50, color=PARITY, linewidth=1, linestyle=':', alpha=0.5)

for x, pct, na in zip(snapshot_years_display, pct_above, n_above_list):
    ax_bot.text(x, pct + 2, f'{pct:.0f}%', ha='center', fontsize=10, fontweight='bold', color=FEMALE)
    ax_bot.text(x, -6, f'{na}/{n_consistent}', ha='center', fontsize=8, color='#555555')

ax_bot.set_xlim(1987, 2023)
ax_bot.set_ylim(-10, 100)
ax_bot.set_ylabel('% of countries with GPI > 1')
ax_bot.set_xlabel('Year')
ax_bot.set_title(f'Share of Countries Where Women Outnumber Men (N={n_consistent} countries)', pad=10)
ax_bot.spines['top'].set_visible(False)
ax_bot.spines['right'].set_visible(False)

fig.savefig('figs/fig5_historical.png', facecolor=BG)
plt.close()


# ══════════════════════════════════════════════════════════════════════════════
# NEW FIGURE 6: GPI vs Female LFPR — the education-employment disconnect
# ══════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(10, 7))

# Draw all countries
for r in lfpr_data:
    color = REGION_COLORS.get(r['region'], '#6b7280')
    size = max(25, min(200, 25 + np.sqrt(r['pop_millions'] / 1429) * 200))
    alpha = 0.75 if r['region'] == 'Middle East & North Africa' else 0.45
    zorder = 5 if r['highlight'] else 3
    ax.scatter(r['gpi'], r['female_lfpr'], s=size, c=color, alpha=alpha,
               edgecolors='white', linewidths=0.3, zorder=zorder)

# Label highlights
label_offsets = {
    'JOR': (8, -8), 'IRN': (-10, 8), 'EGY': (8, 5), 'TUN': (8, -5),
    'DZA': (-10, -10), 'QAT': (8, 5), 'IND': (8, -8), 'JPN': (-8, 8),
    'KOR': (-8, -10), 'PSE': (8, 8), 'MDV': (8, -8), 'BGD': (-8, -10),
}
for r in lfpr_data:
    if r['highlight']:
        dx, dy = label_offsets.get(r['iso3'], (8, 0))
        ax.annotate(r['economy'], xy=(r['gpi'], r['female_lfpr']),
                    fontsize=8, color='#333333', fontweight='bold',
                    xytext=(dx, dy), textcoords='offset points',
                    arrowprops=dict(arrowstyle='-', color='#999999', lw=0.5),
                    zorder=10)

# Reference lines
ax.axvline(1.0, color=PARITY, linewidth=1.2, linestyle='--', alpha=0.4)
ax.axhline(50, color='#999999', linewidth=1, linestyle=':', alpha=0.5)

# Quadrant labels
ax.text(0.55, 85, 'Low GPI, High LFPR\n(Sub-Saharan Africa)', fontsize=8, color='#555555', style='italic')
ax.text(1.35, 8, 'High GPI, Low LFPR\n(The MENA puzzle)', fontsize=8, color=MENA, style='italic', fontweight='bold')

# Legend
from matplotlib.lines import Line2D
legend_items = [Line2D([0],[0], marker='o', color='w', markerfacecolor=c, markersize=8, label=r, linewidth=0)
                for r, c in REGION_COLORS.items() if r in set(d['region'] for d in lfpr_data)]
ax.legend(handles=legend_items, loc='upper left', fontsize=8, framealpha=0.9,
          facecolor='white', edgecolor='#cccccc', labelcolor='#333333')

ax.set_xlabel('Tertiary Enrollment GPI (higher = more women enrolled)')
ax.set_ylabel('Female Labor Force Participation Rate (%)')
ax.set_title('Educated but Not Employed: GPI vs. Female LFPR', pad=12)
ax.set_xlim(0.6, 1.9)
ax.set_ylim(5, 90)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.text(0.99, 0.02, 'Note: Gulf state LFPR includes large expat workforce',
        transform=ax.transAxes, fontsize=7, color='#666666', style='italic',
        ha='right', va='bottom')

fig.savefig('figs/fig6_gpi_vs_lfpr.png', facecolor=BG)
plt.close()

print("Done. 6 figures saved to figs/")
