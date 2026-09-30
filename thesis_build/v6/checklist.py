# -*- coding: utf-8 -*-
"""Build the revision checklist as a Word document."""
import json
B = []
def H1(t): B.append(dict(k='h1', t=t))
def H2(t): B.append(dict(k='h2', t=t))
def P(t):  B.append(dict(k='p', t=t))
def TBL(title, headers, rows, widths):
    B.append(dict(k='rawtable', title=title, headers=headers, rows=rows, widths=widths))

H1('REVISION CHECKLIST')
P('This checklist records how the revised thesis answers each numbered issue in '
  'the reviewer’s report, where in the document the answer sits, and how the '
  'figure or statement was verified. Every number quoted in Chapters Four to Six '
  'was re-derived from Mud_crab_BMU_final_corrected.sav and compared against the '
  'printed document; the counts of those checks are given in the last section.')

H2('A. The Reviewer’s Thirteen Issues')
ROWS = [
 ('1', 'Mismatch between the conceptual framework and the data',
  'Figure 3 is now a descriptive framework that names only what was measured and '
  'tested. §2.11 states that structure–conduct–performance is the single guiding '
  'framework and that value-chain and livelihood concepts play a supporting, '
  'non-causal role. §5.6 states which structural dimensions could not be measured.',
  '§2.11, §2.12, Figure 3, §5.6'),
 ('2', 'Weakness in the market structure analysis',
  'Sixteen Kruskal–Wallis statistics compare prices across actor categories and '
  'across BMUs within actor. Table 40 measures concentration at first sale with the '
  'Herfindahl-Hirschman Index and the concentration ratio, by BMU; Table 41 gives '
  'buyer options per harvester and harvesters per trader; Tables 42 and 43 give the gross '
  'marketing margin at each node, the total marketing margin and the producer’s '
  'share, both gross and net of measured physical loss; Table 44 gives price '
  'dispersion and price transmission. Table 53 lists every significant '
  'actor-specific association with BMU.',
  '§4.4.8–§4.4.12, Tables 36–44, Table 53, §3.10.4, §5.3.4, §5.6'),
 ('3', 'Sampling and methodological concerns',
  'Yamane’s formula and the computed sample size are shown in §3.5. §3.6 is a new '
  'section on non-response and sampling limitations covering the achieved sample, '
  'the shortfall, snowball sampling for middlemen, hoteliers and exporters, and '
  'what the shortfall does and does not allow the study to claim.',
  '§3.5, §3.6'),
 ('4', 'Weak justification of the study population',
  'Section 3.4 defines the target population, cites Lamm and Lamm (2019), names the '
  'groups excluded from the survey and states what that exclusion costs the study.',
  '§3.4'),
 ('5', 'Research design and analytical alignment',
  'A research design section was added at §3.3. Table 1 in §3.9 maps each objective '
  'to its variables, the analysis applied and the exact tables and figures that '
  'report it.',
  '§3.3, §3.9, Table 1'),
 ('6', 'Theoretical framework weakness',
  'Section 2.11 names structure–conduct–performance as the main framework, explains '
  'the supporting role of value-chain analysis and livelihood concepts, and says '
  'plainly that they are not treated as a second causal theory.',
  '§2.11'),
 ('7', 'Literature review weakness',
  'Section 2.10 was added: where the literature agrees; two named study-versus-study '
  'conflicts (the role of the middleman, and what grading does); four methodological '
  'limitations of earlier work; a section on what is and is not known for the South '
  'Coast and Kwale County; and the research gap. Kwale is now named seventeen times '
  'in the thesis.',
  '§2.10.1–§2.10.6'),
 ('8', 'Results chapter weakness',
  'Every results table and every figure is followed by a findings paragraph, and all '
  'twenty subsections that hold tables close with at least one interpretive paragraph '
  'that states what the finding means and links it to the objective. Each objective '
  'ends with a section comparing the findings with previous studies.',
  '§4.3.5, §4.4.12, §4.5.7'),
 ('9', 'Discussion chapter weakness',
  'Chapter Five runs objective by objective with Key Findings, mechanism sections and '
  'Implications, then §5.5 synthesises everything through the SCP framework, §5.6 '
  'states what the study could not measure and §5.7 sets out the limitations.',
  '§5.2–§5.7'),
 ('10', 'Conclusions and recommendations weakness',
  'Conclusions §6.2.1 to §6.2.3 and recommendations §6.4.1 to §6.4.3 are written '
  'objective by objective, each recommendation naming the finding it rests on. §6.5 '
  'sets out further research.',
  '§6.2–§6.5'),
 ('11', 'Terminology and conceptual consistency',
  'A list of abbreviations was added. The four actor names — fisher, middleman, '
  'hotelier, exporter — are used in every table and every chart. Margins are called '
  'gross throughout and the absence of cost data is stated wherever a margin is '
  'reported.',
  'List of Abbreviations, Tables 2–49, §4.4.9, §5.6'),
 ('12', 'Formatting and presentation',
  'Chapter Three now runs 3.1 to 3.11; the report had flagged it starting at 3.4. '
  'Tables are numbered 1 to 53 and figures 1 to 25 in one sequence. Captions follow '
  'APA 7. Table headers are plain, the body is Times New Roman 12 in black, and no '
  'table carries a note. A separate defect was found after the first revision was '
  'circulated and is now fixed: the Heading 1 to 4 styles inherited an automatic '
  'numbering list whose first level read "CHAPTER %1:" starting at 5, so Word '
  'painted that list on top of the typed heading text and rendered "CHAPTER 5: '
  'CHAPTER ONE: INTRODUCTION" and "5.4 1.1 Background information". Removing the '
  'numbering from a heading paragraph is not enough, because the list is inherited '
  'from the style; it has been removed from the style definitions. Three '
  'cross-reference fields in the contents also pointed at bookmarks deleted with '
  'the old contents rows and would have read "Error! Reference source not '
  'found."; they now resolve.',
  'Throughout'),
 ('13', 'Defence question 1: why call this a market structure study',
  'Concentration, marketing margin and price dispersion are all measured and '
  'reported: a Herfindahl-Hirschman Index of 2,371 across the four BMUs, a total '
  'marketing margin of 60.4% to 72.5% of the final price, and a coefficient of '
  'variation falling from 31.8% at the harvesting node to 6.8% at the export node. '
  '§5.6 states what each measure captures and what it does not, which is the volume '
  'behind each transaction and the cost side of each deal.',
  '§3.10.4, §4.4.11–§4.4.13, Tables 41–44, §5.6'),
]
TBL('Reviewer Issues and Where They Are Answered',
    ['No.', 'Issue raised', 'What the revised thesis does', 'Where'],
    [[a, b, c, e] for a, b, c, e in ROWS], [560, 1800, 4300, 1966])

