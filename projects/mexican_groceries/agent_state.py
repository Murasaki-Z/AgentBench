from typing import TypedDict, List, Dict, Literal
from typing_extensions import NotRequired

class AgentState(TypedDict):
    """
    Defines the structure of our agent's memory.
    """
    request: str                  # The initial request from the user
    intent: NotRequired[Literal["recipe_request", "off_topic", "ambiguous"]] # what the user is talking about
    ingredients_list: NotRequired[List[str]]   # The list of ingredients identified by the LLM
    store_search_results: NotRequired[List[Dict]] # Raw results from searching the store inventories
    shopping_list: NotRequired[str]            # The final, formatted shopping list for the user
    missing_items: NotRequired[List[str]]      # Ingredients that could not be found in any store
    clarification_question: NotRequired[str]  #if base LLM isnt sure use a smaller model to clarify
    dish_name: NotRequired[str]