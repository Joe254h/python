#!/bin/sh
# Rebuild the whole thesis from the data. Run from the scratchpad root.
set -e
echo "== figures =="
python3 v3/charts.py        >/dev/null
python3 v5/extra_charts.py  >/dev/null
echo "== tables =="
# v5/tables.py and v5/tables_num.py rebuild the raw table set from the .sav;
# the de-duplicated set is frozen in v6/tables_final_dedup.json, so they are
# run only when the data changes, not on every build.
cp v6/ch4_dedup.json v6/ch4.json
cp v6/tables_final_dedup.json v6/tables_final.json
echo "== chapters four to six =="
node v6/build.js
python3 repack.py v6/Chapters_Four_to_Six.docx v6/_t.docx >/dev/null
mv v6/_t.docx v6/Chapters_Four_to_Six.docx
echo "== assemble the thesis =="
# add_methods_measures must run before fix_toc so section 3.10.4 gets a
# contents row of its own, and fix_defects before either so the empty heading
# in the base document never reaches the table of contents
for s in merge move_align_table fix_ch2 fix_headings fix_defects \
         add_methods_measures front_matter fix_abstract abbrev fix_outline \
         fix_toc fix_refs fix_align fix_heading_styles; do
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
python3 v7/turnitin_copy.py
python3 v7/wordcount.py
echo "== verify =="
python3 /mnt/skills/public/docx/scripts/office/validate.py v6/thesis.docx | tail -1
python3 v6/verify_render.py   v6/thesis.docx
python3 v6/render_headings.py v6/thesis.docx | tail -1
python3 v6/verify_sav.py
python3 v6/verify_prices.py
python3 v6/verify_misc.py
python3 v6/verify_structure.py
python3 v6/verify_counts.py
python3 v6/verify_cells_in_prose.py
python3 v6/verify_exhibit_refs.py | tail -1
python3 v6/verify_apa.py     | tail -3
python3 v6/verify_humanizer.py | tail -2
python3 v6/verify_appendix.py | tail -2
python3 v6/check_sps.py     | tail -3
echo "done"
