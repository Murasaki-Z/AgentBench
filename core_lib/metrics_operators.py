"""
The "Toolbox" for our MetricEngine.
This file contains all the individual, chainable operator functions
that perform the actual metric calculations. It is our "SQL Function Library".
"""
from typing import Any, List, Callable
import re

# ==============================================================================
# --- Helper Function for Parsing Operator Arguments ---
# ==============================================================================

def _parse_op_with_arg(op_str: str) -> tuple[str, str | None]:
    """Parses an operator string like 'where(>5)' into ('where', '>5')."""
    match = re.match(r"(\w+)\((.*)\)", op_str)
    if match:
        return match.groups()
    return op_str, None

# ==============================================================================
# --- Aggregation Operators (List -> Single Value) ---
# ==============================================================================

def op_count(data: List[Any]) -> int:
    """Counts the number of items in a list."""
    return len(data) if isinstance(data, list) else 0

def op_sum(data: List[Any]) -> float:
    """Sums a list of numbers. Ignores non-numeric types."""
    if not isinstance(data, list): return 0.0
    return sum(item for item in data if isinstance(item, (int, float)))

def op_average(data: List[Any]) -> float:
    """Calculates the average of a list of numbers."""
    numeric_items = [item for item in data if isinstance(item, (int, float))]
    if not numeric_items: return 0.0
    return sum(numeric_items) / len(numeric_items)
        
def op_max(data: List[Any]) -> float | None:
    """Finds the maximum value in a list of numbers."""
    numeric_items = [item for item in data if isinstance(item, (int, float))]
    return max(numeric_items) if numeric_items else None

def op_min(data: List[Any]) -> float | None:
    """Finds the minimum value in a list of numbers."""
    numeric_items = [item for item in data if isinstance(item, (int, float))]
    return min(numeric_items) if numeric_items else None

# ==============================================================================
# --- List Transformation Operators (List -> List) ---
# ==============================================================================

def op_distinct(data: List[Any]) -> List[Any]:
    """Returns a list of unique items, preserving order."""
    if not isinstance(data, list): return []
    seen = set()
    # This clever line returns a list of unique items while preserving the
    # original order of their first appearance.
    return [x for x in data if not (x in seen or seen.add(x))]
        
def op_flatten(data: List[Any]) -> List[Any]:
    """Flattens a list of lists into a single list."""
    if not isinstance(data, list): return []
    return [item for sublist in data if isinstance(sublist, list) for item in sublist]

def op_sort(data: List[Any], reverse: bool = False) -> List[Any]:
    """Sorts a list. Can handle mixed types by converting to string."""
    if not isinstance(data, list): return []
    # Using a try-except block to handle un-sortable types gracefully
    try:
        return sorted(data, reverse=reverse)
    except TypeError:
        # Fallback for mixed types (e.g., numbers and strings)
        return sorted(data, key=str, reverse=reverse)

def op_reverse(data: List[Any]) -> List[Any]:
    """Reverses the order of a list."""
    if not isinstance(data, list): return []
    return data[::-1]

def op_where(data: List[Any], condition: str) -> List[Any]:
    """
    Filters a list based on a simple condition string.
    Examples: '>5', '<=10', 'contains "Store"', 'is_not_empty'
    """
    if not isinstance(data, list) or not condition: return []
    
    # Handle simple keywords
    if condition == 'is_not_empty':
        return [item for item in data if item is not None and item != '']
    
    # Handle 'contains' for strings
    match = re.match(r"contains\s+['\"](.*)['\"]", condition, re.IGNORECASE)
    if match:
        substring = match.group(1)
        return [item for item in data if isinstance(item, str) and substring in item]
        
    # Handle numeric comparisons
    match = re.match(r"([><]=?|==|!=)\s*(-?\d+\.?\d*)", condition)
    if match:
        op, num_str = match.groups()
        num = float(num_str)
        
        op_map: Dict[str, Callable[[Any, float], bool]] = {
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
        }
        
        if op in op_map:
            op_func = op_map[op]
            return [item for item in data if isinstance(item, (int, float)) and op_func(item, num)]
            
    return [] # Return empty list if condition is not understood


# ==============================================================================
# Operator Map
# ==============================================================================
# This dictionary is what the MetricEngine will import and use.
# It maps the name used in the YAML to the actual Python function.

OPERATOR_MAP = {
    # Aggregators
    'count': op_count,
    'sum': op_sum,
    'total':op_sum,
    'average': op_average,
    'avg': op_average,
    'max': op_max,
    'highest':op_max,
    'min': op_min,
    'smallest':op_min,
    
    # Transformers
    'distinct': op_distinct,
    'unique':op_distinct,
    'flatten': op_flatten,
    'sort': op_sort,

    # The reverse operator needs a lambda to fit the standard function signature
    'reverse': op_reverse,

    # Operators with arguments have special handling in the engine
    'where': op_where
}