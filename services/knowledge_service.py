"""
Knowledge service: load/save medical knowledge base, search, clinical decision support,
and disease management (add, edit, delete).
"""

import json
import re
import os

# Normalize symptom strings for matching (e.g. "Runny nose" vs "runny nose").
from utils.formatting import normalize_symptom_text


def _data_path(filename: str = "medical_knowledge.json") -> str:
    """Resolve path to data file relative to project root (where app.py lives)."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", filename)


def load_knowledge_base(filepath: str | None = None) -> dict:
    """
    Load the medical knowledge base from JSON.
    Returns dict with key "diseases" (list of disease objects).
    Raises FileNotFoundError or json.JSONDecodeError on failure.
    """
    path = filepath or _data_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _symptom_matches(user_symptom: str, known_symptom: str) -> bool:
    """True if normalized user input matches or is contained in known symptom (or vice versa)."""
    u = normalize_symptom_text(user_symptom)
    k = normalize_symptom_text(known_symptom)
    if not u or not k:
        return False
    return u == k or u in k or k in u


def search_diseases_by_name(query: str, kb: dict | None = None) -> list[dict]:
    """
    Search diseases by name (case-insensitive substring match).
    Returns list of disease objects that match. Empty list if no match or empty query.
    """
    if not query or not query.strip():
        return []
    if kb is None:
        kb = load_knowledge_base()
    q = query.strip().lower()
    return [d for d in kb.get("diseases", []) if q in (d.get("name") or "").lower()]


def search_diseases_by_symptom(symptom: str, kb: dict | None = None) -> list[dict]:
    """
    Find all diseases that list the given symptom (normalized match).
    Returns list of disease objects.
    """
    if not symptom or not symptom.strip():
        return []
    if kb is None:
        kb = load_knowledge_base()
    return [
        d for d in kb.get("diseases", [])
        if any(_symptom_matches(symptom, s) for s in (d.get("symptoms") or []))
    ]


def get_possible_conditions_for_symptoms(symptoms: list[str], kb: dict | None = None) -> list[dict]:
    """
    Clinical decision support: given a list of symptoms, return possible conditions
    with a match score. Each condition is augmented with:
      - matched_symptoms: list of symptoms that matched
      - score: 0–1 (fraction of user symptoms that matched, weighted with fraction of condition symptoms covered)
    Sorted by score descending. Used when one symptom matches multiple diseases
    or when user enters multiple symptoms to narrow down conditions.
    """
    if kb is None:
        kb = load_knowledge_base()
    user_list = [s.strip() for s in symptoms if s and s.strip()]
    if not user_list:
        return []

    results = []
    for disease in kb.get("diseases", []):
        known = [str(s).strip() for s in disease.get("symptoms") or []]
        matched = []
        for us in user_list:
            for ks in known:
                if _symptom_matches(us, ks):
                    matched.append(ks)
                    break
        if not matched:
            continue
        user_ratio = len(matched) / len(user_list)
        condition_ratio = len(matched) / len(known) if known else 0
        score = round(0.6 * user_ratio + 0.4 * condition_ratio, 2)
        results.append({
            **disease,
            "matched_symptoms": list(dict.fromkeys(matched)),
            "score": score,
            "total_known_symptoms": len(known),
        })

    results.sort(key=lambda x: (-x["score"], -len(x["matched_symptoms"])))
    return results


def get_all_symptoms(kb: dict | None = None) -> list[str]:
    """Return sorted list of all unique symptoms in the knowledge base (for UI dropdowns)."""
    if kb is None:
        kb = load_knowledge_base()
    seen = set()
    for d in kb.get("diseases", []):
        for s in d.get("symptoms") or []:
            t = str(s).strip()
            if t:
                seen.add(t)
    return sorted(seen)


def get_disease_by_id(disease_id: str, kb: dict | None = None) -> dict | None:
    """Return the full disease object for the given id, or None."""
    if kb is None:
        kb = load_knowledge_base()
    for d in kb.get("diseases", []):
        if d.get("id") == disease_id:
            return d
    return None


def save_knowledge_base(kb: dict, filepath: str | None = None) -> None:
    """Write the knowledge base (with key 'diseases') to JSON."""
    path = filepath or _data_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)


def _make_id(name: str, existing_ids: set[str]) -> str:
    """Generate a unique id from disease name (slug)."""
    base = re.sub(r"[^\w\s]", "", name.lower()).replace(" ", "_")[:40] or "disease"
    out = base
    i = 0
    while out in existing_ids or not out:
        i += 1
        out = f"{base}_{i}"
    return out


def add_disease(
    kb: dict,
    name: str,
    description: str,
    symptoms: list[str],
    diagnostics: list[str],
    treatment: list[str],
    references: str = "",
) -> dict:
    """Append a new disease to the knowledge base. Returns updated kb."""
    diseases = list(kb.get("diseases", []))
    existing_ids = {d.get("id", "") for d in diseases}
    new_id = _make_id(name, existing_ids)
    symptoms_clean = [s.strip() for s in symptoms if s and str(s).strip()]
    diagnostics_clean = [s.strip() for s in diagnostics if s and str(s).strip()]
    treatment_clean = [s.strip() for s in treatment if s and str(s).strip()]
    diseases.append({
        "id": new_id,
        "name": name.strip(),
        "description": (description or "").strip(),
        "symptoms": symptoms_clean,
        "diagnostics": diagnostics_clean,
        "treatment": treatment_clean,
        "references": (references or "").strip(),
    })
    kb["diseases"] = diseases
    return kb


def update_disease(
    kb: dict,
    disease_id: str,
    name: str,
    description: str,
    symptoms: list[str],
    diagnostics: list[str],
    treatment: list[str],
    references: str = "",
) -> dict:
    """Update an existing disease by id. Returns updated kb."""
    diseases = []
    for d in kb.get("diseases", []):
        if d.get("id") == disease_id:
            diseases.append({
                "id": disease_id,
                "name": name.strip(),
                "description": (description or "").strip(),
                "symptoms": [s.strip() for s in symptoms if s and str(s).strip()],
                "diagnostics": [s.strip() for s in diagnostics if s and str(s).strip()],
                "treatment": [s.strip() for s in treatment if s and str(s).strip()],
                "references": (references or "").strip(),
            })
        else:
            diseases.append(d)
    kb["diseases"] = diseases
    return kb


def delete_disease(kb: dict, disease_id: str) -> dict:
    """Remove a disease by id. Returns updated kb."""
    kb["diseases"] = [d for d in kb.get("diseases", []) if d.get("id") != disease_id]
    return kb
