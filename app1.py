import streamlit as st
import fitz
import re
import google.generativeai as genai
import pandas as pd
import io
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="AI Evaluator", layout="wide")

# -------- PREMIUM SaaS UI --------
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* Background */
body {
    background: linear-gradient(135deg, #002349, #001a33);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #001a33;
    border-right: 1px solid #957C3D;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid rgba(149,124,61,0.3);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    transition: 0.3s;
}

.card:hover {
    transform: translateY(-6px) scale(1.01);
}

/* Titles */
.title {
    font-size: 34px;
    font-weight: 600;
    color: #957C3D;
}

.subtitle {
    font-size: 16px;
    color: #ccc;
}
/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    margin-bottom: 10px;
    background: transparent;
    color: #e6e6e6;
    border: 1px solid #957C3D;
    border-radius: 10px;
    transition: 0.3s;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #957C3D;
    color: black;
    transform: scale(1.02);
}
/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #957C3D, #b89b4a);
    border-radius: 10px;
    font-weight: bold;
    transition: 0.3s;
    color: black;
}

.stButton > button:hover {
    transform: scale(1.05);
}

/* Inputs */
input, textarea {
    border-radius: 10px !important;
}

/* Fade animation */
.fade-in {
    animation: fadeIn 0.8s ease-in;
}

@keyframes fadeIn {
    from {opacity: 0; transform: translateY(10px);}
    to {opacity: 1; transform: translateY(0);}
}

</style>
""", unsafe_allow_html=True)

# -------- HEADER --------
st.markdown("""
<div class="fade-in card">
<div class="title">📄 Examify</div>
<div class="subtitle">
Evaluation • Question Generator • Marksheet Automation
</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card fade-in">
    <h3>📊 Evaluate</h3>
    <p>AI-based answer sheet evaluation</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card fade-in">
    <h3>📝 Generate</h3>
    <p>Create question papers instantly</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card fade-in">
    <h3>📑 Marksheet</h3>
    <p>Premium student reports</p>
    </div>
    """, unsafe_allow_html=True)

# -------- SIDEBAR MODE --------
with st.sidebar:

    st.markdown("""
    <div style="text-align:center; padding:10px;">
        <h2 style="color:#957C3D;">🎓 Teacher Assistant</h2>
        <p style="color:#aaa;">Tools</p>
        <hr style="border:1px solid #957C3D;">
    </div>
    """, unsafe_allow_html=True)

    if "mode" not in st.session_state:
        st.session_state.mode = "Evaluate Answer Sheets"

    # Navigation Buttons
    if st.button("📊 Evaluation"):
        st.session_state.mode = "Evaluate Answer Sheets"

    if st.button("📑 Marksheet"):
        st.session_state.mode = "Custom Marksheet Generator"

    if st.button("📝 Question Paper"):
        st.session_state.mode = "Question Paper Generator"

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <p style='text-align:center; color:#888; font-size:12px;'>
     Precision. Performance. Evaluation
    </p>
    """, unsafe_allow_html=True)

mode = st.session_state.mode
# -------- API --------
import os
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# -------- FUNCTIONS --------
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
    stop = {"the","is","was","and","of","in","to","a","it"}
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
            res[m.group(1)+"."] = {
                "score": int(m.group(2)),
                "feedback": m.group(4).strip() or "Evaluated by AI"
            }
    return res

def get_grade(total, max_total):
    p = (total/max_total)*100
    if p>=85: return "A+"
    elif p>=70: return "A"
    elif p>=55: return "B"
    elif p>=40: return "C"
    else: return "F"

