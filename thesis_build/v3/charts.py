# -*- coding: utf-8 -*-
"""Chapter Four figures, SPSS Chart Builder look, APA 7.
Every actor-level chart carries all four actor categories. Percentage axes
always run the full 0-100% range. Figure numbers and titles live in the
document, never inside the image."""
import sys, json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
sys.path.insert(0, 'v3')
from engine import DF, VL, ACT, BMU, ACTORS, SITES4, SITES5, vals, categories, valid_n

SER = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#7a5cd0']
INK, INK2, AXIS, GRID, SURF = '#000000', '#3d3d3d', '#000000', '#d0d0d0', '#ffffff'
plt.rcParams.update({
 'font.family': 'sans-serif',
 'font.sans-serif': ['Liberation Sans', 'Arial', 'DejaVu Sans'],
 'font.size': 11.5, 'axes.labelsize': 12, 'axes.titlesize': 12,
 'xtick.labelsize': 11, 'ytick.labelsize': 11, 'legend.fontsize': 11,
 'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK,
 'axes.facecolor': SURF, 'figure.facecolor': SURF, 'savefig.facecolor': SURF,
 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .8, 'grid.alpha': 1.0,
 'legend.frameon': False, 'legend.handlelength': 1.5, 'legend.handleheight': 1.3,
 'legend.borderpad': .4, 'legend.labelspacing': .7, 'legend.columnspacing': 1.4,
 'legend.title_fontsize': 10.5})

def axes_v(ax, ylab=None, pct=True):
    ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_visible(True); ax.spines[s].set_color(AXIS); ax.spines[s].set_linewidth(1.0)
    ax.xaxis.grid(False); ax.yaxis.grid(True)
    ax.tick_params(axis='both', color=AXIS, length=4, width=1.0, pad=5)
    if ylab: ax.set_ylabel(ylab, labelpad=9)
    if pct:
        ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
        ax.set_yticks(list(range(0, 101, 20))); ax.set_ylim(0, 100)

def axes_h(ax, xlab=None, pct=True):
    ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_visible(True); ax.spines[s].set_color(AXIS); ax.spines[s].set_linewidth(1.0)
    ax.yaxis.grid(False); ax.xaxis.grid(True)
    ax.tick_params(axis='both', color=AXIS, length=4, width=1.0, pad=5)
    if xlab: ax.set_xlabel(xlab, labelpad=9)
    if pct:
        ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
        ax.set_xticks(list(range(0, 101, 20))); ax.set_xlim(0, 100)

def save(fig, name):
    fig.savefig(f'v3/fig/{name}.png', dpi=240, bbox_inches='tight', pad_inches=.14)
    plt.close(fig); print('  ', name)

def pct_by_actor(var, cat):
    """Valid percentage of `cat` within each actor category; None where the
    actor gave no valid response at all."""
    out = []
    for a in ACTORS:
        s = vals(var, ACT == a)
        out.append(None if len(s) == 0 else 100 * (s.astype(str) == cat).sum() / len(s))
    return out

def actor_labels(var):
    return [f'{a}\n(n = {valid_n(var, a)})' for a in ACTORS]

def clustered_actor(var, order, fname, legend_title, ylab='Percentage within actor category',
                    figsize=(9.2, 5.0), rot=0):
    cats = [c for c in (order or categories(var)) if c in categories(var)]
    n = len(cats); xp = np.arange(len(ACTORS)); w = .92 / n
    fig, ax = plt.subplots(figsize=figsize)
    for i, c in enumerate(cats):
        v = [x if x is not None else 0 for x in pct_by_actor(var, c)]
        b = ax.bar(xp + (i - (n-1)/2) * w, v, w * .95, label=c, color=SER[i % len(SER)],
                   edgecolor=SURF, linewidth=.8, zorder=3)
        for r, vv in zip(b, v):
            if vv > 0:
                ax.annotate(f'{vv:.0f}%', (r.get_x() + r.get_width()/2, vv),
                            textcoords='offset points', xytext=(0, 3), ha='center',
                            fontsize=9.6, color=INK, zorder=4)
    ax.set_xticks(xp); ax.set_xticklabels(actor_labels(var), rotation=rot)
    axes_v(ax, ylab=ylab)
    ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title=legend_title)
    save(fig, fname)

