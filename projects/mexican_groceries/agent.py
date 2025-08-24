# projects/mexican_cooking_bot/agent.py
import json
from pathlib import Path
from . import config
from .agent_state import AgentState
from core_lib.llm_service import OpenAIService
from core_lib.data_sinks import JSONDataSink 


# --- SERVICE and DATA LOADING ---

# Initialize the LLM service once
llm_service = OpenAIService(api_key=config.OPENAI_API_KEY)

# Load the store data once to avoid repeated file reads
def load_store_data():
    data_path = Path(__file__).parent / "data"
    with open(data_path / "mexican_store.json") as f:
        mexican_store_data = json.load(f)
    with open(data_path / "produce_store.json") as f:
        produce_store_data = json.load(f)
    return mexican_store_data, produce_store_data

MEXICAN_STORE, PRODUCE_STORE = load_store_data()

log_file_path = Path(__file__).parent / "logs" / "run_log.jsonl"
data_sink = JSONDataSink(log_path=log_file_path)


# --- AGENT NODES ---

def identify_ingredients_node(state: AgentState) -> dict:
    """
    Node 1: Takes the user request and uses the LLM to identify ingredients.
    """
    print("---NODE: Identifying Ingredients---")
    user_request = state['request']
    
    prompt = f"""
    You are an expert Mexican chef. A user wants to make a dish.
    Your task is to identify the core ingredients needed for the recipe.
    List the ingredients as a simple comma-separated string. Do not add any other text.
    For example: Nachos, Cheese, Beef, Salt

    User's request: "{user_request}"
    Ingredients:
    """
    
    response_text = llm_service.invoke(prompt, model=config.DEFAULT_MODEL)
    
    # Clean up the response and split it into a list
    ingredients = [item.strip() for item in response_text.split(',')]
    
    print(f" > Ingredients identified: {ingredients}")
    return {"ingredients_list": ingredients}


def search_stores_node(state: AgentState) -> dict:
    """
    Node 2: Takes the ingredient list and searches both store JSON files.
    This is a pure Python function, no LLM call.
    """
    print("---NODE: Searching Stores---")
    ingredients = state['ingredients_list']
    found_items = []
    missing_items = []

    for ingredient in ingredients:
        item_found_in_a_store = False
        # Search Mexican Store
        for item in MEXICAN_STORE:
            if ingredient.lower() in item['item'].lower():
                found_items.append({"ingredient": ingredient, "store": "Mexican Store", **item})
                item_found_in_a_store = True
        
        # Search Produce Store
        for item in PRODUCE_STORE:
            if ingredient.lower() in item['item'].lower():
                found_items.append({"ingredient": ingredient, "store": "Produce Store", **item})
                item_found_in_a_store = True
        
        if not item_found_in_a_store:
            missing_items.append(ingredient)

    print(f" > Found items: {len(found_items)}")
    print(f" > Missing items: {missing_items}")
    return {"store_search_results": found_items, "missing_items": missing_items}


def compile_shopping_list_node(state: AgentState) -> dict:
    """
    Node 3: Compiles the final shopping list, finding the best price for each item.
    This is also a pure Python function.
    """
    print("---NODE: Compiling Shopping List---")
    search_results = state['store_search_results']
    missing = state['missing_items']
    
    # Group found items by the original ingredient name
    items_by_ingredient = {}
    for item in search_results:
        ingredient = item['ingredient']
        if ingredient not in items_by_ingredient:
            items_by_ingredient[ingredient] = []
        items_by_ingredient[ingredient].append(item)
        
    final_list_parts = []
    total_cost = 0

    # For each ingredient, find the cheapest option
    for ingredient, options in items_by_ingredient.items():
        best_option = min(options, key=lambda x: x['price'])
        part = (f"- {best_option['item'].title()}: ${best_option['price']:.2f} "
                f"({best_option['unit']}) at {best_option['store']}")
        final_list_parts.append(part)
        total_cost += best_option['price']

    # Assemble the final message
    shopping_list_str = "Here is your optimized shopping list:\n"
    shopping_list_str += "\n".join(final_list_parts)
    shopping_list_str += f"\n\nEstimated Total Cost: ${total_cost:.2f}"

    if missing:
        shopping_list_str += f"\n\nNote: I could not find prices for: {', '.join(missing)}."
        
    print(" > Final list generated.")
    return {"shopping_list": shopping_list_str}

def log_results_node(state: AgentState) -> None:
    """
    Node 4: Logs the final state of the agent run to our data sink.
    This is a "fire-and-forget" node; it doesn't return anything to update the state.
    """
    print("---NODE: Logging Results---")
    # The state dictionary is already a JSON-serializable format
    data_sink.write(state)
    # No return value needed as this is the final step
    return {}


# --- GRAPH ASSEMBLY ---

from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

# Add the nodes to the graph
workflow.add_node("identify_ingredients", identify_ingredients_node)
workflow.add_node("search_stores", search_stores_node)
workflow.add_node("compile_list", compile_shopping_list_node)
workflow.add_node("log_results", log_results_node)


# Define the sequence of operations
workflow.set_entry_point("identify_ingredients")
workflow.add_edge("identify_ingredients", "search_stores")
workflow.add_edge("search_stores", "compile_list")
workflow.add_edge("compile_list", "log_results")
workflow.add_edge("log_results", END) # <-- ADD THIS


# Compile the graph
graph = workflow.compile()