# -------- PDF FUNCTIONS --------
def generate_pdf(name, questions, student, total, max_total, grade, percentage):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    # -------- HEADER --------
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

    # -------- SUMMARY BOX --------
    summary_data = [
        ["Total Marks", f"{total}/{max_total}"],
        ["Percentage", f"{percentage}%"],
        ["Grade", grade]
    ]

    summary_table = Table(summary_data, colWidths=[150, 200])
    summary_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,-1), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # -------- QUESTION DETAILS --------
    elements.append(Paragraph("<b>Detailed Evaluation</b>", styles['Heading3']))
    elements.append(Spacer(1, 10))

    for q in questions:
        data = student["marks"][q]
        answer = student["answers"].get(q, "")

        elements.append(Paragraph(f"<b>{q}</b>", styles['Normal']))
        elements.append(Paragraph(f"Marks: {data['score']} / {questions[q]['marks']}", styles['Normal']))

        elements.append(Paragraph("<b>Student Answer:</b>", styles['Normal']))
        elements.append(Paragraph(answer[:500], styles['Normal']))

        elements.append(Paragraph("<b>Feedback:</b>", styles['Normal']))
        elements.append(Paragraph(data["feedback"], styles['Normal']))

        elements.append(Spacer(1, 15))

    # -------- FOOTER --------
    elements.append(Spacer(1, 30))

    sign_table = Table([
        ["__________________", "__________________"],
        ["Examiner", "Head of Department"]
    ], colWidths=[200, 200])

    elements.append(sign_table)

    doc.build(elements)

    buffer.seek(0)
    return buffer

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_custom_pdf(name, subjects, marks, total, grade, inst, exam, teacher):

    buffer = io.BytesIO()

    # -------- CUSTOM PAGE (FOR BORDER) --------
    def draw_border(canvas, doc):
        width, height = A4

        # Outer border
        canvas.setStrokeColor(colors.HexColor("#002349"))
        canvas.setLineWidth(4)
        canvas.rect(20, 20, width-40, height-40)

        # Inner border (gold)
        canvas.setStrokeColor(colors.HexColor("#957C3D"))
        canvas.setLineWidth(2)
        canvas.rect(30, 30, width-60, height-60)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    elements = []

    # -------- HEADER --------
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

    # -------- STUDENT INFO --------
    info_data = [
        ["Student Name", name],
        ["Total Marks", str(total)],
        ["Grade", grade]
    ]

    # 👉 Only add teacher if exists
    if teacher:
        info_data.insert(1, ["Class Teacher", teacher])

    info_table = Table(info_data, colWidths=[150, 250])
    info_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,-1), colors.whitesmoke),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 30))

    # -------- SUBJECT TABLE --------
    table_data = [["Subject", "Marks"]]

    for s, m in zip(subjects, marks):
        table_data.append([s, str(m)])

    subject_table = Table(table_data, colWidths=[250, 150])
    subject_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),

        # Header styling
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#002349")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        # Body styling
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
    ]))

    elements.append(subject_table)
    elements.append(Spacer(1, 40))

    # -------- SIGNATURE --------
    sign_table = Table([
        ["____________________", "____________________"],
        ["Class Teacher", "Principal"]
    ], colWidths=[200, 200])

    sign_table.setStyle(TableStyle([
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 25),
    ]))

    elements.append(sign_table)

    # -------- BUILD --------
    doc.build(elements, onFirstPage=draw_border)

    buffer.seek(0)
    return buffer
def generate_question_paper(content, sections):

    prompt = f"""
You are an expert exam paper setter.

Generate a structured question paper based on the given content:

{content}

Follow STRICT rules:

{sections}

Rules:
- Do not change number of questions
- Do not change marks per question
- Cover topics evenly
- Avoid repetition

Output format:

QUESTION PAPER:

SECTION A:
Q1:
Q2:

SECTION B:
...

ANSWER KEY:

Q1:
...
"""

    return model.generate_content(prompt).text
# -------- SESSION --------
from reportlab.lib.pagesizes import A4

def split_question_answer(output):
    parts = output.split("ANSWER KEY:")
    q_part = parts[0]
    a_part = parts[1] if len(parts) > 1 else ""
    return q_part.strip(), a_part.strip()


def add_header_footer(canvas, doc):
    width, height = A4

    canvas.saveState()

    # Header
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(width / 2, height - 30, doc.inst_name)

    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(width / 2, height - 45, doc.exam_name)

    # Footer
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(width / 2, 20, f"Page {doc.page}")

    canvas.restoreState()


def generate_exam_pdf(content, title, inst, exam, total_marks):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=70,
        bottomMargin=50
    )

    doc.inst_name = inst
    doc.exam_name = exam

    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(
        f"<para align='center'><b>{title}</b></para>",
        styles['Heading2']
    ))

    elements.append(Spacer(1,10))

    elements.append(Paragraph(
        f"<b>Total Marks:</b> {total_marks}",
        styles['Normal']
    ))

    elements.append(Spacer(1,15))

    # Body
    lines = content.split("\n")

    for line in lines:
        line = line.strip()

        if not line:
            elements.append(Spacer(1,8))

        elif "SECTION" in line:
            elements.append(Paragraph(f"<b>{line}</b>", styles['Heading3']))

        elif line.startswith("Q"):
            elements.append(Paragraph(line, styles['Normal']))

        else:
            elements.append(Paragraph(line, styles['Normal']))

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    buffer.seek(0)
    return buffer
if "evaluated" not in st.session_state:
    st.session_state.evaluated = False
if "results" not in st.session_state:
    st.session_state.results = []

