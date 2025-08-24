from typing import TypedDict, List, Dict

class AgentState(TypedDict):
    """
    Defines the structure of our agent's memory.
    """
    request: str                  # The initial request from the user
    ingredients_list: List[str]   # The list of ingredients identified by the LLM
    store_search_results: List[Dict] # Raw results from searching the store inventories
    shopping_list: str            # The final, formatted shopping list for the user
    missing_items: List[str]      # Ingredients that could not be found in any store