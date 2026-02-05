"""
Medical Knowledge System — Streamlit application.
Single entry point for the UI. Uses JSON-based knowledge base (no external database).
"""

import streamlit as st

from services.knowledge_service import (
    load_knowledge_base,
    save_knowledge_base,
    search_diseases_by_name,
    search_diseases_by_symptom,
    get_possible_conditions_for_symptoms,
    get_all_symptoms,
    get_disease_by_id,
    add_disease,
    update_disease,
    delete_disease,
)


# -----------------------------------------------------------------------------
# Page config and session state
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Medical Knowledge System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "page" not in st.session_state:
    st.session_state.page = "Home"

# -----------------------------------------------------------------------------
# Custom styling for a more engaging, polished look
# -----------------------------------------------------------------------------

st.markdown("""
<style>
    /* Softer, medical-friendly palette */
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: #e2e8f0; }

    /* Hero / big title */
    .hero-title { font-size: 2.25rem; font-weight: 800; color: #f8fafc; margin-bottom: 0.25rem; }
    .hero-tagline { font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.5rem; }

    /* Quick-action cards on home */
    .quick-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
    }
    .quick-card:hover { border-color: #38bdf8; box-shadow: 0 8px 24px rgba(56, 189, 248, 0.15); }
    .quick-card .icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .quick-card .label { font-size: 1.1rem; font-weight: 600; color: #f1f5f9; }
    .quick-card .hint { font-size: 0.85rem; color: #94a3b8; }

    /* Disease result cards */
    .disease-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
    }
    .disease-card .disease-name { font-size: 1.35rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.5rem; }
    .disease-card .disease-desc { color: #cbd5e1; font-size: 0.95rem; line-height: 1.5; margin-bottom: 0.75rem; }
    .match-bar-wrap { background: #334155; border-radius: 8px; height: 8px; margin: 0.5rem 0 0.75rem 0; overflow: hidden; }
    .match-bar { height: 100%; border-radius: 8px; background: linear-gradient(90deg, #22c55e, #38bdf8); transition: width 0.5s ease; }
    .match-label { font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem; }

    /* Stat tiles on home */
    .stat-tile {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .stat-tile .value { font-size: 1.75rem; font-weight: 800; color: #38bdf8; }
    .stat-tile .label { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Tip box */
    .tip-box { background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%); border: 1px solid #475569; border-radius: 12px; padding: 1rem 1.25rem; margin: 1rem 0; }
    .tip-box .tip-title { font-size: 0.85rem; font-weight: 600; color: #38bdf8; margin-bottom: 0.35rem; }
    .tip-box .tip-text { color: #cbd5e1; font-size: 0.9rem; }

    /* Sidebar nav buttons feel more like tabs */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


def render_disease_card(disease: dict, show_score: bool = False):
    """Display one disease in a styled card with optional match score bar."""
    name = disease.get("name") or "Unknown"
    desc = disease.get("description") or "No description available."
    symptoms = disease.get("symptoms") or []
    diagnostics = disease.get("diagnostics") or []
    treatment = disease.get("treatment") or []
    references = disease.get("references") or ""

    score = disease.get("score") if show_score else None
    score_pct = int((score or 0) * 100)

    st.subheader(name)
    st.write(desc[:400] + ("…" if len(desc) > 400 else ""))

    if score is not None:
        st.progress(score, text=f"Match strength: {score_pct}% — {'High' if score >= 0.6 else 'Medium' if score >= 0.3 else 'Low'} relevance")

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📋 Symptoms"):
            for s in symptoms:
                st.write(f"• {s}")
    with col2:
        with st.expander("🔬 Diagnostics"):
            for d in diagnostics:
                st.write(f"• {d}")
    with st.expander("💊 Treatment"):
        for t in treatment:
            st.write(f"• {t}")
    if references:
        st.caption(f"📎 {references}")
    st.markdown("---")


# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------

def page_home():
    st.markdown('<p class="hero-title">🩺 Medical Knowledge System</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-tagline">Search conditions by name or symptom, explore possible diagnoses, and manage the knowledge base — all in one place.</p>', unsafe_allow_html=True)

    try:
        kb = load_knowledge_base()
        diseases = kb.get("diseases", [])
        n_diseases = len(diseases)
        n_symptoms = len(get_all_symptoms(kb))
    except Exception as e:
        n_diseases = 0
        n_symptoms = 0
        st.error(f"Could not load knowledge base: {e}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-tile"><div class="value">{n_diseases}</div><div class="label">Diseases in database</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-tile"><div class="value">{n_symptoms}</div><div class="label">Unique symptoms</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="stat-tile"><div class="value">∞</div><div class="label">Searches you can run</div></div>', unsafe_allow_html=True)

    st.markdown("#### What do you want to do?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 **Search by disease name**\n\nFind a condition by typing its name.", use_container_width=True, key="home_search_name"):
            st.session_state.page = "Disease Search"
            st.session_state.search_mode = "Name"
            st.rerun()
        if st.button("🩸 **Search by symptom**\n\nPick a symptom and see which diseases list it.", use_container_width=True, key="home_search_symptom"):
            st.session_state.page = "Disease Search"
            st.session_state.search_mode = "Symptom"
            st.rerun()
    with col2:
        if st.button("🧩 **Symptom checker**\n\nEnter several symptoms and get possible conditions with match scores.", use_container_width=True, key="home_symptom"):
            st.session_state.page = "Symptom Checker"
            st.rerun()
        if st.button("✏️ **Manage diseases**\n\nAdd, edit, or remove entries in the knowledge base.", use_container_width=True, key="home_manage"):
            st.session_state.page = "Manage Diseases"
            st.rerun()

    st.markdown("---")
    import random
    tips = [
        "Tip: In Symptom Checker, the more symptoms you enter, the more focused the list of possible conditions.",
        "Did you know? You can search by partial disease names — e.g. \"cold\" will find Common Cold.",
        "The match score combines how many of your symptoms fit the condition and how many of that condition’s symptoms you listed.",
    ]
    tip = random.choice(tips)
    st.markdown(f'<div class="tip-box"><div class="tip-title">💡 Quick tip</div><div class="tip-text">{tip}</div></div>', unsafe_allow_html=True)


def page_disease_search():
    st.markdown("### 🔍 Disease Search")
    st.caption("Find conditions by name or by a single symptom.")

    try:
        kb = load_knowledge_base()
    except Exception as e:
        st.error(f"Could not load knowledge base: {e}")
        return

    default_idx = 1 if st.session_state.get("search_mode") == "Symptom" else 0
    search_mode = st.radio(
        "Search by",
        ["Name", "Symptom"],
        horizontal=True,
        index=default_idx,
        label_visibility="collapsed",
        key="search_radio",
    )

    if search_mode == "Name":
        query = st.text_input("Disease name", placeholder="e.g. Asthma, Migraine, Cold", key="name_search")
        if query:
            results = search_diseases_by_name(query, kb)
            if not results:
                st.info("No diseases found with that name. Try a shorter or different term.")
            else:
                st.success(f"Found **{len(results)}** disease(s).")
                for d in results:
                    render_disease_card(d)
    else:
        all_symptoms = get_all_symptoms(kb)
        if not all_symptoms:
            st.warning("No symptoms in the knowledge base yet. Add diseases in **Manage Diseases**.")
            return
        selected = st.selectbox("Select a symptom", options=[""] + all_symptoms, key="symptom_search_select", placeholder="Choose one…")
        if selected:
            results = search_diseases_by_symptom(selected, kb)
            if not results:
                st.info("No diseases list this symptom.")
            else:
                st.success(f"**{selected}** may be associated with **{len(results)}** condition(s).")
                for d in results:
                    render_disease_card(d)


def page_symptom_checker():
    st.markdown("### 🧩 Symptom Checker")
    st.markdown("Enter **multiple symptoms** to see possible conditions, sorted by how well they match.")

    try:
        kb = load_knowledge_base()
    except Exception as e:
        st.error(f"Could not load knowledge base: {e}")
        return

    all_symptoms = get_all_symptoms(kb)
    input_method = st.radio(
        "How to enter symptoms",
        ["Select from list", "Type (comma-separated)"],
        horizontal=True,
        key="symptom_input_method",
    )

    symptoms = []
    if input_method == "Select from list":
        symptoms = st.multiselect("Symptoms", options=all_symptoms, placeholder="Choose one or more…", key="symptom_multiselect")
    else:
        raw = st.text_input("Symptoms", placeholder="e.g. headache, nausea, sensitivity to light", key="symptom_text")
        if raw:
            symptoms = [s.strip() for s in raw.split(",") if s.strip()]

    if st.button("🔎 Check possible conditions", type="primary", key="symptom_check_btn"):
        if not symptoms:
            st.warning("Enter or select at least one symptom.")
        else:
            results = get_possible_conditions_for_symptoms(symptoms, kb)
            if not results:
                st.info("No conditions closely match these symptoms. Try different or fewer terms.")
            else:
                st.success(f"**{len(results)}** possible condition(s) — sorted by match strength below.")
                for d in results:
                    render_disease_card(d, show_score=True)


def page_system_info():
    st.markdown("### ⚙️ System Info")
    st.caption("Optional system monitoring when **psutil** is installed.")
    try:
        import psutil
        col1, col2 = st.columns(2)
        with col1:
            cpu = psutil.cpu_percent(interval=1)
            st.metric("CPU usage", f"{cpu:.1f}%")
        with col2:
            mem = psutil.virtual_memory()
            st.metric("Memory usage", f"{mem.percent:.1f}%")
        st.caption("Values are current at time of page load.")
    except ImportError:
        st.info("**psutil** is not installed. To enable CPU and memory display, run: `pip install psutil`")


def _parse_list_text(text: str) -> list[str]:
    """Parse newline- or comma-separated text into list of non-empty stripped strings."""
    if not text or not text.strip():
        return []
    items = []
    for line in text.replace(",", "\n").split("\n"):
        s = line.strip()
        if s:
            items.append(s)
    return items


def page_manage_diseases():
    st.markdown("### ✏️ Manage Diseases")
    st.caption("Add new conditions or edit existing ones. Changes are saved to the knowledge base.")

    try:
        kb = load_knowledge_base()
    except Exception as e:
        st.error(f"Could not load knowledge base: {e}")
        return

    diseases = kb.get("diseases", [])
    disease_options = ["— Add new disease —"] + [f"{d.get('name', '')} (id: {d.get('id', '')})" for d in diseases]
    choice = st.selectbox("Select disease to edit or add new", options=disease_options, key="manage_choice")

    is_new = choice.startswith("— Add new disease —")
    edit_id = None if is_new else diseases[disease_options.index(choice) - 1].get("id")
    current = get_disease_by_id(edit_id, kb) if edit_id else None

    with st.form("disease_form", clear_on_submit=is_new):
        name = st.text_input("Name", value=(current.get("name", "") if current else ""), placeholder="e.g. Common Cold")
        description = st.text_area("Description", value=(current.get("description", "") if current else ""), placeholder="Brief clinical description.", height=100)
        symptoms_text = st.text_area("Symptoms (one per line)", value="\n".join(current.get("symptoms", [])) if current else "", placeholder="runny nose\nsore throat\ncough", height=120)
        diagnostics_text = st.text_area("Diagnostics (one per line)", value="\n".join(current.get("diagnostics", [])) if current else "", placeholder="Clinical examination\nLab test", height=100)
        treatment_text = st.text_area("Treatment (one per line)", value="\n".join(current.get("treatment", [])) if current else "", placeholder="Rest\nFluids\nMedication", height=100)
        references = st.text_input("References", value=(current.get("references", "") if current else ""), placeholder="Optional source or citation.")

        col1, col2, col3 = st.columns(3)
        with col1:
            submitted = st.form_submit_button("Save")
        with col2:
            delete_submitted = st.form_submit_button("Delete") if not is_new else None
        with col3:
            pass

    if submitted:
        if not name or not name.strip():
            st.warning("Name is required.")
        else:
            symptoms_list = _parse_list_text(symptoms_text)
            diagnostics_list = _parse_list_text(diagnostics_text)
            treatment_list = _parse_list_text(treatment_text)
            try:
                if is_new:
                    kb = add_disease(kb, name.strip(), description, symptoms_list, diagnostics_list, treatment_list, references)
                    st.success(f"Added **{name.strip()}**.")
                else:
                    kb = update_disease(kb, edit_id, name.strip(), description, symptoms_list, diagnostics_list, treatment_list, references)
                    st.success(f"Updated **{name.strip()}**.")
                save_knowledge_base(kb)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save: {e}")

    if not is_new and delete_submitted:
        try:
            kb = delete_disease(kb, edit_id)
            save_knowledge_base(kb)
            st.success("Disease removed.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete: {e}")


# -----------------------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🩺 Medical Knowledge System")
    st.markdown("---")
    st.markdown("**Navigation**")
    cur = st.session_state.page
    if st.button(("🏠 Home" + (" ✓" if cur == "Home" else "")), use_container_width=True, key="nav_home", type="primary" if cur == "Home" else "secondary"):
        st.session_state.page = "Home"
        st.rerun()
    if st.button(("🔍 Disease Search" + (" ✓" if cur == "Disease Search" else "")), use_container_width=True, key="nav_search", type="primary" if cur == "Disease Search" else "secondary"):
        st.session_state.page = "Disease Search"
        st.rerun()
    if st.button(("🧩 Symptom Checker" + (" ✓" if cur == "Symptom Checker" else "")), use_container_width=True, key="nav_symptom", type="primary" if cur == "Symptom Checker" else "secondary"):
        st.session_state.page = "Symptom Checker"
        st.rerun()
    if st.button(("✏️ Manage Diseases" + (" ✓" if cur == "Manage Diseases" else "")), use_container_width=True, key="nav_manage", type="primary" if cur == "Manage Diseases" else "secondary"):
        st.session_state.page = "Manage Diseases"
        st.rerun()
    if st.button(("⚙️ System Info" + (" ✓" if cur == "System Info" else "")), use_container_width=True, key="nav_sysinfo", type="primary" if cur == "System Info" else "secondary"):
        st.session_state.page = "System Info"
        st.rerun()
    st.markdown("---")

# -----------------------------------------------------------------------------
# Main: render selected page
# -----------------------------------------------------------------------------

if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "Disease Search":
    page_disease_search()
elif st.session_state.page == "Symptom Checker":
    page_symptom_checker()
elif st.session_state.page == "Manage Diseases":
    page_manage_diseases()
elif st.session_state.page == "System Info":
    page_system_info()
else:
    page_home()
