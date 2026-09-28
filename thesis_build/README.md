# Thesis build pipeline

Rebuilds the whole thesis, the appendix, the SPSS syntax and the Excel
workbook from `out/Mud_crab_BMU_final_corrected.sav`. Every number printed in
Chapters Four to Six is generated here, never typed.

## Run it

```sh
cd thesis_build
sh v6/make.sh
```

That regenerates the 33 figures, the 61 tables, Chapters Four to Six, the
assembled thesis (`v6/thesis.docx`), Appendix A, the SPSS syntax and the
workbook, then runs the verification suite. It needs `python3` with
`pyreadstat`, `pandas`, `scipy`, `matplotlib`, `python-docx` and `openpyxl`,
and `node` with the `docx` package.

## Layout

| Path | What it is |
|---|---|
| `out/Mud_crab_BMU_final_corrected.sav` | The dataset. R051 carries the corrected Msambweni medium-crab price of KSh 650/kg. |
| `out/analysis.json` | Monte Carlo chi-square and Kruskal–Wallis results, computed once and used as the authority for every p-value printed. |
| `v5/engine.py` | Builds one actor-by-BMU table block: four actors against five BMUs with a p-value column. |
| `v5/tables.py` | The 56 categorical tables, as (title, variables) pairs. |
| `v5/tables_num.py` | The numeric tables: sample, income and age, prices, Kruskal–Wallis, margins, spread, significant associations. |
| `v6/ch4.json`, `v5/ch56.json` | Chapters Four to Six as block lists (`h1`/`h2`/`h3`/`p`/`table`/`fig`). |
| `v5/ch2_critical.py` | Section 2.10, the critical assessment of the literature. |
| `v3/charts.py`, `v5/extra_charts.py` | The 33 figures. Percentage axes always run 0–100%. |
| `v6/build.js` | Renders Chapters Four to Six to .docx. |
| `v6/merge.py` … `v6/fix_refs.py` | The assembly pipeline, run in the order `make.sh` lists. |
| `v3/thesis.docx` | The source of Chapters One to Three that `merge.py` splices the new chapters into. |

## Verification

`make.sh` ends by running these. All of them must report zero mismatches.

| Script | Checks |
|---|---|
| `v6/verify_sav.py` | Re-derives all 5,544 categorical cells from the .sav with plain pandas and compares them against the finished .docx. |
| `v6/verify_prices.py` | Recomputes the 207 price, margin, share and spread figures. |
| `v6/verify_misc.py` | Recomputes the sample, income, age and significant-association tables. |
| `v6/verify_counts.py`, `v6/verify_prose.py`, `v6/verify_cells_in_prose.py` | Match every count and percentage claim in the prose to a real table cell or valid n. |
| `v6/verify_appendix.py` | Re-derives all 924 appendix cells. |
| `v6/check_sps.py` | Every SPSS command well formed, every variable present in the .sav, every table indexed. |
| `v6/audit.py` | References, caption numbering, front-matter lists, fonts, colours, shading. |
| `v6/reviewer_check.py` | Each of the reviewer's thirteen issues against concrete evidence in the document. |

## Caveat

Page numbers in the table of contents and the two lists are Word `PAGEREF`
fields. They resolve only when the document is opened in Word and updated with
Ctrl+A then F9. Nothing in this pipeline can fill them in.
