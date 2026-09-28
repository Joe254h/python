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


print('Rendering the two extra BMU charts:')
SITES4 = ['Shimoni','Majoreni','Vanga','Msambweni']
def by_site(var, actor, sites, order, fname, legend_title, figsize=(9.2,5.0)):
    cats=[c for c in (order or categories(var)) if c in categories(var)]
    coln=[int(((ACT==actor)&(BMU==s)&DF[var].notna()).sum()) for s in sites]
    n=len(cats); xp=np.arange(len(sites)); w=.92/n
    fig,ax=plt.subplots(figsize=figsize)
    for i,c in enumerate(cats):
        v=[]
        for s in sites:
            ss=vals(var,(ACT==actor)&(BMU==s))
            v.append(0 if len(ss)==0 else 100*(ss.astype(str)==c).sum()/len(ss))
        b=ax.bar(xp+(i-(n-1)/2)*w, v, w*.95, label=c, color=SER[i%len(SER)],
                 edgecolor=SURF, linewidth=.8, zorder=3)
        for r,vv in zip(b,v):
            if vv>0: ax.annotate(f'{vv:.0f}%',(r.get_x()+r.get_width()/2,vv),
                                 textcoords='offset points',xytext=(0,3),ha='center',
                                 fontsize=9.4,zorder=4)
    ax.set_xticks(xp); ax.set_xticklabels([f'{s}\n(n = {n_})' for s,n_ in zip(sites,coln)])
    axes_v(ax, ylab='Percentage within BMU')
    ax.legend(loc='center left', bbox_to_anchor=(1.01,.5), title=legend_title)
    fig.savefig(f'v5/fig/{fname}.png', dpi=240, bbox_inches='tight', pad_inches=.14)
    plt.close(fig); print('  ',fname)

by_site('gear_0_2','Fisher',SITES4,['Hand collection','Scoop net','Hooked stick','Sweep nets'],
        'f30_gear_site','Gear type')
by_site('catch_daily_0_2','Fisher',SITES4,['2-3 kg','4-5 kg','5-10 kg','Above 10 kg'],
        'f31_catch_site','Daily catch')
by_site('time_market_0_2','Fisher',SITES4,['1 hour','6 hours'],
        'f32_traveltime_site','Travel time to market', figsize=(8.2,4.6))
by_site('management_plan_0_3','Fisher',SITES4,['Yes','No'],
        'f33_mgmtplan_site','Aware of the management plan', figsize=(8.2,4.6))
print('done')
