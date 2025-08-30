# The Metrics & Evaluation System

This directory contains everything you need to understand your bot's performance, find its weaknesses, and make it smarter over time.

This guide will focus on our "dumb metrics" system, which is powered by the metrics_definition.yaml file.

## The Core Idea: "Configure, Don't Code"

Our philosophy is to make measuring your bot as easy as possible. You shouldn't have to be a software expert to get valuable insights.

For most common metrics, you just need to declare what you want to measure in the metrics_definition.yaml file. Our analytics engine will see your configuration and handle all the complicated calculation logic for you.
Think of the keys in your agent's final_state object as the raw ingredients. You just need to tell our factory which ingredients to use, and it will cook up the final report for you.
## "Easy Mode": Available Metric types in YAML
This is the fun part. Here are the pre-built metric "recipes" you can use in your metrics_definition.yaml file.

type: derive_path

This is for figuring out which major workflow or "path" your agent took. It's perfect for understanding the results of your routers and conditional logic.

What it does: It checks for the existence of certain keys in the final_state in the order you provide them. The first rule that matches wins.

Example:

```
Yaml
- name: agent_path
  description: "The primary logical path the agent took."
  type: derive_path
  paths:
    # Rule 1: If the 'shopping_list' key exists and isn't empty...
    - name: recipe_path
      if_field_exists: shopping_list
    # Rule 2: Otherwise, if the 'clarification_question' key exists...
    - name: clarification_path
      if_field_exists: clarification_question
    # Rule 3: If nothing else matched, use this as the default.
    - name: unknown_path
```

type: ratio

This is your go-to for calculating percentages, like success rates or accuracy scores.

What it does: It calculates numerator / denominator. You just need to tell it how to find those two numbers.

Example:

```
Yaml
- name: ingredient_find_rate_percent
  description: "% of identified ingredients that were successfully found."
  type: ratio
  numerator:
    # How to calculate the top number. Here, we're counting unique
    # values of the 'ingredient' key inside the 'store_search_results' list.
    type: count_unique_in_list
    field: store_search_results.ingredient
  denominator:
    # How to calculate the bottom number. Here, we're just counting
    # the total number of items in the 'ingredients_list'.
    type: count_list
    field: ingredients_list
  options:
    # Tell the engine to multiply the final result by 100.
    format_as_percent: true
    # To avoid a divide-by-zero error, what value should be returned
    # if the denominator is 0?
    on_zero_denominator: 100.0
```

Calculation Helpers
The ratio type uses other calculation types to find its numbers. You can use these on their own, too!
type: count_list
Counts the number of items in a list.

```
Yaml
- name: num_ingredients_identified
  type: count_list
  field: ingredients_list

type: count_unique_in_list
Counts the number of unique values for a specific key within a list of dictionaries. This is useful for when your agent might find the same item multiple times.

```
Yaml
- name: num_unique_items_found
  type: count_unique_in_list
  field: store_search_results.ingredient # Looks in the 'store_search_results' list for the 'ingredient' key

## "Minecraft Mode": The Custom Code Escape Hatch
What if you need a metric that's way too complex for YAML? No problem. We've got a "crafting table" for that.

If our engine detects a custom_metrics.py file in this directory, it will automatically load and run any custom metric classes you define there. You just need to follow a simple "contract."

The Contract (BaseMetric):
Your custom class must inherit from BaseMetric and implement a name, description, and calculate method.

Example (evaluation/custom_metrics.py):
```
<!-- Python -->
from core_library.metrics_base import BaseMetric # You'd import this

class MyCustomMetric(BaseMetric):
    @property
    def name(self) -> str:
        return "my_super_specific_metric"

    @property
    def description(self) -> str:
        return "A metric that does some crazy custom logic."

    def calculate(self, final_state: dict) -> float:
        # You have the full power of Python here!
        # Do whatever complex calculation you need.
        if final_state.get("some_key") == "some_value":
            return 100.0
        return 0.0
```
This gives you the best of both worlds: simple configuration for the easy stuff and unlimited power for the hard stuff.