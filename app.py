import streamlit as st
import json
import re
import os
from groq import Groq

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="Builder School in a Box", page_icon="🚀", layout="wide")

# ─────────────────────────────────────────────
# SIDEBAR — API KEY + STAGE TRACKER
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Free at console.groq.com — no card needed."
    )
    st.caption("Get a free key at console.groq.com")
    st.divider()
    st.markdown("**Progress**")
    current_stage = st.session_state.get("stage", 1) or 1
    for i, label in enumerate(["Idea Input", "Refinement", "Mentor Session", "Score & Blueprint", "Prototype"], 1):
        icon = "✅" if current_stage > i else ("🔵" if current_stage == i else "⬜")
        st.markdown(f"{icon} Step {i}: {label}")

# Resolve API key: sidebar > environment
resolved_key = api_key_input.strip() if api_key_input.strip() else os.environ.get("GROQ_API_KEY", "")

if not resolved_key:
    st.warning("⬅️ Enter your Groq API key in the sidebar to get started.")
    st.caption("No card needed. Sign up free at console.groq.com")
    st.stop()

client = Groq(api_key=resolved_key)
MODEL = "llama-3.3-70b-versatile"   # best free model on Groq — 70B, fast, great at JSON

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
ALL_KEYS = ["stage", "idea", "student_class", "idea_type",
            "structured_output", "mentor_questions", "mentor_answers",
            "mentor_responses", "prototype_code", "current_question_idx",
            "readiness_score", "improved_blueprint"]

for key in ALL_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None

if st.session_state.stage is None:
    st.session_state.stage = 1
if st.session_state.mentor_answers is None:
    st.session_state.mentor_answers = []
if st.session_state.mentor_responses is None:
    st.session_state.mentor_responses = []
if st.session_state.current_question_idx is None:
    st.session_state.current_question_idx = 0


def full_reset():
    for key in ALL_KEYS:
        st.session_state[key] = None
    st.session_state.stage = 1
    st.session_state.mentor_answers = []
    st.session_state.mentor_responses = []
    st.session_state.current_question_idx = 0
    st.session_state.readiness_score = None
    st.session_state.improved_blueprint = None


def reset_from_stage(from_stage: int):
    if from_stage <= 2:
        st.session_state.structured_output = None
    if from_stage <= 3:
        st.session_state.mentor_questions = None
        st.session_state.mentor_answers = []
        st.session_state.mentor_responses = []
        st.session_state.current_question_idx = 0
    if from_stage <= 4:
        st.session_state.prototype_code = None
        st.session_state.readiness_score = None
        st.session_state.improved_blueprint = None


