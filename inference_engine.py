"""
Inference engine for the Medical Knowledge-Based System (KBS).
Implements forward chaining: rule matching against user-selected symptoms.
Knowledge (rules in JSON) is separate from this reasoning logic.
Returns matched diseases with confidence and full explanation data.
"""

from typing import Any

# -----------------------------------------------------------------------------
# Normalization (consistent matching between user input and rule antecedents)
# -----------------------------------------------------------------------------


def _normalize(s: str) -> str:
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.strip().lower().split())


def _symptom_matches(user_symptom: str, rule_symptom: str) -> bool:
    u = _normalize(user_symptom)
    r = _normalize(rule_symptom)
    if not u or not r:
        return False
    return u == r or u in r or r in u


# -----------------------------------------------------------------------------
# Forward chaining (KBS: IF antecedent THEN consequent; no medical logic in UI)
# -----------------------------------------------------------------------------


def forward_chain(user_symptoms: list[str], kb: dict) -> list[dict]:
    """
    Forward chaining: find all rules whose IF part is (fully or partially) satisfied
    by user symptoms, then return concluded diseases with confidence and explanation.

    A rule fires when at least one symptom in rule.if_symptoms matches a user symptom.
    Confidence is scaled by how many rule symptoms matched: rule_confidence * (matched / total).
    Multiple rules can fire for the same disease; overall confidence is the maximum over firing rules.
    """
    user_symptoms = [s.strip() for s in user_symptoms if s and s.strip()]
    if not user_symptoms:
        return []

    diseases_by_id = {d["id"]: d for d in kb.get("diseases", []) if isinstance(d, dict) and d.get("id")}
    rules = kb.get("rules", [])
    results: dict[str, dict] = {}  # disease_id -> result entry

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if_syms = rule.get("if_symptoms") or []
        then_id = rule.get("then_disease_id")
        base_confidence = rule.get("confidence", 0.5)
        rule_id = rule.get("id", "")

        matched_in_rule = []
        for rs in if_syms:
            if any(_symptom_matches(us, rs) for us in user_symptoms):
                matched_in_rule.append(rs)

        # Fire if at least one rule symptom matched (partial match)
        if not matched_in_rule or not then_id:
            continue

        # Scale confidence by fraction of rule symptoms matched
        rule_confidence = round(base_confidence * (len(matched_in_rule) / len(if_syms)), 2)

        if then_id not in results:
            disease = diseases_by_id.get(then_id, {})
            results[then_id] = {
                "disease_id": then_id,
                "disease_name": disease.get("name", then_id),
                "confidence": rule_confidence,
                "fired_rules": [],
                "matched_symptoms": list(matched_in_rule),
                "explanation": "",
            }
        entry = results[then_id]
        entry["fired_rules"].append({
            "rule_id": rule_id,
            "matched_symptoms": list(matched_in_rule),
            "rule_confidence": rule_confidence,
        })
        if rule_confidence > entry["confidence"]:
            entry["confidence"] = rule_confidence
        entry["matched_symptoms"] = list(dict.fromkeys(entry["matched_symptoms"] + matched_in_rule))

    # Build human-readable explanation for each result
    for disease_id, entry in results.items():
        parts = []
        for fr in entry["fired_rules"]:
            parts.append(
                f"Rule '{fr['rule_id']}' fired: symptoms {fr['matched_symptoms']} matched (confidence {fr['rule_confidence']:.0%})."
            )
        entry["explanation"] = " ".join(parts) if parts else "No rule explanation available."

    out = list(results.values())
    out.sort(key=lambda x: (-x["confidence"], -len(x["matched_symptoms"])))
    return out


def get_disease_by_id(disease_id: str, kb: dict) -> dict | None:
    """Return full disease record for explanation view."""
    for d in kb.get("diseases", []):
        if isinstance(d, dict) and d.get("id") == disease_id:
            return d
    return None


def get_all_symptoms_from_kb(kb: dict) -> list[str]:
    """Unique sorted symptoms from diseases and rules for UI dropdowns."""
    seen = set()
    for d in kb.get("diseases", []):
        for s in (d.get("symptoms") or []) if isinstance(d, dict) else []:
            t = str(s).strip()
            if t:
                seen.add(t)
    for r in kb.get("rules", []):
        for s in (r.get("if_symptoms") or []) if isinstance(r, dict) else []:
            t = str(s).strip()
            if t:
                seen.add(t)
    return sorted(seen)
