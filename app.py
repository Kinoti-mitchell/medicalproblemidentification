"""
Medical Knowledge-Based System (KBS) — Streamlit UI.
Satisfies classical KBS: knowledge in JSON, inference in engine, explanation facility, read-only.
"""

import json
import os
from datetime import datetime

import streamlit as st

import knowledge_loader as loader
import inference_engine as engine

# Max recent searches to keep in history
MAX_RECENT_SEARCHES = 100

# -----------------------------------------------------------------------------
# Page config and session state
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Medical Knowledge-Based System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "last_inference_result" not in st.session_state:
    st.session_state.last_inference_result = []
if "last_user_symptoms" not in st.session_state:
    st.session_state.last_user_symptoms = []


# -----------------------------------------------------------------------------
# Styling (engaging medical UI: dark theme, stat tiles, tip box)
# -----------------------------------------------------------------------------

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: #e2e8f0; }
    .hero-title { font-size: 2.25rem; font-weight: 800; color: #f8fafc; margin-bottom: 0.25rem; }
    .hero-tagline { font-size: 1.1rem; color: #94a3b8; margin-bottom: 1rem; }
    .stat-tile { background: linear-gradient(145deg, #1e293b 0%, #334155 100%); border: 1px solid #475569;
        border-radius: 12px; padding: 1rem 1.25rem; text-align: center; margin: 0.5rem 0; }
    .stat-tile .value { font-size: 1.75rem; font-weight: 800; color: #38bdf8; }
    .stat-tile .label { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
    .tip-box { background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%); border: 1px solid #475569;
        border-radius: 12px; padding: 1rem 1.25rem; margin: 1rem 0; }
    .tip-box .tip-title { font-size: 0.85rem; font-weight: 600; color: #38bdf8; margin-bottom: 0.35rem; }
    .tip-box .tip-text { color: #cbd5e1; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Load knowledge once; fail gracefully with message
# -----------------------------------------------------------------------------

@st.cache_data(ttl=300)
def _load_kb_cached():
    """Cache loaded knowledge for performance (1000+ rules). Only successful loads are cached."""
    return loader.load_knowledge(use_cache=True)


def get_kb():
    try:
        return _load_kb_cached()
    except Exception as e:
        st.error(f"Could not load knowledge base: {e}. Check data/knowledge_base.json.")
        return None


def _parse_list_text(text: str) -> list[str]:
    """Parse newline- or comma-separated text into list of non-empty strings."""
    if not text or not text.strip():
        return []
    return [s.strip() for s in text.replace(",", "\n").split("\n") if s.strip()]


def _symptom_history_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "data", "symptom_history.json")


def _load_symptom_history() -> dict:
    path = _symptom_history_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"symptom_counts": {}, "recent_searches": []}


def _save_symptom_history(data: dict) -> None:
    path = _symptom_history_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_symptom_search(symptoms: list[str]) -> None:
    """Record a symptom check: update counts and append to recent searches."""
    if not symptoms:
        return
    data = _load_symptom_history()
    counts = data.get("symptom_counts", {})
    for s in symptoms:
        key = s.strip().lower()
        if key:
            counts[key] = counts.get(key, 0) + 1
    data["symptom_counts"] = counts
    recent = data.get("recent_searches", [])
    recent.insert(0, {"symptoms": list(symptoms), "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")})
    data["recent_searches"] = recent[:MAX_RECENT_SEARCHES]
    _save_symptom_history(data)


def clear_symptom_history() -> None:
    """Reset symptom counts and recent searches."""
    _save_symptom_history({"symptom_counts": {}, "recent_searches": []})


# -----------------------------------------------------------------------------
# Helpers: disease card (no medical logic, display only)
# -----------------------------------------------------------------------------

def render_disease_card(disease: dict, confidence: float | None = None):
    name = disease.get("name") or "Unknown"
    desc = disease.get("description") or ""
    symptoms = disease.get("symptoms") or []
    diagnostics = disease.get("diagnostics") or []
    treatment = disease.get("treatment") or []
    references = disease.get("references") or ""
    st.subheader(name)
    if confidence is not None:
        st.progress(confidence, text=f"Confidence: {confidence:.0%}")
    st.write(desc)
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
    kb = get_kb()
    if kb is None:
        return
    n_diseases = len(kb.get("diseases", []))
    n_symptoms = len(engine.get_all_symptoms_from_kb(kb)) if kb else 0
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-tile"><div class="value">{n_diseases}</div><div class="label">Diseases in database</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-tile"><div class="value">{n_symptoms}</div><div class="label">Unique symptoms</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="stat-tile"><div class="value">∞</div><div class="label">Searches you can run</div></div>', unsafe_allow_html=True)
    st.markdown("**What do you want to do?**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 **Disease Search**\n\nFind by name or by a single symptom.", use_container_width=True, key="home_search"):
            st.session_state.page = "Disease Search"
            st.rerun()
        if st.button("🧩 **Symptom Checker**\n\nEnter symptoms; get rule-based suggestions with confidence.", use_container_width=True, key="home_symptom"):
            st.session_state.page = "Symptom Checker"
            st.rerun()
    with col2:
        if st.button("📋 **Explanation View**\n\nSee which rules fired and why a condition was suggested.", use_container_width=True, key="home_explanation"):
            st.session_state.page = "Explanation View"
            st.rerun()
        if st.button("⚙️ **System Info**\n\nKnowledge version, load time, CPU/memory.", use_container_width=True, key="home_sysinfo"):
            st.session_state.page = "System Info"
            st.rerun()
    if st.button("✏️ **Manage**\n\nManage diseases and rules in the knowledge base.", use_container_width=True, key="home_manage"):
            st.session_state.page = "Manage Diseases"
            st.rerun()
    if st.button("📊 **Symptom History**\n\nView most asked symptoms and recent searches; clear history.", use_container_width=True, key="home_history"):
            st.session_state.page = "Symptom History"
            st.rerun()
    st.markdown("---")
    import random
    tips = [
        "Rules use partial matching: the more of a rule’s symptoms you have, the higher the confidence.",
        "Explanation View shows the last Symptom Checker result — run a check first to see why each condition was suggested.",
        "The knowledge base is read-only; rules and diseases are defined in data/knowledge_base.json.",
    ]
    tip = random.choice(tips)
    st.markdown(f'<div class="tip-box"><div class="tip-title">💡 Quick tip</div><div class="tip-text">{tip}</div></div>', unsafe_allow_html=True)


def page_disease_search():
    st.markdown("### 🔍 Disease Search")
    st.caption("Find conditions by name or by a single symptom.")
    kb = get_kb()
    if kb is None:
        return
    search_mode = st.radio("Search by", ["Name", "Symptom"], horizontal=True, label_visibility="collapsed")
    if search_mode == "Name":
        query = st.text_input("Disease name", placeholder="e.g. Asthma, Migraine", key="name_search")
        if query:
            q = query.strip().lower()
            results = [d for d in kb.get("diseases", []) if d.get("name") and q in d.get("name", "").lower()]
            if not results:
                st.info("No diseases found with that name.")
            else:
                for d in results:
                    render_disease_card(d)
    else:
        all_symptoms = engine.get_all_symptoms_from_kb(kb)
        if not all_symptoms:
            st.warning("No symptoms in knowledge base.")
            return
        selected = st.selectbox("Select a symptom", options=[""] + all_symptoms, key="symptom_search")
        if selected:
            results = [d for d in kb.get("diseases", []) if selected in (d.get("symptoms") or [])]
            if not results:
                st.info("No diseases list this symptom.")
            else:
                st.success(f"**{selected}** may be associated with {len(results)} condition(s).")
                for d in results:
                    render_disease_card(d)


def page_symptom_checker():
    st.markdown("### 🧩 Symptom Checker")
    st.caption("Enter symptoms; the inference engine matches rules and returns possible conditions with confidence.")
    kb = get_kb()
    if kb is None:
        return
    all_symptoms = engine.get_all_symptoms_from_kb(kb)
    input_method = st.radio(
        "How to enter symptoms",
        ["Select from list", "Type (comma-separated)"],
        horizontal=True,
        key="symptom_input_method",
    )
    check_clicked = st.button("🔎 Check possible conditions", type="primary", key="symptom_check_btn")
    st.markdown("**Enter or select symptoms:**")
    symptoms = []
    if input_method == "Select from list":
        symptoms = st.multiselect("Symptoms", options=all_symptoms, placeholder="Choose one or more…", key="symptom_multiselect", label_visibility="collapsed")
    else:
        raw = st.text_input("Symptoms", placeholder="e.g. headache, nausea, sensitivity to light", key="symptom_text", label_visibility="collapsed")
        if raw:
            symptoms = [s.strip() for s in raw.split(",") if s.strip()]
    if check_clicked:
        if not symptoms:
            st.warning("Enter or select at least one symptom.")
        else:
            record_symptom_search(list(symptoms))
            results = engine.forward_chain(symptoms, kb)
            st.session_state.last_inference_result = results
            st.session_state.last_user_symptoms = list(symptoms)
            if not results:
                st.info("No rules matched these symptoms. Try different or additional symptoms.")
            else:
                st.success(f"**{len(results)}** possible condition(s) from rule matching.")
                for r in results:
                    disease = engine.get_disease_by_id(r["disease_id"], kb)
                    if disease:
                        render_disease_card(disease, confidence=r["confidence"])
                        with st.expander("Why was this suggested?"):
                            st.write(r.get("explanation", ""))


def page_explanation_view():
    st.markdown("### 📋 Explanation View")
    st.caption("See which rules fired and which symptoms matched for each recommendation.")
    kb = get_kb()
    if kb is None:
        return
    results = st.session_state.get("last_inference_result", [])
    user_symptoms = st.session_state.get("last_user_symptoms", [])
    if not results:
        st.info("Run **Symptom Checker** first to see explanations for recommendations.")
        return
    st.markdown(f"**Your symptoms:** {', '.join(user_symptoms)}")
    st.markdown("---")
    for r in results:
        st.markdown(f"#### {r.get('disease_name', '')} (confidence {r.get('confidence', 0):.0%})")
        st.markdown("**Matched symptoms:** " + ", ".join(r.get("matched_symptoms", [])))
        st.markdown("**Rules that fired:**")
        for fr in r.get("fired_rules", []):
            st.write(f"- Rule **{fr.get('rule_id', '')}**: matched {fr.get('matched_symptoms', [])} → confidence {fr.get('rule_confidence', 0):.0%}")
        st.markdown("**Explanation:** " + (r.get("explanation") or ""))
        st.markdown("---")


def page_manage_diseases():
    st.markdown("### ✏️ Manage")
    st.caption("Manage symptoms, diseases, and rules in the knowledge base. Changes are saved to data/knowledge_base.json.")
    kb = get_kb()
    if kb is None:
        return
    diseases = kb.get("diseases", [])
    rules = kb.get("rules", [])
    disease_options = [(d.get("id", ""), d.get("name", "") or "Unnamed") for d in diseases]

    tab_symptoms, tab_diseases, tab_rules = st.tabs(["🩺 Symptoms", "📋 Diseases", "📐 Rules"])

    with tab_symptoms:
        managed_symptoms = loader.get_symptoms_list(kb)
        with st.expander("➕ Add new symptom(s)", expanded=False):
            with st.form("add_symptom_form", clear_on_submit=True):
                add_symptom_text = st.text_area("Symptom name(s), one per line", key="add_symptom_text", placeholder="e.g. runny nose\nsore throat", height=80)
                add_symptom_submitted = st.form_submit_button("Add")
            if add_symptom_submitted:
                to_add = _parse_list_text(add_symptom_text)
                if not to_add:
                    st.warning("Enter at least one symptom.")
                else:
                    try:
                        for name in to_add:
                            kb = loader.add_symptom(kb, name)
                        loader.save_knowledge_base(kb)
                        st.cache_data.clear()
                        st.success(f"Added {len(to_add)} symptom(s).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")

        with st.expander("✏️ Edit or delete symptom", expanded=False):
            if not managed_symptoms:
                st.info("No managed symptoms yet. Add symptoms above (or they will appear here once added via diseases/rules and facts).")
            else:
                edit_sym_choice = st.selectbox("Select symptom to edit or delete", options=managed_symptoms, key="edit_symptom_choice", placeholder="Choose one…")
                if edit_sym_choice:
                    with st.form("edit_symptom_form"):
                        edit_symptom_new = st.text_input("New name (leave unchanged to only delete)", value=edit_sym_choice, key="edit_symptom_new")
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_symptom_save = st.form_submit_button("Save (rename)")
                        with col2:
                            edit_symptom_delete = st.form_submit_button("Delete symptom")
                    if edit_symptom_save and edit_symptom_new and edit_symptom_new.strip() != edit_sym_choice:
                        try:
                            kb = loader.update_symptom(kb, edit_sym_choice, edit_symptom_new.strip())
                            loader.save_knowledge_base(kb)
                            st.cache_data.clear()
                            st.success(f"Renamed to **{edit_symptom_new.strip()}**.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to rename: {e}")
                    if edit_symptom_delete:
                        try:
                            kb = loader.delete_symptom(kb, edit_sym_choice)
                            loader.save_knowledge_base(kb)
                            st.cache_data.clear()
                            st.success("Symptom removed from knowledge base.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")

    with tab_diseases:
        with st.expander("➕ Add new disease", expanded=False):
            with st.form("add_disease_form", clear_on_submit=True):
                add_name = st.text_input("Name", key="add_name", placeholder="e.g. Common Cold")
                add_description = st.text_area("Description", key="add_desc", placeholder="Brief clinical description.", height=100)
                add_symptoms = st.text_area("Symptoms (one per line)", key="add_symptoms", placeholder="runny nose\nsore throat\ncough", height=120)
                add_diagnostics = st.text_area("Diagnostics (one per line)", key="add_diagnostics", placeholder="Clinical examination\nLab test", height=100)
                add_treatment = st.text_area("Treatment (one per line)", key="add_treatment", placeholder="Rest\nFluids\nMedication", height=100)
                add_references = st.text_input("References", key="add_refs", placeholder="Optional source or citation.")
                add_submitted = st.form_submit_button("Save new disease")
            if add_submitted and add_name and add_name.strip():
                try:
                    kb = loader.add_disease(kb, add_name.strip(), add_description or "", _parse_list_text(add_symptoms), _parse_list_text(add_diagnostics), _parse_list_text(add_treatment), add_references or "")
                    loader.save_knowledge_base(kb)
                    st.cache_data.clear()
                    st.success(f"Added **{add_name.strip()}**.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")
            elif add_submitted:
                st.warning("Name is required.")

        with st.expander("✏️ Edit existing disease", expanded=False):
            if not diseases:
                st.info("No diseases yet. Use **Add new disease** above.")
            else:
                edit_options = [d.get("name", "") or "Unnamed" for d in diseases]
                edit_choice = st.selectbox("Select disease to edit", options=edit_options, key="edit_choice", placeholder="Choose one…")
                selected_idx = edit_options.index(edit_choice)
                edit_id = diseases[selected_idx].get("id")
                current = loader.get_disease_by_id(edit_id, kb)
                if current:
                    form_key = f"edit_form_{edit_id}"
                    with st.form(form_key):
                        edit_name = st.text_input("Name", value=current.get("name", ""), key=f"edit_name_{edit_id}")
                        edit_description = st.text_area("Description", value=current.get("description", ""), key=f"edit_desc_{edit_id}", height=100)
                        edit_symptoms = st.text_area("Symptoms (one per line)", value="\n".join(current.get("symptoms", [])), key=f"edit_symptoms_{edit_id}", height=120)
                        edit_diagnostics = st.text_area("Diagnostics (one per line)", value="\n".join(current.get("diagnostics", [])), key=f"edit_diagnostics_{edit_id}", height=100)
                        edit_treatment = st.text_area("Treatment (one per line)", value="\n".join(current.get("treatment", [])), key=f"edit_treatment_{edit_id}", height=100)
                        edit_references = st.text_input("References", value=current.get("references", ""), key=f"edit_refs_{edit_id}")
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_submitted = st.form_submit_button("Save changes")
                        with col2:
                            delete_submitted = st.form_submit_button("Delete disease")
                    if edit_submitted and edit_name and edit_name.strip():
                        try:
                            kb = loader.update_disease(kb, edit_id, edit_name.strip(), edit_description or "", _parse_list_text(edit_symptoms), _parse_list_text(edit_diagnostics), _parse_list_text(edit_treatment), edit_references or "")
                            loader.save_knowledge_base(kb)
                            st.cache_data.clear()
                            st.success(f"Updated **{edit_name.strip()}**.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save: {e}")
                    if delete_submitted:
                        try:
                            kb = loader.delete_disease(kb, edit_id)
                            loader.save_knowledge_base(kb)
                            st.cache_data.clear()
                            st.success("Disease removed.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")

    with tab_rules:
        all_symptom_options = engine.get_all_symptoms_from_kb(kb)

        def _next_rule_id(kb_dict):
            existing = {r.get("id", "") for r in kb_dict.get("rules", []) if isinstance(r, dict)}
            i = 1
            while f"R{i}" in existing:
                i += 1
            return f"R{i}"

        add_rule_submitted = False
        next_rid = _next_rule_id(kb)
        with st.expander("➕ Add new rule", expanded=False):
            if not disease_options:
                st.info("Add at least one disease above before adding rules.")
            else:
                with st.form("add_rule_form", clear_on_submit=True):
                    st.caption("Rule ID (auto)")
                    st.text(next_rid)
                    add_if_symptoms = st.text_area("IF symptoms (one per line)", key="add_rule_if", placeholder="runny nose\nsore throat\ncough", height=100)
                    add_then_id = st.selectbox("THEN disease", options=[did for did, _ in disease_options], format_func=lambda x: next((n for i, n in disease_options if i == x), x), key="add_rule_then")
                    add_confidence = st.number_input("Confidence (0–1)", min_value=0.0, max_value=1.0, value=0.8, step=0.05, key="add_rule_conf")
                    add_rule_submitted = st.form_submit_button("Save new rule")
            if add_rule_submitted and disease_options:
                if not add_then_id:
                    st.warning("Select a disease (THEN).")
                else:
                    try:
                        kb = loader.add_rule(kb, next_rid, _parse_list_text(add_if_symptoms), add_then_id, add_confidence)
                        loader.save_knowledge_base(kb)
                        st.cache_data.clear()
                        st.success("Rule added.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")

        with st.expander("✏️ Edit existing rule", expanded=False):
            if not rules:
                st.info("No rules yet. Add a rule above.")
            else:
                rule_options = [f"{r.get('id', '')}: {', '.join((r.get('if_symptoms') or [])[:3])}{'…' if len(r.get('if_symptoms') or []) > 3 else ''} → {next((n for i, n in disease_options if i == r.get('then_disease_id')), r.get('then_disease_id', ''))}" for r in rules]
                rule_choice = st.selectbox("Select rule to edit", options=rule_options, key="rule_edit_choice")
                rule_idx = rule_options.index(rule_choice)
                rule_id = rules[rule_idx].get("id")
                current_rule = loader.get_rule_by_id(rule_id, kb)
                if current_rule:
                    form_key = f"edit_rule_form_{rule_id}"
                    with st.form(form_key):
                        st.text_input("Rule ID (read-only)", value=rule_id, key=f"edit_rule_id_{rule_id}", disabled=True)
                        edit_rule_if = st.text_area("IF symptoms (one per line)", value="\n".join(current_rule.get("if_symptoms", [])), key=f"edit_rule_if_{rule_id}", height=100)
                        rule_then_ids = [did for did, _ in disease_options]
                        rule_then_idx = rule_then_ids.index(current_rule.get("then_disease_id")) if current_rule.get("then_disease_id") in rule_then_ids else 0
                        edit_rule_then = st.selectbox("THEN disease", options=rule_then_ids, index=rule_then_idx, format_func=lambda x: next((n for i, n in disease_options if i == x), x), key=f"edit_rule_then_{rule_id}")
                        edit_rule_conf = st.number_input("Confidence (0–1)", min_value=0.0, max_value=1.0, value=float(current_rule.get("confidence", 0.8)), step=0.05, key=f"edit_rule_conf_{rule_id}")
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_rule_submitted = st.form_submit_button("Save changes")
                        with col2:
                            delete_rule_submitted = st.form_submit_button("Delete rule")
                    if edit_rule_submitted:
                        try:
                            kb = loader.update_rule(kb, rule_id, _parse_list_text(edit_rule_if), edit_rule_then, edit_rule_conf)
                            loader.save_knowledge_base(kb)
                            st.cache_data.clear()
                            st.success("Rule updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save: {e}")
                    if delete_rule_submitted:
                        try:
                            kb = loader.delete_rule(kb, rule_id)
                            loader.save_knowledge_base(kb)
                            st.cache_data.clear()
                            st.success("Rule removed.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")


def page_symptom_history():
    st.markdown("### 📊 Symptom History")
    st.caption("Most asked symptoms and recent symptom checks. Manage or clear history below.")
    data = _load_symptom_history()
    counts = data.get("symptom_counts", {})
    recent = data.get("recent_searches", [])

    st.markdown("**Most asked symptoms**")
    if not counts:
        st.info("No symptom checks recorded yet. Use **Symptom Checker** to run a search.")
    else:
        sorted_symptoms = sorted(counts.items(), key=lambda x: -x[1])
        for i, (symptom, count) in enumerate(sorted_symptoms, 1):
            st.write(f"{i}. **{symptom}** — searched {count} time(s)")
    st.markdown("---")
    st.markdown("**Recent searches**")
    if not recent:
        st.caption("No recent searches.")
    else:
        for i, entry in enumerate(recent[:20]):
            syms = entry.get("symptoms", [])
            ts = entry.get("timestamp", "")
            st.caption(f"{ts[:19] if ts else '—'} — {', '.join(syms)}")
    st.markdown("---")
    if st.button("Clear history", type="secondary", key="clear_symptom_history"):
        clear_symptom_history()
        st.success("History cleared.")
        st.rerun()


def page_system_info():
    st.markdown("### ⚙️ System Info")
    info = loader.get_load_info()
    st.markdown("**Knowledge base**")
    st.write(f"- Version: {info['knowledge_version']}")
    st.write(f"- Last updated (KB): {info['last_updated']}")
    st.write(f"- Load time: {info['load_time']}")
    st.write(f"- Validation status: {info['validation_status']}")
    if info.get("validation_errors"):
        st.warning("Validation issues: " + "; ".join(info["validation_errors"][:5]))
    st.markdown("**System monitoring**")
    try:
        import psutil
        col1, col2 = st.columns(2)
        with col1:
            st.metric("CPU usage", f"{psutil.cpu_percent(interval=0.5):.1f}%")
        with col2:
            st.metric("Memory usage", f"{psutil.virtual_memory().percent:.1f}%")
    except ImportError:
        st.info("Install **psutil** for CPU and memory display. The app runs without it.")


# -----------------------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🩺 Medical KBS")
    st.markdown("---")
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
    if st.button(("📋 Explanation View" + (" ✓" if cur == "Explanation View" else "")), use_container_width=True, key="nav_explanation", type="primary" if cur == "Explanation View" else "secondary"):
        st.session_state.page = "Explanation View"
        st.rerun()
    if st.button(("✏️ Manage" + (" ✓" if cur == "Manage Diseases" else "")), use_container_width=True, key="nav_manage", type="primary" if cur == "Manage Diseases" else "secondary"):
        st.session_state.page = "Manage Diseases"
        st.rerun()
    if st.button(("📊 Symptom History" + (" ✓" if cur == "Symptom History" else "")), use_container_width=True, key="nav_history", type="primary" if cur == "Symptom History" else "secondary"):
        st.session_state.page = "Symptom History"
        st.rerun()
    if st.button(("⚙️ System Info" + (" ✓" if cur == "System Info" else "")), use_container_width=True, key="nav_sysinfo", type="primary" if cur == "System Info" else "secondary"):
        st.session_state.page = "System Info"
        st.rerun()
    st.markdown("---")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if st.session_state.page == "Home":
    page_home()
elif st.session_state.page == "Disease Search":
    page_disease_search()
elif st.session_state.page == "Symptom Checker":
    page_symptom_checker()
elif st.session_state.page == "Explanation View":
    page_explanation_view()
elif st.session_state.page == "Manage Diseases":
    page_manage_diseases()
elif st.session_state.page == "Symptom History":
    page_symptom_history()
elif st.session_state.page == "System Info":
    page_system_info()
else:
    page_home()
