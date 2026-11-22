import re, copy, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches as DInches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_COLOR_INDEX, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_BREAK
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from pptx import Presentation
from pptx.util import Inches, Pt as PPt, Emu
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn as pqn
from lxml import etree

from essay import SECTIONS
from slides import SLIDES, QA
from refs import REFS

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
import os; os.makedirs(OUT, exist_ok=True)

NAVY = RGBColor(0x1F, 0x38, 0x64)
PH = re.compile(r"(\[[^\]]+\])")
TOC_PAGES = {}  # filled on second pass
if os.path.exists(os.path.join(OUT, "toc_pages.txt")):
    for line in open(os.path.join(OUT, "toc_pages.txt")):
        k, v = line.rstrip("\n").split("\t"); TOC_PAGES[k] = v

# ---------------------------------------------------------------- docx helpers
def add_runs(p, text, italic=False, bold=False, size=None):
    for part in PH.split(text):
        if not part: continue
        r = p.add_run(part)
        r.italic = italic; r.bold = bold
        if size: r.font.size = Pt(size)
        if PH.fullmatch(part):
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return p

def add_field(run, instr):
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = "1"
    f3 = OxmlElement("w:fldChar"); f3.set(qn("w:fldCharType"), "end")
    for e in (f1, it, f2, t, f3): run._r.append(e)

def setup_doc(spacing=1.5, size=11):
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Arial"; st.font.size = Pt(size)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    pf = st.paragraph_format
    pf.line_spacing = spacing; pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, sz in (("Heading 1", 14), ("Heading 2", 12), ("Title", 22), ("Subtitle", 14)):
        s = d.styles[name]
        s.font.name = "Arial"; s.font.size = Pt(sz); s.font.color.rgb = NAVY
        rpr = s.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None: rf = OxmlElement("w:rFonts"); rpr.append(rf)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): rf.set(qn(a), "Arial")
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
        s.font.bold = name.startswith("Heading") or name == "Title"
        s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        s.paragraph_format.space_before = Pt(12 if name.startswith("Heading") else 0)
        s.paragraph_format.space_after = Pt(6)
        s.paragraph_format.line_spacing = 1.15
    # remove the Title style's bottom border
    tp = d.styles["Title"].element.find(qn("w:pPr"))
    if tp is not None:
        for b in tp.findall(qn("w:pBdr")): tp.remove(b)
    sec = d.sections[0]
    sec.page_height = Cm(29.7); sec.page_width = Cm(21.0)
    for m in ("left_margin", "right_margin"): setattr(sec, m, Cm(2.54))
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    return d

def d_footer_stops():
    return [DInches(3.25), DInches(6.5)]

def footer(sec):
    f = sec.footer; f.is_linked_to_previous = False
    p = f.paragraphs[0]; p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    width = sec.page_width - sec.left_margin - sec.right_margin
    for ts in d_footer_stops(): p.paragraph_format.tab_stops.add_tab_stop(ts, WD_TAB_ALIGNMENT.CLEAR)
    p.paragraph_format.tab_stops.add_tab_stop(width, WD_TAB_ALIGNMENT.RIGHT)
    p.paragraph_format.line_spacing = 1.0
    add_runs(p, "Student ID: [add ID]", size=10)
    r = p.add_run("\tPage "); r.font.size = Pt(10)
    r = p.add_run(); r.font.size = Pt(10); add_field(r, "PAGE")

def page_break(d):
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

def cover(d, title, subtitle, extra):
    for _ in range(5): d.add_paragraph()
    d.add_paragraph(title, style="Title")
    d.add_paragraph(subtitle, style="Subtitle")
    d.add_paragraph()
    for line in extra:
        p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_runs(p, line)

