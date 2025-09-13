# core_library/assertion_operators.py
"""
The "Toolbox" for our AssertionEngine.
Contains the pure Python functions that execute declarative assertions.
"""
from typing import Any, Dict, List

def check_must_exist_one_of(config: Dict[str, Any], state: Dict[str, Any]) -> tuple[bool, str]:
    """Checks if at least one of the specified fields exists and is not empty."""
    fields = config.get("fields", [])
    for field in fields:
        if state.get(field): # .get() returns None if not found, which is "falsy"
            return True, "Check passed."
    return False, f"Critical failure: None of the required fields {fields} were present in the final state."

def check_fields_must_be_consistent(config: Dict[str, Any], state: Dict[str, Any]) -> tuple[bool, str]:
    """Checks a set of conditional rules for consistency."""
    conditions = config.get("conditions", [])
    for rule in conditions:
        if_clause = rule.get("if", {})
        then_clause = rule.get("then", {})

        if_field = if_clause.get("field")
        if_equals = if_clause.get("equals")

        # Check if the 'if' condition for this rule is met
        if state.get(if_field) == if_equals:
            # If it is, then check the 'then' condition
            then_field = then_clause.get("field")
            must_exist = then_clause.get("must_exist")

            if must_exist and not state.get(then_field):
                reason = (f"Consistency check failed: Intent was '{if_equals}', "
                          f"but required field '{then_field}' was missing.")
                return False, reason
    
    return True, "Check passed."


ASSERTION_OPERATOR_MAP = {
    "must_exist_one_of": check_must_exist_one_of,
    "fields_must_be_consistent": check_fields_must_be_consistent,
}