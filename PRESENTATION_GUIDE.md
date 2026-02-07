# Medical Knowledge System — Presentation Guide

Use this for your lecturer presentation: project basics and answers to common questions.

---

## 1. Project basics (what to say)

### What it is
- A **Medical Knowledge-Based System (KBS)** that helps explore possible medical conditions from symptoms.
- It is **rule-based**: knowledge is stored as IF–THEN rules in JSON (e.g. *IF runny nose, sore throat, cough THEN common cold with 85% confidence*).
- The system does **not** diagnose; it suggests possible conditions and explains why, for **educational** use.

### Tech stack
- **Language:** Python  
- **UI:** Streamlit (web app)  
- **Storage:** JSON only (no database) — `data/knowledge_base.json` for diseases and rules, `data/symptom_history.json` for search history  
- **Libraries:** Built-in (json, os, datetime, etc.) + Streamlit; **psutil** optional (CPU/memory on System Info)  
- **Environment:** Virtual environment (.venv)

### Main features (show in the app)
1. **Home** — Overview, stats (diseases, symptoms, “searches you can run”), quick links.  
2. **Disease Search** — Find conditions by **name** or by **one symptom** (which diseases list that symptom).  
3. **Symptom Checker** — User enters **multiple symptoms** → system matches rules (forward chaining) → shows possible conditions with **confidence** and **explanation** (which rules fired, which symptoms matched).  
4. **Explanation View** — Shows last Symptom Checker result: which rules fired and why each condition was suggested.  
5. **Manage** — Three tabs: **Symptoms** (add/edit/delete symptoms; renames sync to diseases and rules), **Diseases** (add/edit/delete diseases), **Rules** (add with auto rule ID, edit, delete IF–THEN rules). All saved to JSON.  
6. **Symptom History** — Most asked symptoms (counts) and recent searches; can clear history.  
7. **System Info** — Knowledge base version, load time, validation status; CPU/memory if psutil is installed.

### Architecture (important for KBS)
- **Knowledge (data):** In JSON — **facts.symptoms** (managed symptom list), **diseases** (name, description, symptoms, diagnostics, treatment, references), and **rules** (id, if_symptoms, then_disease_id, confidence).  
- **Reasoning (logic):** In Python — **inference_engine.py** does forward chaining (match user symptoms to rules, compute confidence, build explanations).  
- **Separation:** UI (**app.py**) does not contain medical logic; it only calls the inference engine and displays results.  
- **Validation:** **knowledge_loader.py** loads JSON, checks schema, duplicate rules, conflicting conclusions, and invalid disease references.  
- **Manage:** Symptoms, diseases, and rules are edited via the Manage page (tabs); rule IDs are auto-generated when adding rules.

---

## 2. Possible questions and answers

### “What is a Knowledge-Based System?”
- A system whose behaviour is driven by **explicit knowledge** (here: rules and facts in JSON) and a **reasoning mechanism** (here: forward chaining in Python).  
- The knowledge is **separate** from the code so it can be updated (e.g. new rules) without changing the inference logic.

### “What is forward chaining?”
- **Forward chaining** means: start from what we know (user’s symptoms), find rules whose **IF** part is satisfied, and then conclude the **THEN** part (possible disease).  
- Here: we match the user’s symptoms to each rule’s `if_symptoms`; if at least one symptom matches, the rule can fire. Confidence is scaled by how many of the rule’s symptoms matched.

### “Why JSON and not a database?”
- The project requirement was **no external database**; JSON keeps the project simple and portable.  
- For a single-user or demo system, file-based JSON is enough; a database would be needed for many users or heavy concurrency.

### “How do you handle when one symptom matches many diseases?”
- We show **all** matching conditions, each with a **confidence** score.  
- The **Explanation View** (and the “Why was this suggested?” expander) shows which rules fired and which symptoms matched, so the user sees why each disease appeared.

### “How is confidence calculated?”
- Each rule has a base **confidence** (e.g. 0.85).  
- We use **partial matching**: if only some of the rule’s symptoms match, confidence is scaled: `rule_confidence × (number of matched symptoms / total symptoms in the rule)`.  
- If several rules suggest the same disease, we take the **maximum** confidence among those rules.

### “What if the user enters a symptom that isn’t in the knowledge base?”
- If no rule’s symptoms match the user input, the system returns “No rules matched these symptoms” and suggests trying different or additional symptoms.  
- New symptoms can be added via **Manage → Symptoms** (or when adding/editing diseases or rules); the knowledge base is updated in JSON.

### “How do you validate the knowledge base?”
- **knowledge_loader.py** checks: (1) **Schema** — required keys (metadata, diseases, rules) and structure; (2) **Duplicate rules** — same IF and THEN; (3) **Conflicting conclusions** — same IF but different THEN; (4) **References** — every rule’s `then_disease_id` must exist in diseases.  
- Validation runs on load; results appear on the **System Info** page (version, load time, validation status).

### “Why separate inference_engine.py and knowledge_loader.py from app.py?”
- **Separation of concerns:** UI only displays and collects input; reasoning and data loading are in dedicated modules.  
- **Testability:** The inference engine and loader can be tested without the UI.  
- **Classical KBS design:** Knowledge (JSON), reasoning (inference engine), and acquisition/validation (loader) are distinct from the interface.

### “What are the limitations?”
- **Not a diagnostic tool** — only suggests possible conditions; no replacement for a doctor.  
- **Depends on the rules** — coverage and accuracy depend on the quality and completeness of the JSON rules.  
- **No learning** — the system doesn’t learn from users; it only applies the fixed rules.  
- **Single-user / file-based** — JSON and symptom history file are not designed for many simultaneous users.

### “What could you add in the future?”
- **More diseases, rules, and symptoms** in the JSON for broader coverage.  
- **Backward chaining** (e.g. “What symptoms would suggest disease X?”).  
- **Export** — e.g. export results or explanation as PDF.  
- **User accounts and cloud storage** if the project were to scale.

### “How do you run the project?”
- Create and activate .venv, run `pip install -r requirements.txt`, then `streamlit run app.py` from the project root.  
- Open the URL shown (e.g. http://localhost:8501).  
- The app loads `data/knowledge_base.json` at startup; no database setup.

### “Where is the code / repo?”
- Code is on the machine in the project folder; also on **GitHub** (e.g. repo: medicalproblemidentification, user: Kinoti-mitchell) if you pushed it there.

---

## 3. One-minute summary (elevator pitch)

*“I built a Medical Knowledge-Based System in Python and Streamlit. The knowledge is stored as IF–THEN rules in JSON, along with a managed list of symptoms and diseases. When a user enters symptoms, the inference engine uses forward chaining to find matching rules and suggests possible conditions with a confidence score. Each suggestion can be explained: which rules fired and which symptoms matched. The app lets you search diseases by name or symptom, manage symptoms and diseases and rules from one page with tabs, and view symptom search history. The system is read-only in terms of diagnosis — it’s for education and exploration, not to replace a doctor.”*

---

Good luck with your presentation.
