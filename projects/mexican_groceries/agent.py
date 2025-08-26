# projects/mexican_cooking_bot/agent.py
import json
from pathlib import Path

from itertools import chain


# --- LangChain Core Imports ---
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- Local Project Imports ---
from . import config
from .agent_state import AgentState
from .schemas import Recipe, Intent
from core_lib.semantic_tools import find_best_match


# --- SERVICE and DATA LOADING ---

llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, model=config.DEFAULT_MODEL)

llm_small = ChatOpenAI(api_key=config.OPENAI_API_KEY, model=config.SMALL_MODEL)

def load_store_data():

    data_path = Path(__file__).parent / "data"

    with open(data_path / "mexican_store.json") as f:
        mexican_store_data = json.load(f)

    with open(data_path / "produce_store.json") as f:
        produce_store_data = json.load(f)
    

    # Pre-process for easier lookup
    mexican_store_map = {item['item'].lower(): item for item in mexican_store_data}
    produce_store_map = {item['item'].lower(): item for item in produce_store_data}

    return mexican_store_map, produce_store_map

MEXICAN_STORE, PRODUCE_STORE = load_store_data()
ALL_STORE_ITEMS = list(MEXICAN_STORE.keys()) + list(PRODUCE_STORE.keys())


# --- AGENT NODES ---

def classify_intent_node(state: AgentState) -> dict:
    """
    Node: Classifies the user's intent to decide on the overall workflow.
    """
    print("---NODE: Classifying Intent---")
    user_request = state['request']

    print(f"Request: {user_request}" )

    parser = JsonOutputParser(pydantic_object=Intent)

    prompt = PromptTemplate(
        template="""You are an expert at classifying user requests for a Mexican cooking bot.
        You speak English but can speak other languages
    Your goal is to determine the user's intent from their message.
    The available intents are: "recipe_request", "off_topic", "ambiguous".
    "recipe_request": The user is asking for a recipe, a shopping list, or ingredients for a specific dish.
    "off_topic": The user is asking about something completely unrelated to cooking, recipes, or groceries.
    "ambiguous": The user's request is related to food but is too vague to be a specific recipe request (e.g., "tacos", "help me").
    User's request: "{request}"
    {format_instructions}
    """,
    input_variables=["request"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm_small | parser
    
    try:
        response = chain.invoke({"request": user_request})
        intent = response['intent']
        print(f" > Classified intent as: {intent}")
        return {"intent": intent}
    except Exception as e:
        print(f" > Failed to classify intent. Defaulting to ambiguous. Error: {e}")
        return {"intent": "ambiguous"}

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

def clarify_request_node(state: AgentState) -> dict:
    """
    Node: Asks the user for clarification if the initial request is ambiguous.
    """
    print("---NODE: Clarifying Request---")
    user_request = state['request']
    
    prompt = f"""You are a friendly and helpful cooking assistant for Mexican food.
    The user's request is too vague or off-topic for you to create a shopping list.
    Your task is to ask a polite, clarifying question to get the user back on track.
    Ask about what specific dish they would like to make. Speak the same language as user, default English
    User's request: "{user_request}"
    Your clarifying question:
    """
    response = llm_small.invoke(prompt)
    
    print(f" > Generated question: {response.content}")
    return {"clarification_question": response.content}


def search_stores_node(state: AgentState) -> dict:
    """
    Node 2 Searches stores using a hybrid approach.
    """
    print("---NODE: Searching Stores (V2 with Self-Correction)---")

    ingredients_to_find = state['ingredients_list']
    found_items = []
    missing_items = []

    for ingredient in ingredients_to_find:
        print(f"  - Searching for: '{ingredient}'")
        item_found = False

        # --- Step 1: Try simple, fast matching first ---
        for store_item_name, item_details in chain(MEXICAN_STORE.items(), PRODUCE_STORE.items()):
            if ingredient.lower() in store_item_name:
                store_name = "Mexican Store" if store_item_name in MEXICAN_STORE else "Produce Store"
                found_items.append({"ingredient": ingredient, "store": store_name, **item_details})
                item_found = True

        # --- Step 2: If simple matching fails, engage Self-Correction ---
        if not item_found:
            print(f"    > Simple search failed. Engaging LLM for semantic match...")
            # We pass the small, fast LLM client to our tool
            best_match = find_best_match(ingredient, ALL_STORE_ITEMS, llm_client= llm_small)

            if best_match:
                print(f"    > Semantic match found: '{ingredient}' -> '{best_match}'")
                if best_match in MEXICAN_STORE:
                    store_name = "Mexican Store"
                    item_details = MEXICAN_STORE[best_match]
                else:
                    store_name = "Produce Store"
                    item_details = PRODUCE_STORE[best_match]
                
                found_items.append({"ingredient": ingredient, "store": store_name, **item_details})
                item_found = True
            else:
                 print(f"    > Semantic match failed. Item not found.")

        if not item_found:
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
    
# --- CONDITIONAL ROUTER ---

def master_router(state: AgentState) -> str:
    """
    This is the master router. It directs the workflow based on the
    classified intent of the user's request.
    """
    print("---MASTER ROUTER---")
    intent = state.get("intent")

    if intent == "recipe_request":
        print(" > Decision: Intent is a recipe request. Routing to IDENTIFY_INGREDIENTS.")
        return "identify_ingredients"
    elif intent == "ambiguous":
        print(" > Decision: Intent is ambiguous. Routing to CLARIFY.")
        return "clarify"
    elif intent == "off_topic":
        print(" > Decision: Intent is off-topic. Routing to CLARIFY.")
        return "clarify"
    else:
        # A fallback case, though it should ideally not be reached
        print(" > Decision: No clear intent. Defaulting to CLARIFY.")
        return "clarify"

# --- GRAPH ASSEMBLY ---
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("identify_ingredients", identify_ingredients_node)
workflow.add_node("clarify_request", clarify_request_node)
workflow.add_node("search_stores", search_stores_node)
workflow.add_node("compile_list", compile_shopping_list_node)

workflow.set_entry_point("classify_intent")


# --- Add the Conditional Edge ---
# decide the main path
workflow.add_conditional_edges(
    "classify_intent",
    master_router,
    {
        "identify_ingredients": "identify_ingredients",
        "clarify": "clarify_request"
    }
)

workflow.add_edge("identify_ingredients", "search_stores")
workflow.add_edge("search_stores", "compile_list")
workflow.add_edge("compile_list", END)
workflow.add_edge("clarify_request", END)

graph = workflow.compile()