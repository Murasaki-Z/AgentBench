# projects/mexican_cooking_bot/agent.py
import json
from pathlib import Path

# --- LangChain Core Imports ---
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- Local Project Imports ---
from . import config
from .agent_state import AgentState
from .schemas import Recipe # <-- Import our new Pydantic schema
from core_lib.data_sinks import JSONDataSink

# --- SERVICE and DATA LOADING ---

llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, model=config.DEFAULT_MODEL)

def load_store_data():
    data_path = Path(__file__).parent / "data"
    with open(data_path / "mexican_store.json") as f:
        mexican_store_data = json.load(f)
    with open(data_path / "produce_store.json") as f:
        produce_store_data = json.load(f)
    return mexican_store_data, produce_store_data

MEXICAN_STORE, PRODUCE_STORE = load_store_data()

# --- DATA SINK SETUP ---
log_file_path = Path(__file__).parent / "logs" / "run_log.jsonl"
data_sink = JSONDataSink(log_path=log_file_path)


# --- AGENT NODES ---

def identify_ingredients_node(state: AgentState) -> dict:
    """
    Node 1 Uses an LLM with an Output Parser to identify and
    normalize ingredients into a structured format.
    """
    print("---NODE: Identifying Ingredients (V2 with Parser)---")
    user_request = state['request']

    # 1. Create an instance of our parser, linked to our Pydantic schema
    parser = JsonOutputParser(pydantic_object=Recipe)

    # 2. Create a new, more detailed prompt template
    prompt = PromptTemplate(
        template="""
You are an expert Mexican chef and grocery list assistant.
A user wants to make a dish. Your task is to identify the core ingredients.

For each ingredient, you MUST normalize its name to a common, base form that would be found in a store's inventory system.
For example:
- "chipotle peppers in adobo" should be normalized to "chipotles in adobo".
- "chicken breasts" should be normalized to "chicken breast".

User's request: "{request}"

{format_instructions}
""",
        input_variables=["request"],
        # 3. The magic! We inject the parser's formatting instructions into the prompt.
        # This tells the LLM exactly how to format the JSON output.
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # 4. Create the processing chain using LangChain Expression Language (LCEL)
    chain = prompt | llm | parser

    # 5. Invoke the chain with the user's request
    response = chain.invoke({"request": user_request})

    # The 'response' is now a dictionary that matches our Recipe schema
    # We extract just the list of normalized names for the next step.
    normalized_ingredients = [i['normalized_name'] for i in response['ingredients']]

    print(f" > Normalized ingredients identified: {normalized_ingredients}")
    return {"ingredients_list": normalized_ingredients}

def search_stores_node(state: AgentState) -> dict:
    """Node 2: Takes the ingredient list and searches both store JSON files."""
    print("---NODE: Searching Stores---")
    ingredients = state['ingredients_list']
    found_items = []
    missing_items = []

    for ingredient in ingredients:
        item_found_in_a_store = False
        for item in MEXICAN_STORE:
            if ingredient.lower() in item['item'].lower():
                found_items.append({"ingredient": ingredient, "store": "Mexican Store", **item})
                item_found_in_a_store = True
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
    """Node 3: Compiles the final shopping list, finding the best price."""
    print("---NODE: Compiling Shopping List---")
    
    search_results = state['store_search_results']
    missing = state['missing_items']
    items_by_ingredient = {}
    for item in search_results:
        ingredient = item['ingredient']
        if ingredient not in items_by_ingredient:
            items_by_ingredient[ingredient] = []
        items_by_ingredient[ingredient].append(item)
    final_list_parts = []
    total_cost = 0
    for ingredient, options in items_by_ingredient.items():
        best_option = min(options, key=lambda x: x['price'])
        part = (f"- {best_option['item'].title()}: ${best_option['price']:.2f} "
                f"({best_option['unit']}) at {best_option['store']}")
        final_list_parts.append(part)
        total_cost += best_option['price']
    shopping_list_str = "Here is your optimized shopping list:\n"
    shopping_list_str += "\n".join(final_list_parts)
    shopping_list_str += f"\n\nEstimated Total Cost: ${total_cost:.2f}"
    if missing:
        shopping_list_str += f"\n\nNote: I could not find prices for: {', '.join(missing)}."
    print(" > Final list generated.")
    return {"shopping_list": shopping_list_str}

def log_results_node(state: AgentState) -> None:
    """Node 4: Logs the final state of the agent run."""
    print("---NODE: Logging Results---")
    data_sink.write(state)
    return {}

# --- GRAPH ASSEMBLY ---
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)
workflow.add_node("identify_ingredients", identify_ingredients_node)
workflow.add_node("search_stores", search_stores_node)
workflow.add_node("compile_list", compile_shopping_list_node)
workflow.add_node("log_results", log_results_node)
workflow.set_entry_point("identify_ingredients")
workflow.add_edge("identify_ingredients", "search_stores")
workflow.add_edge("search_stores", "compile_list")
workflow.add_edge("compile_list", "log_results")
workflow.add_edge("log_results", END)
graph = workflow.compile()