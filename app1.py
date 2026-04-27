import streamlit as st
import fitz
import re
import google.generativeai as genai
import pandas as pd
import io
import zipfile
import os
import hashlib
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ============================================================
#  PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Examify · AI Evaluation Suite",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
#  GLOBAL CSS — Premium SaaS Dark Theme
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── App background ── */
.stApp {
    background: radial-gradient(ellipse at 20% 20%, #0a1628 0%, #050d1a 60%, #000810 100%);
    min-height: 100vh;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #05111f 0%, #030c18 100%);
    border-right: 1px solid rgba(149,124,61,0.25);
    padding-top: 0 !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}

/* ── Sidebar nav buttons ── */
section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    margin-bottom: 8px;
    background: transparent;
    color: #c8b97a;
    border: 1px solid rgba(149,124,61,0.3);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.3px;
    transition: all 0.25s ease;
    text-align: left;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(149,124,61,0.15);
    border-color: #957C3D;
    color: #f0dfa0;
    transform: translateX(4px);
    box-shadow: 0 0 12px rgba(149,124,61,0.2);
}

/* ── Main action buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #957C3D 0%, #c4a44e 50%, #957C3D 100%);
    background-size: 200% auto;
    color: #0a0a0a;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.4px;
    padding: 10px 22px;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background-position: right center;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(149,124,61,0.4);
}

/* ── Download buttons ── */
.stDownloadButton > button {
    background: rgba(149,124,61,0.12);
    color: #c8b97a;
    border: 1px solid rgba(149,124,61,0.4);
    border-radius: 10px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.25s ease;
}
.stDownloadButton > button:hover {
    background: rgba(149,124,61,0.25);
    border-color: #957C3D;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(149,124,61,0.3);
}

/* ── Inputs, textareas ── */
input[type="text"], input[type="number"], textarea, .stTextInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(149,124,61,0.25) !important;
    border-radius: 10px !important;
    color: #e8e0d0 !important;
    transition: border-color 0.2s ease !important;
}
input[type="text"]:focus, input[type="number"]:focus, textarea:focus {
    border-color: #957C3D !important;
    box-shadow: 0 0 0 2px rgba(149,124,61,0.15) !important;
}

/* ── File uploader ── */
.stFileUploader {
    border: 1px dashed rgba(149,124,61,0.3);
    border-radius: 14px;
    padding: 10px;
    background: rgba(149,124,61,0.04);
}

/* ── Dataframes ── */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(149,124,61,0.2);
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: rgba(149,124,61,0.07);
    border: 1px solid rgba(149,124,61,0.2);
    border-radius: 14px;
    padding: 16px !important;
}

/* ── Info / success / warning / error banners ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(149,124,61,0.25) !important;
    border-radius: 10px !important;
    color: #e8e0d0 !important;
}

/* ── Number input ── */
.stNumberInput > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(149,124,61,0.25) !important;
    border-radius: 10px !important;
}

/* ── Label text ── */
label, .stTextInput label, .stTextArea label, .stFileUploader label {
    color: #a89870 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
}

/* ── Divider ── */
hr {
    border: none;
    border-top: 1px solid rgba(149,124,61,0.2);
    margin: 20px 0;
}

/* ── Custom card component ── */
.ex-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(149,124,61,0.03) 100%);
    backdrop-filter: blur(20px);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 24px;
    border: 1px solid rgba(149,124,61,0.18);
    box-shadow: 0 4px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
    transition: box-shadow 0.3s ease, transform 0.3s ease;
}
.ex-card:hover {
    box-shadow: 0 8px 40px rgba(0,0,0,0.45), 0 0 0 1px rgba(149,124,61,0.25);
    transform: translateY(-2px);
}

/* ── Section heading ── */
.ex-section-title {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 700;
    color: #d4b96a;
    margin-bottom: 6px;
}

/* ── Hero banner ── */
.ex-hero {
    background: linear-gradient(135deg, rgba(149,124,61,0.12) 0%, rgba(0,35,73,0.4) 100%);
    border: 1px solid rgba(149,124,61,0.22);
    border-radius: 20px;
    padding: 32px 36px 28px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.ex-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(149,124,61,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.ex-hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 40px;
    font-weight: 700;
    background: linear-gradient(135deg, #f0dfa0 0%, #957C3D 60%, #c4a44e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin-bottom: 8px;
}
.ex-hero-sub {
    font-size: 15px;
    color: rgba(200,185,122,0.7);
    font-weight: 400;
    letter-spacing: 0.5px;
}

/* ── Feature pill ── */
.ex-pill {
    display: inline-block;
    background: rgba(149,124,61,0.1);
    border: 1px solid rgba(149,124,61,0.3);
    border-radius: 100px;
    padding: 4px 14px;
    font-size: 12px;
    color: #c8b97a;
    margin: 4px 4px 0 0;
    font-weight: 500;
    letter-spacing: 0.3px;
}

/* ── Feature card (dashboard row) ── */
.feat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(149,124,61,0.18);
    border-radius: 16px;
    padding: 22px 20px 18px;
    text-align: center;
    transition: all 0.25s ease;
    height: 100%;
}
.feat-card:hover {
    background: rgba(149,124,61,0.08);
    border-color: rgba(149,124,61,0.4);
    transform: translateY(-4px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.4);
}
.feat-card-icon {
    font-size: 32px;
    margin-bottom: 10px;
    display: block;
}
.feat-card-title {
    font-size: 16px;
    font-weight: 600;
    color: #d4b96a;
    margin-bottom: 6px;
}
.feat-card-desc {
    font-size: 13px;
    color: rgba(200,185,122,0.6);
    line-height: 1.5;
}

/* ── Student result block ── */
.student-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 24px 0 12px;
}
.student-avatar {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #957C3D, #c4a44e);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 15px;
    color: #0a0a0a;
    flex-shrink: 0;
}
.student-name {
    font-size: 17px;
    font-weight: 600;
    color: #e8d8a8;
}