# ─────────────────────────────────────────────
# LLM CORE — GROQ
# ─────────────────────────────────────────────
def call_groq(system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
    """Central Groq call with error handling."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        err = str(e).lower()
        if "401" in err or "invalid" in err or "api key" in err or "auth" in err:
            st.error("❌ Invalid API key. Check what you entered in the sidebar.")
        elif "429" in err or "rate" in err or "quota" in err:
            st.error("⏳ Rate limit hit. Wait a few seconds and try again.")
        elif "503" in err or "unavailable" in err:
            st.error("⚠️ Groq service temporarily unavailable. Try again in a moment.")
        else:
            st.error(f"❌ Error: {e}")
        st.stop()


def extract_json(text: str) -> str:
    """Strip all markdown fences and extract only the JSON object/array."""
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    match = re.search(r"[\[{]", text)
    if match:
        text = text[match.start():]
    last = max(text.rfind("}"), text.rfind("]"))
    if last != -1:
        text = text[:last + 1]
    return text.strip()


# ─────────────────────────────────────────────
# STAGE 2: STRUCTURED REFINEMENT
# ─────────────────────────────────────────────
def get_structured_idea(idea: str, student_class: str, idea_type: str) -> dict:
    system = f"""You are an expert startup mentor for school students (classes 6-12).
Analyze the startup idea and return ONLY a valid JSON object.
No markdown, no code fences, no text before or after the JSON.

Return exactly this structure:
{{
  "problem_statement": "2-3 sentences describing the specific real-world problem",
  "target_user": "named specific user group (e.g. 'Class 9-10 students who miss assignment deadlines')",
  "core_features": [
    "Feature 1 — specific and actionable",
    "Feature 2 — specific and actionable",
    "Feature 3 — specific and actionable"
  ],
  "revenue_model": "one simple realistic revenue mechanism for a school-level startup",
  "five_day_plan": [
    {{"day": 1, "task": "specific task"}},
    {{"day": 2, "task": "specific task"}},
    {{"day": 3, "task": "specific task"}},
    {{"day": 4, "task": "specific task"}},
    {{"day": 5, "task": "specific task"}}
  ]
}}

Rules:
- Use Class {student_class} level language — clear, no jargon
- Be specific to THIS exact idea, not generic startup advice
- Output ONLY the JSON object, nothing else"""

    raw = call_groq(system, f"Idea: {idea}\nType: {idea_type}\nClass: {student_class}", max_tokens=1200)
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        st.error(f"JSON parse failed.\n\nRaw output:\n{raw}\n\nError: {e}")
        st.stop()


# ─────────────────────────────────────────────
# STAGE 3: MENTOR QUESTIONS + RESPONSE
# ─────────────────────────────────────────────
def get_mentor_questions(idea: str, structured: dict) -> list:
    system = """You are a sharp startup mentor for a school student.
Generate exactly 3 targeted follow-up questions that expose real gaps in their thinking.

DO NOT ask generic questions like "Have you done market research?".
Make each question specific to this exact idea, targeting:
- Q1: How they will validate demand BEFORE building anything
- Q2: What makes this different from existing alternatives
- Q3: Who exactly will pay, how much, and why

Return ONLY a JSON array of exactly 3 strings. No markdown, no extra text.
Format: ["Question 1?", "Question 2?", "Question 3?"]"""

    user = f"""Idea: {idea}
Problem: {structured['problem_statement']}
Target user: {structured['target_user']}
Revenue model: {structured['revenue_model']}
Features: {', '.join(structured['core_features'])}"""

    raw = call_groq(system, user, max_tokens=400)
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        st.error(f"Could not parse mentor questions: {e}\nRaw: {raw}")
        st.stop()


def get_mentor_response(question: str, answer: str, idea: str) -> str:
    system = """You are a mentor giving honest feedback on a school student's startup answer.
Write exactly 3 sentences:
1. What is strong about their answer
2. The critical gap or weakness you see
3. One concrete next step they should take this week
Be direct. Do not sugarcoat. Write in prose, no bullet points."""

    return call_groq(system,
                     f"Startup: {idea}\nQuestion: {question}\nStudent answer: {answer}",
                     max_tokens=250)


# ─────────────────────────────────────────────
# NEW FEATURE 1: STARTUP READINESS SCORE
# ─────────────────────────────────────────────
def get_readiness_score(idea: str, structured: dict, mentor_answers: list, mentor_responses: list) -> dict:
    """
    After mentor session, evaluate the startup across 4 dimensions.
    Returns a dict with scores + overall + short verdict.
    """
    answers_text = ""
    for i, (a, r) in enumerate(zip(mentor_answers, mentor_responses), 1):
        answers_text += f"Q{i} Answer: {a}\nMentor Feedback: {r}\n\n"

    system = """You are a startup evaluator scoring a school student's startup idea.
Based on the idea details and how the student answered mentor questions, return ONLY a valid JSON object.
No markdown, no code fences, no text before or after.

Return exactly this structure:
{
  "problem_clarity": 7,
  "monetization_clarity": 6,
  "differentiation": 5,
  "student_feasibility": 8,
  "overall": 6.5,
  "verdict": "2-sentence honest verdict on the startup's potential",
  "biggest_strength": "one specific strength",
  "biggest_risk": "one specific risk to address"
}

Scoring rules:
- Each dimension scored 1-10 (integer)
- overall = average of 4 scores, rounded to 1 decimal
- Be honest, not encouraging — judges will read this
- Output ONLY the JSON object"""

    user = f"""Startup: {idea}
Problem: {structured['problem_statement']}
Target user: {structured['target_user']}
Revenue model: {structured['revenue_model']}
Features: {', '.join(structured['core_features'])}

Student's mentor session answers:
{answers_text}"""

    raw = call_groq(system, user, max_tokens=500)
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        st.error(f"Score parse failed: {e}\nRaw: {raw}")
        st.stop()


# ─────────────────────────────────────────────
# NEW FEATURE 2: IMPROVED IDEA BLUEPRINT
# ─────────────────────────────────────────────
def get_improved_blueprint(idea: str, structured: dict, mentor_answers: list, mentor_responses: list, score: dict) -> dict:
    """
    After mentor session + scoring, regenerate an improved version of the startup
    incorporating mentor insights. This shows the iteration/learning loop.
    """
    answers_text = ""
    for i, (a, r) in enumerate(zip(mentor_answers, mentor_responses), 1):
        answers_text += f"Q{i} — Student said: {a} | Mentor noted: {r}\n"

    system = """You are a startup mentor creating an IMPROVED version of a student's startup idea.
Based on the original idea + mentor session insights, generate a refined blueprint.
Return ONLY a valid JSON object. No markdown, no fences, no extra text.

Return exactly this structure:
{
  "improved_name": "A sharper startup name",
  "refined_problem": "Clearer 2-sentence problem statement incorporating mentor feedback",
  "pivot_or_sharpen": "What specifically changed from original — pivot or sharpening?",
  "updated_features": [
    "Updated Feature 1 — reflects mentor insights",
    "Updated Feature 2 — reflects mentor insights",
    "Updated Feature 3 — reflects mentor insights"
  ],
  "stronger_revenue_model": "Improved revenue model based on who-pays clarity from mentor session",
  "key_improvement": "The single most important change from v1 to v2"
}

Rules:
- MUST reflect actual mentor feedback, not generic improvements
- Be specific — show that answers influenced the output
- Output ONLY the JSON object"""

    user = f"""Original idea: {idea}
Original problem: {structured['problem_statement']}
Original features: {', '.join(structured['core_features'])}
Original revenue: {structured['revenue_model']}

Mentor session insights:
{answers_text}

Weakest area (from scoring): {score.get('biggest_risk', 'differentiation')}"""

    raw = call_groq(system, user, max_tokens=800)
    try:
        return json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        st.error(f"Blueprint parse failed: {e}\nRaw: {raw}")
        st.stop()


# ─────────────────────────────────────────────
# STAGE 4: PROTOTYPE GENERATOR
# ─────────────────────────────────────────────
def get_prototype(idea: str, idea_type: str, structured: dict) -> str:
    features_str = "\n".join(f"- {f}" for f in structured["core_features"])
    context = f"""Startup: {idea}
Problem: {structured['problem_statement']}
Target user: {structured['target_user']}
Core features:
{features_str}"""

    if idea_type == "App or Website":
        system = """Generate a complete self-contained HTML landing page for a student startup.

STRICT REQUIREMENTS:
- Single .html file, all CSS inline
- Load Tailwind CSS from CDN: <script src="https://cdn.tailwindcss.com"></script>
- Sections in order: navbar with startup name, hero (bold headline + subheading + CTA button),
  3 feature cards in a grid, simple footer
- Use indigo or teal as accent color throughout
- Must look modern and professional in a browser
- Output ONLY the HTML starting with <!DOCTYPE html>
- No explanation text, no markdown fences, no extra text"""

    elif idea_type == "AI Tool":
        system = """Generate a complete runnable Streamlit Python app for an AI tool startup.

Start with EXACTLY this comment block (fill in real values for this idea):
# ============================================================
# AI TOOL: [Tool Name]
# DESCRIPTION: [One sentence]
# SETUP: pip install streamlit groq
# RUN:   streamlit run ai_tool.py
# ============================================================

STRICT REQUIREMENTS:
- Import streamlit and groq
- Sidebar: st.text_input for GROQ_API_KEY (type="password")
- st.title() and st.write() description
- Input area relevant to this specific idea
- A Generate button
- On click: call Groq llama-3.3-70b-versatile with a SPECIFIC system prompt for this use case
- Display response with st.markdown
- try/except for errors with st.error()
- ZERO placeholders — all code must be runnable immediately

Output ONLY Python code starting with the comment block. No markdown fences."""

    else:  # Marketplace
        system = """Generate a complete marketplace startup prototype in THREE sections.

Use EXACTLY these headers:

## SECTION 1: HTML FRONTEND
Self-contained HTML with Tailwind CDN (<script src="https://cdn.tailwindcss.com"></script>).
Include: navbar, buyer listing grid with search bar, seller post-listing form.

## SECTION 2: DATABASE SCHEMA
SQL CREATE TABLE statements for: users, listings, transactions, reviews.
Include PRIMARY KEY, FOREIGN KEY constraints, and indexes.

## SECTION 3: FLASK API SCAFFOLD
Start with: # pip install flask flask-sqlalchemy
Include 5 routes: GET /listings, POST /listings, POST /users/register, POST /users/login, POST /transactions
JSON responses, basic input validation, SQLite setup.

Output ONLY code with the three section headers. No other explanation."""

    return call_groq(system, context, max_tokens=3500)


# ─────────────────────────────────────────────
# SESSION EXPORT — builds full JSON snapshot
# ─────────────────────────────────────────────
def build_session_export() -> dict:
    """
    Collects EVERYTHING from session state into one clean dict.
    Used for JSON download and the summary panel.
    """
    ss = st.session_state

    # Build mentor Q&A thread
    mentor_thread = []
    questions  = ss.mentor_questions  or []
    answers    = ss.mentor_answers    or []
    responses  = ss.mentor_responses  or []
    for i, q in enumerate(questions):
        mentor_thread.append({
            "question":        q,
            "student_answer":  answers[i]  if i < len(answers)   else None,
            "mentor_feedback": responses[i] if i < len(responses) else None,
        })

    export = {
        "meta": {
            "app": "Builder School in a Box",
            "stage_reached": ss.stage or 1,
        },
        "step1_input": {
            "idea":          ss.idea,
            "student_class": ss.student_class,
            "idea_type":     ss.idea_type,
        },
        "step2_refinement":   ss.structured_output,
        "step3_mentor_session": {
            "questions_and_answers": mentor_thread
        },
        "step4_evaluation": {
            "readiness_score":    ss.readiness_score,
            "improved_blueprint": ss.improved_blueprint,
        },
        "step5_prototype": {
            "code": ss.prototype_code
        },
    }
    return export


def render_session_summary():
    """
    Shows a collapsible full-journey summary panel with a JSON download button.
    Rendered at every stage >= 2 so user never loses previous data.
    """
    stage = st.session_state.get("stage", 1) or 1
    if stage < 2:
        return  # nothing to show yet

    export = build_session_export()
    export_json = json.dumps(export, indent=2, ensure_ascii=False)

    with st.expander("📋 Full Session Summary — click to review all previous steps", expanded=False):
        # ── Input ───────────────────────────────────
        if export["step1_input"]["idea"]:
            st.markdown("#### 💡 Your Idea")
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"**Idea:** {export['step1_input']['idea']}")
            col2.markdown(f"**Class:** {export['step1_input']['student_class']}")
            col3.markdown(f"**Type:** {export['step1_input']['idea_type']}")

        # ── Refinement ──────────────────────────────
        s2 = export["step2_refinement"]
        if s2:
            st.divider()
            st.markdown("#### 🧠 Idea Refinement")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Problem:** {s2['problem_statement']}")
                st.markdown(f"**Target User:** {s2['target_user']}")
                st.markdown(f"**Revenue:** {s2['revenue_model']}")
            with c2:
                st.markdown("**Features:**")
                for f in s2["core_features"]:
                    st.markdown(f"- {f}")
                st.markdown("**5-Day Plan:**")
                for d in s2["five_day_plan"]:
                    st.markdown(f"- Day {d['day']}: {d['task']}")

        # ── Mentor Session ───────────────────────────
        thread = export["step3_mentor_session"]["questions_and_answers"]
        if thread:
            st.divider()
            st.markdown("#### 🧑‍🏫 Mentor Session")
            for i, item in enumerate(thread, 1):
                st.markdown(f"**Q{i}:** {item['question']}")
                if item["student_answer"]:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;🎓 *You:* {item['student_answer']}")
                if item["mentor_feedback"]:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;💬 *Feedback:* {item['mentor_feedback']}")

        # ── Score ───────────────────────────────────
        sc = export["step4_evaluation"]["readiness_score"]
        if sc:
            st.divider()
            st.markdown("#### 📊 Readiness Score")
            st.markdown(
                f"Problem Clarity: **{sc['problem_clarity']}/10** | "
                f"Monetization: **{sc['monetization_clarity']}/10** | "
                f"Differentiation: **{sc['differentiation']}/10** | "
                f"Feasibility: **{sc['student_feasibility']}/10** | "
                f"**Overall: {sc['overall']}/10**"
            )
            st.markdown(f"Verdict: {sc['verdict']}")

        # ── Improved Blueprint ───────────────────────
        bp = export["step4_evaluation"]["improved_blueprint"]
        if bp:
            st.divider()
            st.markdown("#### 🔄 Improved Blueprint (v2)")
            st.markdown(f"**New Name:** {bp['improved_name']}")
            st.markdown(f"**Refined Problem:** {bp['refined_problem']}")
            st.markdown(f"**Key Improvement:** {bp['key_improvement']}")

        # ── Prototype ───────────────────────────────
        if export["step5_prototype"]["code"]:
            st.divider()
            st.markdown("#### 🛠 Prototype")
            st.markdown("✅ Prototype code generated — download it from Step 5.")

        # ── Download button ──────────────────────────
        st.divider()
        st.download_button(
            label="⬇️ Download Full Session as JSON",
            data=export_json,
            file_name="builder_school_session.json",
            mime="application/json",
            use_container_width=True,
            help="Save everything — your idea, refinement, mentor Q&A, score, blueprint, and prototype."
        )


# ─────────────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────────────
st.title("🚀 Builder School in a Box")
st.caption("AI Startup Builder Assistant — Idea → Structure → Mentorship → Prototype")

progress_map = {1: 0.1, 2: 0.35, 3: 0.6, 4: 0.8, 5: 1.0}
st.progress(progress_map.get(st.session_state.stage, 0))
st.subheader({
    1: "Step 1: Your Idea",
    2: "Step 2: Idea Refinement",
    3: "Step 3: Mentor Session",
    4: "Step 4: Score & Improved Blueprint",
    5: "Step 5: Your Prototype"
}.get(st.session_state.stage, ""))

# ── Session Summary Panel (visible from Stage 2 onward) ──────────────────────
render_session_summary()

st.divider()

# ═══════════════════════════════════════════
# STAGE 1 — IDEA INPUT
# ═══════════════════════════════════════════
if st.session_state.stage == 1:
    with st.form("idea_form"):
        idea = st.text_area(
            "Describe your startup idea", height=130,
            placeholder="e.g. An app that connects school students with local tutors for last-minute exam help..."
        )
        col1, col2 = st.columns(2)
        with col1:
            student_class = st.selectbox("Your Class", [str(i) for i in range(6, 13)], index=6)
        with col2:
            idea_type = st.radio("Type of Idea", ["App or Website", "AI Tool", "Marketplace"])
        submitted = st.form_submit_button("🔍 Refine My Idea →", use_container_width=True, type="primary")

    if submitted:
        if not idea.strip():
            st.error("Please describe your idea before continuing.")
        else:
            reset_from_stage(2)
            st.session_state.idea = idea.strip()
            st.session_state.student_class = student_class
            st.session_state.idea_type = idea_type
            st.session_state.stage = 2
            st.rerun()

# ═══════════════════════════════════════════
# STAGE 2 — STRUCTURED REFINEMENT
# ═══════════════════════════════════════════
elif st.session_state.stage == 2:
    if st.session_state.structured_output is None:
        with st.spinner("🧠 Analyzing your idea..."):
            st.session_state.structured_output = get_structured_idea(
                st.session_state.idea,
                st.session_state.student_class,
                st.session_state.idea_type
            )

    s = st.session_state.structured_output
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🎯 Problem Statement")
        st.info(s["problem_statement"])
        st.markdown("#### 👤 Target User")
        st.info(s["target_user"])
        st.markdown("#### 💰 Revenue Model")
        st.success(s["revenue_model"])
    with col2:
        st.markdown("#### ⚙️ Core Features")
        for i, f in enumerate(s["core_features"], 1):
            st.markdown(f"**{i}.** {f}")
        st.markdown("#### 📅 5-Day Action Plan")
        for day in s["five_day_plan"]:
            st.markdown(f"**Day {day['day']}:** {day['task']}")

    st.divider()
    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("← Change Idea", use_container_width=True):
            full_reset()
            st.rerun()
    with col_b:
        if st.button("Start Mentor Session →", use_container_width=True, type="primary"):
            reset_from_stage(3)
            st.session_state.stage = 3
            st.rerun()

# ═══════════════════════════════════════════
# STAGE 3 — MENTOR SESSION
# ═══════════════════════════════════════════
elif st.session_state.stage == 3:
    if st.session_state.mentor_questions is None:
        with st.spinner("🧑‍🏫 Preparing mentor questions..."):
            st.session_state.mentor_questions = get_mentor_questions(
                st.session_state.idea,
                st.session_state.structured_output
            )

    questions = st.session_state.mentor_questions
    idx = st.session_state.current_question_idx

    # Threaded conversation display — completed exchanges
    for i in range(min(idx, len(questions))):
        st.markdown(
            f"""<div style="background:#f0f4ff;border-left:4px solid #4f6ef7;
            padding:12px 16px;border-radius:6px;margin-bottom:6px;">
            <strong>🧑‍🏫 Mentor Q{i+1}:</strong><br>{questions[i]}</div>""",
            unsafe_allow_html=True)
        if i < len(st.session_state.mentor_answers):
            st.markdown(
                f"""<div style="background:#f6fff6;border-left:4px solid #28a745;
                padding:12px 16px;border-radius:6px;margin-bottom:6px;margin-left:32px;">
                <strong>🎓 You:</strong><br>{st.session_state.mentor_answers[i]}</div>""",
                unsafe_allow_html=True)
        if i < len(st.session_state.mentor_responses):
            st.markdown(
                f"""<div style="background:#fffbf0;border-left:4px solid #f0ad00;
                padding:12px 16px;border-radius:6px;margin-bottom:18px;">
                <strong>🧑‍🏫 Feedback:</strong><br>{st.session_state.mentor_responses[i]}</div>""",
                unsafe_allow_html=True)

    # Active question
    if idx < len(questions):
        st.markdown(
            f"""<div style="background:#f0f4ff;border-left:4px solid #4f6ef7;
            padding:12px 16px;border-radius:6px;margin-bottom:12px;">
            <strong>🧑‍🏫 Mentor Q{idx+1} of {len(questions)}:</strong><br>{questions[idx]}</div>""",
            unsafe_allow_html=True)

        with st.form(f"mentor_form_{idx}"):
            answer = st.text_area("Your Answer", height=110,
                                  placeholder="Be specific — vague answers get tough feedback.")
            col_r, col_s = st.columns([1, 3])
            with col_r:
                restart = st.form_submit_button("↺ Restart Q&A")
            with col_s:
                submitted = st.form_submit_button("Submit Answer →", type="primary", use_container_width=True)

        if restart:
            st.session_state.mentor_answers = []
            st.session_state.mentor_responses = []
            st.session_state.current_question_idx = 0
            st.rerun()
        if submitted:
            if not answer.strip():
                st.error("Write an answer first.")
            else:
                st.session_state.mentor_answers.append(answer.strip())
                with st.spinner("Mentor is responding..."):
                    resp = get_mentor_response(questions[idx], answer, st.session_state.idea)
                st.session_state.mentor_responses.append(resp)
                st.session_state.current_question_idx += 1
                st.rerun()

    else:
        st.success("✅ All 3 mentor questions answered!")
        st.divider()
        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("← Back to Refinement"):
                st.session_state.stage = 2
                st.rerun()
        with col_b:
            if st.button("📊 See Score & Improved Blueprint →", use_container_width=True, type="primary"):
                st.session_state.readiness_score = None
                st.session_state.improved_blueprint = None
                st.session_state.stage = 4
                st.rerun()

# ═══════════════════════════════════════════
# STAGE 4 — SCORE & IMPROVED BLUEPRINT (NEW)
# ═══════════════════════════════════════════
elif st.session_state.stage == 4:
    # Generate readiness score
    if st.session_state.readiness_score is None:
        with st.spinner("📊 Evaluating your startup idea..."):
            st.session_state.readiness_score = get_readiness_score(
                st.session_state.idea,
                st.session_state.structured_output,
                st.session_state.mentor_answers,
                st.session_state.mentor_responses
            )

    # Generate improved blueprint
    if st.session_state.improved_blueprint is None:
        with st.spinner("🔄 Generating improved blueprint based on mentor insights..."):
            st.session_state.improved_blueprint = get_improved_blueprint(
                st.session_state.idea,
                st.session_state.structured_output,
                st.session_state.mentor_answers,
                st.session_state.mentor_responses,
                st.session_state.readiness_score
            )

    sc = st.session_state.readiness_score
    bp = st.session_state.improved_blueprint

    # ── READINESS SCORE DISPLAY ──────────────────
    st.markdown("### 📊 Startup Readiness Score")

    col1, col2, col3, col4, col5 = st.columns(5)
    def score_color(s):
        if s >= 8: return "#28a745"
        if s >= 6: return "#f0ad00"
        return "#dc3545"

    with col1:
        c = score_color(sc["problem_clarity"])
        st.markdown(f"""<div style="text-align:center;background:#f8f9fa;border-radius:10px;padding:16px;border-top:4px solid {c};">
        <div style="font-size:2rem;font-weight:bold;color:{c};">{sc["problem_clarity"]}/10</div>
        <div style="font-size:0.8rem;color:#555;">Problem Clarity</div></div>""", unsafe_allow_html=True)
    with col2:
        c = score_color(sc["monetization_clarity"])
        st.markdown(f"""<div style="text-align:center;background:#f8f9fa;border-radius:10px;padding:16px;border-top:4px solid {c};">
        <div style="font-size:2rem;font-weight:bold;color:{c};">{sc["monetization_clarity"]}/10</div>
        <div style="font-size:0.8rem;color:#555;">Monetization</div></div>""", unsafe_allow_html=True)
    with col3:
        c = score_color(sc["differentiation"])
        st.markdown(f"""<div style="text-align:center;background:#f8f9fa;border-radius:10px;padding:16px;border-top:4px solid {c};">
        <div style="font-size:2rem;font-weight:bold;color:{c};">{sc["differentiation"]}/10</div>
        <div style="font-size:0.8rem;color:#555;">Differentiation</div></div>""", unsafe_allow_html=True)
    with col4:
        c = score_color(sc["student_feasibility"])
        st.markdown(f"""<div style="text-align:center;background:#f8f9fa;border-radius:10px;padding:16px;border-top:4px solid {c};">
        <div style="font-size:2rem;font-weight:bold;color:{c};">{sc["student_feasibility"]}/10</div>
        <div style="font-size:0.8rem;color:#555;">Feasibility</div></div>""", unsafe_allow_html=True)
    with col5:
        overall = sc["overall"]
        c = score_color(overall)
        st.markdown(f"""<div style="text-align:center;background:#f8f9fa;border-radius:10px;padding:16px;border-top:4px solid {c};">
        <div style="font-size:2rem;font-weight:bold;color:{c};">{overall}/10</div>
        <div style="font-size:0.8rem;color:#555;"><strong>Overall</strong></div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_s, col_r = st.columns(2)
    with col_s:
        st.success(f"💪 **Biggest Strength:** {sc['biggest_strength']}")
    with col_r:
        st.warning(f"⚠️ **Biggest Risk:** {sc['biggest_risk']}")
    st.info(f"**Verdict:** {sc['verdict']}")

    st.divider()

    # ── IMPROVED BLUEPRINT DISPLAY ────────────────
    st.markdown("### 🔄 Improved Startup Blueprint (v2)")
    st.caption("Generated by incorporating your mentor session answers")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"#### 🏷️ New Name")
        st.markdown(f"**{bp['improved_name']}**")
        st.markdown(f"#### 🎯 Refined Problem")
        st.info(bp["refined_problem"])
        st.markdown(f"#### 💰 Stronger Revenue Model")
        st.success(bp["stronger_revenue_model"])
    with col_b:
        st.markdown(f"#### ⚙️ Updated Features")
        for i, f in enumerate(bp["updated_features"], 1):
            st.markdown(f"**{i}.** {f}")
        st.markdown(f"#### 🔀 What Changed from v1")
        st.warning(bp["pivot_or_sharpen"])
        st.markdown(f"#### ✅ Key Improvement")
        st.success(bp["key_improvement"])

    st.divider()
    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Back to Mentor"):
            st.session_state.stage = 3
            st.rerun()
    with col_next:
        if st.button("🛠 Generate Prototype →", use_container_width=True, type="primary"):
            st.session_state.prototype_code = None
            st.session_state.stage = 5
            st.rerun()

