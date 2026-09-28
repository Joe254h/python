# -*- coding: utf-8 -*-
"""Appendix A: the SPSS output that backs Chapter Four.

Crosstabulations are reproduced BY actor, so every output table carries the
four actor categories, followed by the chi-square tests against study site,
the Kruskal-Wallis price comparisons and the descriptive statistics."""
import json, sys, numpy as np
sys.path.insert(0, 'v5')
from engine import DF, VL, LBL, ACT, BMU, ACTORS, SITES, NA as DASH, vals, categories, valid_n, _MC, fmt_p
SITES4 = SITES[:4]; SITES5 = SITES
from scipy import stats

B = []
def H1(t): B.append(dict(k='h1', t=t))
def H2(t): B.append(dict(k='h2', t=t))
def P(t):  B.append(dict(k='p', t=t))
def TBL(title, headers, rows, widths=None, note=None):
    B.append(dict(k='rawtable', title=title, headers=headers, rows=rows,
                  widths=widths, note=note))

H1('APPENDIX A: IBM SPSS STATISTICS OUTPUT')
P('This appendix reproduces the IBM SPSS Statistics output behind Chapter Four. '
  'Crosstabulations are run BY actor, so each table carries fishers, middlemen, '
  'hoteliers and exporters. Cells show the count with the column percentage in '
  'parentheses; an em dash marks an actor category that recorded no valid response. '
  'The syntax that produces every table here is supplied as '
  'Mud_crab_BMU_analysis.sps.')

# ---- A1 crosstabulations by actor ----------------------------------------
H2('A.1 Crosstabulations by Actor Category')
GROUPS = [
 ('Objective One', ['age_group_0_1','gender_0_1','education_0_1','marital_0_1','experience_0_1',
                    'primary_role_0_1','scale_0_1','income_band_0_1','other_activity_0_1',
                    'licence_0_1','loans_0_1','loan_source_0_1','training_0_1',
                    'cooperative_0_1','self_help_0_1','market_supply_0_1']),
 ('Objective Two', ['acquisition_0_2','source_trade_0_2','buyer_category_0_2','market_channel_0_2',
                    'consumer_contact_0_2','gear_0_2','catch_daily_0_2','proportion_sold_0_2',
                    'time_market_0_2','preparation_0_2','packaging_0_2','preserve_process_0_2',
                    'transport_0_2','grading_0_2','grade_basis_0_2','quality_before_0_2',
                    'quality_control_0_2','size_large_0_2','grade_large_0_2','size_medium_0_2',
                    'grade_medium_0_2','size_small_0_2','grade_small_0_2','mortality_0_2',
                    'spoilage_0_2','payment_0_2','price_standard_0_2','price_setting_0_2',
                    'price_factors_0_2','location_sale_0_2','fishers_tied_0_2','traders_tied_0_2',
                    'formal_agreement_0_2','intermediary_role_0_2','negotiation_terms_0_2',
                    'technology_0_2','market_research_0_2']),
 ('Objective Three', ['main_constraint_0_3','infrastructure_0_3','infra_improvement_0_3',
                      'market_barriers_0_3','experienced_challenges_0_3','risk_management_0_3',
                      'innovation_0_3','market_changes_0_3','adaptation_0_3','regulation_0_3',
                      'management_plan_0_3','persons_interest_0_3','industry_updates_0_3',
                      'well_structured_0_3','species_integrated_0_3','policy_framework_0_3',
                      'opportunity_0_3','system_enhancement_0_3','youth_0_3','diversification_0_3']),
]
for obj, varlist in GROUPS:
    for var in varlist:
        rows = []
        for c in categories(var):
            r = [c]
            for a in ACTORS:
                s = vals(var, ACT == a)
                if len(s) == 0:
                    r.append(DASH)
                else:
                    n = int((s.astype(str) == c).sum())
                    r.append(f'{n} ({100*n/len(s):.1f}%)')
            s_all = vals(var)
            n = int((s_all.astype(str) == c).sum())
            r.append(f'{n} ({100*n/len(s_all):.1f}%)')
            rows.append(r)
        tot = ['Total']
        for a in ACTORS:
            n = valid_n(var, a)
            tot.append(f'{n} (100.0%)' if n else DASH)
        tot.append(f'{len(vals(var))} (100.0%)')
        rows.append(tot)
        TBL(f'{LBL.get(var, var)} * actor Crosstabulation  [{obj}]',
            ['Response'] + ACTORS + ['Total'], rows,
            [2300, 1400, 1500, 1350, 1350, 1126])

