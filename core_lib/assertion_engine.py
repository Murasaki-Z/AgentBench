# core_library/assertion_engine.py
import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .assertion_operators import ASSERTION_OPERATOR_MAP

class AssertionEngine:
    """
    Runs a suite of objective, pass/fail checks against an agent's final state.
    """
    def __init__(self, config_path: Path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self.assertion_definitions = config.get("assertions", [])
        print(f"--- AssertionEngine: Initialized with {len(self.assertion_definitions)} assertions from {config_path.name} ---")

    def run_all(self, final_state: Dict[str, Any]) -> List[str]:
        """
        Runs all defined assertions and returns a list of failure messages.
        An empty list means all assertions passed.
        """
        failures = []
        for assertion_config in self.assertion_definitions:
            assertion_type = assertion_config.get("type")
            assertion_name = assertion_config.get("name", "Unnamed Assertion")
            
            if assertion_type in ASSERTION_OPERATOR_MAP:
                check_function = ASSERTION_OPERATOR_MAP[assertion_type]
                is_pass, reason = check_function(assertion_config, final_state)
                
                if not is_pass:
                    failures.append(f"'{assertion_name}': {reason}")
            else:
                # Placeholder for custom python checks later
                pass
        
        return failures