# ============================
# 🟢 MODE 1: EVALUATION
# ============================
if mode == "Evaluate Answer Sheets":

    # -------- CARD 1: UPLOAD --------
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("## 📥 Upload Files")

    col1, col2, col3 = st.columns(3)

    with col1:
        q_file = st.file_uploader("📘 Question Paper", type="pdf")
    with col2:
        m_file = st.file_uploader("📗 Model Answer", type="pdf")
    with col3:
        student_files = st.file_uploader("📄 Student Sheets", type="pdf", accept_multiple_files=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # -------- CARD 2: BUTTON --------
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)

    if st.button("Start Evaluation"):

        q_text = extract_text(q_file)
        m_text = extract_text(m_file)

        questions = extract_questions(q_text)
        model_answers = split_answers(m_text)

        for q in questions:
            questions[q]["model_answer"] = model_answers.get(q, "")
            questions[q]["keywords"] = generate_keywords(questions[q]["model_answer"])

        all_results = []

        for file in student_files:
            name = file.name.replace(".pdf","")
            s_text = extract_text(file)
            s_ans = split_answers(s_text)

            ai_map = parse_ai(ai_eval(questions, s_ans))

            student_data = {"Name": name, "answers": s_ans, "marks": {}}

            for q in questions:
                kw = questions[q]["keywords"]
                k = keyword_score(s_ans.get(q,""), kw)
                max_k = max(sum(kw.values()),1)
                k_ratio = k/max_k

                ai = ai_map.get(q, {"score":0,"feedback":"fallback"})
                ai_score = ai["score"]
                marks = questions[q]['marks']

                if ai_score >= marks*0.7:
                    final = ai_score
                else:
                    final = round((k_ratio*marks)*0.3 + ai_score*0.7,1)

                student_data["marks"][q] = {"score": final, "feedback": ai["feedback"]}

            all_results.append(student_data)

        st.session_state.results = all_results
        st.session_state.questions = questions
        st.session_state.evaluated = True

    st.markdown('</div>', unsafe_allow_html=True)

    # -------- CARD 3: RESULTS --------
    if st.session_state.evaluated:

        st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
        st.markdown("## 📊 Evaluation Results")

        results = st.session_state.results
        questions = st.session_state.questions

        final_table = []

        for student in results:
            st.markdown(f"### 👤 {student['Name']}")

            total = 0
            max_total = 0
            row = {"Name": student['Name']}

            for q in questions:
                marks = questions[q]['marks']
                stored = student["marks"][q]["score"]

                edited = st.number_input(
                    f"{student['Name']} - {q}",
                    0.0,
                    float(marks),
                    float(stored),
                    key=f"{student['Name']}_{q}"
                )

                student["marks"][q]["score"] = edited

                total += edited
                max_total += marks
                row[q] = edited

                st.write(f"{q} → {edited}/{marks}")
                st.info(student["marks"][q]["feedback"])

            percentage = round((total/max_total)*100,1)
            grade = get_grade(total,max_total)

            row["Total"] = total
            row["Grade"] = grade

            final_table.append(row)

            st.success(f"{total}/{max_total} | {percentage}% | {grade}")

            st.markdown("---")

        df = pd.DataFrame(final_table)
        df["Rank"] = df["Total"].rank(ascending=False).astype(int)

        st.subheader("📋 Final Marksheet")
        st.dataframe(df)

        st.download_button("📥 Download CSV", df.to_csv(index=False), "marks.csv")

        zip_buffer = io.BytesIO()
        zipf = zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED)

        for student in results:
            name = student["Name"]

            total = sum(student["marks"][q]["score"] for q in questions)
            max_total = sum(questions[q]["marks"] for q in questions)
            percentage = round((total/max_total)*100,1)
            grade = get_grade(total, max_total)

            pdf = generate_pdf(
                name,
                questions,
                student,
                total,
                max_total,
                grade,
                percentage
            )

            zipf.writestr(f"{name}.pdf", pdf.getvalue())

        zipf.close()
        zip_buffer.seek(0)

        st.download_button("📥 Download Reports ZIP", zip_buffer, "reports.zip")

        st.markdown('</div>', unsafe_allow_html=True)
# ============================
# 🟡 MODE 2: CUSTOM MARKSHEET
# ============================
if mode == "Custom Marksheet Generator":

    st.markdown("## 📑 Custom Marksheet Generator")

    csv_file = st.file_uploader("Upload CSV", type="csv")
    inst = st.text_input("Institution Name")
    exam = st.text_input("Exam Name")
    teacher = st.text_input("Class Teacher")

    if csv_file:

        df = pd.read_csv(csv_file)
        st.dataframe(df)

        if st.button("Generate ZIP"):

            zip_buffer = io.BytesIO()
            zipf = zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED)

            for _, row in df.iterrows():

                name = row["Name"]
                subjects = list(df.columns[1:-2])
                marks = [row[s] for s in subjects]

                pdf = generate_custom_pdf(name, subjects, marks, row["Total"], row["Grade"], inst, exam, teacher)

                zipf.writestr(f"{name}.pdf", pdf.getvalue())

            zipf.close()
            zip_buffer.seek(0)

            st.download_button("Download Marksheet ZIP", zip_buffer, "marksheets.zip")
