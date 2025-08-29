# synthetic_users/e2e_evaluator.py
import sys
import asyncio
from pathlib import Path

# Path Hack
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# LangChain & Project Imports
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from projects.mexican_groceries.schemas import Grade
from projects.mexican_groceries import config
from projects.mexican_groceries.evaluation.test_cases import TEST_CASES
from core_lib.data_sinks import JSONDataSink
from synthetic_users.e2e_client import E2EDiscordClient

# --- Global Services ---
grader_llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, model=config.SMALL_MODEL)
log_file_path = project_root / "projects" / "mexican_cooking_bot" / "logs" / "e2e_run_log.jsonl"
data_sink = JSONDataSink(log_path=log_file_path)

async def grade_response(query: str, bot_reply: str) -> dict:
    # This function is unchanged
    print("--- Grader: Evaluating response ---")
    agent_output = bot_reply
    parser = JsonOutputParser(pydantic_object=Grade)
    prompt = PromptTemplate(
        template="""You are an expert evaluator... {format_instructions}""",
        input_variables=["query", "response"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | grader_llm | parser
    try:
        grade = await chain.ainvoke({"query": query, "response": agent_output})
        print(f" > Grade received: Score={grade['score']}, Reason='{grade['reason']}'")
        return grade
    except Exception as e:
        print(f"--- Grader: FAILED to evaluate response. Error: {e} ---")
        return {"is_helpful": False, "reason": "Grader failed to execute.", "score": 0}

async def run_evaluation():
    """
    Runs the full E2E evaluation suite against the LIVE Discord bot.
    """
    print("--- e2e_evaluator.py: Starting E2E Evaluation Suite ---")
    print(f"Found {len(TEST_CASES)} test cases to run.")
    
    total_score = 0
    
    for i, case in enumerate(TEST_CASES):
        print(f"\n----- Running Test Case {i+1}/{len(TEST_CASES)} -----")
        print(f"ID: {case['case_id']}")
        print(f"Persona: {case['persona']}")
        print(f"Query: \"{case['query']}\"")
        print("-----------------------------------------")
        
        # --- THE FIX: Instantiate a new client for each test run ---
        # This ensures each test starts with a fresh, clean connection state.
        e2e_client = E2EDiscordClient(
            token=config.DISCORD_BOT_TOKEN,
            test_channel_id=int(config.DISCORD_TEST_CHANNEL_ID)
        )
        
        bot_reply = await e2e_client.send_and_wait_for_reply(
            message_content=f"Mexican Cooking Bot {case['query']}",
            timeout=45 # seconds
        )
        
        if bot_reply is None:
            print("❌ Test case failed: Bot did not reply in time.")
            grade = {"is_helpful": False, "reason": "Timeout: Bot failed to reply.", "score": 0}
        else:
            print("✅ Bot replied.")
            grade = await grade_response(query=case['query'], bot_reply=bot_reply)

        log_entry = { "test_case": case, "bot_reply": bot_reply, "evaluation_grade": grade }
        data_sink.write(log_entry)
        total_score += grade.get('score', 0)

    average_score = (total_score / len(TEST_CASES)) * 100 if TEST_CASES else 0
    
    print("\n\n========== E2E Evaluation Summary ==========")
    print(f"Total test cases: {len(TEST_CASES)}")
    print(f"📈 Overall Helpfulness Score: {average_score:.2f}%")
    print("==========================================")
    print("\nE2E Evaluation complete. Check the new log file for detailed results:")
    print(f"--> {log_file_path}")

if __name__ == "__main__":
    print("--- IMPORTANT ---")
    print("Make sure your live bot is RUNNING in a separate terminal before you start this.")
    asyncio.run(run_evaluation())