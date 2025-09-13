# projects/mexican_cooking_bot/schemas.py
from pydantic import BaseModel, Field
from typing import List, Literal

class Ingredient(BaseModel):
    """
    A Pydantic model for a single ingredient.
    This defines the structure we expect for each item.
    """
    name: str = Field(description="The common name of the ingredient, e.g., 'onion' or 'avocado'.")
    normalized_name: str = Field(description="The name of the ingredient, normalized to match a store's inventory. For example, 'chipotle peppers in adobo' should be normalized to 'chipotle in adobo'.")

class Recipe(BaseModel):
    """
    A Pydantic model for a recipe, which is a list of ingredients.
    This is the top-level object we want the LLM to return.
    """
    dish_name: str = Field(description="The common, canonical name of the dish requested by the user, e.g., 'Chicken Tinga' or 'Carnitas'.")
    ingredients: List[Ingredient] = Field(description="The list of ingredients for the recipe.")

class Grade(BaseModel):
    """
    A Pydantic model for the grader's evaluation of an agent's response.
    """
    is_helpful: bool = Field(description="True if the response is helpful and relevant to the user's query, False otherwise.")
    reason: str = Field(description="A brief, one-sentence explanation for the grade.")
    score: Literal[0, 1] = Field(description="A binary score. 1 for helpful, 0 for not helpful.")

class Intent(BaseModel):
    """
    A Pydantic model for classifying the user's intent.
    """
    intent: Literal["recipe_request", "off_topic", "ambiguous"] = Field(
        description="The classified intent of the user's request."
    )
    reason: str = Field(description="A brief, one-sentence explanation for the classification.")