# ---------------------------------------------------------------- assignment
def build_assignment():
    d = setup_doc()
    footer(d.sections[0])
    body_words = sum(len(p.split()) for _, ps in SECTIONS for p in ps)
    cover(d, "Nursing care for an adult with hypertension",
          "Supporting care plan and critical rationale",
          ["Student ID: [add ID]",
           "Module code: MOD004785",
           "Module title: [add module title]",
           "Submission date: [add date]",
           f"Word count: {body_words:,} (main body, including in-text citations; excluding cover, contents, headings, references and appendix)",
           "Referencing: ARU Harvard",
           "Confidentiality: Mr A is a pseudonym. The patient, staff, organisation and care setting are anonymised in line with the NMC Code (NMC, 2018)."])
    page_break(d)
    d.add_paragraph("Contents", style="Title")
    entries = [h for h, _ in SECTIONS] + ["References", "Appendix 1: Care plan"]
    width = d.sections[0].page_width - d.sections[0].left_margin - d.sections[0].right_margin
    for e in entries:
        p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.tab_stops.add_tab_stop(width, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        p.add_run(f"{e}\t{TOC_PAGES.get(e, '0')}")
    page_break(d)
    first = True
    for h, ps in SECTIONS:
        d.add_paragraph(h, style="Heading 1")
        for t in ps:
            add_runs(d.add_paragraph(), t)
    page_break(d)
    d.add_paragraph("References", style="Heading 1")
    for ref in REFS:
        p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0)
        for text, it in ref: p.add_run(text).italic = it
    # Appendix in landscape
    sec = d.add_section(WD_SECTION.NEW_PAGE)
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    footer(sec)
    d.add_paragraph("Appendix 1: Care plan", style="Heading 1")
    p = d.add_paragraph("Summary of the care plan discussed in the main text. Excluded from the word count.")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    cols = ["Priority need", "Goal", "Nursing interventions", "Rationale and evidence", "Evaluation"]
    rows = [
     ["1. Persistently raised blood pressure (172/104, then 168/102 mmHg) with risk of cardiovascular and renal harm",
      "Same-day report to prescriber; documented review and reliable baseline; investigations completed within the timescale set; progress towards clinic <140/90 or home <135/85 mmHg",
      "Check cuff, position and rest; repeat measurement. Report readings, symptoms and missed doses. Request urine ACR and haematuria, U&E, HbA1c, lipids, ECG, fundoscopy. Teach validated home monitoring; paper diary with named reviewer and action limits. Safety-net emergency symptoms.",
      "Silent target-organ damage (Oparil et al., 2018). Targets, thresholds and investigations (NICE, 2026). Supported self-monitoring more effective than monitoring alone (Tucker et al., 2017; McManus et al., 2021). Work within competence (NMC, 2018).",
      "Review documented with date; results seen by named clinician; home average compared with baseline and target; earlier review if symptoms or rising readings"],
     ["2. Difficulty sustaining prescribed treatment (2 to 3 missed doses a week; shift work; worry about lifelong medicine)",
      "Within two weeks: explains regimen, demonstrates monitoring and, if agreed as realistic, misses no more than one dose in seven days",
      "Explore beliefs and barriers without blame. Pharmacist agrees a dosing time and daily cue that fits shifts. Teach-back. Explain missed-dose advice (never double). Refer side effects to prescriber. Paper information; partner involved only with consent.",
      "Supportive-educative nursing system (Orem, 2001). Adherence and shared decisions (NICE, 2009; 2021). Once-daily dosing (NHS, 2026). Consent and confidentiality (NMC, 2018).",
      "Diary: missed doses and reasons; plan explained in own words; technique observed; goal met or renegotiated"],
    ]
    t = d.add_table(rows=1 + len(rows), cols=len(cols))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Cm(4.0), Cm(4.4), Cm(6.2), Cm(5.6), Cm(4.4)]
    t.autofit = False
    for i, w in enumerate(widths): t.columns[i].width = w
    for i, c in enumerate(cols):
        cell = t.rows[0].cells[i]; cell.text = ""
        pp = cell.paragraphs[0]; r = pp.add_run(c); r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255)
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "1F3864")
        cell._tc.get_or_add_tcPr().append(shd)
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for ri, row in enumerate(rows, 1):
        for ci, val in enumerate(row):
            cell = t.rows[ri].cells[ci]; cell.text = ""
            pp = cell.paragraphs[0]; pp.add_run(val).bold = (ci == 0)
    for row in t.rows:
        for ci, cell in enumerate(row.cells):
            cell.width = widths[ci]
            for pp in cell.paragraphs:
                pp.alignment = WD_ALIGN_PARAGRAPH.LEFT
                pp.paragraph_format.line_spacing = 1.15; pp.paragraph_format.space_after = Pt(2)
    path = os.path.join(OUT, "hypertension_supporting_assignment_2700_words.docx")
    d.save(path); return path

