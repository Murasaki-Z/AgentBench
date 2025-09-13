# core_library/assertion_operators.py
"""
The "Toolbox" for our AssertionEngine.
Contains the pure Python functions that execute declarative assertions.
"""
from typing import Any, Dict

def check_must_exist_one_of(config: Dict[str, Any], state: Dict[str, Any]) -> tuple[bool, str]:
    fields = config.get("fields", [])
    for field in fields:
        if state.get(field):
            return True, "Check passed."
    return False, f"None of the required fields {fields} were present."

def check_fields_must_be_consistent(config: Dict[str, Any], state: Dict[str, Any]) -> tuple[bool, str]:
    conditions = config.get("conditions", [])
    for rule in conditions:
        if_clause = rule.get("if", {})
        then_clause = rule.get("then", {})

        # --- Evaluate the IF condition ---
        if_field = if_clause.get("field")
        if_field_value = state.get(if_field)
        
        if_condition_met = False
        if "equals" in if_clause:
            if_condition_met = (if_field_value == if_clause["equals"])
        elif "exists" in if_clause:
            if_condition_met = (if_field_value is not None and if_field_value != '')
        
        # --- If the condition is met, evaluate the THEN clause ---
        if if_condition_met:
            then_field = then_clause.get("field")
            then_field_value = state.get(then_field)
            
            if "must_exist" in then_clause and then_clause["must_exist"]:
                if not then_field_value:
                    return False, f"Consistency failed: '{if_field}' was '{if_field_value}', but required field '{then_field}' was missing."
            
            if "must_not_exist" in then_clause and then_clause["must_not_exist"]:
                if then_field_value:
                    return False, f"Consistency failed: '{if_field}' was '{if_field_value}', but field '{then_field}' should NOT exist."

            if "is_in" in then_clause:
                valid_values = then_clause["is_in"]
                if then_field_value not in valid_values:
                    return False, f"Consistency failed: Field '{then_field}' had value '{then_field_value}', which is not in the allowed list {valid_values}."

    return True, "Check passed."

ASSERTION_OPERATOR_MAP = {
    "must_exist_one_of": check_must_exist_one_of,
    "fields_must_be_consistent": check_fields_must_be_consistent,
}