# How to Measure Your Bot's Performance

Welcome! This is your guide to using the `metrics_definition.yaml` file, which is the control panel for measuring how well your AI agent is doing.

You don't need to write any code. This guide will show you how to set up "dumb metrics"—simple, objective measurements that give you a clear, unbiased view of your bot's performance.

## The Big Idea: Tell Us What to Measure

Your agent produces a data record (called the `final_state`) every time it runs. To create a metric, you just need to tell our system which piece of data to look at in that record.

---

### **Step 1: Know Your Data (What's in the `final_state`?)**

Before you can measure anything, you need to know what data is available. The best way to see this is to look at your `production_log.jsonl` or `local_run_log.jsonl` file.

Each line in the log is a complete record of a single agent run. Here is an example of what the `final_state` for our Mexican Cooking Bot looks like after a successful run:

**Example `final_state` Payload:**
```json
{
  "request": "I want to make chicken tinga",
  "intent": "recipe_request",
  "ingredients_list": [
    "chicken breast",
    "tomatoes",
    "onion",
    "chipotles in adobo"
  ],
  "store_search_results": [
    {
      "ingredient": "chicken breast",
      "store": "Produce Store",
      "item": "chicken breast",
      "price": 5.99,
      "unit": "lb"
    },
    {
      "ingredient": "onion",
      "store": "Produce Store",
      "item": "onion",
      "price": 0.99,
      "unit": "lb"
    },
    {
      "ingredient": "chipotles in adobo",
      "store": "Mexican Store",
      "item": "chipotles in adobo",
      "price": 2.99,
      "unit": "can"
    }
  ],
  "shopping_list": "Here is your optimized shopping list...",
  "missing_items": [
    "tomatoes"
  ],
  "clarification_question": null
}
```

**Use this as your menu.** The `field` names in your metric definitions below should match the keys from this JSON object (e.g., `ingredients_list`, `store_search_results`).

---

### **Step 2: Choose Your Metric Types**

Now that you know what data you have, you can pick the right calculator for the job. Here are the pre-built metric calculators you can use.

#### `type: derive_path`

**Use this to:** Figure out which main path or workflow your agent took. This is great for tracking how often your bot succeeds vs. asks for clarification.
It is a fantastic tool for behavioural analysis, a near-substitute for Clickstream.

**Example:**
```yaml
- name: agent_path
  type: derive_path
  paths:
    # Based on our example payload, the 'shopping_list' key exists,
    # so this rule would match and the metric value would be 'recipe_path'.
    - name: recipe_path
      if_field_exists: shopping_list

    - name: clarification_path
      if_field_exists: clarification_question
```

---

#### `type: count_list`

**Use this to:** Count the total number of items in a list.

**Example:**
```yaml
- name: num_ingredients_identified
  type: count_list
  # This will look at our example payload and count the items in the
  # 'ingredients_list'. The result would be 4.
  field: ingredients_list
```

---

#### `type: count_unique_in_list`

**Use this to:** Count the unique items in a list of objects.

**Example:**
```yaml
- name: num_unique_items_found
  type: count_unique_in_list
  # This looks at the 'store_search_results' list in our payload.
  # It then looks at the 'ingredient' key for each object inside that list.
  # The result would be 3 (chicken breast, onion, chipotles in adobo).
  field: store_search_results.ingredient
```

---

#### `type: ratio`

**Use this to:** Calculate percentages, like a success rate. This type works by combining other calculators.

**Example:**
```yaml
- name: ingredient_find_rate_percent
  type: ratio
  numerator:
    # This will calculate 'num_unique_items_found' from the example above. Result: 3
    type: count_unique_in_list
    field: store_search_results.ingredient
  denominator:
    # This will calculate 'num_ingredients_identified'. Result: 4
    type: count_list
    field: ingredients_list
  options:
    # The final result will be (3 / 4) * 100 = 75.0
    format_as_percent: true
    on_zero_denominator: 100.0
```

By first looking at your data payload and then using these building blocks, you can create a comprehensive and objective view of your agent's performance.