# ---- A2 chi-square tests --------------------------------------------------
H2('A.2 Chi-Square Tests Against Study Site')
P('Tests were run separately for fishers, across the four Beach Management Units, '
  'and for middlemen, across the three sites where traders were sampled. Two-sided '
  'Monte Carlo significance is based on 10,000 sampled tables with a 99% confidence '
  'interval. Hoteliers and exporters were not tested because their site coverage was '
  'too uneven for the test to be meaningful.')
rows = []
for (var, actor), r in sorted(_MC.items(), key=lambda kv: (kv[1]['objective'], kv[1]['actor'], kv[1]['label'])):
    rows.append([r['label'], actor, f"{r['chi2']:.3f}", str(r['df']), str(r['N']),
                 fmt_p(r['p']).replace('= ', ''),
                 f"[{r['ci'][0]:.3f}, {r['ci'][1]:.3f}]".replace('0.', '.'),
                 f"{r['min_exp']:.2f}", 'Yes' if r['sig'] else 'No'])
TBL('Chi-Square Tests: Monte Carlo significance (10,000 samples)',
    ['Variable', 'Actor', 'Pearson χ²', 'df', 'N', 'p', '99% CI', 'Min expected', 'p < .05'],
    rows, [2400, 1000, 1000, 550, 600, 750, 1200, 1050, 776])

# ---- A3 Kruskal-Wallis ----------------------------------------------------
H2('A.3 Kruskal–Wallis Tests of Reported Prices')
G = [('Large (Grade A)', 'price_large_0_2'), ('Medium (Grade B)', 'price_medium_0_2'),
     ('Small (Grade C)', 'price_small_0_2')]
def series(var, mask):
    s = DF.loc[mask, var].dropna(); return s[s > 0]
def kw(var, group, mask, levels):
    gs = [series(var, mask & (group == lv)) for lv in levels]
    gs = [g for g in gs if len(g)]
    if len(gs) < 2: return None
    H, p = stats.kruskal(*gs)
    return H, len(gs) - 1, sum(len(g) for g in gs), p
rows = []
for lab, group, mask, levels in [
        ('Price by actor category', ACT, ACT.notna(), ACTORS),
        ('Fisher price by study site', BMU, (ACT == 'Fisher') & BMU.isin(SITES4), SITES4),
        ('Middleman price by study site', BMU, (ACT == 'Middleman') & BMU.isin(SITES4[:3]), SITES4[:3])]:
    for gl, var in G:
        r = kw(var, group, mask, levels)
        rows.append([lab, gl] + ([f'{r[0]:.3f}', str(r[1]), str(r[2]),
                                  fmt_p(r[3]).replace('= ', '')] if r else [DASH]*4))
TBL('Kruskal–Wallis Test Statistics', ['Comparison', 'Size grade', 'H', 'df', 'N', 'p'],
    rows, [2600, 1700, 1200, 700, 800, 1026])

# ---- A4 descriptives ------------------------------------------------------
H2('A.4 Descriptive Statistics')
def desc(s):
    if len(s) == 0: return [DASH] * 7
    q1, q3 = np.percentile(s, [25, 75])
    return [str(len(s)), f'{s.mean():,.1f}', f'{s.std(ddof=1):,.1f}' if len(s) > 1 else '0.0',
            f'{np.median(s):,.1f}', f'{q1:,.1f}', f'{q3:,.1f}', f'{s.min():,.0f}–{s.max():,.0f}']
rows = []
for lab, var in [('Reported monthly mud crab income (KSh)', 'income_ksh_0_1'),
                 ('Age in completed years', 'age_0_1'),
                 ('Large-crab price (KSh/kg)', 'price_large_0_2'),
                 ('Medium-crab price (KSh/kg)', 'price_medium_0_2'),
                 ('Small-crab price (KSh/kg)', 'price_small_0_2')]:
    for a in ACTORS:
        rows.append([lab if a == 'Fisher' else '', a] + desc(series(var, ACT == a)))
TBL('Descriptives by Actor Category',
    ['Variable', 'Actor', 'N', 'Mean', 'SD', 'Median', 'Q1', 'Q3', 'Range'],
    rows, [2200, 1100, 550, 950, 900, 900, 800, 800, 1126])

json.dump(B, open('v5/appendix.json', 'w'), indent=1)
print('appendix blocks:', len(B), '| output tables:', sum(1 for b in B if b['k'] == 'rawtable'))