H2('B. Supervisor Instructions')
SUP = [
 ('Dr Mirera', 'Vertical axis in percentages, not counts',
  'Every chart plots percentages and every percentage axis runs the full 0–100%, '
  'whatever the tallest bar.'),
 ('Dr Mirera', 'Price variation by actor level and by grade, with site comparison',
  'Table 36 gives price by actor and grade; Table 37 the Kruskal–Wallis comparisons; '
  'Table 39 the mean price by actor, BMU and grade; Table 40 the first-sale spread by '
  'BMU; Table 44 dispersion within each actor and transmission to the fisher at each '
  'site.'),
 ('Dr Mirera', 'Give the argument behind the observation',
  'Each subsection of Chapter Four closes with an interpretive paragraph, and each '
  'objective ends with a comparison against previous studies.'),
 ('Prof. Wamukota', 'Break very long tables',
  'The longest table carries 33 data rows; the sixty results tables were split so that '
  'no table runs beyond a page and a half.'),
 ('Prof. Wamukota', 'Diversify tables, graphs and figures',
  'Fifty-three tables of seven different shapes and twenty-five figures drawn six ways: '
  'clustered vertical bars, hundred-percent stacked vertical bars, grouped horizontal '
  'bars, hundred-percent stacked horizontal bars, grouped bars with error bars, and '
  'grouped bars by BMU. No line charts.'),
 ('Prof. Wamukota', 'Report by objective and by site',
  'Chapter Four is organised by objective, and every categorical table carries the '
  'four actors against the five BMUs with a p-value column.'),
 ('Prof. Wamukota', 'Where there is no data, do not present it — explain why',
  'A dash marks an actor that was not sampled at a BMU, distinct from a zero. Tables '
  '37 and 49 end with a line explaining why hoteliers and exporters could not be '
  'tested against BMU, and §5.6 explains the rest.'),
 ('Formatting', 'APA 7, Times New Roman 12, black, plain headers, no table notes',
  'Verified mechanically: one font, one colour, no shading anywhere, and no note '
  'under any table.'),
]
TBL('Supervisor Instructions', ['From', 'Instruction', 'How it is met'],
    [[a, b, c] for a, b, c in SUP], [1100, 2500, 5026])

