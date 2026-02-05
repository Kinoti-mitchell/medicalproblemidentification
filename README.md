# Medical Knowledge System

A **Medical Knowledge System** built with **Python** and **Streamlit**. It uses a JSON-based knowledge base (no external database) to search diseases by name or symptom and provide basic clinical decision support when multiple symptoms are entered.

---

## Application structure

- **Single entry point:** `app.py`
- **Modular layout:**
  - `data/` — JSON medical knowledge base
  - `services/` — knowledge loading, search, symptom matching
  - `utils/` — text normalization for matching
- **No external databases** — all data is in JSON files.

---

## Setup instructions

### 1. Create a virtual environment (.venv)

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

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This installs **Streamlit** (required) and **psutil** (optional, for system monitoring).

### 3. Run the app

From the **project root** (same folder as `app.py`), with `.venv` activated:

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (e.g. **http://localhost:8501**).

---

## Features

- **Sidebar navigation:** Home, Disease Search, Symptom Checker, System Info.
- **Disease Search:** Find conditions by **name** (text input) or by **symptom** (selectbox).
- **Symptom Checker:** Enter multiple symptoms (multiselect or comma-separated text); see **possible conditions** with a match score (clinical decision support).
- **Structured display:** Each disease shows description, symptoms, diagnostics, treatment, and references in expanders.
- **System Info:** If **psutil** is installed, shows CPU and memory usage; if not, the app still runs and the page shows a short message.

---

## Knowledge base (JSON)

- **Path:** `data/medical_knowledge.json`
- **Content:** List of **diseases**. Each disease has:
  - `name`, `description`
  - `symptoms` (list)
  - `diagnostics` (list)
  - `treatment` (list)
  - `references` (text)
- The file is **read-only** at runtime; no patient data is stored.

---

## Quality and safety

- **Read-only knowledge base** — no patient data; fast, local lookups.
- **Clear separation** — UI in `app.py`, logic in `services/`, helpers in `utils/`.
- **Comments** in code explain medical and technical choices where relevant.
- **No placeholder code or TODOs** — all features are implemented.
