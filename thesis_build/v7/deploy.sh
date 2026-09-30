#!/bin/sh
# Copy the built files into the repository and refresh the pipeline snapshot.
set -e
D=/home/user/python/Mercy_Sangura_Thesis_Final
B=/home/user/python/thesis_build
mkdir -p "$D/Figures" "$B"

# the candidate's own file, with the trimmed text carried into it, is the master
cp v8/thesis_trimmed.docx          "$D/Mercy_Sangura_Thesis_FINAL.docx"
cp v8/thesis_turnitin.docx         "$D/Mercy_Sangura_Thesis_Turnitin_Copy.docx"
cp v8/Chapters_Four_to_Six.docx    "$D/"
cp v6/Appendix_A_SPSS_Output.docx  "$D/"
cp v6/Revision_Checklist.docx      "$D/"
cp out/Mud_crab_BMU_final_corrected.sav "$D/"
cp out/Mud_crab_BMU_analysis.sps        "$D/"
cp v6/Mud_crab_analysis_workbook.xlsx   "$D/Mud_crab_analysis_workbook.xlsx"
cp figs/*.png "$D/Figures/" 2>/dev/null || cp v3/figs/*.png "$D/Figures/" 2>/dev/null || true

# the pipeline, so the build can be repeated from the repository
for d in v3 v5 v6 v7 v8 out; do
  mkdir -p "$B/$d"
done
cp v6/*.py v6/*.js v6/*.sh v6/*.json "$B/v6/" 2>/dev/null || true
cp v5/*.py v5/*.json "$B/v5/" 2>/dev/null || true
cp v7/*.py v7/*.sh "$B/v7/" 2>/dev/null || true
cp v8/*.py "$B/v8/" 2>/dev/null || true
cp v3/charts.py "$B/v3/" 2>/dev/null || true
cp repack.py doc_lib.js "$B/" 2>/dev/null || true
cp out/Mud_crab_BMU_final_corrected.sav out/analysis.json "$B/out/" 2>/dev/null || true

ls -la "$D"
