# -*- coding: utf-8 -*-
"""Per-variable fact digest: modal response per actor, site range, p-values."""
import sys, json
sys.path.insert(0, 'v5')
from engine import (DF, VL, LBL, ACT, BMU, ACTORS, SITES, vals, valid_n, sampled,
                    categories, _MC, fmt_p)

def digest(var, order=None):
    out = {'var': var, 'label': LBL.get(var, var), 'actors': {}, 'p': {}}
    cats = categories(var, order)
    for a in ACTORS:
        n = valid_n(var, a)
        if n == 0:
            out['actors'][a] = None; continue
        s = vals(var, ACT == a)
        counts = {c: int((s.astype(str) == c).sum()) for c in cats}
        top = max(counts, key=counts.get)
        d = {'n': n, 'modal': top, 'modal_n': counts[top],
             'modal_pct': round(100*counts[top]/n, 1),
             'dist': {c: (counts[c], round(100*counts[c]/n, 1)) for c in cats if counts[c]}}
        rng = {}
        for site in SITES:
            if not sampled(a, site): continue
            ss = vals(var, (ACT == a) & (BMU == site))
            if len(ss) == 0: continue
            k = int((ss.astype(str) == top).sum())
            rng[site] = (k, round(100*k/len(ss), 1), len(ss))
        d['modal_by_site'] = rng
        out['actors'][a] = d
    for a in ('Fisher', 'Middleman'):
        r = _MC.get((var, a))
        out['p'][a] = fmt_p(r['p']) if r else None
    return out

VARS = ['age_group_0_1','gender_0_1','education_0_1','ethnicity_0_1','marital_0_1',
        'experience_0_1','primary_role_0_1','own_manage_0_1','scale_0_1','income_band_0_1',
        'other_activity_0_1','licence_0_1','loans_0_1','loan_source_0_1','knowledge_source_0_1',
        'training_0_1','cooperative_0_1','self_help_0_1','market_supply_0_1',
        'acquisition_0_2','source_trade_0_2','gear_0_2','catch_daily_0_2','proportion_sold_0_2',
        'time_market_0_2','buyer_category_0_2','market_channel_0_2','consumer_contact_0_2',
        'preparation_0_2','preserve_process_0_2','packaging_0_2','transport_0_2',
        'grading_0_2','grade_basis_0_2','quality_before_0_2','quality_control_0_2',
        'size_large_0_2','grade_large_0_2','size_medium_0_2','grade_medium_0_2',
        'size_small_0_2','grade_small_0_2','mortality_0_2','spoilage_0_2','payment_0_2',
        'price_standard_0_2','price_setting_0_2','price_factors_0_2','location_sale_0_2',
        'fishers_tied_0_2','traders_tied_0_2','formal_agreement_0_2','intermediary_role_0_2',
        'negotiation_terms_0_2','technology_0_2','market_research_0_2',
        'main_constraint_0_3','infrastructure_0_3','infra_improvement_0_3','market_barriers_0_3',
        'experienced_challenges_0_3','risk_management_0_3','innovation_0_3','market_changes_0_3',
        'adaptation_0_3','regulation_0_3','management_plan_0_3','persons_interest_0_3',
        'industry_updates_0_3','well_structured_0_3','species_integrated_0_3',
        'policy_framework_0_3','opportunity_0_3','system_enhancement_0_3','youth_0_3',
        'diversification_0_3']
D = {v: digest(v) for v in VARS}
json.dump(D, open('v5/digest.json', 'w'), indent=1)

for v in VARS:
    d = D[v]
    print(f"\n### {v}  ({d['label']})   p: F={d['p']['Fisher']} M={d['p']['Middleman']}")
    for a in ACTORS:
        x = d['actors'][a]
        if x is None:
            print(f"   {a:10s} no valid response"); continue
        sites = ', '.join(f"{s} {k}/{tot} ({p}%)" for s, (k, p, tot) in x['modal_by_site'].items())
        print(f"   {a:10s} n={x['n']:<3} modal={x['modal']!r} {x['modal_n']} ({x['modal_pct']}%)")
        print(f"              dist={x['dist']}")
        if sites: print(f"              modal by site: {sites}")
