# Medical Knowledge-Based System (KBS)

A **classical Knowledge-Based System** for medical knowledge: rule-based representation (IF–THEN in JSON), forward-chaining inference engine, explanation facility, and read-only, non-diagnostic use. Built with **Python** and **Streamlit**.

---

## Tech stack

- **Language:** Python  
- **UI:** Streamlit  
- **Libraries:** psutil (optional; app runs without it), built-in only: json, os, sys, datetime, typing  
- **Environment:** .venv virtual environment  
- **Storage:** JSON files only (no external databases)

---

## Application structure

| File / folder        | Role |
|----------------------|------|
| **app.py**           | Streamlit UI: Home, Disease Search, Symptom Checker, Explanation View, System Info. Global disclaimer. No medical logic in UI. |
| **inference_engine.py** | Forward chaining, rule matching, confidence, explanation data. Knowledge (JSON) separate from reasoning (Python). |
| **knowledge_loader.py** | Load and validate JSON knowledge base; schema and consistency checks; versioning and load-time logging; cache for performance. |
| **data/knowledge_base.json** | Structured KBS knowledge: metadata (version, last_updated), facts (symptoms, diagnostics, treatments), diseases, rules (IF symptoms THEN disease_id, confidence). |

---

## Setup instructions

### 1. Create virtual environment (.venv)

**Windows (PowerShell):**
```powershell
cd "c:\Users\k\Desktop\medical problem identification system"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
cd "c:\Users\k\Desktop\medical problem identification system"
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
cd "/path/to/medical problem identification system"
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Installs **Streamlit** (required) and **psutil** (optional; system monitoring). The app runs if psutil is missing.

### 3. Run the app

From the project root (folder containing `app.py`), with `.venv` activated:

```bash
streamlit run app.py
```

Open the URL shown (e.g. **http://localhost:8501**). The app loads `data/knowledge_base.json` at startup and runs immediately after dependency installation.

---

## KBS features implemented

1. **Knowledge base** — Structured JSON: metadata (version, last_updated), facts (symptoms, diagnostics, treatments), diseases, rules (IF–THEN with confidence).  
2. **Knowledge representation** — Rule-based (IF symptoms A,B,C THEN disease X); knowledge in JSON, reasoning in Python; schema validation on load.  
3. **Inference engine** — Forward chaining; rule matching against user-selected symptoms; returns matched diseases and confidence; no medical logic in UI.  
4. **Explanation facility** — For each recommendation: which rules fired, which symptoms matched, human-readable explanation (Symptom Checker expander and Explanation View page).  
5. **Knowledge acquisition & maintenance** — Safe updates by replacing JSON; validation detects duplicate rules, conflicting conclusions, invalid references; load info logs version, load time, validation status.  
6. **UI** — Sidebar: Home, Disease Search, Symptom Checker, Explanation View, System Info; clear medical terminology; global disclaimer.  
7. **Consistency & validation** — Duplicate rules, conflicting conclusions, rules referencing missing diseases; graceful failure with clear errors.  
8. **Performance** — Cached knowledge (Streamlit cache + loader cache); efficient rule evaluation; suitable for 1000+ rules.  
9. **Ethical & legal** — Read-only, non-diagnostic; disclaimer: “This system provides educational medical knowledge and does not replace professional medical judgment.”  
10. **System monitoring** — System Info shows knowledge version/load/validation; if psutil is installed, CPU and memory; otherwise page still works.

---

## Knowledge base schema (JSON)

- **metadata:** `version`, `last_updated`  
- **facts:** (optional) `symptoms`, `diagnostics`, `treatments` arrays  
- **diseases:** array of `{ id, name, description, symptoms[], diagnostics[], treatment[], references }`  
- **rules:** array of `{ id, if_symptoms[], then_disease_id, confidence }`  

Rules are IF–THEN: if all symptoms in `if_symptoms` match the user’s input, the rule fires and suggests `then_disease_id` with the given `confidence`.

---

## Disclaimer

This system provides educational medical knowledge and does not replace professional medical judgment.