def stacked_actor(var, order, fname, legend_title, figsize=(8.8, 4.9),
                  ylab='Percentage within actor category'):
    cats = [c for c in (order or categories(var)) if c in categories(var)]
    fig, ax = plt.subplots(figsize=figsize); bottom = np.zeros(len(ACTORS))
    for i, c in enumerate(cats):
        v = np.array([x if x is not None else 0 for x in pct_by_actor(var, c)])
        ax.bar(range(len(ACTORS)), v, .74, bottom=bottom, label=c, color=SER[i % len(SER)],
               edgecolor=SURF, linewidth=1.2, zorder=3)
        for j, (vv, bb) in enumerate(zip(v, bottom)):
            if vv >= 8:
                ax.text(j, bb + vv/2, f'{vv:.0f}%', ha='center', va='center',
                        fontsize=10, color='white', fontweight='bold', zorder=4)
        bottom += v
    ax.set_xticks(range(len(ACTORS))); ax.set_xticklabels(actor_labels(var))
    axes_v(ax, ylab=ylab)
    ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title=legend_title)
    save(fig, fname)

def hbar_actor(var, order, fname, legend_title='Actor category', figsize=(9.0, 4.8),
               short=None):
    cats = [c for c in (order or categories(var)) if c in categories(var)]
    labels = short or cats
    fig, ax = plt.subplots(figsize=figsize)
    yp = np.arange(len(cats)); h = .86 / len(ACTORS)
    for i, a in enumerate(ACTORS):
        v = []
        for c in cats:
            s = vals(var, ACT == a)
            v.append(0 if len(s) == 0 else 100 * (s.astype(str) == c).sum() / len(s))
        b = ax.barh(yp + (i - (len(ACTORS)-1)/2) * h, v, h * .95, label=f'{a} (n = {valid_n(var, a)})',
                    color=SER[i], edgecolor=SURF, linewidth=.9, zorder=3)
        for r, vv in zip(b, v):
            if vv <= 0: continue
            y = r.get_y() + r.get_height()/2
            if vv >= 86:
                ax.annotate(f'{vv:.0f}%', (vv, y), textcoords='offset points', xytext=(-5, 0),
                            ha='right', va='center', fontsize=9.6, color='white',
                            fontweight='bold', zorder=4)
            else:
                ax.annotate(f'{vv:.0f}%', (vv, y), textcoords='offset points', xytext=(4, 0),
                            ha='left', va='center', fontsize=9.6, zorder=4)
    ax.set_yticks(yp); ax.set_yticklabels(labels); ax.invert_yaxis()
    axes_h(ax, xlab='Percentage within actor category')
    ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title=legend_title)
    save(fig, fname)

print('Rendering four-actor figures:')

AGE   = ['Under 18', '18-35', '36-49', '50-60', 'Over 60']
EDU   = ['No formal education', 'Primary', 'Secondary', 'Certificate', 'Diploma', 'Undergraduate']
INC   = ['Below KSh 13,900', 'KSh 13,900-69,500', 'KSh 69,501-139,000']
SCALE = ['Small-scale', 'Medium-scale', 'Large-scale']
LIK4  = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree']
MORT  = ['Frozen / no mortality', '0.5-1 kg', '4-5 kg', 'Above 10 kg']

# ---- F1  sample composition within each study site --------------------------
fig, ax = plt.subplots(figsize=(8.8, 4.9)); bottom = np.zeros(len(SITES5))
coln = [int((BMU == s).sum()) for s in SITES5]
for i, a in enumerate(ACTORS):
    v = np.array([100 * ((ACT == a) & (BMU == s)).sum() / max(1, n) for s, n in zip(SITES5, coln)])
    ax.bar(range(len(SITES5)), v, .74, bottom=bottom, label=a, color=SER[i],
           edgecolor=SURF, linewidth=1.2, zorder=3)
    for j, (vv, bb) in enumerate(zip(v, bottom)):
        if vv >= 8:
            ax.text(j, bb + vv/2, f'{vv:.1f}%', ha='center', va='center',
                    fontsize=10, color='white', fontweight='bold', zorder=4)
    bottom += v
ax.set_xticks(range(len(SITES5)))
ax.set_xticklabels([f'{s}\n(n = {n})' for s, n in zip(SITES5, coln)])
axes_v(ax, ylab='Percentage of respondents within site')
ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title='Actor category')
save(fig, 'f01_sample_by_site')

# ---- Objective One ----------------------------------------------------------
clustered_actor('age_group_0_1', AGE, 'f02_age_actor', 'Age group')
stacked_actor('education_0_1', EDU, 'f03_education_actor', 'Highest education attained')
stacked_actor('income_band_0_1', INC, 'f04_income_actor', 'Monthly income band')
hbar_actor('scale_0_1', SCALE, 'f05_scale_actor', figsize=(8.6, 4.2))

