# 🚀 Builder School in a Box  
### AI Startup Builder Assistant  

An AI-powered venture building workflow that helps school students go from:

**Raw Idea → Structured Startup → Mentor Refinement → Readiness Score → Working Prototype**

All inside one guided AI system.

---

## 🌟 Problem

School students often have creative startup ideas but lack:

- Structured thinking
- Business validation skills
- Access to mentorship
- Technical ability to build prototypes

Most AI tools act like chatbots and generate unstructured advice.

This project builds the **core intelligence layer of an AI-native venture studio designed specifically for school students.**

---

## 🧠 What This System Does

### ✅ Step 1 – Idea Input
Student provides:
- Startup idea (free text)
- Class (6–12)
- Idea Type:
  - App or Website
  - AI Tool
  - Marketplace

---

### ✅ Step 2 – Structured Idea Refinement

The system generates strictly structured JSON output:

- Clear problem statement  
- Specific target user  
- Three actionable core features  
- Simple revenue model  
- Five-day action plan  

No generic paragraphs.  
Output is enforced and parsed as JSON.

---

### ✅ Step 3 – Mentor Session

The system generates exactly **3 intelligent follow-up questions** targeting:

1. Demand validation  
2. Differentiation from existing solutions  
3. Monetization clarity  

For each student answer, the system provides:

- What is strong  
- What is weak  
- One concrete next step  

This simulates real startup mentorship.

---

### ✅ Step 4 – Startup Readiness Score

The idea is evaluated across four venture dimensions:

- Problem Clarity (1–10)  
- Monetization Clarity (1–10)  
- Differentiation (1–10)  
- Student Feasibility (1–10)  

It also returns:

- Overall score  
- Honest verdict  
- Biggest strength  
- Biggest risk  

This introduces a structured evaluation layer.

---

### ✅ Step 5 – Improved Blueprint (Version 2)

Using mentor feedback and scoring insights, the system generates:

- Refined startup name  
- Sharpened problem statement  
- Updated features  
- Stronger revenue model  
- Clear explanation of what changed  

This demonstrates **iteration and learning**, not just generation.

---

### ✅ Step 6 – Prototype Generator

Based on idea type:

#### 🖥 App or Website
- Complete self-contained HTML landing page
- Tailwind-based UI
- Live preview inside Streamlit
- Downloadable `.html` file

#### 🤖 AI Tool
- Runnable Streamlit app
- Groq API integration
- Structured prompt logic
- Downloadable `.py` file

#### 🛒 Marketplace
- HTML frontend scaffold
- SQL database schema
- Flask API scaffold
- Downloadable scaffold file

All prototypes are scaffold-level but logically coherent and runnable.

---

## 🏗 Architecture Overview

The system is modular and stage-based.

```
Idea Input
    ↓
Structured Refinement (JSON enforced)
    ↓
Mentor Question Generator
    ↓
Mentor Feedback Engine
    ↓
Startup Readiness Scoring Engine
    ↓
Improved Blueprint Generator
    ↓
Conditional Prototype Generator
    ↓
Full Session JSON Export
```

Each stage:

- Uses controlled prompts  
- Enforces structured JSON outputs  
- Maintains session state  
- Prevents raw LLM dumps  

This is not a chatbot — it is a structured AI workflow engine.

---

## 🛠 Tech Stack

- Python  
- Streamlit  
- Groq API (LLaMA 3.3 70B)  
- JSON-based orchestration  
- Stateful session management  

---

## 📦 Installation

```bash
pip install streamlit groq
```

Run the app:

```bash
streamlit run app.py
```

Add your Groq API key in line 17 of app.py file (edit: "enter your api key").

Free API key available at:
https://console.groq.com

---

## 📂 Session Export Feature

At the end of the workflow, the system exports:

- Idea input  
- Structured refinement  
- Mentor Q&A  
- Readiness score  
- Improved blueprint  
- Prototype code  

Saved as:

```
builder_school_session.json
```

This ensures transparency and structured evaluation.

---

## 💡 What Makes This Unique

- Structured JSON enforcement instead of free-form AI responses  
- Stage-based guided progression  
- Startup scoring layer  
- Iterative improvement blueprint  
- Conditional multi-format prototype generation  
- Full journey export as structured data  

It mirrors how real venture studios refine and evaluate startups — simplified for school founders.

---

## 🎯 Goal

To build the intelligence layer of an AI-powered venture studio that enables school students to:

- Think clearly  
- Validate properly  
- Iterate intelligently  
- Build practically  

All inside a structured AI workflow.

---
