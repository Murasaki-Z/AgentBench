from typing import TypedDict, List

class AgentState(TypedDict):
    """
    Defines the structure of our agent's memory or "state".
    This is what will be passed between nodes in the graph.
    """
    request: str      # The initial request from the user
    response: str     # The final response from the LLM