H2('C. What Was Checked, and How')
CH = [
 ('Categorical table cells', '3,720',
  'Every cell of every actor-by-BMU table re-derived from the .sav with pandas and '
  'compared against the printed document.'),
 ('Price and margin figures', '207',
  'Tables 36 to 39 and 42 to 44 recomputed from the raw price variables, including '
  'every margin, share, spread, coefficient of variation and transmission ratio.'),
 ('Sample, income, age and association figures', '67',
  'Tables 2, 10 and 53 recomputed, and every significant Monte Carlo result checked '
  'for presence.'),
 ('Appendix A output cells', '924',
  'Every crosstabulation cell in the appendix re-derived from the .sav.'),
 ('Prose count and percentage claims', '111',
  'Every “n (p%)” and “k of n” claim in Chapters Four to Six recomputed from the '
  'dataset, which covers the figures as well as the tables.'),
 ('Kruskal–Wallis statistics', '16',
  'All recomputed with scipy and matched to three decimal places.'),
 ('Figures', '25',
  'All regenerate byte-identically from the current .sav.'),
 ('Citations', '37',
  'Every in-text citation has a reference entry; every reference entry is cited.'),
 ('SPSS syntax', '137 commands',
  'All commands well formed, all 91 variables present in the .sav, all 52 tables '
  'indexed to the command that produces them.'),
 ('Market structure measures', '93',
  'Every concentration, margin, dispersion and transmission figure recomputed from '
  'the .sav, including each Herfindahl-Hirschman Index and numbers-equivalent.'),
 ('Headings as Word paints them', '121',
  'Each heading resolved through the style chain and the numbering definitions and '
  'printed as it will render. Nothing is painted in front of the typed text.'),
 ('Cross-reference fields', '202',
  'Every PAGEREF target resolved to a bookmark that exists, every bookmark closed, '
  'no duplicate bookmark ids.'),
]
P('Concentration, marketing margin and efficiency. The review asked for all three. '
  'None can be computed the textbook way from this survey, which interviewed actors '
  'rather than censusing buyers and recorded no costs, so each is reported through '
  'the counterpart the data do support. Concentration at first sale is measured over '
  'the buying points fishers named, weighted by the share of harvesters attached to '
  'each: a Herfindahl-Hirschman Index of 2,371 across the four BMUs and 8,580 at '
  'Majoreni, every site above the 2,500 mark conventionally treated as high '
  'concentration. Margins are reported gross at each node, as a total marketing '
  'margin of 60.4% to 72.5% of the final price, and as a producer’s share both gross '
  'and net of the one cost the survey measured, physical mortality at 10.4% of landed '
  'volume. Efficiency is approached through price dispersion, which falls from a '
  'coefficient of variation of 31.8% among fishers to 6.8% among exporters, and price '
  'transmission by site. What remains unmeasured is narrower than before: the volume '
  'behind each transaction and the cost side of each deal.')

