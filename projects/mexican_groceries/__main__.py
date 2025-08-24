# projects/mexican_cooking_bot/__main__.py
from .agent import graph

def main():
    print("--- Mexican Cooking Bot (Tool-Using Edition) ---")

    # A task-oriented prompt for our agent
    prompt = "I want to make some chicken tinga for tacos. What do I need to buy?"

    print(f"\n> Invoking graph with request: '{prompt}'")

    initial_state = {"request": prompt}

    # Run the graph
    final_state = graph.invoke(initial_state)

    print("\n✅ --- Graph Execution Complete --- ✅")
    print("\n< FINAL AGENT OUTPUT >")
    print(final_state['shopping_list'])
    
    # Optional: You can uncomment this to see the full final state
    # import json
    # print("\n< FULL FINAL STATE >")
    # print(json.dumps(final_state, indent=2))
    
    # --- Generate Visualization ---
    print("\n> Generating graph visualization...")
    try:
        image_bytes = graph.get_graph().draw_png()
        with open("graph_visualization.png", "wb") as f:
            f.write(image_bytes)
        print("... Visualization saved to 'graph_visualization_v2.png'")
    except Exception as e:
        print(f"!!! Could not generate visualization. Error: {e}")

if __name__ == "__main__":
    main()