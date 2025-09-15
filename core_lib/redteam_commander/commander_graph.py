# core_library/redteam_commander/commander_graph.py
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List

# --- LangChain & LangGraph Imports ---
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import StateGraph, END

# --- Local Project Imports ---
from .commander_state import RedTeamCommanderState
from .codebase_analyzer import ingest_and_index_code_node
from .prompts import (
    DRAFT_DESCRIPTION_PROMPT,
    GENERATE_PERSONAS_PROMPT,
    GENERATE_SCENARIOS_PROMPT,
    ScenarioQueries
)

# ==============================================================================
# --- LLM and Parser Setup ---
# ==============================================================================
# We'll use a powerful model for the synthesis and generation tasks.
def get_llm_from_state(state: RedTeamCommanderState) -> ChatOpenAI:
    api_key = state.get('openai_api_key')
    model = state.get('default_model')
    if not api_key:
        raise ValueError("OpenAI API key not found in agent state.")
    return ChatOpenAI(api_key=api_key, model=model)

# ==============================================================================
# --- LangGraph Node Functions ---
# ==============================================================================

# We already have `ingest_and_index_code_node` from the other file.

def draft_capability_description_node(state: RedTeamCommanderState) -> Dict[str, Any]:
    """Uses the RAG index to generate a first draft of the agent's capabilities."""
    print("--- Node: Draft Capability Description ---")
    code_index = state["code_index"]
    
    retriever = code_index.as_retriever(search_kwargs={"k": 10}) # Get more context
    query = "What are the core capabilities, tools, and logical flows of this agent?"
    relevant_chunks = retriever.invoke(query)
    
    # Format the retrieved chunks into a single string for the prompt
    context_str = "\n---\n".join([chunk.page_content for chunk in relevant_chunks])
    
    prompt = PromptTemplate.from_template(DRAFT_DESCRIPTION_PROMPT)
    
    llm = get_llm_from_state(state)
    chain = prompt | llm | StrOutputParser()
    
    draft = chain.invoke({"context": context_str})
    
    return {"draft_description": draft}

def get_human_feedback_node(state: RedTeamCommanderState) -> Dict[str, Any]:
    """Pauses the graph and waits for the human user to provide feedback."""
    print("--- Node: Get Human Feedback ---")
    draft = state["draft_description"]
    
    print("\n==================[ AI Analysis Complete ]==================")
    print("I have analyzed the code. Here is my understanding of the agent:")
    print("------------------------------------------------------------")
    print(draft)
    print("------------------------------------------------------------")
    print("\nPlease review the description and questions above.")
    print("Provide any corrections, additions, or answers below.")
    print("Type 'confirm' on a new line when you are finished.")
    
    feedback_lines = []
    while True:
        line = input()
        if line.strip().lower() == 'confirm':
            break
        feedback_lines.append(line)
        
    feedback = "\n".join(feedback_lines)
    return {"human_feedback": feedback}

def finalize_context_node(state: RedTeamCommanderState) -> Dict[str, Any]:
    """Combines the draft and human feedback into a final context document."""
    print("--- Node: Finalize Context ---")
    # For now, we'll just append the feedback. A more advanced version could
    # use an LLM to intelligently merge the two.
    final_context = state["draft_description"] + "\n\n--- Human Feedback & Additions ---\n" + state["human_feedback"]
    return {"final_context": final_context}

def generate_personas_node(state: RedTeamCommanderState) -> Dict[str, Any]:
    """Generates a list of diverse user personas."""
    print("--- Node: Generate Personas ---")
    context = state["final_context"]
    prompt = PromptTemplate.from_template(GENERATE_PERSONAS_PROMPT)

    llm = get_llm_from_state(state)
    chain = prompt | llm | JsonOutputParser()
    
    personas = chain.invoke({"context": context})
    return {"generated_personas": personas}

def generate_scenarios_and_write_file_node(state: RedTeamCommanderState) -> Dict[str, Any]:
    """Generates test cases for each persona and writes the final Python file."""
    print("--- Node: Generate Scenarios & Write File ---")
    personas = state["generated_personas"]
    context = state["final_context"]
    
    all_test_cases = []
    
    parser = JsonOutputParser(pydantic_object=ScenarioQueries)

    prompt = PromptTemplate(
        template=GENERATE_SCENARIOS_PROMPT,
        input_variables=["persona_name", "persona_motivation", "persona_description", "context"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )


    llm = ChatOpenAI(#fix for json bug
        api_key=state.get("openai_api_key"),
        model="gpt-5-mini-2025-08-07",
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    chain = prompt | llm | JsonOutputParser()

    for i, persona in enumerate(personas):
        print(f" > Generating scenarios for persona {i+1}/{len(personas)}: {persona['name']}, \n{persona['motivation'][:50]}")
        
        queries = chain.invoke({
            "persona_name": persona['name'],
            "persona_motivation": persona['motivation'],
            "persona_description": persona['description'],
            "context": context
        })

        query_list = queries.get('queries', [])

        # Format into the structure our evaluator expects
        for query in query_list:
            all_test_cases.append({
                "case_id": f"{persona['name'].lower().replace(' ', '_')}_{i}",
                "persona": persona['name'],
                "query": query,
            })

    # --- Write the final file ---

    #get save path from the agents state
    target_config = state["target_config"]

    output_filepath_str = target_config.get("autogen_test_cases_filepath")
    if not output_filepath_str:
        raise ValueError("Configuration must provide 'autogen_test_cases_filepath'.")
    
    output_path = Path.cwd() / output_filepath_str

    file_content = "# THIS FILE IS AUTO-GENERATED BY THE RedTeamCommander\n\n"
    file_content += f"TEST_CASES = {json.dumps(all_test_cases, indent=4)}\n"
    
    with open(output_path, 'w') as f:
        f.write(file_content)
        
    print(f"--- ✅ Success! New test file written to {output_path} ---")
    return {"generated_test_cases_filepath": output_path}

# ==============================================================================
# --- Graph Assembly ---
# ==============================================================================

workflow = StateGraph(RedTeamCommanderState)

# Add all the nodes
workflow.add_node("ingest_and_index", ingest_and_index_code_node)
workflow.add_node("draft_description", draft_capability_description_node)
workflow.add_node("get_human_feedback", get_human_feedback_node)
workflow.add_node("finalize_context", finalize_context_node)
workflow.add_node("generate_personas", generate_personas_node)
workflow.add_node("generate_scenarios", generate_scenarios_and_write_file_node)

# Define the linear flow of the graph
workflow.set_entry_point("ingest_and_index")
workflow.add_edge("ingest_and_index", "draft_description")
workflow.add_edge("draft_description", "get_human_feedback")
workflow.add_edge("get_human_feedback", "finalize_context")
workflow.add_edge("finalize_context", "generate_personas")
workflow.add_edge("generate_personas", "generate_scenarios")
workflow.add_edge("generate_scenarios", END)

# Compile the final, runnable graph
commander_graph = workflow.compile()