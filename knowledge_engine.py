"""
Knowledge-based inference engine for medical condition identification.
Matches user-reported symptoms against the condition knowledge base.
"""

import json
import os
import re


def _normalize(s: str) -> str:
    """Normalize text for matching: lowercase, strip, collapse spaces."""
    if not s or not isinstance(s, str):
        return ""
    return " ".join(re.sub(r"[^\w\s]", "", s.lower()).split())


def _symptom_matches(user_symptom: str, known_symptom: str) -> bool:
    """Check if user symptom matches known symptom (exact or contains)."""
    u = _normalize(user_symptom)
    k = _normalize(known_symptom)
    if not u or not k:
        return False
    return u == k or u in k or k in u


def load_knowledge_base(path: str | None = None) -> dict:
    """Load conditions from JSON. Uses optional user-added JSON if present."""
    if path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "knowledge_base", "conditions.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_knowledge_base(data: dict, path: str | None = None) -> None:
    """Save conditions to JSON."""
    if path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "knowledge_base", "conditions.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def identify_conditions(
    user_symptoms: list[str],
    kb: dict | None = None,
) -> list[dict]:
    """
    Match user symptoms to conditions in the knowledge base.
    Returns list of matches with score and matched symptoms.
    """
    if kb is None:
        kb = load_knowledge_base()
    conditions = kb.get("conditions", [])
    user_symptoms = [s.strip() for s in user_symptoms if s and s.strip()]
    if not user_symptoms:
        return []

    results = []
    for cond in conditions:
        known = [str(s).strip() for s in cond.get("symptoms", [])]
        matched = []
        for us in user_symptoms:
            for ks in known:
                if _symptom_matches(us, ks):
                    matched.append(ks)
                    break
        if not matched:
            continue
        # Score: proportion of user symptoms that matched + proportion of condition symptoms covered
        user_matched_ratio = len(matched) / len(user_symptoms) if user_symptoms else 0
        condition_ratio = len(matched) / len(known) if known else 0
        score = 0.6 * user_matched_ratio + 0.4 * condition_ratio
        results.append({
            "id": cond.get("id", ""),
            "name": cond.get("name", ""),
            "category": cond.get("category", ""),
            "matched_symptoms": list(dict.fromkeys(matched)),
            "score": round(score, 2),
            "total_known_symptoms": len(known),
        })

    results.sort(key=lambda x: (-x["score"], -len(x["matched_symptoms"])))
    return results


def get_all_symptoms(kb: dict | None = None) -> list[str]:
    """Return sorted list of all unique symptoms in the knowledge base."""
    if kb is None:
        kb = load_knowledge_base()
    seen = set()
    for cond in kb.get("conditions", []):
        for s in cond.get("symptoms", []):
            t = str(s).strip()
            if t:
                seen.add(t)
    return sorted(seen)


def get_condition_by_id(condition_id: str, kb: dict | None = None) -> dict | None:
    """Return full condition dict by id, or None."""
    if kb is None:
        kb = load_knowledge_base()
    for c in kb.get("conditions", []):
        if c.get("id") == condition_id:
            return c
    return None


def get_conditions_by_category(category: str, kb: dict | None = None) -> list[dict]:
    """Return all conditions in a category."""
    if kb is None:
        kb = load_knowledge_base()
    return [c for c in kb.get("conditions", []) if (c.get("category") or "").strip() == category]


def add_condition(
    name: str,
    symptoms: list[str],
    category: str = "General",
    kb: dict | None = None,
) -> dict:
    """
    Add a new condition to the knowledge base. Returns updated kb.
    """
    if kb is None:
        kb = load_knowledge_base()
    conditions = kb.get("conditions", [])
    existing_ids = {c.get("id", "") for c in conditions}
    base_id = re.sub(r"[^\w]", "", name.lower()).replace(" ", "_")[:40]
    new_id = base_id
    i = 0
    while new_id in existing_ids or not new_id:
        i += 1
        new_id = f"{base_id}_{i}"
    symptoms_clean = [s.strip() for s in symptoms if s and s.strip()]
    conditions.append({
        "id": new_id,
        "name": name.strip(),
        "symptoms": symptoms_clean,
        "category": category.strip() or "General",
    })
    kb["conditions"] = conditions
    return kb


def add_conditions_batch(entries: list[dict], kb: dict | None = None) -> tuple[dict, int]:
    """
    Add multiple conditions. Each entry: {"name": str, "symptoms": list[str], "category": str (optional)}.
    Returns (updated_kb, number_added).
    """
    if kb is None:
        kb = load_knowledge_base()
    added = 0
    for e in entries:
        name = (e.get("name") or "").strip()
        symptoms = e.get("symptoms") or []
        if isinstance(symptoms, str):
            symptoms = [s.strip() for s in symptoms.split(",") if s.strip()]
        else:
            symptoms = [str(s).strip() for s in symptoms if s and str(s).strip()]
        category = (e.get("category") or "General").strip()
        if name and symptoms:
            kb = add_condition(name, symptoms, category, kb)
            added += 1
    return kb, added
