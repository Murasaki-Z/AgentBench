# synthetic_users/evaluator.py
import sys
from pathlib import Path

# --- Path Hack ---
# This is a common pattern in Python scripting. We are adding the project's
# root directory to the Python path. This allows us to import modules
# from 'core_library' and 'projects' as if we were running the script
# from the root directory.
# __file__ is the path to this current script.
# .resolve() makes it an absolute path.
# .parents[1] goes up one level (from synthetic_users/ to the root).
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
# --- End Path Hack ---

# Now we can import from our other project modules
from projects.mexican_groceries.agent import graph
from projects.mexican_groceries.evaluation.test_cases import TEST_CASES

def run_evaluation():
    """
    Runs the full evaluation suite against the agent.
    """
    print("---  evaluator.py: Starting Evaluation Suite ---")
    print(f"Found {len(TEST_CASES)} test cases to run.")

    success_count = 0
    fail_count = 0

    # Loop through each defined test case
    for i, case in enumerate(TEST_CASES):
        print(f"\n----- Running Test Case {i+1}/{len(TEST_CASES)} -----")
        print(f"ID: {case['case_id']}")
        print(f"Persona: {case['persona']}")
        print(f"Query: \"{case['query']}\"")
        print("-----------------------------------------")

        try:
            # Prepare the initial state for the graph
            initial_state = {"request": case['query']}

            # Invoke the agent graph with the test case query
            # The graph will automatically run its course, including the logging node
            final_state = graph.invoke(initial_state)

            print("✅ Test case executed successfully.")
            print("Final Shopping List:")
            print(final_state.get('shopping_list', 'N/A'))
            success_count += 1

        except Exception as e:
            # If any part of the graph execution fails, we catch it here
            print(f"❌ Test case failed with an error: {e}")
            fail_count += 1

    # Print a final summary of the test run
    print("\n\n========== Evaluation Summary ==========")
    print(f"Total test cases: {len(TEST_CASES)}")
    print(f"✅ Successes: {success_count}")
    print(f"❌ Failures: {fail_count}")
    print("====================================")
    print("\nEvaluation complete. Check the log file for detailed results:")
    print("--> projects/mexican_cooking_bot/logs/run_log.jsonl")


if __name__ == "__main__":
    run_evaluation()