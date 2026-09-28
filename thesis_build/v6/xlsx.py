# -*- coding: utf-8 -*-
"""Excel workbook carrying the same 24 four-actor tables as Chapter Four,
the clean dataset, the statistical tests and editable native Excel charts."""
import json, sys, openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter
sys.path.insert(0, 'v5')
import pyreadstat

T = json.load(open('v6/tables_final.json'))
MG = json.load(open('v5/margins.json'))
DF, META = pyreadstat.read_sav('out/Mud_crab_BMU_final_corrected.sav')

BASE = Font(name='Times New Roman', size=11, color='000000')
BOLD = Font(name='Times New Roman', size=11, bold=True, color='000000')
TITLE = Font(name='Times New Roman', size=13, bold=True, color='000000')
SUB = Font(name='Times New Roman', size=10, italic=True, color='404040')
ITAL = Font(name='Times New Roman', size=11, italic=True, color='000000')
RULE = Border(bottom=Side(style='thin', color='000000'))
TOPRULE = Border(top=Side(style='thin', color='000000'))

wb = openpyxl.Workbook()
wb.remove(wb.active)

def sheet(name):
    ws = wb.create_sheet(name[:31])
    ws.sheet_view.showGridLines = False
    return ws

def put(ws, r, c, v, font=BASE, align='left', border=None, wrap=False):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font
    cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=wrap)
    if border: cell.border = border
    return cell

# ---------------------------------------------------------------- Read Me
ws = sheet('Read Me')
put(ws, 1, 1, 'Mud Crab Market Structure, South Coast of Kenya', TITLE)
put(ws, 2, 1, 'Analysis workbook accompanying the thesis by Mercy Sangura', SUB)
notes = [
 ('Dataset', 'Mud_crab_BMU_final_corrected.sav, 96 respondents: 65 fishers, 22 middlemen, 5 hoteliers, 4 exporters.'),
 ('Four-actor tables', 'Every analytical table carries all four actor categories, so fishers, middlemen, hoteliers and exporters read on the same row.'),
 ('Percentages', 'All percentages are valid percentages within the actor category, not out of 96.'),
 ('Dashes', 'In the actor-by-BMU tables a dash means that actor category was not sampled at that BMU, so no percentage exists. It is not a zero: a zero means the actor was sampled there and nobody gave that answer. In the price tables a dash means the figure does not apply to that node.'),
 ('Site tests', 'Monte Carlo chi-square, 10,000 resamples, run separately for fishers and middlemen. Hoteliers and exporters were not tested against site because their site coverage was too uneven.'),
 ('Price tests', 'Kruskal-Wallis, because the price distributions are not normal and the groups are very unequal in size.'),
 ('Margins', 'Price differences between nodes are gross price spreads. No cost, volume or mortality data were collected, so they are not net margins or profit.'),
 ('Price correction', 'Respondent R051 medium-crab price corrected from KSh 800 to KSh 650 per kg against the field records. Every figure here reflects it.'),
 ('Hotelier caution', 'The five hotelier medium-grade prices (mean KSh 380/kg) sit below the fisher price for the same grade. They are retained as entered and excluded from the chain calculation.'),
]
r = 4
for k, v in notes:
    put(ws, r, 1, k, BOLD)
    put(ws, r, 2, v, BASE, wrap=True)
    r += 1
ws.column_dimensions['A'].width = 20
ws.column_dimensions['B'].width = 115
for rr in range(4, r): ws.row_dimensions[rr].height = 30