# ============================
# 🔵 MODE 3: QUESTION GENERATOR (FINAL + MARKING SCHEME)
# ============================
import hashlib

def get_input_hash(content, sections):
    return hashlib.md5((content + sections).encode()).hexdigest()

def clean_text(text):
    return text.replace("**", "")

def split_question_answer(output):
    output_upper = output.upper()

    if "ANSWER KEY" in output_upper:
        idx = output_upper.index("ANSWER KEY")
        return output[:idx].strip(), output[idx:].strip()
    else:
        return output.strip(), "Answer key not generated"


# -------- MARKING SCHEME PARSER --------
def format_answer_key(content):

    lines = content.split("\n")
    formatted = []

    current_q = None
    buffer = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Detect Q1 (5 Marks) or Q1
        if re.match(r'^(Q\s*\d+)', line, re.IGNORECASE):

            if current_q:
                formatted.append((current_q, buffer))
                buffer = []

            current_q = line

        else:
            buffer.append(line)

    if current_q:
        formatted.append((current_q, buffer))

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


def generate_exam_pdf(content, title, inst, exam, total_marks):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=70,
        bottomMargin=50
    )

    doc.inst_name = inst
    doc.exam_name = exam

    styles = getSampleStyleSheet()
    elements = []

    # -------- TITLE --------
    elements.append(Paragraph(f"<para align='center'><b>{title}</b></para>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Total Marks:</b> {total_marks}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # -------- ANSWER KEY (MARKING SCHEME) --------
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

    # -------- SIGN --------
    elements.append(Spacer(1, 40))

    sign_table = Table([
        ["__________________", "__________________"],
        ["Examiner", "Head of Department"]
    ], colWidths=[200, 200])

    elements.append(sign_table)

    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    buffer.seek(0)
    return buffer


# -------- UI --------
if mode == "Question Paper Generator":

    st.markdown("## 📝 Question Paper Generator")

    topic = st.text_area("Enter Topic / Syllabus")
    notes_file = st.file_uploader("Upload Notes PDF (Optional)", type="pdf")

    st.markdown("### ⚙️ Mark Distribution")

    num_sections = st.number_input("Number of Sections", 1, 10, 3)

    sections_data = []
    total = 0

    for i in range(int(num_sections)):

        sec = chr(65+i)
        st.markdown(f"#### Section {sec}")

        col1, col2, col3 = st.columns(3)

        with col1:
            marks = st.number_input(f"Marks ({sec})", key=f"marks_{i}")

        with col2:
            count = st.number_input(f"Questions ({sec})", key=f"count_{i}")

        with col3:
            diff = st.selectbox(f"Difficulty ({sec})", ["Easy","Medium","Hard"], key=f"diff_{i}")

        sections_data.append((sec, marks, count, diff))
        total += marks * count

    st.success(f"Total Marks = {total}")

    if st.button("🚀 Generate Question Paper"):

        content = extract_text(notes_file) if notes_file else topic

        if not content.strip():
            st.error("Enter topic or upload PDF")
        else:

            sections = ""
            difficulty_rules = ""

            for sec, marks, count, diff in sections_data:
                sections += f"\nSECTION {sec}:\n- {count} questions × {marks} marks\n"
                difficulty_rules += f"\nSECTION {sec} should be {diff} difficulty."

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
            st.session_state.total = total
            st.session_state.generated = True

            st.success("✅ Generated")

    if "generated" in st.session_state:

        total = st.session_state.total

        st.markdown("## 📄 Question Paper (Editable)")
        st.session_state.editable_q = st.text_area("Edit Question Paper", st.session_state.editable_q, height=300)

        st.markdown("## 📘 Answer Key (Editable)")
        st.session_state.editable_a = st.text_area("Edit Answer Key", st.session_state.editable_a, height=300)

        inst = st.text_input("Institution Name")
        exam = st.text_input("Exam Name")

        if inst and exam:

            q_pdf = generate_exam_pdf(st.session_state.editable_q, "QUESTION PAPER", inst, exam, total)
            a_pdf = generate_exam_pdf(st.session_state.editable_a, "ANSWER KEY", inst, exam, total)

            st.download_button("📥 Download Question Paper PDF", q_pdf, "question_paper.pdf")
            st.download_button("📥 Download Answer Key PDF", a_pdf, "answer_key.pdf")

        else:
            st.warning("Enter Institution & Exam Name")