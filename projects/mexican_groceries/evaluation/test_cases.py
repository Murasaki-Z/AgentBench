# projects/mexican_cooking_bot/evaluation/test_cases.py

"""
This file contains the test cases for evaluating the mexican_cooking_bot.
Each test case is a dictionary representing a specific scenario.
"""

TEST_CASES = [
    {
        "case_id": "happy_path_1",
        "persona": "Standard User",
        "query": "I want to make chicken tinga. What do I need?",
    },
    {
        "case_id": "complex_request_1",
        "persona": "Ambitious Cook",
        "query": "I'm planning a party. I need to buy ingredients for carnitas and also get some avocados and limes for a side of guacamole.",
    },
    {
        "case_id": "edge_case_missing_item_1",
        "persona": "Adventurous Eater",
        "query": "What ingredients do I need for beef barbacoa?",
        # We know "beef" is not in our stores, so this tests the missing item logic.
    },
    {
        "case_id": "bug_repro_name_mismatch_1",
        "persona": "Bug Hunter",
        "query": "I need to make a salsa. I'll need tomatoes, cilantro, and some green onions.",
        # This specifically tests the "green onions" vs "onion" mismatch we identified.
    },
    {
        "case_id": "ambiguous_request_1",
        "persona": "Confused User",
        "query": "Hello, can you help me? i dont need anything this is a test case. apple.",
    }, 
    {
        "case_id": "test_cost_estimation_behaviour",
        "persona": "Spendthrift",
        "query": "I am taking revenge on my boss, I need to cater for 50 people, however give me the most expensive items possible for a mexican buffet",
    },  
    {
        "case_id": "off_topic_1_orange_ceiling",
        "persona": "Off-topic User",
        "query": "I think orange would have been a better color for my ceiling.",
    }
]