# projects/mexican_cooking_bot/agent.py
from . import config
from .agent_state import AgentState
from core_lib.llm_service import OpenAIService
from langgraph.graph import StateGraph, END

llm_service = OpenAIService(api_key=config.OPENAI_API_KEY)


def call_llm_node(state: AgentState) -> dict:
    """
    This is our first "node". It takes the current agent state,
    calls the LLM, and returns a dictionary with the updates to the state.
    """
    print("---NODE: Calling LLM---")

    # 1. Get the user's request from the state
    user_request = state['request']

    # 2. Call our LLM service with the request
    response_text = llm_service.invoke(
        prompt=user_request,
        model=config.DEFAULT_MODEL
    )

    # 3. Return a dictionary with the key 'response' to update that field in the state
    return {"response": response_text}

# 1. Create a new graph instance, telling it what our state looks like.
workflow = StateGraph(AgentState)

# 2. Add our function as a node in the graph. We give it a name, "llm_call".
workflow.add_node("llm_call", call_llm_node)

# 3. Define the "edges" or the path of the graph.
#    - set_entry_point: This tells the graph where to start. We start at our "llm_call" node.
#    - add_edge: This tells the graph what to do after a node is finished.
#      Here, after "llm_call" finishes, we go to a special node called END, which stops the graph.
workflow.set_entry_point("llm_call")
workflow.add_edge("llm_call", END)

# 4. Compile the workflow into a runnable graph object.
graph = workflow.compile()