# ═══════════════════════════════════════════
# STAGE 5 — PROTOTYPE GENERATOR
# ═══════════════════════════════════════════
elif st.session_state.stage == 5:
    idea_type = st.session_state.idea_type

    if st.session_state.prototype_code is None:
        with st.spinner(f"🛠 Building your {idea_type} prototype..."):
            st.session_state.prototype_code = get_prototype(
                st.session_state.idea,
                idea_type,
                st.session_state.structured_output
            )

    code = st.session_state.prototype_code
    st.success(f"✅ Your **{idea_type}** prototype is ready!")

    if idea_type == "App or Website":
        tab1, tab2 = st.tabs(["💻 Live Preview", "📄 HTML Source"])
        with tab1:
            st.components.v1.html(code, height=650, scrolling=True)
        with tab2:
            st.code(code, language="html")
            st.download_button("⬇️ Download landing_page.html", code,
                               "landing_page.html", "text/html", use_container_width=True)

    elif idea_type == "AI Tool":
        st.code(code, language="python")
        st.info("**To run:** `pip install streamlit groq` → `streamlit run ai_tool.py`")
        st.download_button("⬇️ Download ai_tool.py", code,
                           "ai_tool.py", "text/plain", use_container_width=True)

    else:  # Marketplace
        sections = re.split(r"(## SECTION \d+[^\n]*)", code)
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                header = sections[i].strip()
                content = sections[i + 1].strip() if i + 1 < len(sections) else ""
                lang = "html" if "HTML" in header else ("sql" if "DATABASE" in header else "python")
                with st.expander(header, expanded=True):
                    st.code(content, language=lang)
        else:
            st.code(code, language="python")
        st.download_button("⬇️ Download marketplace_scaffold.txt", code,
                           "marketplace_scaffold.txt", "text/plain", use_container_width=True)

    st.divider()

    # ── Final full-session JSON download ─────────────────────────────────────
    st.markdown("### 📦 Download Your Complete Journey")
    st.caption("Everything in one file: your idea, refinement, mentor Q&A, score, blueprint, and prototype code.")
    final_export = build_session_export()
    final_json   = json.dumps(final_export, indent=2, ensure_ascii=False)
    st.download_button(
        label="⬇️ Download builder_school_session.json",
        data=final_json,
        file_name="builder_school_session.json",
        mime="application/json",
        use_container_width=True,
    )

    # ── Pretty JSON preview ──────────────────────────────────────────────────
    with st.expander("🔍 Preview raw JSON export", expanded=False):
        st.code(final_json, language="json")

    st.divider()
    if st.button("🔁 Start Over with a New Idea", use_container_width=True):
        full_reset()
        st.rerun()