# ---------------------------------------------------------------- timings
def mmss(s): return f"{s//60}:{s%60:02d}"
def timings():
    timed = [s for s in SLIDES if s["time"]]
    w = [len(s["notes"].split()) for s in timed]
    tot = sum(w); cum = 0; out = []
    t0 = 0
    for i, n in enumerate(w):
        cum += n
        t1 = 1200 if i == len(w) - 1 else int(round(cum / tot * 1200 / 5.0) * 5)
        out.append((mmss(t0), mmss(t1), t1 - t0)); t0 = t1
    for s, t in zip(timed, out): s["timing"] = t

# ---------------------------------------------------------------- speaker notes docx
def build_notes():
    d = setup_doc(spacing=1.15, size=12)
    footer(d.sections[0])
    script_words = sum(len(s["notes"].split()) for s in SLIDES if s["time"])
    cover(d, "Hypertension presentation: speaker notes",
          "20-minute script and question preparation",
          ["Student ID: [add ID]", "Module code: MOD004785", "Module title: [add module title]",
           "Presentation date: [add date]"])
    d.add_paragraph()
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.add_run(f"Slides 1 to 18 run for 20 minutes. The script is {script_words:,} words, about {round(script_words/20)} words a minute, which leaves room to pause and point at the tables. The same script is in the PowerPoint notes pane. Questions follow for up to 10 minutes. Replace every yellow placeholder with your own experience before presenting.")
    page_break(d)
    n = 0
    for i, s in enumerate(SLIDES, 1):
        if not s["time"]: continue
        d.add_paragraph(f"Slide {i}: {s['title']}", style="Heading 1")
        a, b, dur = s["timing"]
        p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(f"{a} to {b}  ({dur} seconds)"); r.bold = True; r.font.color.rgb = RGBColor(0x0F, 0x6E, 0x75)
        add_runs(d.add_paragraph(), s["notes"])
    page_break(d)
    d.add_paragraph("Questions and answers (up to 10 minutes)", style="Heading 1")
    for q, a in QA:
        d.add_paragraph(q, style="Heading 2")
        add_runs(d.add_paragraph(), a)
    d.add_paragraph("Before you present", style="Heading 1")
    for line in ["Replace every yellow placeholder with your own anonymised experience. Do not describe care you did not give.",
                 "Add your student ID, module title and presentation date to the title slide and slide footers.",
                 "Rehearse with a timer. If you run long, trim slide 11 first; it carries the most detail."]:
        p = d.add_paragraph(line, style="List Bullet"); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    d.add_paragraph("References", style="Heading 1")
    for ref in REFS:
        p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0)
        for text, it in ref: p.add_run(text).italic = it
    path = os.path.join(OUT, "hypertension_20_minute_speaker_notes_and_questions.docx")
    d.save(path); return path

# ---------------------------------------------------------------- pptx
P_NAVY = PRGB(0x1F, 0x38, 0x64); P_TEAL = PRGB(0x0F, 0x6E, 0x75)
P_TEXT = PRGB(0x22, 0x22, 0x22); P_GREY = PRGB(0x59, 0x59, 0x59)
P_LIGHT = PRGB(0xEE, 0xF3, 0xF8); P_WHITE = PRGB(0xFF, 0xFF, 0xFF)
SW, SH = Inches(13.333), Inches(7.5)

def decorative(shape):
    cNvPr = shape._element.find(".//" + pqn("p:cNvPr"))
    cNvPr.set("descr", "")
    ext_lst = etree.SubElement(cNvPr, pqn("a:extLst"))
    ext = etree.SubElement(ext_lst, pqn("a:ext")); ext.set("uri", "{C183D7F6-B498-43B3-948B-1728B52AA6E4}")
    dec = etree.SubElement(ext, "{http://schemas.microsoft.com/office/drawing/2017/decorative}decorative",
                           nsmap={"adec": "http://schemas.microsoft.com/office/drawing/2017/decorative"})
    dec.set("val", "1")

def rect(slide, x, y, w, h, color, back=True):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background(); s.shadow.inherit = False
    decorative(s)
    if back:
        sp = s._element; tree = sp.getparent(); tree.remove(sp); tree.insert(2, sp)
    return s

