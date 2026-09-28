#!/bin/sh
# Rebuild the whole thesis from the data. Run from the scratchpad root.
set -e
echo "== figures =="
python3 v3/charts.py        >/dev/null
python3 v5/extra_charts.py  >/dev/null
echo "== tables =="
python3 v5/tables.py        >/dev/null
python3 v5/tables_num.py    >/dev/null
echo "== chapters four to six =="
node v6/build.js
python3 repack.py v6/Chapters_Four_to_Six.docx v6/_t.docx >/dev/null
mv v6/_t.docx v6/Chapters_Four_to_Six.docx
echo "== assemble the thesis =="
for s in merge move_align_table fix_ch2 fix_align fix_headings front_matter fix_abstract \
         abbrev fix_outline fix_toc fix_refs fix_heading_styles; do
  python3 v6/$s.py >/dev/null
done
echo "== appendix, syntax, workbook =="
python3 v6/appendix.py      >/dev/null
node    v6/build_appendix.js
python3 repack.py v6/Appendix_A_SPSS_Output.docx v6/_a.docx >/dev/null
mv v6/_a.docx v6/Appendix_A_SPSS_Output.docx
python3 v6/checklist.py       >/dev/null
node    v6/build_checklist.js
python3 repack.py v6/Revision_Checklist.docx v6/_c.docx >/dev/null
mv v6/_c.docx v6/Revision_Checklist.docx
python3 v6/gen_sps.py
python3 v6/xlsx.py          >/dev/null
echo "== verify =="
python3 /mnt/skills/public/docx/scripts/office/validate.py v6/thesis.docx | tail -1
python3 v6/verify_render.py   v6/thesis.docx
python3 v6/render_headings.py v6/thesis.docx | tail -1
python3 v6/verify_sav.py
python3 v6/verify_prices.py
python3 v6/verify_misc.py
python3 v6/verify_counts.py
python3 v6/verify_appendix.py | tail -2
python3 v6/check_sps.py     | tail -3
echo "done"