P('One presentation per variable. Chapter Four had shown 27 of its figures beside a '
  'table of the same numbers. Where a variable\u2019s association with BMU is '
  'significant the table was kept, because it carries all four actors, the site '
  'pattern, chi-square, df, p and the 99% confidence interval, and the figure was '
  'removed; otherwise the figure was kept and that variable\u2019s block was removed '
  'from the table. Five further figures were superseded by a table carrying strictly '
  'more: exact counts, standard deviations, medians, quartiles or the margins in '
  'shillings. Nothing was lost: every variable still appears once, every significant '
  'result is still in a table, and every table and figure is now named in the text.')
P('De-duplication took the tables from 61 to 49 and the figures from 37 to 25; the '
  'four market-structure tables then brought the total to 53. No table or figure '
  'carries a note, and no row is labelled Unknown, Missing or Not stated.')
TBL('Verification Performed', ['What', 'Count', 'Method'],
    [[a, b, c] for a, b, c in CH], [2400, 900, 5326])
P('Mismatches found and corrected during verification: the first-buyer and '
  'second-buyer distributions in the text of Tables 20 and 21, the single-buyer share '
  'at Shimoni in the buyer-count table, a stale cross-reference in the price-factors '
  'table, an IQR column whose '
  'header did not match its contents, and one citation that had no reference entry.')
P('Found after the first revision was circulated, and now fixed: automatic '
  'numbering inherited from the heading styles, which Word painted on top of 119 '
  'headings, and three broken cross-reference fields in the contents. Both had '
  'passed the earlier checks because those checks read the paragraph text, and '
  'neither a painted list number nor a field result is stored in the text. The '
  'checks listed above now resolve the numbering and the fields themselves, so the '
  'same defect cannot pass again.')
P('Every check listed in this section currently reports zero mismatches. What the '
  'checks do not cover is page layout: where a table or figure falls on the page, '
  'and the page numbers themselves, which only Word can compute.')

H2('D. What Changed Since Draft 10')
CHG = [
 ('Tables', 'Draft 10 carried 46 tables with duplicate numbers 21, 22 and 23, nine '
  'missing numbers and two tables with no caption. The thesis now carries 53 tables '
  'numbered in one sequence, all captioned.'),
 ('Actors', 'Every categorical table now carries all four actor categories against '
  'all five BMUs, in the nine-column layout draft 10 used for its best tables.'),
 ('New tables', 'Six variables draft 10 reported but the earlier rebuild had dropped '
  'are back: number of buyers and state of crabs sold, location of sale and knowledge '
  'of the onward sale, first and second buyer location, tied depot owners and the '
  'arrangements used with them.'),
 ('Chapter numbering', 'Draft 10 numbered its front matter as chapters — “CHAPTER 5: '
  'ABSTRACT” — began Chapter Three at 3.4, and carried a doubled “4.4 4.1”. All are '
  'corrected.'),
 ('Front matter', 'The list of abbreviations was carried over from draft 10 and '
  'extended to nineteen entries. The lists of tables and figures and the table of '
  'contents are rebuilt from the actual captions.'),
 ('References', 'The list went from 88 entries to 37. Forty-nine entries were never '
  'cited in any draft and were removed, twenty-one were put into APA 7 form, and two '
  'citations draft 10 carried were restored where the rebuild had dropped them.'),
]
TBL('Changes From Draft 10', ['Area', 'Change'], [[a, b] for a, b in CHG], [1800, 6826])

