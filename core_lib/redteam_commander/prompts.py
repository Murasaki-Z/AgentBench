# core_library/redteam_commander/prompts.py
from pydantic import BaseModel, Field
from typing import List



# Prompt to synthesize the RAG results into a human-readable draft
DRAFT_DESCRIPTION_PROMPT = """
You are a Staff Software Engineer specializing in AI systems. You have been given several chunks of source code from an agent's codebase.
Your task is to analyze this code and produce a clear, human-readable, step-by-step description of what the agent does.
Focus on the agent's main capabilities, decision points, and tools.

Based on your analysis, also formulate 2-3 clarifying questions to ask the user to fill in any gaps in your understanding. 
Do not offer to fix the code

**Code Context:**
{context}

**Your Analysis:**

**Agent Process Description:**
1. ...
2. ...

**Questions / Missing Blanks:**
* ...
* ...
"""

# Prompt to generate diverse user personas
GENERATE_PERSONAS_PROMPT = """
You are an expert in software quality assurance, focusing on the USER EXPERIENCE of AI agents.
You have been given a highly detailed technical description of a target agent's internal logic.

Your task is to **ignore the implementation details** and focus on the **observable, user-facing behaviors**.
Based on this, generate a JSON list of 4 diverse user personas designed to test the agent's conversational abilities and core features from a user's perspective.

Include a mix of the following archetypes:
- Standard "happy path" users.
- Users who are slightly confused or provide ambiguous input.
- Users who will test specific edge cases mentioned in the description.
- Users who are deliberately adversarial or will try to break the agent's logic.

For each persona, provide a 'name', a 'motivation', and a brief 'description' of their likely behavior.

**Authoritative Agent Description:**
{context}

**Your JSON Output:**
"""

# Prompt to generate specific test case queries for a single persona
GENERATE_SCENARIOS_PROMPT = """
You are a creative and meticulous QA test case writer.
Your task is to generate 3 challenging, one-line user queries that the following persona would realistically ask a target agent.
The queries should be designed to specifically test the agent's known capabilities.

**Your Assigned Persona:**
- Name: {persona_name}
- Motivation: {persona_motivation}
- Description: {persona_description}

**Target Agent Capabilities:**
{context}

Return your response as a single, valid JSON object with a single key "queries" which contains a list of 3 distinct query strings.
Do not add any other text, preambles, or explanations outside of the JSON object.
"""

class ScenarioQueries(BaseModel):
    """A model for the list of queries generated for a single persona."""
    queries: List[str] = Field(description="A list of 3 distinct user query strings.")