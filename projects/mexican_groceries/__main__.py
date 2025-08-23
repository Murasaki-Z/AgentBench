# projects/mexican_cooking_bot/__main__.py
import json
from .agent import graph

def main():
    print("--- Mexican Cooking Bot (LangGraph Edition) ---")


    print("\n> Generating graph visualization...")
    try:
        # Get the graph structure as a PNG image
        image_bytes = graph.get_graph().draw_png()

        # Save the image to a file
        with open("graph_visualization.png", "wb") as f:
            f.write(image_bytes)
        print("... Visualization saved to 'graph_visualization.png'")
    except Exception as e:
        print(f"!!! Could not generate visualization. Make sure Graphviz is installed. Error: {e}")
    # --- END NEW ---

    # Define a test prompt.
    prompt = "What are the three most essential ingredients in Mexican cooking?"

    print(f"\n> Invoking graph with request: '{prompt}'")

    # The input to a graph is a dictionary where keys match the fields in our AgentState.
    initial_state = {"request": prompt}

    # The .invoke() method runs the graph from the entry point to the end.
    final_state = graph.invoke(initial_state)

    print("\n< Final State Received:")
    # Pretty-print the dictionary for readability
    print(json.dumps(final_state, indent=2))

    print("\n--- Run Complete ---")


if __name__ == "__main__":
    main()