# synthetic_users/evaluator.py
import sys
from pathlib import Path

# --- Path Hack ---
# We are adding the project's root directory to the Python path. 
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
# --- End Path Hack ---

from projects.mexican_groceries.agent import graph
from projects.mexican_groceries.evaluation.test_cases import TEST_CASES

from core_lib.data_sinks import JSONDataSink #JSON LOGGING


# --- LangChain Imports for Grader ---
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- Project Imports for Grader ---
# We need to import the Grade schema and the config for the API key
from projects.mexican_groceries.schemas import Grade
from projects.mexican_groceries import config

grader_llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, model=config.SMALL_MODEL)


log_file_path = project_root / "projects" / "mexican_groceries" / "logs" / "run_log.jsonl"
data_sink = JSONDataSink(log_path=log_file_path)


def grade_response(query: str, response_state: dict) -> dict:
    """
    Uses an LLM to grade the helpfulness of the agent's response.
    """
    print("--- Grader: Evaluating response ---")
    
    # Determine what the agent's final output was
    if response_state.get("shopping_list"):
        agent_output = response_state["shopping_list"]
    elif response_state.get("clarification_question"):
        agent_output = response_state["clarification_question"]
    else:
        agent_output = "The agent did not produce a final output."
    
    parser = JsonOutputParser(pydantic_object=Grade)
    
    prompt = PromptTemplate(
        template="""You are an expert evaluator for an AI cooking assistant.
        Your task is to grade the assistant's response based on the user's query.
        The user's query was: "{query}"
        The assistant's response was: "{response}"
        Evaluate whether the response was helpful and relevant. For example:
        If the user asked for a recipe and got a shopping list, that's helpful.
        If the user asked a vague question and the assistant asked a good clarifying question, that's helpful.
        If the user asked for a recipe and the assistant asked for clarification, that's NOT helpful.
        If the user's query was off-topic and the assistant tried to create a shopping list, that's NOT helpful.
        {format_instructions}
        """,
        input_variables=["query", "response"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
        )
    
    chain = prompt | grader_llm | parser
    
    try:
        grade = chain.invoke({"query": query, "response": agent_output})
        print(f" > Grade received: Score={grade['score']}, Reason='{grade['reason']}'")
        return grade
    except Exception as e:
        print(f"--- Grader: FAILED to evaluate response. Error: {e} ---")
        # Return a default failure grade
        return {"is_helpful": False, "reason": "Grader failed to execute.", "score": 0}

def run_evaluation():
    """
    Runs the full evaluation suite against the agent, now with AI-assisted grading.
    """
    print("--- evaluator.py: Starting Evaluation Suite (with AI Grader) ---")
    
    
    total_score = 0
    
    for i, case in enumerate(TEST_CASES):
        
        try:
        
            initial_state = {
            "request": case['query'],
            "intent": None,
            "ingredients_list": [],
            "store_search_results": [],
            "shopping_list": None,
            "missing_items": [],
            "clarification_question": None,
            "evaluation_grade": None,
            }

            # Invoke the graph with the complete initial state
            final_state = graph.invoke(initial_state)

            # --- NEW: Call the grader ---
            grade = grade_response(query=case['query'], response_state=final_state)
            
            # Add the grade to the final state before it gets logged
            final_state['evaluation_grade'] = grade

            data_sink.write(final_state)
            
            total_score += grade.get('score', 0)

            print("✅ Test case executed and graded.")
            
        except Exception as e:
            print(f"❌ Test case failed with an error: {e}")

    # --- NEW: Report the average score ---
    average_score = (total_score / len(TEST_CASES)) * 100 if TEST_CASES else 0
    
    print("\n\n========== Evaluation Summary ==========")
    print(f"Total test cases: {len(TEST_CASES)}")
    print(f"📈 Overall Helpfulness Score: {average_score:.2f}%")
    print("====================================")
    print("\nEvaluation complete. Check the log file for detailed graded results:")
    print("--> projects/mexican_cooking_bot/logs/run_log.jsonl")


if __name__ == "__main__":
    run_evaluation()