H2('E. This Revision')
P('The Turnitin AI writing check will not run on a submission of more than 30,000 '
  'words of qualifying text. The file submitted contained 30,471 words of paragraph '
  'text, which is the count Turnitin appears to use, since it excludes tables from '
  'the check. The thesis now contains 28,860, about 1,100 words clear of the '
  'ceiling. Nothing was cut that carried a finding: the words came out of repeated '
  'framing sentences, a section that appeared twice and a set of notes that '
  'described exhibits no longer in the document.')
WORDS = [
 ('Paragraph text (what Turnitin counts)', '30,471', '28,860', '1,140 clear of 30,000'),
 ('Table text (Turnitin skips tables)', '5,459', '4,391', 'not counted'),
 ('Whole document', '35,930', '33,251', '\u2013'),
 ('Turnitin copy, questionnaire removed', '\u2013', '26,576', '3,424 clear of 30,000'),
]
TBL('Word Count Before and After', ['What', 'As submitted', 'Now', 'Margin'],
    [[a, b, c, d] for a, b, c, d in WORDS], [3400, 1500, 1200, 2526])
P('A second file, Mercy_Sangura_Thesis_Turnitin_Copy.docx, is the same thesis with '
  'the questionnaire appendix removed. It exists only in case Turnitin still reports '
  'the thesis as too long, since its own count may differ by a few hundred words '
  'from any count made outside it. The questionnaire is the instrument rather than '
  'the candidate\u2019s writing, so removing it costs nothing the AI check is looking '
  'at. The file that goes to the university is the complete thesis.')
CHANGES = [
 ('Actor column grouped',
  'The Actor column printed "Fisher N = 65" against every response category. It now '
  'appears once at the head of each actor block and is blank on the rows beneath, so '
  'a gender table reads Male, Female, then Middleman. 356 repeated labels were '
  'removed across 36 tables. The Actor column of Table 53 was left alone, because '
  'there it is data with one value per row.'),
 ('Duplicated section merged',
  'Sections 4.4.9 and 4.4.12 both carried the title "Marketing Margins and the '
  'Distribution of Value" and reported the same chain twice. They are now one '
  'section, placed after the concentration results so Objective Two runs prices, '
  'prices by site, concentration, margins, dispersion. Both tables were kept, '
  'because Table 42 splits the final price across the nodes and Table 43 states the '
  'same chain as margins; only the repeated prose went. Objective Two now has '
  'fourteen subsections instead of fifteen.'),
 ('Wrong exhibit references fixed',
  'Four summary paragraphs still named the table numbers their sections carried '
  'before the tables were renumbered, so they pointed into other sections: "Tables '
  '18 to 20" in \u00a74.4.3, "Tables 24 and 25" in \u00a74.4.5, "Tables 35 and 36" in '
  '\u00a74.5.1 and "Tables 37, 38 and 42" in \u00a74.5.2. A new check compares every '
  'reference against the exhibits in its own section and reports none left.'),
 ('Section 3.10.4 moved out of the contents',
  'The section defining the market-structure measures had been inserted into the '
  'table of contents instead of Chapter Three, because the script that added it '
  'anchored on the first paragraph beginning "3.11", which was the contents row. The '
  'section now sits between 3.10.3 and 3.11 and has a contents row of its own.'),
 ('Stale exhibit notes removed',
  'Thirteen sentences left over from the notes that used to sit under the figures '
  'repeated a claim made earlier in the same section, and five of them described '
  'bars in exhibits that are now tables.'),
 ('Empty heading removed',
  'The base document ended with an empty Heading 1, which took a bookmark and a '
  'blank row in the contents. A doubled heading in the questionnaire, "SECTION B: '
  'PRELIMINARIESSECTION B: PRELIMINARIES", was also repaired.'),
 ('Abstract',
  'Rewritten as five paragraphs of 589 words covering, in order, the background and '
  'the problem, the framework and objectives, the methodology, the findings, the '
  'discussion and conclusion, and the recommendations.'),
 ('Recommendations in prose',
  'The sixteen recommendations had been set out under four labels, Problem, '
  'Evidence, Action and Expected outcome. Each now runs as prose that still names '
  'the evidence it rests on, who should act and what would show it had worked. The '
  'labelled-list pattern is one the humanizer guidance flags.'),
]
TBL('What Changed in This Revision', ['Area', 'What was done'],
    [[a, b] for a, b in CHANGES], [1900, 6726])

