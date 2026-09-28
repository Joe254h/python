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
| `v6/verify_structure.py` | The 93 concentration, margin, dispersion and transmission figures. |
| `v6/verify_misc.py` | Recomputes the sample, income, age and significant-association tables. |
| `v6/verify_counts.py`, `v6/verify_prose.py`, `v6/verify_cells_in_prose.py` | Match every count and percentage claim in the prose to a real table cell or valid n. |
| `v6/verify_appendix.py` | Re-derives all 924 appendix cells. |
| `v6/check_sps.py` | Every SPSS command well formed, every variable present in the .sav, every table indexed. |
| `v6/verify_render.py` | What Word will PAINT, not what the text says: no automatic numbering on any heading style or paragraph, every PAGEREF target resolves to a bookmark that exists, every bookmark closed, heading and Normal styles resolve to Times New Roman. |
| `v6/render_headings.py` | Resolves each heading through the style chain and the numbering definitions and prints it as Word will render it. Fails if anything is painted in front of the typed text. |
| `v6/audit.py` | References, caption numbering, front-matter lists, fonts, colours, shading. |
| `v6/reviewer_check.py` | Each of the reviewer's thirteen issues against concrete evidence in the document. |

## The market-structure measures

The review asked for concentration, marketing margin and efficiency. None can
be computed the textbook way from this survey, which interviewed actors rather
than censusing buyers and recorded no costs or transaction volumes. Each has a
counterpart the data support, and `v6/market_structure.py` computes all three
into `v6/market_structure.json`; `v6/add_structure.py` writes them into
sections 4.4.11 to 4.4.13 as Tables 41 to 44.

| Measure | What is computed | What it is not |
|---|---|---|
| Concentration | Herfindahl-Hirschman Index, CR1 and the numbers-equivalent over the buying points fishers named at first sale, weighted by the share of harvesters attached to each, per BMU and overall. Also buyer options per harvester and harvesters per trader. | Not volume-weighted. A buying point many fishers name but that takes little from each is overweighted. |
| Margin | Gross marketing margin at each node, total marketing margin, producer's share, and the producer's share net of physical mortality, the one cost the survey measured. | Not a profit. No transport, holding, ice, packaging or cost of capital was priced. |
| Efficiency | Coefficient of variation of price within actor and grade, and the share of the middleman price transmitted to the fisher at each BMU. | Not a cost-based efficiency ratio. |

`v6/verify_structure.py` re-derives all 93 figures in those four tables from
the .sav. Section 3.10.4 of the thesis defines each measure, and section 7B of
the SPSS syntax produces the counts they are formed from, including the
`RECODE` statements that turn the mortality and catch bands into midpoints.

## One presentation per variable

Chapter Four originally showed 27 of its figures beside a table of the same
numbers. `v6/dedupe.py` and `v6/dedupe2.py` resolve that, once, and their
result is frozen as `v6/ch4_dedup.json` and `v6/tables_final_dedup.json`, which
`make.sh` copies in at the start of every build. The rule:

- the variable's association with BMU is significant → keep the **table**, which
  carries all four actors, the site pattern, chi-square, df, p and the 99%
  confidence interval, and drop the figure;
- otherwise → keep the **figure** and remove that variable's block from the
  table; the non-significant p-value is already in the prose;
- a figure superseded by a table carrying strictly more (exact counts, SD,
  median, quartiles, margins in shillings) goes as well.

`v6/fix_exhibit_refs.py` then makes sure every table and figure is named by a
sentence. `v6/tables_all.json` and `v6/ch4_all.json` keep the pre-figure set,
because Appendix A and the SPSS syntax must still cover every variable the
thesis reports, not only those that ended up as a table.

Re-running `v5/tables.py` and `v5/tables_num.py` rebuilds the raw table set from
the .sav and would undo the de-duplication, so `make.sh` does not call them. Run
them only when the data changes, then redo the de-duplication.

## Caveat

Page numbers in the table of contents and the two lists are Word `PAGEREF`
fields. They resolve only when the document is opened in Word and updated with
Ctrl+A then F9. Nothing in this pipeline can fill them in.

## Why the render checks exist

An earlier revision shipped with every heading rendering as
`CHAPTER 5: CHAPTER ONE: INTRODUCTION` and `5.4 1.1 Background information`,
and with three contents entries reading
`Error! Reference source not found.` Both passed every check at the time,
because those checks read paragraph text — and neither a painted list number
nor a field result is stored in the text. The cause was `numPr` on the
`Heading1`–`Heading4` **style** definitions, pointing at an abstract list whose
level 0 read `CHAPTER %1:` starting at 5; stripping `numPr` from paragraphs
does nothing, since the list is inherited. `v6/fix_heading_styles.py` removes
it at the style, and `verify_render.py` and `render_headings.py` make the same
defect impossible to ship again.
