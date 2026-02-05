# Services layer: knowledge loading, search, clinical decision support, and disease management.

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

__all__ = [
    "load_knowledge_base",
    "save_knowledge_base",
    "search_diseases_by_name",
    "search_diseases_by_symptom",
    "get_possible_conditions_for_symptoms",
    "get_all_symptoms",
    "get_disease_by_id",
    "add_disease",
    "update_disease",
    "delete_disease",
]
