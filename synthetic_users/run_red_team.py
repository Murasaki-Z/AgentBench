# synthetic_users/run_red_team.py
"""
The main entry point for running the autonomous RedTeamCommander agent.

This script reads a configuration file, prepares the initial state, and
invokes the commander graph to generate a new suite of test cases.
"""
import yaml
import argparse
from pathlib import Path
import sys

# --- Path Hack ---
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# --- Import the compiled graph from our core library ---
from core_lib.redteam_commander.commander_graph import commander_graph

# Import the config for the API key
from projects.mexican_groceries import config as bot_config 


def main():
    """Main function to parse arguments and run the commander."""
    
    # 1. Set up the command-line argument parser
    parser = argparse.ArgumentParser(
        description="Run the autonomous RedTeamCommander to generate test cases."
    )
    
    default_config_path = (
        project_root
        / "projects"
        / "mexican_groceries"
        / "evaluation"
        / "red_team_config.yaml"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config_path,
        help="Path to the Red Team configuration YAML file."
    )
    
    args = parser.parse_args()
    
    # 2. Load the configuration file
    print(f"--- Loading Red Team config from: {args.config} ---")
    if not args.config.exists():
        print(f"--- FATAL ERROR: Configuration file not found at {args.config} ---")
        return
        
    with open(args.config, 'r') as f:
        target_config = yaml.safe_load(f)

    # 3. Prepare the initial state for the LangGraph graph
    initial_state = {
        "target_config": target_config
        , "openai_api_key": bot_config.OPENAI_API_KEY
        , "default_model": bot_config.DEFAULT_MODEL
    }
    
    # 4. Invoke the commander graph and let it run its course
    print("\n--- Invoking RedTeamCommander Graph ---")
    final_state = commander_graph.invoke(initial_state)
    
    # 5. Print a final summary message
    print("\n==================[ Red Team Run Complete ]==================")
    if final_state.get("generated_test_cases_filepath"):
        print("✅ Success!")
        print(f"A new test case file has been generated at:")
        print(f"   -> {final_state['generated_test_cases_filepath']}")
        print("\nYou can now rename this file to 'test_cases.py' to use it with the evaluators.")
    else:
        print("❌ The process finished, but no test case file was generated.")
    
    print("\n--- Generating graph visualization... ---")
    try:
        # Get the graph structure as a PNG image
        image_bytes = commander_graph.get_graph().draw_png()
        
        # Define the output path in the root of the project
        output_path = project_root / "red_team_commander_graph.png"
        
        # Save the image to a file
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"✅ Visualization saved successfully to: {output_path}")
    except Exception as e:
        print(f"---a WARNING: Could not generate visualization. ---")
        print(f"--- This usually means the 'graphviz' system package is not installed. ---")
        print(f"--- See: https://graphviz.org/download/ ---")
        print(f"--- Error details: {e} ---")

if __name__ == "__main__":
    main()