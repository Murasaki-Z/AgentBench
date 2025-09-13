# core_library/assertion_engine.py
import yaml
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict

from .assertion_operators import ASSERTION_OPERATOR_MAP

class AssertionEngine:
    """
    Runs a suite of objective, pass/fail checks against an agent's state,
    organized by stage.
    """
    def __init__(self, config_path: Path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.assertions_by_stage = defaultdict(list)
        all_assertions = config.get("assertions", [])
        for assertion_def in all_assertions:
            stage = assertion_def.get("stage", "default_stage")
            self.assertions_by_stage[stage].append(assertion_def)

        print(f"--- AssertionEngine: Initialized with {len(all_assertions)} assertions across {len(self.assertions_by_stage)} stages. ---")

    def run_stage(self, stage_name: str, state: Dict[str, Any]) -> List[str]:
        """
        Runs all assertions for a specific stage and returns a list of failure messages.
        """
        failures = []
        assertions_to_run = self.assertions_by_stage.get(stage_name, [])
        
        for config in assertions_to_run:
            type = config.get("type")
            name = config.get("name", "Unnamed Assertion")
            
            if type in ASSERTION_OPERATOR_MAP:
                check_function = ASSERTION_OPERATOR_MAP[type]
                is_pass, reason = check_function(config, state)
                
                if not is_pass:
                    failures.append(f"'{name}': {reason}")
            # ... (placeholder for custom checks)
        
        return failures