# ---------------------------------------------------------------- tables
def write_table(ws, r, t):
    put(ws, r, 1, f"Table {t['num']}", BOLD); r += 1
    put(ws, r, 1, t['title'], ITAL); r += 2
    ncol = len(t['headers'])
    for j, h in enumerate(t['headers'], 1):
        put(ws, r, j, h.replace('\n', ' '), BOLD, 'center' if j > 1 else 'left', RULE, wrap=True)
    ws.row_dimensions[r].height = 30
    r += 1
    for row in t['rows']:
        lbl = str(row[0])
        if lbl.startswith('__BLOCK__'):
            put(ws, r, 1, lbl.replace('__BLOCK__', ''), ITAL, wrap=True)
            ws.row_dimensions[r].height = 28
        else:
            for j, v in enumerate(row, 1):
                put(ws, r, j, v, BASE, 'center' if j > 1 else 'left')
        r += 1
    for j in range(1, ncol + 1):
        ws.cell(row=r - 1, column=j).border = RULE
    return r + 2

# Sheets follow Chapter Four's own sections, so every table in the thesis
# is on the sheet named after the section it appears in.
GROUPS = [('Sample',              [2]),
          ('Obj1 Demographics',   [3, 4, 5, 6, 7]),
          ('Obj1 Business',       [8, 9, 10, 11, 12]),
          ('Obj1 Knowledge',      [13, 14]),
          ('Obj2 Acquisition',    [15, 16]),
          ('Obj2 Buyers',         [17, 18, 19, 20, 21]),
          ('Obj2 Handling',       [22]),
          ('Obj2 Grading',        [23, 24, 25, 26, 27]),
          ('Obj2 Losses',         [28]),
          ('Obj2 Payment Pricing',[29, 30]),
          ('Obj2 Relationships',  [31, 32, 33, 34, 35]),
          ('Price Analysis',      [36, 37, 38, 39, 40]),
          ('Market Structure',    [41, 42, 43, 44]),
          ('Obj3 Constraints',    [45, 46, 47, 48, 49]),
          ('Obj3 Regulation',     [50, 51, 52]),
          ('Site Associations',   [53])]
_all = [n for _, ns in GROUPS for n in ns]
assert _all == sorted(t['num'] for t in T), 'workbook sheets do not cover every table'
for grp, nums in GROUPS:
    ws = sheet(grp)
    put(ws, 1, 1, grp, TITLE)
    put(ws, 2, 1, 'Percentages are valid percentages within the actor category at that '
                  'BMU. A dash means the actor was not sampled there.', SUB)
    r = 4
    for n in nums:
        r = write_table(ws, r, next(t for t in T if t['num'] == n))
    ws.column_dimensions['A'].width = 38
    ws.column_dimensions['B'].width = 18
    for j in range(3, 11):
        ws.column_dimensions[get_column_letter(j)].width = 16

# ---------------------------------------------------------------- charts
SER = ['2a78d6', 'eb6834', '1baf7a', 'eda100', 'e87ba4']
def add_chart(ws, anchor, title, ylab, cats, series, srow, scol, pct=True, ymax=None):
    put(ws, srow, scol, 'Category', BOLD, 'left', RULE)
    for j, (nm, _) in enumerate(series, 1):
        put(ws, srow, scol + j, nm, BOLD, 'center', RULE)
    for i, c in enumerate(cats, 1):
        put(ws, srow + i, scol, c, BASE)
        for j, (_, vals) in enumerate(series, 1):
            put(ws, srow + i, scol + j, round(vals[i - 1], 1), BASE, 'center')
    ch = BarChart(); ch.type = 'col'; ch.grouping = 'clustered'; ch.overlap = -10
    ch.title = title; ch.y_axis.title = ylab
    data = Reference(ws, min_col=scol + 1, max_col=scol + len(series), min_row=srow,
                     max_row=srow + len(cats))
    cref = Reference(ws, min_col=scol, min_row=srow + 1, max_row=srow + len(cats))
    ch.add_data(data, titles_from_data=True); ch.set_categories(cref)
    for i, s in enumerate(ch.series):
        s.graphicalProperties.solidFill = SER[i % len(SER)]
        s.graphicalProperties.line.solidFill = SER[i % len(SER)]
    ch.dataLabels = DataLabelList(); ch.dataLabels.showVal = True
    if pct:
        ch.y_axis.scaling.min = 0
        ch.y_axis.scaling.max = ymax or 100
        ch.y_axis.numFmt = '0"%"'
    ch.height = 8.5; ch.width = 18
    ws.add_chart(ch, anchor)

