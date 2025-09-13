# core_library/graph_components.py
from typing import Dict, Any, List



from .assertion_engine import AssertionEngine

# ==============================================================================
# --- GENERIC ROUTER FUNCTIONS ---
# ==============================================================================

def route_on_assertion(state: Dict[str, Any]) -> str:
    """
    A generic router function for conditional edges after a checkpoint.
    
    Checks the 'assertion_failures' key in the state.
    
    Returns:
        "pass": If the list is empty.
        "fail": If the list contains any failure messages.
    """

    print("--- Checkpoint Router: Checking for assertion failures... ---")
    failures = state.get("assertion_failures", [])
    
    if failures:
        print(f"  > Decision: FAIL. Failures found: {failures}")
        return "fail"
    else:
        print("  > Decision: PASS. No failures found.")
        return "pass"

# ==============================================================================
# --- REUSABLE GRAPH NODE CLASSES ---
# ==============================================================================

class AssertionCheckpointNode:
    """
    A reusable LangGraph node that acts as a "gatekeeper".
    
    It runs a specific stage of assertions and updates the agent's state
    with any failures, allowing a conditional router to direct the workflow.
    """
    def __init__(self, assertion_engine: "AssertionEngine", stage_name: str):
        """
        Initializes the checkpoint.

        Args:
            assertion_engine: An initialized instance of the AssertionEngine.
            stage_name: The name of the assertion stage to run (must match the YAML).
        """
        if assertion_engine is None:
            raise ImportError("AssertionEngine is required but was not imported. Please check dependencies.")
        
        self.assertion_engine = assertion_engine
        self.stage_name = stage_name
        print(f"--- Checkpoint Node '{self.stage_name}': Initialized. ---")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        The method that will be executed by LangGraph.
        """
        print(f"--- Checkpoint Node: Running stage '{self.stage_name}' ---")
        
        # We don't want failures from a previous checkpoint to affect this one.
        # However, it might be useful to accumulate them. For now, we overwrite.
        state["assertion_failures"] = [] 

        failures = self.assertion_engine.run_stage(self.stage_name, state)
        
        state["assertion_failures"] = failures
        
        return state # Always return the full state