# licensing / credit / training / collective membership, all four actors
fig, ax = plt.subplots(figsize=(9.0, 4.6))
inds = ['Holds an operating licence', 'Uses loans', 'Received formal training',
        'Cooperative or association member', 'Self-help group member']
srcs = ['licence_0_1', 'loans_0_1', 'training_0_1', 'cooperative_0_1', 'self_help_0_1']
yp = np.arange(len(inds)); h = .86 / len(ACTORS)
for i, a in enumerate(ACTORS):
    v = []
    for var in srcs:
        s = vals(var, ACT == a)
        v.append(np.nan if len(s) == 0 else 100 * (s.astype(str) == 'Yes').sum() / len(s))
    b = ax.barh(yp + (i - 1.5) * h, np.nan_to_num(v), h * .95, label=a, color=SER[i],
                edgecolor=SURF, linewidth=.9, zorder=3)
    for r, vv in zip(b, v):
        y = r.get_y() + r.get_height()/2
        if np.isnan(vv):
            ax.annotate('no data', (0.7, y), fontsize=8.6, va='center', color=INK2, zorder=4)
        elif vv > 0:
            if vv >= 86:
                ax.annotate(f'{vv:.0f}%', (vv, y), textcoords='offset points', xytext=(-5, 0),
                            ha='right', va='center', fontsize=9.6, color='white',
                            fontweight='bold', zorder=4)
            else:
                ax.annotate(f'{vv:.0f}%', (vv, y), textcoords='offset points', xytext=(4, 0),
                            ha='left', va='center', fontsize=9.6, zorder=4)
        else:
            ax.annotate('0%', (0.7, y), fontsize=9.2, va='center', zorder=4)
ax.set_yticks(yp); ax.set_yticklabels(inds); ax.invert_yaxis()
axes_h(ax, xlab='Percentage answering Yes within actor category')
ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title='Actor category')
save(fig, 'f06_institutional_actor')

# ---- Objective Two ----------------------------------------------------------
hbar_actor('source_trade_0_2', None, 'f07_sourcing_actor', figsize=(9.4, 4.0),
           short=['Catches personally', 'Buys from middlemen', 'Buys from middlemen\nor agents'])
hbar_actor('buyer_category_0_2', None, 'f08_buyer_actor', figsize=(9.4, 5.2))
hbar_actor('preparation_0_2', None, 'f09_preparation_actor', figsize=(9.2, 4.0),
           short=['Cleaning, sorting\nand grading', 'Processing', 'Tying claws'])
hbar_actor('packaging_0_2', None, 'f10_packaging_actor', figsize=(9.2, 4.8))
hbar_actor('transport_0_2', None, 'f11_transport_actor', figsize=(9.2, 4.8))
hbar_actor('grade_basis_0_2', None, 'f12_grading_actor', figsize=(9.4, 3.6),
           short=['Size, weight, shell condition\nand claw size', 'Weight only'])
clustered_actor('mortality_0_2', MORT, 'f13_mortality_actor', 'Reported daily mortality',
                figsize=(9.4, 5.0))
hbar_actor('payment_0_2', None, 'f14_payment_actor', figsize=(9.2, 4.8))
hbar_actor('price_setting_0_2', None, 'f15_pricesetting_actor', figsize=(9.0, 3.4))

# ---- prices --------------------------------------------------------------
G = [('Large (Grade A)', 'price_large_0_2'), ('Medium (Grade B)', 'price_medium_0_2'),
     ('Small (Grade C)', 'price_small_0_2')]
def pser(var, mask):
    s = DF.loc[mask, var].dropna(); return s[s > 0]

# F16 mean price by actor and grade, SD error bars
fig, ax = plt.subplots(figsize=(9.0, 5.0)); xp = np.arange(len(ACTORS)); w = .27
for i, (gl, var) in enumerate(G):
    mns, sds = [], []
    for a in ACTORS:
        s = pser(var, ACT == a)
        mns.append(s.mean() if len(s) else 0); sds.append(s.std(ddof=1) if len(s) > 1 else 0)
    b = ax.bar(xp + (i-1)*w, mns, w*.95, yerr=sds, capsize=3.4, label=gl, color=SER[i],
               edgecolor=SURF, linewidth=.9, zorder=3,
               error_kw=dict(ecolor=AXIS, lw=.9, capthick=.9, zorder=4))
    for r, v, e in zip(b, mns, sds):
        if v: ax.annotate(f'{v:,.0f}', (r.get_x()+r.get_width()/2, v+e), textcoords='offset points',
                          xytext=(0, 4), ha='center', fontsize=9.0, zorder=5)