def style_run(r, size, color=P_TEXT, bold=False, italic=False):
    r.font.name = "Arial"; r.font.size = PPt(size); r.font.color.rgb = color
    r.font.bold = bold; r.font.italic = italic

def ptext(p, text, size, color=P_TEXT, bold=False, italic=False):
    for part in PH.split(text):
        if not part: continue
        r = p.add_run(); r.text = part; style_run(r, size, color, bold, italic)
        if PH.fullmatch(part):
            hl = etree.SubElement(r._r.get_or_add_rPr(), pqn("a:highlight"))
            c = etree.SubElement(hl, pqn("a:srgbClr")); c.set("val", "FFFF00")
            # highlight must follow fill elements in schema order; move to end is fine for solidFill/latin? place before latin
            rPr = r._r.get_or_add_rPr(); rPr.remove(hl)
            latin = rPr.find(pqn("a:latin"))
            if latin is not None: latin.addprevious(hl)
            else: rPr.append(hl)

def footer_bar(slide, num):
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(7.0), Inches(9), Inches(0.35))
    tf = tb.text_frame; tf.margin_left = tf.margin_right = 0; tf.word_wrap = True
    from pptx.enum.text import MSO_AUTO_SIZE; tf.auto_size = MSO_AUTO_SIZE.NONE
    ptext(tf.paragraphs[0], "MOD004785  |  Student ID [add ID]", 12, P_GREY)
    tb2 = slide.shapes.add_textbox(Inches(11.9), Inches(7.0), Inches(0.83), Inches(0.35))
    tb2.text_frame.word_wrap = True
    p = tb2.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    ptext(p, str(num), 12, P_GREY)

def header(slide, title):
    rect(slide, 0, 0, SW, Inches(1.15), P_NAVY)
    rect(slide, 0, Inches(1.15), SW, Inches(0.07), P_TEAL)
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.6), Inches(0.1), Inches(12.1), Inches(0.95)
    tf = t.text_frame; tf.clear(); tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    ptext(p, title, 30, P_WHITE, bold=True)

def set_notes(slide, s):
    tf = slide.notes_slide.notes_text_frame
    if s.get("timing"):
        a, b, dur = s["timing"]
        tf.text = f"Time {a} to {b} ({dur} seconds)\n\n{s['notes']}"
    else:
        tf.text = s["notes"]

