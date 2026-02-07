"""
Knowledge loader for the Medical Knowledge-Based System (KBS).
Loads and validates JSON knowledge base; enforces schema; checks consistency.
Knowledge (rules and facts) is kept separate from reasoning logic.
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Any

# -----------------------------------------------------------------------------
# Schema and validation (KBS: enforce structure so reasoning is reliable)
# -----------------------------------------------------------------------------

REQUIRED_TOP_KEYS = {"metadata", "diseases", "rules"}
OPTIONAL_TOP_KEYS = {"facts"}  # Facts: symptoms, diagnostics, treatments (optional for backward compatibility)
REQUIRED_METADATA_KEYS = {"version", "last_updated"}
REQUIRED_DISEASE_KEYS = {"id", "name", "description", "symptoms", "diagnostics", "treatment", "references"}
REQUIRED_RULE_KEYS = {"id", "if_symptoms", "then_disease_id", "confidence"}


def _normalize_symptom(s: str) -> str:
    """Normalize symptom string for consistent matching."""
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.strip().lower().split())


def validate_schema(kb: dict) -> tuple[bool, list[str]]:
    """
    Validate knowledge base structure. Returns (is_valid, list of error messages).
    KBS principle: enforce schema so inference engine can rely on structure.
    """
    errors: list[str] = []
    if not isinstance(kb, dict):
        return False, ["Knowledge base must be a JSON object."]

    missing = REQUIRED_TOP_KEYS - set(kb.keys())
    if missing:
        errors.append(f"Missing top-level keys: {missing}")

    # Metadata
    meta = kb.get("metadata")
    if isinstance(meta, dict):
        missing_meta = REQUIRED_METADATA_KEYS - set(meta.keys())
        if missing_meta:
            errors.append(f"metadata missing keys: {missing_meta}")
    else:
        errors.append("metadata must be an object with version and last_updated.")

    # Diseases
    diseases = kb.get("diseases")
    if not isinstance(diseases, list):
        errors.append("diseases must be an array.")
    else:
        disease_ids = set()
        for i, d in enumerate(diseases):
            if not isinstance(d, dict):
                errors.append(f"diseases[{i}] must be an object.")
                continue
            missing_d = REQUIRED_DISEASE_KEYS - set(d.keys())
            if missing_d:
                errors.append(f"diseases[{i}] missing keys: {missing_d}")
            did = d.get("id")
            if did in disease_ids:
                errors.append(f"Duplicate disease id: {did}")
            if did:
                disease_ids.add(did)

    # Rules
    rules = kb.get("rules")
    if not isinstance(rules, list):
        errors.append("rules must be an array.")
    else:
        rule_ids = set()
        for i, r in enumerate(rules):
            if not isinstance(r, dict):
                errors.append(f"rules[{i}] must be an object.")
                continue
            missing_r = REQUIRED_RULE_KEYS - set(r.keys())
            if missing_r:
                errors.append(f"rules[{i}] missing keys: {missing_r}")
            rid = r.get("id")
            if rid and rid in rule_ids:
                errors.append(f"Duplicate rule id: {rid}")
            if rid:
                rule_ids.add(rid)

    return len(errors) == 0, errors


def check_duplicate_rules(rules: list[dict]) -> list[str]:
    """Detect rules with identical antecedent and consequent. Returns list of messages."""
    messages: list[str] = []
    seen: dict[tuple, str] = {}
    for r in rules:
        key = (tuple(sorted(_normalize_symptom(s) for s in (r.get("if_symptoms") or []))), r.get("then_disease_id"))
        if key in seen:
            messages.append(f"Duplicate rule: same IF-THEN as rule '{seen[key]}' (rule '{r.get('id', '')}').")
        else:
            seen[key] = r.get("id", "")
    return messages


def check_conflicting_conclusions(rules: list[dict]) -> list[str]:
    """
    Detect rules with same antecedent but different consequent (same symptoms, different disease).
    In KBS this can be intentional (differential) but we flag for review.
    """
    messages: list[str] = []
    by_antecedent: dict[str, set[str]] = {}
    for r in rules:
        ant = tuple(sorted(_normalize_symptom(s) for s in (r.get("if_symptoms") or [])))
        tid = r.get("then_disease_id", "")
        key = str(ant)
        if key not in by_antecedent:
            by_antecedent[key] = set()
        by_antecedent[key].add(tid)
    for ant, disease_ids in by_antecedent.items():
        if len(disease_ids) > 1:
            messages.append(f"Conflicting conclusions for same symptom set: {disease_ids}")
    return messages


def validate_rules_reference_diseases(kb: dict) -> list[str]:
    """Ensure every rule's then_disease_id exists in diseases."""
    messages: list[str] = []
    disease_ids = {d.get("id") for d in kb.get("diseases", []) if isinstance(d, dict) and d.get("id")}
    for r in kb.get("rules", []):
        if not isinstance(r, dict):
            continue
        tid = r.get("then_disease_id")
        if tid and tid not in disease_ids:
            messages.append(f"Rule '{r.get('id', '')}' references unknown disease id: {tid}")
    return messages