ax.set_xticks(xp)
ax.set_xticklabels([f'{a}\n(n = {len(pser("price_large_0_2", ACT==a))})' for a in ACTORS])
ax.set_axisbelow(True)
for s_ in ('top', 'right'): ax.spines[s_].set_visible(False)
ax.xaxis.grid(False); ax.yaxis.grid(True)
ax.set_ylabel('Mean reported price (KSh/kg)', labelpad=9)
ax.set_ylim(0, 3300); ax.yaxis.set_major_formatter(lambda v, p: f'{v:,.0f}')
ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title='Size grade')
save(fig, 'f16_price_actor_grade')

# F17 share of the final chain price at each node
MG = json.load(open('v3/margins.json'))
CH = [('Large (Grade A) sold on to exporters', 'Large (Grade A)\nsold on to exporters'),
      ('Large (Grade A) sold on to hoteliers', 'Large (Grade A)\nsold on to hoteliers'),
      ('Medium (Grade B) sold on to exporters', 'Medium (Grade B)\nsold on to exporters')]
SEG = ['Retained by the fisher', 'Added at the middleman node', 'Added at the final buyer node']
fig, ax = plt.subplots(figsize=(9.2, 4.5))
yp = np.arange(len(CH))[::-1]; left = np.zeros(len(CH))
segs = [[MG['chain'][k]['f_share'] for k, _ in CH],
        [MG['chain'][k]['m_share'] for k, _ in CH],
        [MG['chain'][k]['t_share'] for k, _ in CH]]
for i, (v, lb) in enumerate(zip(segs, SEG)):
    v = np.array(v)
    ax.barh(yp, v, .58, left=left, label=lb, color=SER[i], edgecolor=SURF, linewidth=1.3, zorder=3)
    for y, vv, ll in zip(yp, v, left):
        if vv >= 7:
            ax.text(ll + vv/2, y, f'{vv:.1f}%', ha='center', va='center', fontsize=10.5,
                    color='white', fontweight='bold', zorder=4)
    left = left + v
ax.set_yticks(yp); ax.set_yticklabels([t for _, t in CH])
axes_h(ax, xlab='Percentage of the final chain price')
ax.set_ylim(-.7, len(CH) - .3)
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.20), ncol=3)
save(fig, 'f17_chain_share')

# F18 price by study site and grade, all four actors
fig, ax = plt.subplots(figsize=(9.6, 5.0))
xp = np.arange(len(SITES5)); w = .92 / len(ACTORS)
for i, a in enumerate(ACTORS):
    v = []
    for s_ in SITES5:
        ss = pser('price_large_0_2', (ACT == a) & (BMU == s_))
        v.append(ss.mean() if len(ss) else 0)
    b = ax.bar(xp + (i - 1.5) * w, v, w * .95, label=a, color=SER[i], edgecolor=SURF,
               linewidth=.8, zorder=3)
    for r, vv in zip(b, v):
        if vv: ax.annotate(f'{vv:,.0f}', (r.get_x()+r.get_width()/2, vv), textcoords='offset points',
                           xytext=(0, 3), ha='center', fontsize=8.8, zorder=4)
ax.set_xticks(xp); ax.set_xticklabels(SITES5)
ax.set_axisbelow(True)
for s_ in ('top', 'right'): ax.spines[s_].set_visible(False)
ax.xaxis.grid(False); ax.yaxis.grid(True)
ax.set_ylabel('Mean large-crab price (KSh/kg)', labelpad=9)
ax.set_ylim(0, 2700); ax.yaxis.set_major_formatter(lambda v, p: f'{v:,.0f}')
ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title='Actor category')
save(fig, 'f18_price_site_actor')

# F19 fisher price as a percentage of the middleman price, by site
S3 = SITES4[:3]
fig, ax = plt.subplots(figsize=(8.4, 4.9)); xp = np.arange(len(S3)); w = .34
for i, (g, gl) in enumerate([('Large (Grade A)', 'Large (Grade A)'),
                             ('Medium (Grade B)', 'Medium (Grade B)')]):
    v = [MG['site'][f'{g}|{s_}']['share'] for s_ in S3]
    b = ax.bar(xp + (i - .5) * w, v, w * .94, label=gl, color=SER[i], edgecolor=SURF,
               linewidth=.9, zorder=3)
    for r, vv in zip(b, v):
        ax.annotate(f'{vv:.1f}%', (r.get_x()+r.get_width()/2, vv), textcoords='offset points',
                    xytext=(0, 3), ha='center', fontsize=10, zorder=4)
