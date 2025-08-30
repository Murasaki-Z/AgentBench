# core_library/metric_engine.py
import yaml
from pathlib import Path
from typing import Any, Dict, List

class MetricEngine:
    """
    A factory that calculates metrics based on a declarative YAML configuration.
    """
    def __init__(self, config_path: Path):
        if not config_path.exists():
            raise FileNotFoundError(f"Metric configuration file not found at {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.metric_definitions = config.get("metrics", [])
        print(f"--- MetricEngine: Initialized with {len(self.metric_definitions)} metric definitions from {config_path.name} ---")

    def calculate_all(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """

        Calculates all metrics defined in the YAML for a given agent final state.
        """
        results = {}
        for metric_config in self.metric_definitions:
            metric_type = metric_config.get("type")
            metric_name = metric_config.get("name", "unnamed_metric")
            
            try:
                if metric_type == "derive_path":
                    results[metric_name] = self._calculate_derive_path(metric_config, final_state)
                elif metric_type == "ratio":
                    results[metric_name] = self._calculate_ratio(metric_config, final_state)
                # We can add more 'elif' blocks here for new metric types in the future
                else:
                    results[metric_name] = "Unsupported metric type"
            except Exception as e:
                print(f"  > ERROR calculating metric '{metric_name}': {e}")
                results[metric_name] = "CALCULATION_ERROR"
        return results

    # --- Private Helper Methods for Calculation ---

    def _get_value_from_state(self, field_path: str, state: Dict[str, Any]) -> Any:
        """A simple helper to get a value from a dictionary. V2 will use JMESPath."""
        return state.get(field_path)

    def _calculate_value(self, config: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """A central dispatcher to call the right calculation helper for sub-tasks."""
        calc_type = config["type"]
        if calc_type == "count_list":
            field_path = config["field"]
            data_list = self._get_value_from_state(field_path, state)
            return len(data_list) if isinstance(data_list, list) else 0
        
        if calc_type == "count_unique_in_list":
            field_path = config["field"]
            list_path, key_to_count = field_path.rsplit('.', 1)
            data_list = self._get_value_from_state(list_path, state)
            if not isinstance(data_list, list): return 0
            unique_values = {item.get(key_to_count) for item in data_list if isinstance(item, dict)}
            return len(unique_values)
        
        raise ValueError(f"Unknown calculation type: {calc_type}")

    def _calculate_derive_path(self, config: Dict[str, Any], state: Dict[str, Any]) -> str:
        for rule in config.get("paths", []):
            field_to_check = rule.get("if_field_exists")
            if field_to_check:
                if state.get(field_to_check):
                    return rule["name"]
            else: # Default/fallback rule
                return rule["name"]
        return "no_path_matched"

    def _calculate_ratio(self, config: Dict[str, Any], state: Dict[str, Any]) -> float:
        numerator_config = config["numerator"]
        denominator_config = config["denominator"]
        options = config.get("options", {})

        numerator_value = self._calculate_value(numerator_config, state)
        denominator_value = self._calculate_value(denominator_config, state)

        if denominator_value == 0:
            return float(options.get("on_zero_denominator", 0.0))
        
        result = numerator_value / denominator_value
        return result * 100.0 if options.get("format_as_percent") else result