"""
Orchestrates metric calculation based on a declarative YAML configuration,
supporting chained pipeline operators with arguments.
"""
import yaml
from pathlib import Path
from typing import Any, Dict

# --- Import our enhanced toolbox ---
from .metrics_operators import OPERATOR_MAP, _parse_op_with_arg

class MetricEngine:
    """
    Orchestrates metric calculation based on a declarative YAML configuration,
    supporting chained pipeline operators with arguments.
    """
    def __init__(self, config_path: Path):
        """Initializes the engine by loading and parsing a YAML metric definition file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Metric configuration file not found at {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self.metric_definitions = config.get("metrics", [])
        print(f"--- MetricEngine: Initialized with {len(self.metric_definitions)} metric definitions from {config_path.name} ---")

    def calculate_all(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates all metrics defined in the YAML for a given agent final state."""
        results = {}
        for metric_config in self.metric_definitions:
            metric_name = metric_config.get("name", "unnamed_metric")
            try:
                # --- Handle special, non-pipeline metric types first ---
                metric_type = metric_config.get("type")
                if metric_type == "ratio":
                    results[metric_name] = self._calculate_ratio(metric_config, final_state)
                elif metric_type == "derive_path":
                    results[metric_name] = self._calculate_derive_path(metric_config, final_state)
                # --- Otherwise, assume it's a standard pipeline ---
                else:
                    results[metric_name] = self._execute_pipeline(metric_config, final_state)
            except Exception as e:
                print(f"  > ERROR calculating metric '{metric_name}': {e}")
                results[metric_name] = "CALCULATION_ERROR"
        return results
    
    def _execute_pipeline(self, config: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """
        Executes a pipeline of chained operators, parsing arguments as needed.
        """
        type_str = config["type"]
        operators = [op.strip() for op in type_str.split('|')]
        
        # The pipeline starts with the data from the 'field'.
        current_value = self._get_value_from_state(config.get("field", ""), state)
        
        # Apply each operator in sequence.
        for op_str in operators:
            # --- NEW: Parse operator and its potential argument ---
            op_name, op_arg = _parse_op_with_arg(op_str)

            if op_name not in OPERATOR_MAP:
                raise ValueError(f"Unknown operator in pipeline: '{op_name}'")
            
            op_func = OPERATOR_MAP[op_name]
            
            # --- NEW: Call the function with an argument if it was parsed ---
            if op_arg is not None:
                current_value = op_func(current_value, op_arg)
            else:
                current_value = op_func(current_value)
            
        return current_value

    def _get_value_from_state(self, field_path: str, state: Dict[str, Any]) -> Any:
        """A robust helper to get a value from a state dictionary using dot-notation."""
        if not field_path: return state # Allow operating on the whole state
        
        keys = field_path.split('.')
        current_value = state
        
        for key in keys:
            if current_value is None: return None
            if isinstance(current_value, dict):
                current_value = current_value.get(key)
            elif isinstance(current_value, list):
                # Extract the attribute from each dictionary in the list.
                return [item.get(key) for item in current_value if isinstance(item, dict)]
            else:
                return None
        return current_value

    def _calculate_ratio(self, config: Dict[str, Any], state: Dict[str, Any]) -> float:
        """Calculates a ratio, where sub-fields are now full pipelines."""
        numerator_config = config["numerator"]
        denominator_config = config["denominator"]
        options = config.get("options", {})

        numerator_value = self._execute_pipeline(numerator_config, state)
        denominator_value = self._execute_pipeline(denominator_config, state)

        if denominator_value == 0:
            return float(options.get("on_zero_denominator", 0.0))
        
        result = numerator_value / denominator_value
        return result * 100.0 if options.get("format_as_percent") else result

    def _calculate_derive_path(self, config: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Calculates a metric by checking for the existence of fields in the state."""
        for rule in config.get("paths", []):
            field_to_check = rule.get("if_field_exists")
            if field_to_check:
                if state.get(field_to_check):
                    return rule["name"]
            else: # Default/fallback rule
                return rule["name"]
        return "no_path_matched"