ax.set_xticks(xp)
ax.set_xticklabels([f'{s_}\n(fishers n = {MG["site"]["Large (Grade A)|"+s_]["nf"]};\n'
                    f'middlemen n = {MG["site"]["Large (Grade A)|"+s_]["nm"]})' for s_ in S3])
axes_v(ax, ylab='Fisher price as a percentage of\nthe middleman price')
ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title='Size grade')
save(fig, 'f19_fisher_share_site')

# ---- Objective Three -------------------------------------------------------
CONS = ['Price fluctuations', 'Mortality', 'Market seasonality',
        'High freight, flight delays and supply risk']
hbar_actor('main_constraint_0_3', CONS, 'f20_constraint_actor', figsize=(9.4, 4.6),
           short=['Price fluctuations', 'Mortality', 'Market seasonality',
                  'Freight, flight delays\nand supply risk'])
INFRA = ['Poor road infrastructure', 'Lack of aggregation facilities', 'Limited transport',
         'Market seasonality', 'High freight, flight delays and mortality']
hbar_actor('infrastructure_0_3', INFRA, 'f21_infra_actor', figsize=(9.6, 5.0),
           short=['Poor roads', 'No aggregation facilities', 'Limited transport',
                  'Market seasonality', 'Freight, flight delays\nand mortality'])
stacked_actor('well_structured_0_3', LIK4, 'f22_structure_actor',
              'Response to "the market is well structured"', figsize=(9.2, 4.8))
hbar_actor('opportunity_0_3', None, 'f23_opportunity_actor', figsize=(9.2, 3.4))
hbar_actor('system_enhancement_0_3', None, 'f24_enhancement_actor', figsize=(9.6, 4.8))
stacked_actor('youth_0_3', ['Very low', 'Low', 'Neutral'], 'f25_youth_actor',
              'Reported youth involvement', figsize=(9.0, 4.6))
stacked_actor('diversification_0_3', ['Negative', 'Not explored yet', 'Neutral', 'Positive'],
              'f26_diversification_actor', 'Perceived diversification potential', figsize=(9.2, 4.8))

# ---- BMU figures for fishers and middlemen ---------------------------------
def by_site(var, actor, sites, order, fname, legend_title, figsize=(9.2, 5.0)):
    cats = [c for c in (order or categories(var)) if c in categories(var)]
    coln = [int(((ACT == actor) & (BMU == s) & DF[var].notna()).sum()) for s in sites]
    n = len(cats); xp = np.arange(len(sites)); w = .92 / n
    fig, ax = plt.subplots(figsize=figsize)
    for i, c in enumerate(cats):
        v = []
        for s in sites:
            ss = vals(var, (ACT == actor) & (BMU == s))
            v.append(0 if len(ss) == 0 else 100 * (ss.astype(str) == c).sum() / len(ss))
        b = ax.bar(xp + (i - (n-1)/2) * w, v, w * .95, label=c, color=SER[i % len(SER)],
                   edgecolor=SURF, linewidth=.8, zorder=3)
        for r, vv in zip(b, v):
            if vv > 0:
                ax.annotate(f'{vv:.0f}%', (r.get_x()+r.get_width()/2, vv), textcoords='offset points',
                            xytext=(0, 3), ha='center', fontsize=9.4, zorder=4)
    ax.set_xticks(xp); ax.set_xticklabels([f'{s}\n(n = {n_})' for s, n_ in zip(sites, coln)])
    axes_v(ax, ylab=f'Percentage within study site')
    ax.legend(loc='center left', bbox_to_anchor=(1.01, .5), title=legend_title)
    save(fig, fname)

by_site('age_group_0_1', 'Fisher', SITES4, AGE, 'f27_fisher_age_site', 'Age group')
by_site('main_constraint_0_3', 'Middleman', SITES4[:3], ['Price fluctuations', 'Mortality'],
        'f28_middleman_constraint_site', 'Main constraint', figsize=(7.6, 4.6))
by_site('size_large_0_2', 'Fisher', SITES4, ['Large', 'All sizes / mixed'],
        'f29_fisher_sizelabel_site', 'Large-crab size label', figsize=(8.2, 4.6))
print('done')
