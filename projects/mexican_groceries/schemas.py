# projects/mexican_cooking_bot/schemas.py
from pydantic import BaseModel, Field
from typing import List

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
    ingredients: List[Ingredient] = Field(description="The list of ingredients for the recipe.")