VL = META.variable_value_labels
ACT = DF['actor'].map(VL['actor'])
ACTORS = ['Fisher', 'Middleman', 'Hotelier', 'Exporter']
def pct_actor(var, cat):
    out = []
    for a in ACTORS:
        s = DF.loc[ACT == a, var].map(VL[var]).dropna() if var in VL else DF.loc[ACT == a, var].dropna()
        out.append(0.0 if len(s) == 0 else 100 * (s.astype(str) == cat).sum() / len(s))
    return out

ws = sheet('Charts')
put(ws, 1, 1, 'Charts (all four actor categories; source data sits beside each chart and can be edited)', TITLE)
add_chart(ws, 'A3', 'Age distribution within each actor category', '% within actor',
          ACTORS, [(c, pct_actor('age_group_0_1', c)) for c in
                   ['Under 18', '18-35', '36-49', '50-60', 'Over 60']], 3, 14)
add_chart(ws, 'A22', 'Highest education attained within each actor category', '% within actor',
          ACTORS, [(c, pct_actor('education_0_1', c)) for c in
                   ['No formal education', 'Primary', 'Secondary', 'Certificate', 'Diploma', 'Undergraduate']], 22, 14)
add_chart(ws, 'A41', 'Grading criteria used within each actor category', '% within actor',
          ACTORS, [(c, pct_actor('grade_basis_0_2', c)) for c in
                   ['Weight only', 'Size, weight, shell condition and claw size']], 41, 14)
add_chart(ws, 'A60', 'Main operational or marketing constraint within each actor category', '% within actor',
          ACTORS, [(c, pct_actor('main_constraint_0_3', c)) for c in
                   ['Price fluctuations', 'Mortality', 'Market seasonality',
                    'High freight, flight delays and supply risk']], 60, 14)
CH = [('Large (Grade A) sold on to exporters', 'Large to exporter'),
      ('Large (Grade A) sold on to hoteliers', 'Large to hotelier'),
      ('Medium (Grade B) sold on to exporters', 'Medium to exporter')]
add_chart(ws, 'A79', 'Share of the final chain price held at each actor node', '% of the final price',
          [lbl for _, lbl in CH],
          [('Retained by the fisher', [MG['chain'][k]['f_share'] for k, _ in CH]),
           ('Added at the middleman node', [MG['chain'][k]['m_share'] for k, _ in CH]),
           ('Added at the final buyer node', [MG['chain'][k]['t_share'] for k, _ in CH])], 79, 14)
S3 = ['Shimoni', 'Majoreni', 'Vanga']
add_chart(ws, 'A98', 'Fisher price as a percentage of the middleman price, by study site',
          '% of the middleman price', S3,
          [(g, [MG['site'][f'{g}|{s}']['share'] for s in S3])
           for g in ['Large (Grade A)', 'Medium (Grade B)']], 98, 14)
ws.column_dimensions['N'].width = 34

# ---------------------------------------------------------------- clean data
ws = sheet('Clean Data')
cols = list(DF.columns)
for j, c in enumerate(cols, 1):
    put(ws, 1, j, c, BOLD, 'center', RULE)
for i in range(len(DF)):
    for j, c in enumerate(cols, 1):
        v = DF.iloc[i][c]
        if c in VL:
            v = VL[c].get(v, v)
        try:
            if v != v: v = ''
        except Exception:
            pass
        ws.cell(row=i + 2, column=j, value=v).font = BASE

wb.save('v6/Mud_crab_analysis_workbook.xlsx')
print('workbook written:', len(wb.sheetnames), 'sheets')
for s in wb.sheetnames: print('   ', s)