# -----------------------------------------------------------------------------
# Load and cache (KBS: single load, validate once, reuse)
# -----------------------------------------------------------------------------

_loaded_kb: dict | None = None
_load_time: datetime | None = None
_validation_status: str = "not_loaded"
_validation_errors: list[str] = []


def get_data_path(filename: str = "knowledge_base.json") -> str:
    """Path to knowledge JSON under data/."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "data", filename)


def load_knowledge(filepath: str | None = None, use_cache: bool = True) -> dict:
    """
    Load knowledge base from JSON. Validates schema and consistency.
    Caches result for performance (1000+ rules). Returns validated kb dict.
    """
    global _loaded_kb, _load_time, _validation_status, _validation_errors
    path = filepath or get_data_path()

    if use_cache and _loaded_kb is not None and path == get_data_path():
        return _loaded_kb

    try:
        with open(path, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except FileNotFoundError:
        _validation_status = "error"
        _validation_errors = [f"File not found: {path}"]
        raise
    except json.JSONDecodeError as e:
        _validation_status = "error"
        _validation_errors = [f"Invalid JSON: {e}"]
        raise

    ok, schema_errors = validate_schema(kb)
    if not ok:
        _validation_status = "invalid_schema"
        _validation_errors = schema_errors
        raise ValueError("Knowledge base schema invalid: " + "; ".join(schema_errors[:5]))

    rules = kb.get("rules", [])
    dup = check_duplicate_rules(rules)
    conflict = check_conflicting_conclusions(rules)
    refs = validate_rules_reference_diseases(kb)
    all_errors = dup + conflict + refs
    if all_errors:
        _validation_status = "consistency_warnings"
        _validation_errors = all_errors
    else:
        _validation_status = "valid"
        _validation_errors = []

    _loaded_kb = kb
    _load_time = datetime.utcnow()
    return kb


def get_load_info() -> dict[str, Any]:
    """Return version, load time, and validation status for UI and logging."""
    return {
        "knowledge_version": _loaded_kb.get("metadata", {}).get("version", "unknown") if _loaded_kb else "unknown",
        "last_updated": _loaded_kb.get("metadata", {}).get("last_updated", "") if _loaded_kb else "",
        "load_time": _load_time.isoformat() + "Z" if _load_time else "",
        "validation_status": _validation_status,
        "validation_errors": list(_validation_errors),
    }


def clear_cache() -> None:
    """Clear cached knowledge (e.g. after file replace for maintenance)."""
    global _loaded_kb, _load_time, _validation_status, _validation_errors
    _loaded_kb = None
    _load_time = None
    _validation_status = "not_loaded"
    _validation_errors = []


# -----------------------------------------------------------------------------
# Knowledge maintenance: save, add, update, delete diseases (for Manage UI)
# -----------------------------------------------------------------------------


def save_knowledge_base(kb: dict, filepath: str | None = None) -> None:
    """Write knowledge base to JSON. Clears cache so next load is fresh."""
    path = filepath or get_data_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    clear_cache()


def _make_disease_id(name: str, existing_ids: set[str]) -> str:
    """Generate unique disease id from name."""
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
    """Append a new disease. Returns updated kb (call save_knowledge_base after)."""
    diseases = list(kb.get("diseases", []))
    existing_ids = {d.get("id", "") for d in diseases if isinstance(d, dict)}
    new_id = _make_disease_id(name.strip(), existing_ids)
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
        if isinstance(d, dict) and d.get("id") == disease_id:
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
    """Remove a disease by id. Returns updated kb. Rules pointing to it will need manual update."""
    kb["diseases"] = [d for d in kb.get("diseases", []) if not (isinstance(d, dict) and d.get("id") == disease_id)]
    return kb


def get_disease_by_id(disease_id: str, kb: dict | None = None) -> dict | None:
    """Return disease dict by id (for Manage form)."""
    if kb is None:
        kb = load_knowledge(use_cache=True)
    for d in kb.get("diseases", []):
        if isinstance(d, dict) and d.get("id") == disease_id:
            return d
    return None