/* ── Badge ── */
.grade-badge {
    display: inline-block;
    padding: 3px 14px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-gold   { background: rgba(149,124,61,0.25); color: #f0d060; border: 1px solid rgba(240,208,96,0.4); }
.badge-blue   { background: rgba(60,120,220,0.2);  color: #80b0ff; border: 1px solid rgba(60,120,220,0.4); }
.badge-red    { background: rgba(220,60,60,0.2);   color: #ff8080; border: 1px solid rgba(220,60,60,0.4); }
.badge-green  { background: rgba(60,180,100,0.2);  color: #80e8a8; border: 1px solid rgba(60,180,100,0.4); }

/* ── Sidebar branding ── */
.sidebar-brand {
    padding: 28px 20px 20px;
    border-bottom: 1px solid rgba(149,124,61,0.2);
    margin-bottom: 18px;
}
.sidebar-logo {
    font-family: 'Playfair Display', serif;
    font-size: 26px;
    font-weight: 700;
    color: #d4b96a;
    letter-spacing: 0.5px;
}
.sidebar-tagline {
    font-size: 11px;
    color: rgba(200,185,122,0.5);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 3px;
}
.sidebar-nav-label {
    font-size: 10px;
    color: rgba(200,185,122,0.4);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
    margin: 16px 0 8px 2px;
}
.sidebar-footer {
    padding: 16px 20px;
    border-top: 1px solid rgba(149,124,61,0.15);
    text-align: center;
}
.sidebar-footer-text {
    font-size: 11px;
    color: rgba(200,185,122,0.35);
    letter-spacing: 0.5px;
}

/* ── Section separator ── */
.ex-separator {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 20px 0;
}
.ex-separator-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(149,124,61,0.3), transparent);
}
.ex-separator-dot {
    width: 6px; height: 6px;
    background: #957C3D;
    border-radius: 50%;
}

/* ── Step indicator ── */
.step-row {
    display: flex;
    gap: 0;
    margin-bottom: 28px;
    position: relative;
}
.step-row::before {
    content: '';
    position: absolute;
    top: 17px; left: 18px;
    right: 18px;
    height: 2px;
    background: rgba(149,124,61,0.2);
    z-index: 0;
}
.step-item {
    flex: 1;
    text-align: center;
    position: relative;
    z-index: 1;
}
.step-circle {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 6px;
}
.step-active   { background: linear-gradient(135deg,#957C3D,#c4a44e); color:#0a0a0a; }
.step-inactive { background: rgba(149,124,61,0.1); color: rgba(200,185,122,0.4); border:1px solid rgba(149,124,61,0.2); }
.step-label {
    font-size: 11px;
    color: rgba(200,185,122,0.5);
    display: block;
    letter-spacing: 0.3px;
}

/* ── Fade-in animation ── */
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.animate-in {
    animation: fadeSlideUp 0.5s ease forwards;
}

/* ── Section number badge ── */
.section-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px; height: 28px;
    border-radius: 8px;
    background: rgba(149,124,61,0.2);
    color: #c8b97a;
    font-size: 13px;
    font-weight: 700;
    margin-right: 10px;
    vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
#  API CONFIGURATION
# ============================================================
API_KEY = os.getenv("API_KEY") 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ============================================================
#  CORE LOGIC FUNCTIONS (unchanged)
# ============================================================
def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join(page.get_text() for page in doc)

def extract_questions(text):
    matches = re.findall(r'(Q\d+)\.\s*(.*?)\((\d+)\s*marks?\)', text)
    return {q + ".": {"question": ques.strip(), "marks": int(m)} for q, ques, m in matches}

def split_answers(text):
    parts = re.split(r'(Q\d+\.)', text)
    return {parts[i].strip(): parts[i+1].strip() for i in range(1, len(parts), 2)}

def generate_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    stop = {"the", "is", "was", "and", "of", "in", "to", "a", "it"}
    kw = {}
    for w in words:
        if w not in stop and len(w) > 3:
            kw[w] = kw.get(w, 0) + 1
    return kw

def keyword_score(answer, keywords):
    answer = answer.lower()
    return sum(weight for k, weight in keywords.items() if k in answer)

def ai_eval(questions, answers):
    prompt = "You are an examiner.\n\n"
    for q in questions:
        prompt += f"""
{q}
Question: {questions[q]['question']}
Model Answer: {questions[q]['model_answer']}
Student Answer: {answers.get(q, "")}
Marks: {questions[q]['marks']}
"""
    prompt += "STRICT FORMAT:\nQ1: Score X/Y | Feedback: short sentence"
    return model.generate_content(prompt).text

def parse_ai(text):
    res = {}
    for line in text.split("\n"):
        m = re.search(r'(Q\d+).*?(\d+)/(\d+).*?(.*)', line)
        if m:
            res[m.group(1) + "."] = {
                "score": int(m.group(2)),
                "feedback": m.group(4).strip() or "Evaluated by AI"
            }
    return res

def get_grade(total, max_total):
    p = (total / max_total) * 100
    if p >= 85:   return "A+"
    elif p >= 70: return "A"
    elif p >= 55: return "B"
    elif p >= 40: return "C"
    else:         return "F"

def grade_badge_html(grade):
    cls = "badge-gold" if grade in ("A+", "A") else ("badge-green" if grade == "B" else ("badge-blue" if grade == "C" else "badge-red"))
    return f'<span class="grade-badge {cls}">{grade}</span>'

# ============================================================
#  PDF GENERATION — EVALUATION REPORT (unchanged logic)
# ============================================================
def generate_pdf(name, questions, student, total, max_total, grade, percentage):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        "<para align='center'><font size=18><b>STUDENT PERFORMANCE REPORT</b></font></para>",
        styles['Normal']
    ))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        f"<para align='center'><font size=12><b>{name}</b></font></para>",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))

    summary_data = [
        ["Total Marks", f"{total}/{max_total}"],
        ["Percentage",  f"{percentage}%"],
        ["Grade",       grade]
    ]
    summary_table = Table(summary_data, colWidths=[150, 200])
    summary_table.setStyle(TableStyle([
        ("GRID",       (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Detailed Evaluation</b>", styles['Heading3']))
    elements.append(Spacer(1, 10))

    for q in questions:
        data   = student["marks"][q]
        answer = student["answers"].get(q, "")

        elements.append(Paragraph(f"<b>{q}</b>", styles['Normal']))
        elements.append(Paragraph(f"Marks: {data['score']} / {questions[q]['marks']}", styles['Normal']))
        elements.append(Paragraph("<b>Student Answer:</b>", styles['Normal']))
        elements.append(Paragraph(answer[:500], styles['Normal']))
        elements.append(Paragraph("<b>Feedback:</b>", styles['Normal']))
        elements.append(Paragraph(data["feedback"], styles['Normal']))
        elements.append(Spacer(1, 15))

    elements.append(Spacer(1, 30))
    sign_table = Table([
        ["__________________", "__________________"],
        ["Examiner",           "Head of Department"]
    ], colWidths=[200, 200])
    elements.append(sign_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ============================================================
#  PDF GENERATION — CUSTOM MARKSHEET (unchanged logic)
# ============================================================
def generate_custom_pdf(name, subjects, marks, total, grade, inst, exam, teacher):
    buffer = io.BytesIO()

    def draw_border(c, doc):
        width, height = A4
        c.setStrokeColor(colors.HexColor("#002349"))
        c.setLineWidth(4)
        c.rect(20, 20, width - 40, height - 40)
        c.setStrokeColor(colors.HexColor("#957C3D"))
        c.setLineWidth(2)
        c.rect(30, 30, width - 60, height - 60)

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=60
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        f"<para align='center'><font size=20 color='#002349'><b>{inst}</b></font></para>",
        styles['Normal']
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"<para align='center'><font size=14 color='#957C3D'><b>{exam}</b></font></para>",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "<para align='center'><font size=16><b>STUDENT MARKSHEET</b></font></para>",
        styles['Normal']
    ))
    elements.append(Spacer(1, 25))

    info_data = [["Student Name", name], ["Total Marks", str(total)], ["Grade", grade]]
    if teacher:
        info_data.insert(1, ["Class Teacher", teacher])

    info_table = Table(info_data, colWidths=[150, 250])
    info_table.setStyle(TableStyle([
        ("GRID",       (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 30))

    table_data = [["Subject", "Marks"]]
    for s, m in zip(subjects, marks):
        table_data.append([s, str(m)])

    subject_table = Table(table_data, colWidths=[250, 150])
    subject_table.setStyle(TableStyle([
        ("GRID",       (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1,  0), colors.HexColor("#002349")),
        ("TEXTCOLOR",  (0, 0), (-1,  0), colors.white),
        ("FONTNAME",   (0, 0), (-1,  0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("ALIGN",      (1, 1), (-1, -1), "CENTER"),
    ]))
    elements.append(subject_table)
    elements.append(Spacer(1, 40))

    sign_table = Table([
        ["____________________", "____________________"],
        ["Class Teacher",        "Principal"]
    ], colWidths=[200, 200])
    sign_table.setStyle(TableStyle([
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 25),
    ]))
    elements.append(sign_table)
    doc.build(elements, onFirstPage=draw_border)
    buffer.seek(0)
    return buffer

# ============================================================
#  QUESTION PAPER UTILITIES (unchanged logic)
# ============================================================
def get_input_hash(content, sections):
    return hashlib.md5((content + sections).encode()).hexdigest()

def clean_text(text):
    return text.replace("**", "")

def split_question_answer(output):
    output_upper = output.upper()
    if "ANSWER KEY" in output_upper:
        idx = output_upper.index("ANSWER KEY")
        return output[:idx].strip(), output[idx:].strip()
    return output.strip(), "Answer key not generated"

def format_answer_key(content):
    lines = content.split("\n")
    formatted = []
    current_q = None
    buffer_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^(Q\s*\d+)', line, re.IGNORECASE):
            if current_q:
                formatted.append((current_q, buffer_lines))
                buffer_lines = []
            current_q = line
        else:
            buffer_lines.append(line)
    if current_q:
        formatted.append((current_q, buffer_lines))
    return formatted

def format_exam_text(content):
    lines = content.split("\n")
    formatted = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("SECTION"):
            formatted.append(("section", line))
        elif re.match(r'^Q\d+', line):
            formatted.append(("question", line))
        else:
            formatted.append(("text", line))
    return formatted

def add_header_footer(c, doc):
    width, height = A4
    c.saveState()
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, height - 30, doc.inst_name)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, height - 45, doc.exam_name)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 20, f"Page {doc.page}")
    c.restoreState()

def generate_exam_pdf(content, title, inst, exam, total_marks):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=70, bottomMargin=50
    )
    doc.inst_name = inst
    doc.exam_name = exam
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<para align='center'><b>{title}</b></para>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Total Marks:</b> {total_marks}", styles['Normal']))
    elements.append(Spacer(1, 20))

    if title == "ANSWER KEY":
        answers = format_answer_key(content)
        if not answers:
            elements.append(Paragraph("Answer key formatting failed.", styles['Normal']))
        else:
            for q, ans_lines in answers:
                elements.append(Paragraph(f"<b>{q}</b>", styles['Heading3']))
                elements.append(Spacer(1, 5))
                for line in ans_lines:
                    elements.append(Paragraph(f"• {line}", styles['Normal']))
                elements.append(Spacer(1, 12))
    else:
        formatted = format_exam_text(content)
        for typ, text in formatted:
            if typ == "section":
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(f"<b>{text}</b>", styles['Heading3']))
            elif typ == "question":
                elements.append(Spacer(1, 8))
                elements.append(Paragraph(text, styles['Normal']))
            else:
                elements.append(Paragraph(text, styles['Normal']))

    elements.append(Spacer(1, 40))
    sign_table = Table([
        ["__________________", "__________________"],
        ["Examiner",           "Head of Department"]
    ], colWidths=[200, 200])
    elements.append(sign_table)

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer

# ============================================================
#  SESSION STATE INIT
# ============================================================
if "mode" not in st.session_state:
    st.session_state.mode = "Evaluate Answer Sheets"
if "evaluated" not in st.session_state:
    st.session_state.evaluated = False
if "results" not in st.session_state:
    st.session_state.results = []
if "step_eval" not in st.session_state:
    st.session_state.step_eval = 1

if "step_marksheet" not in st.session_state:
    st.session_state.step_marksheet = 1

if "step_qp" not in st.session_state:
    st.session_state.step_qp = 1
# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand animate-in">
        <div class="sidebar-logo">🎓 Examify</div>
        <div class="sidebar-tagline">AI Evaluation Suite</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-nav-label">Navigation</div>', unsafe_allow_html=True)

    if st.button("📊  AI Answer Evaluation"):
        st.session_state.mode = "Evaluate Answer Sheets"

    if st.button("📑  Student Marksheet Builder"):
        st.session_state.mode = "Custom Marksheet Generator"

    if st.button("📝  Question Paper Generator"):
        st.session_state.mode = "Question Paper Generator"

    st.markdown("<hr>", unsafe_allow_html=True)

    # Quick-help info
    mode_hints = {
        "Evaluate Answer Sheets": "Upload question paper, model answers, and student PDFs to auto-grade with AI.",
        "Custom Marksheet Generator": "Upload a CSV of marks to bulk-generate branded marksheet PDFs.",
        "Question Paper Generator": "Generate structured question papers with marking schemes in seconds."
    }
    hint = mode_hints.get(st.session_state.mode, "")
    st.markdown(f"""
    <div style="background:rgba(149,124,61,0.07); border:1px solid rgba(149,124,61,0.2);
                border-radius:12px; padding:14px 16px; margin-top:8px;">
        <div style="font-size:11px; color:#a89870; font-weight:600; text-transform:uppercase;
                    letter-spacing:1px; margin-bottom:6px;">Current Module</div>
        <div style="font-size:12px; color:rgba(200,185,122,0.65); line-height:1.6;">{hint}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-footer" style="margin-top:auto; padding-top:32px;">
        <div class="sidebar-footer-text">Precision · Performance · Evaluation</div>
    </div>
    """, unsafe_allow_html=True)

mode = st.session_state.mode

# ============================================================
#  HERO HEADER
# ============================================================
st.markdown("""
<div class="ex-hero animate-in">
    <div class="ex-hero-title">Examify</div>
    <div class="ex-hero-sub">AI-Powered Examination & Evaluation Platform</div>
    <div style="margin-top:14px;">
        <span class="ex-pill">🤖 AI Evaluation</span>
        <span class="ex-pill">📄 PDF Generation</span>
        <span class="ex-pill">📊 Bulk Processing</span>
        <span class="ex-pill">📑 Marksheet Builder</span>
        <span class="ex-pill">📝 Question Papers</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Dashboard feature cards (always visible) ──────────────────
col1, col2, col3 = st.columns(3)
with col1:
    active1 = "border-color:rgba(149,124,61,0.55);" if mode == "Evaluate Answer Sheets" else ""
    st.markdown(f"""
    <div class="feat-card" style="{active1}">
        <span class="feat-card-icon">📊</span>
        <div class="feat-card-title">AI Evaluation</div>
        <div class="feat-card-desc">Automatically grade student answer sheets against model answers using Gemini AI with keyword scoring.</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    active2 = "border-color:rgba(149,124,61,0.55);" if mode == "Question Paper Generator" else ""
    st.markdown(f"""
    <div class="feat-card" style="{active2}">
        <span class="feat-card-icon">📝</span>
        <div class="feat-card-title">Question Paper Generator</div>
        <div class="feat-card-desc">Generate structured exam papers with customisable sections, difficulty levels, and automatic answer keys.</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    active3 = "border-color:rgba(149,124,61,0.55);" if mode == "Custom Marksheet Generator" else ""
    st.markdown(f"""
    <div class="feat-card" style="{active3}">
        <span class="feat-card-icon">📑</span>
        <div class="feat-card-title">Marksheet Builder</div>
        <div class="feat-card-desc">Bulk-generate branded student marksheets from CSV data and download as a ready-to-distribute ZIP.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="ex-separator animate-in">
    <div class="ex-separator-line"></div>
    <div class="ex-separator-dot"></div>
    <div class="ex-separator-line"></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
#  MODE 1 — AI ANSWER SHEET EVALUATION
# ============================================================
if mode == "Evaluate Answer Sheets":

    st.markdown("""
    <div class="animate-in">
        <div class="ex-section-title">📊 AI Answer Sheet Evaluation</div>
        <div style="font-size:13px; color:rgba(200,185,122,0.55); margin-bottom:20px;">
            Upload your documents below. The AI will evaluate each student's answers and generate detailed performance reports.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step indicator ──────────────────────────────────────
    step = st.session_state.step_eval
    st.markdown(f"""
    <div class="step-row animate-in">
        <div class="step-item">
            <div class="step-circle {'step-active' if step >= 1 else 'step-inactive'}">1</div>
            <span class="step-label">Upload Documents</span>
        </div>
        <div class="step-item">
            <div class="step-circle {'step-active' if step >= 2 else 'step-inactive'}">2</div>
            <span class="step-label">Run Evaluation</span>
        </div>
        <div class="step-item">
            <div class="step-circle {'step-active' if step >= 3 else 'step-inactive'}">3</div>
            <span class="step-label">Review & Export</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Upload card ─────────────────────────────────────────
    st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:18px;">
        <span class="section-num">1</span>
        <span style="font-size:16px; font-weight:600; color:#d4b96a;">Upload Examination Documents</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        q_file = st.file_uploader("Question Paper (PDF)", type="pdf", help="The official question paper with marks allocation")
    with col2:
        m_file = st.file_uploader("Model Answer Sheet (PDF)", type="pdf", help="The teacher's model/reference answers")
    with col3:
        student_files = st.file_uploader("Student Answer Sheets (PDF)", type="pdf", accept_multiple_files=True,
                                         help="Upload one or more student answer PDFs")
    if q_file or m_file or student_files:
        if not st.session_state.evaluated:
            st.session_state.step_eval = 1
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Evaluate card ────────────────────────────────────────
    st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:16px;">
        <span class="section-num">2</span>
        <span style="font-size:16px; font-weight:600; color:#d4b96a;">Start AI Evaluation</span>
    </div>
    <div style="font-size:13px; color:rgba(200,185,122,0.5); margin-bottom:16px;">
        Once all three document types are uploaded, click the button below. Processing time varies with the number of students.
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀  Run AI Evaluation"):
        if not q_file or not m_file or not student_files:
            st.error("⚠️  Please upload the Question Paper, Model Answer Sheet, and at least one Student Answer Sheet before proceeding.")
        else:
            with st.spinner("🤖 AI is evaluating answer sheets — this may take a moment…"):
                q_text = extract_text(q_file)
                m_text = extract_text(m_file)

                questions    = extract_questions(q_text)
                model_answers = split_answers(m_text)

                for q in questions:
                    questions[q]["model_answer"] = model_answers.get(q, "")
                    questions[q]["keywords"]     = generate_keywords(questions[q]["model_answer"])

                all_results = []

                for file in student_files:
                    name   = file.name.replace(".pdf", "")
                    s_text = extract_text(file)
                    s_ans  = split_answers(s_text)
                    ai_map = parse_ai(ai_eval(questions, s_ans))

                    student_data = {"Name": name, "answers": s_ans, "marks": {}}

                    for q in questions:
                        kw     = questions[q]["keywords"]
                        k      = keyword_score(s_ans.get(q, ""), kw)
                        max_k  = max(sum(kw.values()), 1)
                        k_ratio = k / max_k

                        ai       = ai_map.get(q, {"score": 0, "feedback": "fallback"})
                        ai_score = ai["score"]
                        marks_q  = questions[q]['marks']

                        if ai_score >= marks_q * 0.7:
                            final = ai_score
                        else:
                            final = round((k_ratio * marks_q) * 0.3 + ai_score * 0.7, 1)

                        student_data["marks"][q] = {"score": final, "feedback": ai["feedback"]}

                    all_results.append(student_data)

                st.session_state.results   = all_results
                st.session_state.questions = questions
                st.session_state.evaluated = True
                st.session_state.step_eval = 2
            st.success(f"✅ Evaluation complete — {len(all_results)} student(s) processed successfully.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Results card ─────────────────────────────────────────
    if st.session_state.evaluated:
        st.session_state.step_eval = 3
        
        results   = st.session_state.results
        questions = st.session_state.questions

        st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom:20px;">
            <span class="section-num">3</span>
            <span style="font-size:16px; font-weight:600; color:#d4b96a;">Review Results & Adjust Scores</span>
        </div>
        <div style="font-size:13px; color:rgba(200,185,122,0.5); margin-bottom:4px;">
            Review AI-generated marks for each student. You can manually adjust any score using the input fields below.
        </div>
        """, unsafe_allow_html=True)

        final_table = []

        for student in results:
            initials = student['Name'][0].upper() if student['Name'] else "?"
            st.markdown(f"""
            <div class="student-header">
                <div class="student-avatar">{initials}</div>
                <div class="student-name">{student['Name']}</div>
            </div>
            """, unsafe_allow_html=True)

            total     = 0
            max_total = 0
            row       = {"Name": student['Name']}

            for q in questions:
                marks_q = questions[q]['marks']
                stored  = student["marks"][q]["score"]

                c1, c2 = st.columns([2, 3])
                with c1:
                    edited = st.number_input(
                        f"{q} (out of {marks_q})",
                        min_value=0.0,
                        max_value=float(marks_q),
                        value=float(stored),
                        step=0.5,
                        key=f"{student['Name']}_{q}"
                    )
                with c2:
                    st.info(f"💬 {student['marks'][q]['feedback']}")

                student["marks"][q]["score"] = edited
                total     += edited
                max_total += marks_q
                row[q]     = edited

            percentage = round((total / max_total) * 100, 1)
            grade      = get_grade(total, max_total)
            row["Total"] = total
            row["Grade"] = grade
            final_table.append(row)

            badge_html = grade_badge_html(grade)
            st.markdown(f"""
            <div style="background:rgba(149,124,61,0.08); border:1px solid rgba(149,124,61,0.2);
                        border-radius:12px; padding:14px 20px; margin:10px 0 20px; display:flex;
                        align-items:center; gap:18px; flex-wrap:wrap;">
                <span style="font-size:14px; color:#c8b97a; font-weight:600;">
                    📈 Score: <span style="color:#f0d060;">{total}/{max_total}</span>
                </span>
                <span style="font-size:14px; color:#c8b97a; font-weight:600;">
                    🎯 Percentage: <span style="color:#f0d060;">{percentage}%</span>
                </span>
                <span style="font-size:14px; color:#c8b97a; font-weight:600;">
                    Grade: {badge_html}
                </span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

        # ── Summary table ─────────────────────────────────
        st.markdown("""
        <div style="margin:8px 0 16px;">
            <span style="font-size:16px; font-weight:600; color:#d4b96a;">📋 Class Summary</span>
        </div>
        """, unsafe_allow_html=True)

        df = pd.DataFrame(final_table)
        df["Rank"] = df["Total"].rank(ascending=False).astype(int)
        st.dataframe(df, use_container_width=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        col_dl1, col_dl2, col_spacer = st.columns([1, 1, 2])

        with col_dl1:
            st.download_button(
                "📥 Export Results (CSV)",
                df.to_csv(index=False),
                "evaluation_results.csv",
                use_container_width=True
            )

        with col_dl2:
            # Build ZIP of individual PDF reports
            zip_buffer = io.BytesIO()
            zipf = zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED)
            for student in results:
                name      = student["Name"]
                total_s   = sum(student["marks"][q]["score"] for q in questions)
                max_total_s = sum(questions[q]["marks"] for q in questions)
                pct       = round((total_s / max_total_s) * 100, 1)
                grade_s   = get_grade(total_s, max_total_s)
                pdf       = generate_pdf(name, questions, student, total_s, max_total_s, grade_s, pct)
                zipf.writestr(f"{name}.pdf", pdf.getvalue())
            zipf.close()
            zip_buffer.seek(0)

            st.download_button(
                "📦 Download Student Reports (ZIP)",
                zip_buffer,
                "student_reports.zip",
                use_container_width=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
#  MODE 2 — CUSTOM MARKSHEET GENERATOR
# ============================================================
if mode == "Custom Marksheet Generator":
    step = st.session_state.step_marksheet
    st.markdown("""
    <div class="animate-in">
        <div class="ex-section-title">📑 Bulk Marksheet Generator</div>
        <div style="font-size:13px; color:rgba(200,185,122,0.55); margin-bottom:20px;">
            Upload a CSV with student marks to instantly generate branded, print-ready marksheets for every student.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step indicator ──────────────────────────────────────
    st.markdown(f"""
<div class="step-row animate-in">
    <div class="step-item">
        <div class="step-circle {'step-active' if step >= 1 else 'step-inactive'}">1</div>
        <span class="step-label">Upload CSV</span>
    </div>
    <div class="step-item">
        <div class="step-circle {'step-active' if step >= 2 else 'step-inactive'}">2</div>
        <span class="step-label">Configure Details</span>
    </div>
    <div class="step-item">
        <div class="step-circle {'step-active' if step >= 3 else 'step-inactive'}">3</div>
        <span class="step-label">Generate & Download</span>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Upload & config card ─────────────────────────────────
    st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:18px;">
        <span class="section-num">1</span>
        <span style="font-size:16px; font-weight:600; color:#d4b96a;">Upload Student Marks (CSV)</span>
    </div>
    <div style="font-size:12px; color:rgba(200,185,122,0.45); margin-bottom:16px;">
        Expected columns: <code style="background:rgba(149,124,61,0.15); padding:2px 8px; border-radius:6px; color:#c8b97a;">Name, Subject1, Subject2, … , Total, Grade</code>
    </div>
    """, unsafe_allow_html=True)

    csv_file = st.file_uploader("Choose a CSV file", type="csv")
    if csv_file:
        st.session_state.step_marksheet = 2

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin:16px 0 10px;">
        <span class="section-num">2</span>
        <span style="font-size:16px; font-weight:600; color:#d4b96a;">Institution Details</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        inst    = st.text_input("Institution / School Name", placeholder="e.g. St. Xavier's College")
    with col2:
        exam    = st.text_input("Examination Name", placeholder="e.g. Semester I — 2025")
    with col3:
        teacher = st.text_input("Class Teacher (optional)", placeholder="e.g. Dr. A. Sharma")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Preview & generate ───────────────────────────────────
    if csv_file:
        st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom:14px;">
            <span class="section-num">3</span>
            <span style="font-size:16px; font-weight:600; color:#d4b96a;">Data Preview</span>
        </div>
        """, unsafe_allow_html=True)

        df = pd.read_csv(csv_file)
        st.dataframe(df, use_container_width=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        col_gen, col_info = st.columns([1, 2])
        with col_gen:
            if st.button("📦 Generate & Download Reports (ZIP)", use_container_width=True):
                st.session_state.step_marksheet = 3
                if not inst or not exam:
                    st.warning("⚠️  Please enter Institution Name and Examination Name before generating.")
                else:
                    with st.spinner(f"🖨️ Generating marksheets for {len(df)} student(s)…"):
                        zip_buffer = io.BytesIO()
                        zipf = zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED)

                        for _, row in df.iterrows():
                            name     = row["Name"]
                            subjects = list(df.columns[1:-2])
                            marks    = [row[s] for s in subjects]
                            pdf      = generate_custom_pdf(
                                name, subjects, marks, row["Total"], row["Grade"],
                                inst, exam, teacher
                            )
                            zipf.writestr(f"{name}.pdf", pdf.getvalue())

                        zipf.close()
                        zip_buffer.seek(0)

                    st.success(f"✅ {len(df)} marksheet(s) generated successfully.")
                    st.download_button(
                        "📥 Download All Student Marksheets (ZIP)",
                        zip_buffer,
                        "student_marksheets.zip",
                        use_container_width=True
                    )

        with col_info:
            st.info(f"📋 **{len(df)} students** detected in the uploaded file. Each will receive an individually branded PDF marksheet.")

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
#  MODE 3 — QUESTION PAPER GENERATOR
# ============================================================
if mode == "Question Paper Generator":

    st.markdown("""
    <div class="animate-in">
        <div class="ex-section-title">📝 AI Question Paper Generator</div>
        <div style="font-size:13px; color:rgba(200,185,122,0.55); margin-bottom:20px;">
            Define your topic, mark distribution, and difficulty levels — the AI will produce a complete question paper with an answer key.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step indicator ──────────────────────────────────────
    generated_flag = "generated" in st.session_state and st.session_state.generated
    st.markdown(f"""
    <div class="step-row animate-in">
        <div class="step-item">
            <div class="step-circle step-active">1</div>
            <span class="step-label">Define Content</span>
        </div>
        <div class="step-item">
            <div class="step-circle {'step-active' if generated_flag else 'step-inactive'}">2</div>
            <span class="step-label">Configure Sections</span>
        </div>
        <div class="step-item">
            <div class="step-circle {'step-active' if generated_flag else 'step-inactive'}">3</div>
            <span class="step-label">Review & Download</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Content input ────────────────────────────────────────
    st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:14px;">
        <span class="section-num">1</span>
        <span style="font-size:16px; font-weight:600; color:#d4b96a;">Syllabus / Topic Content</span>
    </div>
    """, unsafe_allow_html=True)

    col_t, col_u = st.columns([3, 2])
    with col_t:
        topic = st.text_area(
            "Enter topic, syllabus points, or key concepts",
            height=130,
            placeholder="e.g. Photosynthesis, Light and Dark Reactions, Calvin Cycle, Chloroplast structure…"
        )
    with col_u:
        notes_file = st.file_uploader("Or upload your notes / textbook chapter (PDF)", type="pdf")
        st.markdown("""
        <div style="font-size:12px; color:rgba(200,185,122,0.4); margin-top:6px;">
            If a PDF is uploaded, it will be used instead of the text input above.
        </div>
        """, unsafe_allow_html=True)
    if topic or notes_file:
        st.session_state.step_qp = 2
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section configuration ────────────────────────────────
    st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:14px;">
        <span class="section-num">2</span>
        <span style="font-size:16px; font-weight:600; color:#d4b96a;">Mark Distribution & Section Setup</span>
    </div>
    """, unsafe_allow_html=True)

    num_sections = st.number_input("Number of Sections", min_value=1, max_value=10, value=3,
                                   help="How many sections should the question paper have? (A, B, C…)")

    sections_data = []
    total = 0

    for i in range(int(num_sections)):
        sec = chr(65 + i)
        st.markdown(f"""
        <div style="background:rgba(149,124,61,0.06); border:1px solid rgba(149,124,61,0.18);
                    border-radius:12px; padding:16px 20px; margin-bottom:12px;">
            <div style="font-size:13px; font-weight:600; color:#c8b97a; margin-bottom:12px;">
                Section {sec}
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            marks = st.number_input(f"Marks per question (Sec {sec})", min_value=0, key=f"marks_{i}",
                                    help="Marks allocated to each question in this section")
        with col2:
            count = st.number_input(f"Number of questions (Sec {sec})", min_value=0, key=f"count_{i}",
                                    help="Total questions in this section")
        with col3:
            diff  = st.selectbox(f"Difficulty level (Sec {sec})", ["Easy", "Medium", "Hard"], key=f"diff_{i}")

        st.markdown("</div>", unsafe_allow_html=True)
        sections_data.append((sec, marks, count, diff))
        total += marks * count

    col_total, col_spacer = st.columns([1, 2])
    with col_total:
        if total > 0:
            st.success(f"✅ Total Marks: **{total}**")
        else:
            st.info("Configure sections above to calculate total marks.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Generate button ──────────────────────────────────────
    st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)

    if st.button("🚀  Generate Question Paper with Answer Key", use_container_width=False):
        st.session_state.step_qp = 3
        content = extract_text(notes_file) if notes_file else topic

        if not content.strip():
            st.error("⚠️  Please enter a topic or upload a notes PDF before generating.")
        else:
            with st.spinner("✍️ AI is crafting your question paper — please wait…"):
                sections      = ""
                difficulty_rules = ""
                for sec, marks_s, count_s, diff_s in sections_data:
                    sections         += f"\nSECTION {sec}:\n- {count_s} questions × {marks_s} marks\n"
                    difficulty_rules += f"\nSECTION {sec} should be {diff_s} difficulty."

                prompt = f"""
Generate a structured university exam paper.

CONTENT:
{content}

STRUCTURE:
{sections}

DIFFICULTY:
{difficulty_rules}

RULES:
- Do NOT show difficulty
- Do NOT use **
- Maintain structure strictly

ANSWER KEY RULES:
- Provide marking scheme
- Split marks clearly
- Ensure total matches question marks
- Use bullet format

OUTPUT:

QUESTION PAPER:

SECTION A:

ANSWER KEY:

Q1 (X Marks):
• Point – marks
"""
                output = model.generate_content(prompt).text

            q_part, a_part = split_question_answer(output)
            q_part = clean_text(q_part)
            a_part = clean_text(a_part)

            st.session_state.editable_q = q_part
            st.session_state.editable_a = a_part
            st.session_state.total      = total
            st.session_state.generated  = True

            st.success("✅ Question paper generated! Review and edit below, then download your PDFs.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Review & Download ────────────────────────────────────
    if "generated" in st.session_state and st.session_state.generated:
        total_final = st.session_state.total

        st.markdown('<div class="ex-card animate-in">', unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom:8px;">
            <span class="section-num">3</span>
            <span style="font-size:16px; font-weight:600; color:#d4b96a;">Review & Edit Before Downloading</span>
        </div>
        <div style="font-size:12px; color:rgba(200,185,122,0.45); margin-bottom:16px;">
            Both the question paper and answer key are fully editable. Make any corrections before generating your PDFs.
        </div>
        """, unsafe_allow_html=True)

        col_qp, col_ak = st.columns(2)
        with col_qp:
            st.markdown('<div style="font-size:13px; color:#c8b97a; font-weight:600; margin-bottom:6px;">📄 Question Paper</div>', unsafe_allow_html=True)
            st.session_state.editable_q = st.text_area(
                "Edit Question Paper",
                st.session_state.editable_q,
                height=320,
                label_visibility="collapsed"
            )
        with col_ak:
            st.markdown('<div style="font-size:13px; color:#c8b97a; font-weight:600; margin-bottom:6px;">📘 Answer Key / Marking Scheme</div>', unsafe_allow_html=True)
            st.session_state.editable_a = st.text_area(
                "Edit Answer Key",
                st.session_state.editable_a,
                height=320,
                label_visibility="collapsed"
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="margin:14px 0 10px;">
            <span style="font-size:14px; font-weight:600; color:#d4b96a;">Institution Details for PDF Header</span>
        </div>
        """, unsafe_allow_html=True)

        col_inst, col_exam = st.columns(2)
        with col_inst:
            inst_qp = st.text_input("Institution Name", placeholder="e.g. University of Chennai", key="inst_qp")
        with col_exam:
            exam_qp = st.text_input("Examination Name", placeholder="e.g. End Semester — April 2025", key="exam_qp")

        if inst_qp and exam_qp:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            q_pdf = generate_exam_pdf(st.session_state.editable_q, "QUESTION PAPER", inst_qp, exam_qp, total_final)
            a_pdf = generate_exam_pdf(st.session_state.editable_a, "ANSWER KEY",     inst_qp, exam_qp, total_final)

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "📥 Download Question Paper (PDF)",
                    q_pdf,
                    "question_paper.pdf",
                    use_container_width=True
                )
            with col_dl2:
                st.download_button(
                    "📥 Download Answer Key (PDF)",
                    a_pdf,
                    "answer_key.pdf",
                    use_container_width=True
                )
        else:
            st.warning("⚠️  Enter the Institution Name and Examination Name above to unlock PDF downloads.")

        st.markdown('</div>', unsafe_allow_html=True)