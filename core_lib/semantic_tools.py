from typing import List
# from langchain_core.language_models.chat_models import BaseChatModel

def find_best_match(query: str, options: List[str], llm_client) -> str | None:
    """
    Uses an LLM to find the best semantic match for a query within a list of options.

    Args:
        query: The item to search for (e.g., "chipotle in adobo").
        options: A list of available items to search within (e.g., ["corn tortillas", "chipotles in adobo"]).
        llm_client: An initialized LangChain chat model instance to use for the check.

    Returns:
        The best matching string from the options list, or None if no good match is found.
    """
    if not options:
        return None

    prompt = f"""You are a highly intelligent matching assistant. Your task is to find the best match for a given item in a list of available items.
    The user is looking for: "{query}"
    Here are the available items in the store:
    {options}
    Which of the available items is the correct match?
    If there is a clear match, return ONLY the name of the matching item from the list.
    If there is no good match, return the word "None".
    Do not add any other explanation or text.
    """

    try:
        response = llm_client.invoke(prompt)
        # The response content should be the matched item name or "None"
        result = response.content.strip()

        if result.lower() == 'none':
            return None
        
        # As a final check, ensure the LLM returned a valid option
        if result in options:
            return result
        else:
            # The LLM might hallucinate a slightly different name.
            # In this case, we'll consider it a failed match.
            return None

    except Exception as e:
        print(f"An error occurred during semantic matching: {e}")
        return None
        