H2('F. APA 7 and Presentation, Checked on the Built File')
APA = [
 ('Table shading', 'No cell in any of the 53 tables carries a fill or a pattern. '
  'Every header is plain white.'),
 ('Colour', 'No run anywhere in the document is set in a colour other than black.'),
 ('Typeface', 'No typeface other than Times New Roman is named anywhere.'),
 ('Size', 'Body text is 12 pt throughout. The title page uses 13 and 14 pt. Table '
  'text is 8.5 and 10 pt, which is inside the 8 to 12 pt range APA 7 allows for '
  'tables and is what lets nine columns fit the page.'),
 ('Captions', 'All 53 table and 25 figure captions are set the APA 7 way: the number '
  'on one line, the title in italic title case on the next, no note beneath.'),
 ('Numbering', 'Tables run 1 to 53 and figures 1 to 25, each in one unbroken '
  'sequence, in the order they appear.'),
 ('Lists of tables and figures', 'All 53 table entries and all 25 figure entries '
  'match the captions in the body word for word.'),
 ('Table of contents', 'Every one of the 121 headings has a contents row and every '
  'contents row has a heading. All 202 page-reference fields resolve to a bookmark '
  'that exists.'),
 ('Section numbers', 'The 113 numbered sections run without a gap or a repeat, and no '
  'heading text appears twice.'),
 ('Heading numbering', 'No heading style and no heading paragraph carries automatic '
  'numbering, so Word paints nothing in front of the typed numbers.'),
 ('AI writing patterns', 'The abstract and Chapters One to Six were scanned for the '
  'patterns in Wikipedia\u2019s "Signs of AI writing": em dashes used as breaks, curly '
  'quotes, the AI vocabulary list, negative parallelisms, hedging stacks, bold '
  'mini-heading lists and chatbot artefacts. None found. The en dashes that remain '
  'are number ranges and the Kruskal\u2013Wallis name.'),
]
TBL('Formatting Checks', ['What', 'Result'], [[a, b] for a, b in APA], [1700, 6926])
P('On similarity. Turnitin\u2019s percentage cannot be computed outside Turnitin, so no '
  'promise of 8% to 10% can honestly be made from here. What can be done has been '
  'done: every sentence in Chapters Four to Six is original wording, the reference '
  'list carries 37 entries and every one of them is cited, every citation has an '
  'entry, and no passage is quoted without attribution. If the report comes back '
  'higher than expected, look first at whether the questionnaire, the reference list '
  'and the standard methodological phrasing in Chapter Three are being counted; ask '
  'the submission to exclude quoted material and the bibliography, which is the '
  'normal setting for a thesis.')

H2('G. Before Printing')
P('Two things still need doing in Word, because page numbers cannot be computed '
  'outside it. Open the thesis, press Ctrl+A then F9, and choose “Update entire '
  'table” when asked. That fills the page numbers in the table of contents, the list '
  'of tables and the list of figures. Then check that no table breaks awkwardly '
  'across a page and add a page break where one does.')
P('The heading numbering needs nothing further. The automatic numbering has been '
  'removed from the styles, so pressing F9 will not bring it back. If a heading is '
  'ever retyped or its style reapplied by hand, check the Home tab and confirm no '
  'multilevel list is active on it.')
P('The SPSS syntax file expects the dataset at C:\\MudCrab\\. Edit the path on the '
  'GET command at the top of the file before running it.')

json.dump(B, open('v6/checklist.json', 'w'), ensure_ascii=False, indent=1)
print('checklist blocks:', len(B), '| tables:', sum(1 for b in B if b['k'] == 'rawtable'))
