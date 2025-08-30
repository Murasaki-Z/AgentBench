# core_library/semantic_tools.py
from typing import List, Dict

# --- Third-Party Imports ---
from pydantic import BaseModel, Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate

# ==============================================================================
# --- PYDANTIC SCHEMAS FOR STRUCTURED OUTPUT ---
# ==============================================================================

class Match(BaseModel):
    """A Pydantic model for a single successful match."""
    original_query: str = Field(description="The original item the user was searching for.")
    matched_item: str = Field(description="The corresponding item found in the store's inventory list.")

class MatchList(BaseModel):
    """A Pydantic model for a list of successful matches."""
    matches: List[Match] = Field(description="A list of successful matches found.")

# ==============================================================================
# --- SEMANTIC MATCHING TOOLS ---
# ==============================================================================

def find_best_matches_batched(
    queries: List[str],
    options: List[str],
    llm_client: BaseChatModel
) -> Dict[str, str]:
    """
    Uses an LLM to find the best semantic matches for a batch of queries
    within a list of options.

    Args:
        queries: The list of items to search for (e.g., ["chipotle in adobo", "green onion"]).
        options: A list of available items to search within.
        llm_client: An initialized LangChain chat model instance.

    Returns:
        A dictionary mapping the original query to its best matched item.
        Items with no good match are excluded.
    """
    if not queries or not options:
        return {}

    parser = JsonOutputParser(pydantic_object=MatchList)

    prompt = PromptTemplate(
        template="""
    You are a highly intelligent matching assistant. Your task is to find the best
    match for each item in a given list ('Items to Find') from a list of
    available items ('Available Items').

    - For each item in 'Items to Find', find the single best match from 'Available Items'.
    - A good match can be a pluralization, a minor typo, or a very close semantic equivalent.
    - If you find a good match, you must include it in your response.
    - If an item has absolutely no good match in the 'Available Items' list,
    you should simply omit it from your response. Do not guess.

    Available Items:
    {options}

    Items to Find:
    {queries}

    {format_instructions}
        """,
        input_variables=["queries", "options"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm_client | parser

    try:
        response = chain.invoke({"queries": queries, "options": options})
        # The response is a dict like {'matches': [{'original_query': '...', 'matched_item': '...'}]}
        # We convert this list of dicts into a simple mapping dict for easy lookup.
        match_map = {
            match['original_query']: match['matched_item']
            for match in response.get('matches', [])
        }
        return match_map
    except Exception as e:
        print(f"An error occurred during batched semantic matching: {e}")
        return {}

# Note: The old `find_best_match` function is now obsolete and has been removed.