def bullets_slide(prs, s, num):
    sl = prs.slides.add_slide(prs.slide_layouts[1])
    header(sl, s["title"])
    body = sl.placeholders[1]
    body.left, body.top, body.width, body.height = Inches(0.6), Inches(1.55), Inches(12.1), Inches(5.25)
    tf = body.text_frame; tf.clear(); tf.word_wrap = True
    for i, b in enumerate(s["body"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = PPt(14); p.line_spacing = 1.05
        ptext(p, b, 24)
    set_notes(sl, s); footer_bar(sl, num)
    return sl

def table_slide(prs, s, num):
    sl = prs.slides.add_slide(prs.slide_layouts[5])
    header(sl, s["title"])
    tb = s["table"]; nrows = len(tb["rows"]) + 1; ncols = len(tb["cols"])
    shape = sl.shapes.add_table(nrows, ncols, Inches(0.6), Inches(1.55), Inches(sum(tb["widths"])), Inches(0.6 * nrows))
    shape.name = s["title"] + " table"
    tbl = shape.table
    for i, w in enumerate(tb["widths"]): tbl.columns[i].width = Inches(w)
    size = 20
    for ci, c in enumerate(tb["cols"]):
        cell = tbl.cell(0, ci); cell.fill.solid(); cell.fill.fore_color.rgb = P_NAVY
        cell.text_frame.paragraphs[0].text = ""
        ptext(cell.text_frame.paragraphs[0], c, size, P_WHITE, bold=True)
    for ri, row in enumerate(tb["rows"], 1):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci); cell.fill.solid()
            cell.fill.fore_color.rgb = P_LIGHT if ri % 2 else P_WHITE
            cell.text_frame.paragraphs[0].text = ""; cell.text_frame.word_wrap = True
            ptext(cell.text_frame.paragraphs[0], val, size, P_TEXT, bold=(ci == 0))
    avail = Inches(4.7)
    tbl.rows[0].height = Inches(0.6)
    for r in list(tbl.rows)[1:]: r.height = int((avail - Inches(0.6)) / (nrows - 1))
    for r in tbl.rows:
        for c in r.cells:
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = c.margin_right = Inches(0.1); c.margin_top = c.margin_bottom = Inches(0.06)
    if s.get("cite"):
        cb = sl.shapes.add_textbox(Inches(0.6), Inches(6.45), Inches(12.1), Inches(0.4))
        cb.text_frame.word_wrap = True
        ptext(cb.text_frame.paragraphs[0], "Sources: " + s["cite"], 14, P_GREY)
    set_notes(sl, s); footer_bar(sl, num)
    return sl

def title_slide(prs, s):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    rect(sl, 0, 0, SW, SH, P_NAVY)
    rect(sl, Inches(0.8), Inches(3.55), Inches(1.6), Inches(0.09), P_TEAL, back=False)
    # keep the accent bar behind text placeholders
    t = sl.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.8), Inches(1.4), Inches(11.5), Inches(2.0)
    tf = t.text_frame; tf.clear(); tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    ptext(p, "Nursing care for an adult with hypertension", 44, P_WHITE, bold=True)
    sub = sl.placeholders[1]
    sub.left, sub.top, sub.width, sub.height = Inches(0.8), Inches(3.9), Inches(11.5), Inches(2.6)
    tf = sub.text_frame; tf.clear(); tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
    lines = ["Student ID: [add ID]", "Module: MOD004785 [add module title]", "Presentation date: [add date]",
             "Summative assessment: 20-minute presentation"]
    for i, l in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT; p.space_after = PPt(6)
        ptext(p, l, 22, PRGB(0xDD, 0xE6, 0xF0))
    set_notes(sl, s)

def short_ref(ref):
    segs = [list(x) for x in ref]
    m = re.match(r"^(.*?), (\d{4})\. ", segs[0][0])
    if m:
        authors = m.group(1)
        if authors.count(".,") >= 3:
            first = authors.split("., ")[0] + "."
            segs[0][0] = segs[0][0].replace(authors, first + " et al.", 1)
    out = []
    for text, it in segs:
        text = text.replace(" [Accessed 19 November 2026].", "").replace("[online] ", "")
        text = re.sub(r"Available at: <([^>]+)>", r"\1", text)
        out.append((text, it))
    return out

def ref_slides(prs, start):
    groups = [REFS[0:5], REFS[5:9], REFS[9:13]]
    num = start
    for gi, g in enumerate(groups, 1):
        sl = prs.slides.add_slide(prs.slide_layouts[5])
        header(sl, f"References ({gi} of {len(groups)})")
        tb = sl.shapes.add_textbox(Inches(0.6), Inches(1.5), Inches(12.1), Inches(5.3))
        tf = tb.text_frame; tf.word_wrap = True
        for i, ref in enumerate(g):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = PPt(10)
            pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(Inches(0.4))); pPr.set("indent", str(-Inches(0.4)))
            for text, it in short_ref(ref):
                r = p.add_run(); r.text = text; style_run(r, 16, P_TEXT, italic=it)
        if gi == len(groups):
            p = tf.add_paragraph(); p.space_before = PPt(6)
            r = p.add_run(); r.text = "Online sources accessed 19 November 2026. Full author lists are in the written assignment."
            style_run(r, 13, P_GREY)
        sl.notes_slide.notes_text_frame.text = "Reference list. Not part of the spoken script."
        footer_bar(sl, num); num += 1

def build_pptx():
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH
    for i, s in enumerate(SLIDES, 1):
        if s["kind"] == "title": title_slide(prs, s)
        elif s["kind"] == "table": table_slide(prs, s, i)
        else: bullets_slide(prs, s, i)
    ref_slides(prs, len(SLIDES) + 1)
    prs.core_properties.title = "Nursing care for an adult with hypertension"
    prs.core_properties.author = "Student ID"
    path = os.path.join(OUT, "hypertension_summative_20_minutes.pptx")
    prs.save(path); return path

if __name__ == "__main__":
    timings()
    print(build_assignment()); print(build_notes()); print(build_pptx())
