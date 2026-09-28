# -*- coding: utf-8 -*-
"""Resolve a table number from the start of its title.

Hard-coded numbers in the verifiers broke every time a table was inserted or
the set was reordered. They ask for a table by name instead.
"""
import json

_T = json.load(open('v6/tables_final.json'))


def num(fragment):
    hits = [t['num'] for t in _T if t['title'].startswith(fragment)]
    if len(hits) != 1:
        raise KeyError(f'{fragment!r} matched {len(hits)} tables')
    return hits[0]


SAMPLE       = num('Distribution of Respondents')
INCOME_AGE   = num('Reported Monthly Income and Age')
PRICES       = num('Reported Mud Crab Prices by Actor')
KRUSKAL      = num('Kruskal')
MARGINS      = num('Marketing Margins and the Distribution')
PRICE_BMU    = num('Mean Reported Mud Crab Price by Actor')
SPREAD       = num('First-Sale Price Spread')
CONCENTRATION = num('Concentration of First-Sale Outlets')
BUYERS       = num('Buyer Options per Harvester')
GMM          = num('Gross Marketing Margin, Total Margin')
DISPERSION   = num('Price Dispersion Within Each Actor')
ASSOCIATIONS = num('Statistically Significant')

if __name__ == '__main__':
    for k, v in sorted(globals().items()):
        if k.isupper() and isinstance(v, int):
            print(f'  {k:14s} T{v}')
